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


def collect_live(regions: dict, sources: dict) -> tuple[list[dict], list[str]]:
    raw: list[dict] = []
    gaps: list[str] = []
    durable = sources.get("durable_sources", []) or []
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
    log(f"raw items: {len(raw)}")
    return raw, gaps


def normalise(items: list[dict], regions: dict, window_hours: int = 24) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=window_hours)
    out: list[dict] = []
    for it in items:
        if not is_security_relevant(it):
            continue
        country = detect_country(f"{it.get('title','')} {it.get('summary','')}", regions)
        region = country_to_region(country or "", regions) if country else None
        # Finance-relevant items without a country fall into global_finance
        if not region:
            text = f"{it.get('title','')} {it.get('summary','')}".lower()
            if any(k in text for k in ("inflation", "rate", "yield", "default", "downgrade", "central bank", "fx", "oil", "brent")):
                region = "global_finance"
        if not region:
            continue
        occurred = parse_pubdate(it.get("pub", "")) or now.isoformat().replace("+00:00", "Z")
        try:
            occ_dt = dt.datetime.fromisoformat(occurred.replace("Z", "+00:00"))
        except ValueError:
            occ_dt = now
        if occ_dt < cutoff:
            continue
        rel, cred = it["admiralty"]
        out.append({
            "id": make_id(occurred, country or region, it["title"]),
            "region": region,
            "country": country,
            "lat": None, "lon": None,
            "occurred_at_utc": occurred,
            "actors": [],
            "category": categorise(it),
            "headline": it["title"],
            "summary": (it.get("summary") or "")[:600],
            "sources": [{
                "name": it["source"],
                "url": it.get("link"),
                "admiralty_reliability": rel,
                "admiralty_credibility": cred,
                "retrieved_at_utc": now.isoformat().replace("+00:00", "Z"),
            }],
            "single_source": True,
            "confidence_collector": "medium",
        })
    return out


def deduplicate(items: list[dict]) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    for it in items:
        key = (it["region"], it.get("country"),
               it["headline"][:60].lower())
        if key not in by_key:
            by_key[key] = it
            continue
        existing = by_key[key]
        if it["sources"][0] not in existing["sources"]:
            existing["sources"].extend(it["sources"])
            existing["single_source"] = False
    return list(by_key.values())


def cap_per_region(items: list[dict], cap: int = 8) -> list[dict]:
    items.sort(key=lambda x: x["occurred_at_utc"], reverse=True)
    out: list[dict] = []
    counts: dict[str, int] = {}
    for it in items:
        c = counts.get(it["region"], 0)
        if c >= cap:
            continue
        counts[it["region"]] = c + 1
        out.append(it)
    return out


def mock_incidents(regions: dict) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    base = [
        ("europe", "Ukraine", 50.45, 30.52, "kinetic",
         "Drone strikes reported in Kyiv overnight"),
        ("europe", "United Kingdom", 51.50, -0.12, "political",
         "Government tables Russia sanctions extension bill"),
        ("asia", "Taiwan", 25.03, 121.56, "political",
         "Three PLA naval vessels enter ADIZ near Taipei"),
        ("asia", "Japan", 35.68, 139.69, "economic",
         "BOJ policy statement leaves rates unchanged"),
        ("middle_east", "Lebanon", 33.85, 35.50, "kinetic",
         "Reported IDF strike on Hezbollah depot in southern Beirut"),
        ("middle_east", "Iran", 35.69, 51.42, "political",
         "IRGC announces naval exercise in Strait of Hormuz"),
        ("north_america", "Mexico", 32.51, -117.04, "kinetic",
         "Cartel clash in Tijuana leaves multiple dead"),
        ("north_america", "United States", 38.90, -77.04, "political",
         "Senate vote scheduled on Israel security supplemental"),
        ("south_central_america", "Haiti", 18.59, -72.31, "humanitarian",
         "UN reports gang displacement in Port-au-Prince"),
        ("south_central_america", "Venezuela", 10.49, -66.88, "political",
         "Opposition rally banned ahead of regional election"),
        ("global_finance", None, None, None, "economic",
         "Brent crude up 3.2% on Hormuz exercise headlines"),
        ("global_finance", None, None, None, "economic",
         "10-year UST yield +12bp on hot CPI print"),
    ]
    out = []
    for i, (region, country, lat, lon, cat, headline) in enumerate(base):
        out.append({
            "id": f"i-mock-{i:04d}",
            "region": region, "country": country,
            "lat": lat, "lon": lon,
            "occurred_at_utc": now,
            "actors": [],
            "category": cat,
            "headline": headline,
            "summary": headline + " (mock data for dry-run; not from live wires).",
            "sources": [{
                "name": "Mock Wire",
                "url": "https://example.invalid/mock",
                "admiralty_reliability": "B",
                "admiralty_credibility": 2,
                "retrieved_at_utc": now,
            }],
            "single_source": True,
            "confidence_collector": "high",
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--regions", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--cap-per-region", type=int, default=8)
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    raw_dir = wd / "raw"; raw_dir.mkdir(parents=True, exist_ok=True)
    regions = load_json(pathlib.Path(args.regions))
    sources = load_json(pathlib.Path(args.sources))

    if args.mock:
        log("running in mock mode")
        incidents = mock_incidents(regions)
        gaps = ["mock mode: no live collection performed"]
    else:
        raw, gaps = collect_live(regions, sources)
        incidents = normalise(raw, regions)
        incidents = deduplicate(incidents)
        incidents = cap_per_region(incidents, cap=args.cap_per_region)

    out = {
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "window_hours": 24,
        "regions_covered": ["europe", "asia", "middle_east",
                            "north_america", "south_central_america",
                            "global_finance"],
        "incidents": incidents,
        "collection_gaps": gaps,
    }
    out_path = raw_dir / "incidents.json"
    out_path.write_text(json.dumps(out, indent=2))
    log(f"wrote {out_path} ({len(incidents)} incidents)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
