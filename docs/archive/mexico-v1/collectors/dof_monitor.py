#!/usr/bin/env python3
"""DOF (Diario Oficial de la Federación) Daily Monitor.

Fetches daily DOF PDF publication, extracts relevant content by
keyword filtering (energy, security, trade), saves to pipeline.

Usage:
    python3 collectors/dof_monitor.py --fetch        # Fetch latest DOF
    python3 collectors/dof_monitor.py --report       # Summary of recent
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORT_DIR = REPO_ROOT / "exports"
DATA_DIR = REPO_ROOT / "data" / "dof"

# DOF RSS feed — primary access point
DOF_RSS = "https://www.dof.gob.mx/index.php?year=2026&month=05&day=18&edicion=MAT"
DOF_BASE = "https://www.dof.gob.mx"
# SSL: DOF uses self-signed cert
DOF_CTX = None

# Keywords that signal Mexico-relevant content
MX_KEYWORDS = [
    "seguridad", "seguridad pública", "defensa", "sedena", "semar",
    "guardia nacional", "fiscalía", "fgr", "pgr",
    "energía", "pemex", "cfe", "sener", "cre", "cnh", "hidrocarburos",
    "electricidad", "comercio", "economía", "se", "secretría de economía",
    "aduanas", "comercio exterior", "arancel",
    "usmca", "t-mec", "tratado", "acuerdo comercial",
    "migración", "extranjería", "refugiado", "asilo",
    "fentanilo", "precursores", "sustancias químicas",
    "contrataciones", "licitaciones", "compranet",
    "presupuesto", "gasto público", "shcp",
    "medio ambiente", "profepa", "semarnat",
    "educación", "sep", "salud", "ssa",
    "infraestructura", "comunicaciones", "sct",
    "turismo", "sectur", "mundial 2026",
]

SECURITY_KEYWORDS = ["seguridad", "defensa", "sedena", "semar", "guardia nacional", "fiscalía", "fgr",
                     "fentanilo", "precursores", "delincuencia", "crimen organizado", "narcóticos"]
ENERGY_KEYWORDS = ["energía", "pemex", "cfe", "sener", "cre", "cnh", "hidrocarburos", "electricidad"]
TRADE_KEYWORDS = ["comercio", "economía", "arancel", "usmca", "t-mec", "tratado", "aduanas", "comercio exterior"]


def fetch_rss() -> list[dict[str, str]]:
    """Fetch DOF daily edition page and extract article links."""
    items = []
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(DOF_RSS, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        # Extract article links from the daily edition page
        import re
        seen = set()
        import re
        for match in re.finditer(r'<a[^>]*href="([^"]*nota_detalle[^"]*codigo=(\d+)[^"]*fecha=(\d+/\d+/\d+)[^"]*)"[^>]*>\s*(.*?)\s*</a>', html):
            url = match.group(1)
            codigo = match.group(2)
            fecha = match.group(3)
            title = re.sub(r'<[^>]+>', '', match.group(4)).strip()
            title = title.replace('&oacute;', 'ó').replace('&aacute;', 'á').replace('&eacute;', 'é').replace('&iacute;', 'í').replace('&uacute;', 'ú').replace('&ntilde;', 'ñ').replace('&nbsp;', ' ').replace('&#241;', 'ñ').replace('&#243;', 'ó')
            if codigo not in seen:
                seen.add(codigo)
                items.append({
                    "title": title,
                    "link": f"https://www.dof.gob.mx/nota_detalle.php?codigo={codigo}&fecha={fecha}",
                    "pub_date": fecha.replace("/", "-"),
                    "description": f"DOF publication from {fecha}",
                })
        # Also capture texto/imagen links
        for match in re.finditer(r'href="nota_to_imagen_fs\.php\?[^"]*fecha=(\d+/\d+/\d+)"', html):
            fecha = match.group(1)
            if f"imagen-{fecha}" not in seen:
                seen.add(f"imagen-{fecha}")
                items.append({
                    "title": f"DOF Publication Image {fecha}",
                    "link": f"https://www.dof.gob.mx/index.php?year={fecha.split('/')[2]}&month={fecha.split('/')[1]}&day={fecha.split('/')[0]}&edicion=MAT",
                    "pub_date": fecha.replace("/", "-"),
                    "description": f"DOF edition from {fecha}",
                })
    except Exception as exc:
        print(f"[dof] DOF fetch error: {exc}", file=sys.stderr)
    return items


def classify_article(title: str, description: str) -> list[str]:
    """Classify DOF article by theme."""
    text = f"{title} {description}".lower()
    themes = []
    if any(kw in text for kw in SECURITY_KEYWORDS):
        themes.append("cartel_security")
    if any(kw in text for kw in ENERGY_KEYWORDS):
        themes.append("energy_infra")
    if any(kw in text for kw in TRADE_KEYWORDS):
        themes.append("us_mexico")
    if "presupuesto" in text or "shcp" in text or "gasto" in text:
        themes.append("economy_markets")
    if "mundial" in text or "turismo" in text:
        themes.append("worldcup_travel")
    if "reforma" in text or "decreto" in text or "ley" in text:
        themes.append("political_risk")
    return themes or ["unclassified"]


def fetch_and_filter() -> list[dict[str, Any]]:
    """Fetch DOF RSS, filter by keywords, classify."""
    items = fetch_rss()
    
    results = []
    for item in items:
        text = f"{item['title']} {item['description']}".lower()
        matched = [kw for kw in MX_KEYWORDS if kw in text]
        
        if matched:
            themes = classify_article(item["title"], item["description"])
            results.append({
                "title": item["title"],
                "link": item["link"],
                "date": item["pub_date"],
                "matched_keywords": matched[:5],
                "themes": themes,
                "priority": "high" if any(t in ["cartel_security", "us_mexico"] for t in themes) else "medium",
            })
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DOF Daily Monitor")
    parser.add_argument("--fetch", action="store_true", help="Fetch and filter DOF")
    parser.add_argument("--report", action="store_true", help="Generate report")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.fetch:
        print("Fetching DOF RSS...")
        items = fetch_rss()
        print(f"  RSS items: {len(items)}")
        
        filtered = [i for i in items if any(kw in f"{i['title']} {i['description']}".lower() for kw in MX_KEYWORDS)]
        print(f"  Mexico-relevant: {len(filtered)}")
        
        # Classify
        results = []
        for item in filtered:
            themes = classify_article(item["title"], item["description"])
            results.append({**item, "themes": themes})
        
        # Save
        today = datetime.date.today().isoformat()
        out_path = DATA_DIR / f"dof-scan-{today}.json"
        out_path.write_text(json.dumps({"date": today, "total_items": len(items), "mexico_relevant": len(results), "results": results}, indent=2))
        print(f"  Saved: {out_path}")
        
        if results:
            print(f"\n  {'Title':60s} {'Themes':30s}")
            print("  " + "-" * 90)
            for r in results[:10]:
                print(f"  {r['title'][:58]:60s} {', '.join(r['themes']):30s}")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")

    if args.report:
        today = datetime.date.today().isoformat()
        report_paths = sorted(DATA_DIR.glob("dof-scan-*.json"), reverse=True)[:7]
        print(f"# DOF Monitoring Report — Last {len(report_paths)} Days\n")
        for p in report_paths:
            data = json.loads(p.read_text())
            print(f"## {data.get('date', p.stem)}")
            print(f"- RSS items: {data.get('total_items', '?')}")
            print(f"- Mexico relevant: {len(data.get('results', []))}")
        print(f"\nSource: DOF RSS at {DOF_RSS}")


if __name__ == "__main__":
    main()
