#!/usr/bin/env python3
"""Collector worker for the Daily Intel Brief.

Reads the durable source registry (analyst/meta/sources.json) plus a
short list of major wires, pulls the last 24 hours, normalises into
incidents tagged by region per references/regions.json, and writes
WORKING_DIR/raw/incidents.json.

This is a *reference implementation* of agents/collector.md. Subagents
that follow that prompt are free to do better, but this script gives a
deterministic floor and a hand-callable smoke test.

Heavy parsing (NER, geocoding, deduplication) is deliberately simple —
the analyst's prompt is robust to imperfect collector output, and the
24h window keeps the volume small.

Usage:

    python3 scripts/collect.py --working-dir <wd> \
        --regions skills/daily-intel-brief/references/regions.json \
        --sources analyst/meta/sources.json [--mock]

`--mock` short-circuits live network and writes a small canned dataset
into raw/incidents.json so the rest of the pipeline can be exercised.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any
from xml.etree import ElementTree as ET

WIRE_FEEDS = [
    # Major wires — used in addition to durable sources to top up regions.
    ("Reuters World", "https://www.reutersagency.com/feed/?best-topics=international"),
    ("AP World", "https://feeds.apnews.com/apf-WorldNews"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Reuters Business", "https://www.reutersagency.com/feed/?best-topics=business-finance"),
    ("FT World", "https://www.ft.com/world?format=rss"),
]

# Local-language / non-English feeds — added 2026-05-13 for multi-language collection.
# Tuple: (name, url, language_code, admiralty_rank)
# These provide region-specific narratives, local reporting, and alternative baselines.
# The collection model (DeepSeek V4 Flash) can handle multi-lingual content.
LOCAL_LANGUAGE_FEEDS = [
    # Persian / Farsi (Iran)
    ("Mehr News (English)", "https://en.mehrnews.com/rss", "en", ("C", 3)),
    ("Tasnim News (English)", "https://www.tasnimnews.com/en/rss", "en", ("C", 3)),
    # Arabic (Gulf / Middle East)
    ("Al Arabiya (English)", "https://english.alarabiya.net/feed/rss2/en.xml", "en", ("B", 2)),
    ("Al Arabiya (Arabic)", "https://www.alarabiya.net/tools/mrss", "ar", ("B", 2)),
    ("Asharq Al-Awsat (English)", "https://english.aawsat.com/rss.xml", "en", ("B", 2)),
    ("Asharq Al-Awsat (Arabic)", "https://aawsat.com/feeds/rss", "ar", ("B", 2)),
    # Russian
    ("TASS (English)", "https://tass.com/rss/v2.xml", "en", ("C", 3)),
    ("Meduza (English)", "https://meduza.io/rss/en/all", "en", ("B", 2)),
    ("Meduza (Russian)", "https://meduza.io/rss/all", "ru", ("B", 2)),
    ("Moscow Times", "https://www.themoscowtimes.com/rss/news", "en", ("B", 2)),
    ("Kommersant (Russian)", "https://www.kommersant.ru/RSS/main.xml", "ru", ("C", 3)),
    # Chinese
    ("Xinhua (English)", "http://www.xinhuanet.com/english/rss/worldrss.xml", "en", ("C", 3)),
    ("Global Times (English)", "https://www.globaltimes.cn/rss", "en", ("C", 3)),
    ("CGTN (English)", "https://www.cgtn.com/subscribe/rss.html", "en", ("C", 3)),
    # Israeli / Hebrew
    ("Haaretz (English)", "https://www.haaretz.com/srv/haaretz-latest-news-xml", "en", ("B", 2)),
    ("Ynet (Hebrew)", "https://www.ynet.co.il/Integration/StoryRss2.xml", "he", ("B", 2)),
    ("Times of Israel", "https://www.timesofisrael.com/feed/", "en", ("B", 2)),
    ("Israel Hayom (Hebrew)", "https://www.israelhayom.co.il/rss", "he", ("C", 3)),
    # European
    ("Le Monde (English)", "https://www.lemonde.fr/en/rss/une.xml", "en", ("B", 2)),
    ("El País (English)", "https://feeds.elpais.com/mrss-s/pages/ep-english/site/elpais.com/portada", "en", ("B", 2)),
    # Asian
    ("Nikkei Asia", "https://asia.nikkei.com/rss/feed", "en", ("B", 2)),
    # Telegram — real-time OSINT
    ("judean_osint", "https://t.me/s/judean_osint", "en", ("C", 3)),
    ("HormuzMonitor", "https://t.me/s/HormuzMonitor", "en", ("C", 3)),
]

# Gmail intel digest — newsletters from Cipher Brief, Foreign Policy, etc.
NEWS_RAW_PATH = pathlib.Path("/home/ubuntu/.openclaw/workspace/tasks/news_raw.md")

DEFAULT_ADMIRALTY = ("B", 2)  # major wires default; downgrade for state media

USER_AGENT = "TrevorDailyBrief/1.0 (+https://github.com/trevormentis-spec/OpenClawTrevorMentis)"


def log(msg: str) -> None:
    ts = dt.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[collect {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def country_to_region(country: str, regions: dict) -> str | None:
    if not country:
        return None
    overrides = regions.get("country_to_region_overrides", {}) or {}
    if country in overrides:
        return overrides[country]
    for snake, payload in regions["regions"].items():
        if country in (payload.get("countries") or []):
            return snake
    return None


def fetch(url: str, timeout: int = 15) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            try:
                return data.decode("utf-8", errors="replace")
            except Exception:
                return None
    except Exception as exc:
        log(f"fetch failed for {url}: {exc}")
        return None


def parse_rss(xml_text: str, source_name: str, default_admiralty=DEFAULT_ADMIRALTY) -> list[dict]:
    """Very tolerant RSS/Atom parser. Returns a list of normalized items."""
    items: list[dict] = []
    if not xml_text:
        return items
    try:
        # Some feeds embed un-escaped XML; ElementTree is strict — try a
        # forgiving cleanup first.
        cleaned = re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", xml_text)
        root = ET.fromstring(cleaned)
    except ET.ParseError as exc:
        log(f"RSS parse error for {source_name}: {exc}")
        return items

    # RSS 2.0
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        items.append({
            "title": title, "link": link, "summary": desc, "pub": pub,
            "source": source_name, "admiralty": default_admiralty,
        })

    # Atom
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        link_el = entry.find("a:link", ns)
        link = (link_el.get("href") if link_el is not None else "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        pub = (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()
        if not title:
            continue
        items.append({
            "title": title, "link": link, "summary": summary, "pub": pub,
            "source": source_name, "admiralty": default_admiralty,
        })

    return items


COUNTRY_REGEX_CACHE: dict[str, re.Pattern] = {}


def detect_country(text: str, regions: dict) -> str | None:
    """Cheap country detection: longest matching country name in text."""
    if not text:
        return None
    text_l = text.lower()
    candidates: list[str] = []
    for region in regions["regions"].values():
        for c in region.get("countries", []):
            if not c:
                continue
            if c not in COUNTRY_REGEX_CACHE:
                COUNTRY_REGEX_CACHE[c] = re.compile(rf"\b{re.escape(c.lower())}\b")
            if COUNTRY_REGEX_CACHE[c].search(text_l):
                candidates.append(c)
    if not candidates:
        return None
    candidates.sort(key=len, reverse=True)
    return candidates[0]


def parse_pubdate(pub: str) -> str | None:
    if not pub:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            d = dt.datetime.strptime(pub, fmt)
            return d.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    return None


SECURITY_KEYWORDS = re.compile(
    r"\b(strike|attack|killed|wounded|missile|drone|sanction|coup|protest|"
    r"clashes|operation|raid|airstrike|shelling|siege|treaty|election|"
    r"summit|withdrawal|sovereign|default|downgrade|hijack|hostage|cyber|"
    r"ransomware|phishing|breach|cartel|trafficking|seize)\b",
    re.IGNORECASE,
)


def is_security_relevant(item: dict) -> bool:
    text = f"{item.get('title','')} {item.get('summary','')}"
    return bool(SECURITY_KEYWORDS.search(text))


def categorise(item: dict) -> str:
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    if any(k in text for k in ("strike", "missile", "shelling", "airstrike", "raid", "clashes", "casualt")):
        return "kinetic"
    if any(k in text for k in ("cyber", "ransomware", "phishing", "breach", "hack")):
        return "cyber"
    if any(k in text for k in ("vessel", "tanker", "ais", "ukmto", "maritime", "hijack")):
        return "maritime"
    if any(k in text for k in ("flight", "aircraft", "airspace", "ads-b", "no-fly")):
        return "aviation"
    if any(k in text for k in ("aid", "famine", "refugee", "humanitarian", "displaced")):
        return "humanitarian"
    if any(k in text for k in ("inflation", "rate", "fx", "yield", "default", "downgrade", "central bank", "imf")):
        return "economic"
    return "political"


def make_id(occurred: str, country: str, headline: str) -> str:
    h = hashlib.md5(f"{occurred}|{country}|{headline}".encode()).hexdigest()[:4]
    return f"i-{occurred[:10]}-{h}"


def parse_news_raw(path: pathlib.Path) -> list[dict]:
    """Parse news_raw.md into collector-compatible items.

    Handles two formats:
      1. Global News items (### Headline → Source/Summary/Link)
      2. Gmail intel digest (## Newsletter → key development bullets)
    """
    items: list[dict] = []
    if not path.exists():
        return items

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Format 1: ### Headline block
        if line.startswith("### ") and not line.startswith("#### "):
            headline = line[4:].strip()
            source = ""
            summary = ""
            link = ""
            j = i + 1
            while j < len(lines) and j < i + 10:
                s = lines[j].strip()
                if s.startswith("- **Source:**"):
                    source = s.split("**Source:**", 1)[-1].strip()
                elif s.startswith("- **Summary:**"):
                    summary = s.split("**Summary:**", 1)[-1].strip()
                elif s.startswith("- **Link:**"):
                    link = s.split("**Link:**", 1)[-1].strip()
                elif s.startswith("### ") or s.startswith("## "):
                    break
                j += 1
            if source:
                items.append({
                    "title": headline, "link": link,
                    "summary": summary, "pub": "",
                    "source": source.strip(),
                    "admiralty": ("B", 2),
                    "_bypass_filter": True,
                })
            i = j
            continue

        # Format 2: ## Newsletter section
        if line.startswith("## ") and "\u2014" in line:
            section_title = line[3:].strip()
            bullet_source = section_title.split("\u2014")[0].strip()
            j = i + 1
            bullets = []
            while j < len(lines):
                s = lines[j]
                if s.startswith("## ") and s != line:
                    break
                stripped = s.strip()
                if stripped.startswith("- ") and len(stripped) > 20:
                    if not any(stripped.startswith(x) for x in [
                        "- **Source:**", "- **Date:**", "- **Mentions:**"
                    ]):
                        bullets.append(stripped[2:].strip())
                j += 1
            for b in bullets:
                items.append({
                    "title": f"[Intel] {b[:120]}", "link": "",
                    "summary": f"{b} (via {section_title})",
                    "pub": "",
                    "source": bullet_source,
                    "admiralty": ("C", 2),
                    "_bypass_filter": True,
                })
            i = j
            continue

        i += 1

    log(f"news_raw: {len(items)} items ({len([x for x in items if x['admiralty'][0]=='B'])} global + {len([x for x in items if x['admiralty'][0]=='C'])} intel)")
    return items


def collect_live(regions: dict, sources: dict,
                  feeds_to_try: list[tuple[str, str]] | None = None
                  ) -> tuple[list[dict], list[str]]:
    raw: list[dict] = []
    gaps: list[str] = []
    durable = sources.get("durable_sources", []) or []
    if feeds_to_try is None:
        feeds_to_try = WIRE_FEEDS[:]
    # Durable sources without explicit feed URLs are skipped programmatically;
    # the collector subagent prompt explains how to do better with web_fetch
    # when a richer harness is available.
    for fname, furl in feeds_to_try:
        log(f"fetching {fname}")
        body = fetch(furl)
        if not body:
            gaps.append(f"feed unreachable: {fname}")
            continue
        raw.extend(parse_rss(body, fname))