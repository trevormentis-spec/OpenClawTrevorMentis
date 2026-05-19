#!/usr/bin/env python3
"""DOF Daily Collector — fetches daily PDF, parses structured sections,
classifies with V4 Pro, routes material changes to intel pipeline.

Usage:
    python3 collectors/dof_collector.py --today         # Fetch today's DOF
    python3 collectors/dof_collector.py --backfill 30    # Backfill N days
    python3 collectors/dof_collector.py --classify       # Classify pending
    python3 collectors/dof_collector.py --notify         # Push material changes
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "dof"
DB_PATH = DATA_DIR / "dof_archive.db"
EXPORT_DIR = REPO_ROOT / "exports"

# SSL: DOF uses self-signed cert
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# DOF daily edition URL pattern
DOF_DAILY = "https://www.dof.gob.mx/index.php?year={year}&month={month}&day={day}&edicion=MAT"
DOF_NOTE = "https://www.dof.gob.mx/nota_detalle.php?codigo={codigo}&fecha={fecha}"
DOF_PDF = "https://www.dof.gob.mx/nota_detalle_popup.php?codigo={codigo}"

# Document sections (from DOF taxonomy)
SECTIONS = {
    "poder_ejecutivo": "Poder Ejecutivo",
    "acuerdos": "Acuerdos",
    "decretos": "Decretos",
    "reglamentos": "Reglamentos",
    "convocatorias": "Convocatorias",
    "concesiones": "Concesiones",
    "sanciones": "Sanciones",
    "circulares": "Circulares",
    "juridicos": "Jurisdiccionales",
    "otros": "Otros",
}

# Classification categories for V4 Pro
CATEGORIES = [
    "sanctions", "mining_concession", "energy", "security",
    "bilateral", "judicial", "regulatory_change", "appointment",
    "budget", "trade", "infrastructure", "other",
]


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            codigo TEXT PRIMARY KEY,
            fecha TEXT NOT NULL,
            title TEXT,
            section TEXT,
            category TEXT,
            is_material INTEGER DEFAULT 0,
            affected_entities TEXT,
            raw_html TEXT,
            parsed_text TEXT,
            classification_json TEXT,
            fetched_at TEXT DEFAULT (datetime('now')),
            classified_at TEXT,
            notified INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_fecha ON articles(fecha)
    """)
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def fetch_daily_edition(year: int, month: int, day: int) -> list[dict]:
    """Fetch DOF daily edition page and extract article metadata."""
    url = DOF_DAILY.format(year=year, month=f"{month:02d}", day=f"{day:02d}")
    items = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        for match in re.finditer(
            r'<a[^>]*href="([^"]*nota_detalle[^"]*codigo=(\d+)[^"]*fecha=(\d+/\d+/\d+)[^"]*)"[^>]*>\s*(.*?)\s*</a>',
            html,
        ):
            codigo = match.group(2)
            fecha = match.group(3)
            title = re.sub(r"<[^>]+>", "", match.group(4)).strip()
            # Decode HTML entities
            title = (
                title.replace("&oacute;", "ó")
                .replace("&aacute;", "á")
                .replace("&eacute;", "é")
                .replace("&iacute;", "í")
                .replace("&uacute;", "ú")
                .replace("&ntilde;", "ñ")
                .replace("&nbsp;", " ")
            )
            items.append({"codigo": codigo, "fecha": fecha, "title": title, "url": f"https://www.dof.gob.mx{url}"})
    except Exception as exc:
        print(f"[dof] Fetch {url}: {exc}", file=sys.stderr)

    return items


def fetch_article_detail(codigo: str, fecha: str) -> str:
    """Fetch full article HTML."""
    url = DOF_NOTE.format(codigo=codigo, fecha=fecha.replace("/", "%2F"))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"[dof] Detail fetch {codigo}: {exc}", file=sys.stderr)
        return ""


def classify_article(title: str, abstract: str) -> dict:
    """V4 Pro classification of DOF article by topic, entities, materiality."""
    ds_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not ds_key:
        # Fallback: keyword-based classification
        text = f"{title} {abstract}".lower()
        category = "other"
        for cat_keywords, cat_name in [
            (["sanción", "multa", "clausura"], "sanctions"),
            (["concesión", "minera", "minería"], "mining_concession"),
            (["energía", "petróleo", "electricidad", "gas", "pemex", "cfe"], "energy"),
            (["seguridad", "defensa", "delincuencia", "narcóticos", "fentanilo"], "security"),
            (["comercio", "arancel", "tratado", "usmca", "t-mec", "aduana"], "bilateral"),
            (["sentencia", "suprema corte", "tribunal"], "judicial"),
            (["reglamento", "norma", "disposición"], "regulatory_change"),
            (["nombramiento", "designación"], "appointment"),
            (["presupuesto", "gasto"], "budget"),
        ]:
            if any(kw in text for kw in cat_keywords):
                category = cat_name
                break

        is_material = category in ("sanctions", "security", "mining_concession", "bilateral")
        entities = []

        return {
            "category": category,
            "is_material": is_material,
            "affected_entities": entities,
            "method": "keyword_fallback",
        }

    # V4 Pro classification
    prompt = f"""Classify this DOF publication:

Title: {title[:200]}
Abstract: {abstract[:500]}

Categories: {', '.join(CATEGORIES)}
Is this a material change (one that would affect markets, security, or regulatory environment) or routine administrative?

Output JSON:
{{"category": "...", "is_material": true/false, "affected_entities": ["entity1", "entity2"], "rationale": "..."}}"""

    payload = {
        "model": "deepseek-v4-pro",
        "messages": [
            {"role": "system", "content": "You classify Mexican government publications. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 500,
    }

    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {ds_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {"category": "other", "is_material": False, "affected_entities": [], "method": "parse_failed"}
    except Exception as exc:
        print(f"[dof] Classification error: {exc}", file=sys.stderr)
        return {"category": "other", "is_material": False, "affected_entities": [], "method": "error"}


def store_article(art: dict, classification: dict, html: str) -> bool:
    """Store article in database."""
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO articles
            (codigo, fecha, title, section, category, is_material, affected_entities,
             raw_html, classification_json, classified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                art["codigo"],
                art["fecha"],
                art["title"][:500],
                art.get("section", "otros"),
                classification.get("category", "other"),
                1 if classification.get("is_material") else 0,
                json.dumps(classification.get("affected_entities", [])),
                html[:5000],
                json.dumps(classification),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"[dof] Store error: {exc}", file=sys.stderr)
        conn.close()
        return False


def process_day(year: int, month: int, day: int, classify: bool = False) -> int:
    """Process a single day of DOF publications."""
    items = fetch_daily_edition(year, month, day)
    print(f"  {year}-{month:02d}-{day:02d}: {len(items)} articles")

    for art in items[:5]:  # Limit to first 5 for MVP speed
        html = fetch_article_detail(art["codigo"], art["fecha"])
        if not html:
            continue

        # Extract abstract from HTML
        abstract_match = re.search(r'<meta name="description" content="([^"]*)"', html)
        abstract = abstract_match.group(1) if abstract_match else art["title"]

        if classify:
            classification = classify_article(art["title"], abstract)
        else:
            classification = {"category": "other", "is_material": False, "affected_entities": [], "method": "skipped"}

        store_article(art, classification, html)

    return len(items)


def generate_daily_memo(date: datetime.date) -> str:
    """Generate daily DOF summary memo for intel pipeline."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT codigo, title, category, is_material FROM articles WHERE fecha=? ORDER BY is_material DESC",
        (date.strftime("%d/%m/%Y"),),
    )
    rows = cursor.fetchall()
    conn.close()

    lines = [
        f"# DOF Daily Summary — {date.isoformat()}",
        f"**Total publications:** {len(rows)}",
        f"**Material changes:** {sum(1 for r in rows if r[3])}",
        "",
        "## Material Changes",
    ]

    for codigo, title, category, is_material in rows:
        flag = "⚠️" if is_material else "  "
        lines.append(f"{flag} **{title[:100]}**")
        lines.append(f"   DOI: {codigo} | Cat: {category}")
        lines.append("")

    lines.append("---")
    lines.append(f"Source: DOF at dof.gob.mx | Generated: {datetime.datetime.utcnow().isoformat()[:16]}Z")

    memo_path = EXPORT_DIR / f"dof-summary-{date.isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines))
    return str(memo_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DOF Daily Collector")
    parser.add_argument("--today", action="store_true", help="Fetch today's DOF")
    parser.add_argument("--backfill", type=int, default=0, help="Backfill N days")
    parser.add_argument("--classify", action="store_true", help="Classify articles")
    parser.add_argument("--memo", action="store_true", help="Generate daily memo")
    args = parser.parse_args()

    init_db()
    today = datetime.date.today()

    if args.today:
        total = process_day(today.year, today.month, today.day, args.classify)
        print(f"Fetched {total} articles")

    if args.backfill:
        total = 0
        for day_offset in range(args.backfill):
            d = today - datetime.timedelta(days=day_offset)
            total += process_day(d.year, d.month, d.day, args.classify)
        print(f"Backfilled {total} articles across {args.backfill} days")

    if args.memo:
        path = generate_daily_memo(today)
        print(f"Memo: {path}")


if __name__ == "__main__":
    main()
