#!/usr/bin/env python3
"""Cartel Telegram Channel Monitor — OSINT source for Mexico security analysis.

Monitors publicly accessible Telegram channels for Mexico cartel activity signals.
Limited to public channels verifiable through open-source Telegram APIs.
No private channel access. No cartel-affiliated direct communications.

Sources identified through open-source research (journalist referrals, public databases).

Usage:
    python3 collectors/telegram_monitor.py --fetch
    python3 collectors/telegram_monitor.py --report
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "telegram"
DB_PATH = DATA_DIR / "telegram.db"
EXPORT_DIR = REPO_ROOT / "exports"

# Public Telegram channels — open-source, journalist-verified
# These are public channels (accessible without joining), used by journalists
# and analysts for Mexico security monitoring. No private/cartel-affiliated channels.
CHANNELS = {
    "Blog del Narco": {
        "username": "blogdelnarco",
        "language": "es",
        "focus": "Cartel violence news aggregation",
        "admiralty": "C-1 — Aggregated content, verify before citing",
        "public": True,
    },
    "México Seguridad": {
        "username": "mexicoseguridad",
        "language": "es",
        "focus": "Security news, official reports, breaking events",
        "admiralty": "C-2 — Public security news aggregator",
        "public": True,
    },
    "Narco Noticias MX": {
        "username": "narconoticiasmx",
        "language": "es",
        "focus": "Cartel violence updates from local press",
        "admiralty": "C-2 — Press-sourced cartel news",
        "public": True,
    },
    "SEDENA Press": {
        "username": "SEDENAmx",
        "language": "es",
        "focus": "Official Mexican army press releases",
        "admiralty": "A-2 — Official government channel, verified",
        "public": True,
    },
    "FGR Mexico": {
        "username": "FGRMexico",
        "language": "es",
        "focus": "Federal Prosecutor's Office — official announcements",
        "admiralty": "A-2 — Official government channel, verified",
        "public": True,
    },
    "Guardia Nacional": {
        "username": "GN_MX",
        "language": "es",
        "focus": "National Guard official communications",
        "admiralty": "A-2 — Official government channel, verified",
        "public": True,
    },
}

# Telegram API — use existing bot infrastructure
TELEGRAM_API = "https://api.telegram.org/bot{token}"
PUBLIC_VIEW = "https://t.me/s/{username}"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            posted_at TEXT,
            text_content TEXT,
            has_media INTEGER DEFAULT 0,
            category TEXT,
            severity TEXT,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_channel ON posts(channel)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(posted_at)")
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def get_telegram_token() -> str:
    """Get Telegram bot token from env."""
    for key_name in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN"]:
        token = os.environ.get(key_name, "")
        if token:
            return token
    # Check .env
    for env_path in [REPO_ROOT / ".env", pathlib.Path("/home/ubuntu/.openclaw/.env")]:
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if "TELEGRAM" in line and "=" in line:
                    return line.split("=", 1)[1].strip()
    return ""


def fetch_channel_public(username: str) -> list[dict]:
    """Fetch recent messages from a public Telegram channel via web preview."""
    posts = []
    url = PUBLIC_VIEW.format(username=username)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0 Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract messages from t.me/s/ page
        for match in re.finditer(
            r'<div class="tgme_widget_message_wrap[^>]*>.*?'
            r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>',
            html,
            re.DOTALL,
        ):
            text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if text:
                post_id = hashlib.md5(text.encode()).hexdigest()[:12]
                posts.append({
                    "id": post_id,
                    "channel": username,
                    "text": text[:2000],
                    "posted_at": datetime.datetime.utcnow().isoformat() + "Z",
                })
    except Exception as exc:
        print(f"  [telegram] {username}: {exc}", file=sys.stderr)
        # Fallback: log that channel was attempted
        posts.append({
            "id": f"error-{username}",
            "channel": username,
            "text": f"[FETCH ERROR: {exc}]",
            "posted_at": datetime.datetime.utcnow().isoformat() + "Z",
        })

    return posts


def classify_post(text: str) -> dict:
    """Classify Telegram post by topic and severity."""
    text_lower = text.lower()

    # Category detection
    category = "other"
    for cat_keywords, cat in [
        (["fentanilo", "fentanyl", "precursor", "droga", "narcótico"], "narcotics"),
        (["extorsión", "extortion", "piso", "cobro"], "extortion"),
        (["ejecutado", "asesinato", "homicidio", "muerto", "cuerpo"], "violence"),
        (["bloqueo", "quema", "incendio", "narcobloqueo"], "narco_blockade"),
        (["detenido", "captura", "arresto", "aseguramiento"], "enforcement"),
        (["ejército", "sedena", "semar", "guardia nacional", "operativo"], "military_ops"),
        (["desaparecido", "secuestro", "levantón"], "kidnapping"),
        (["decomiso", "incautación", "confiscación"], "seizure"),
        (["municipio", "alcalde", "gobierno local"], "governance"),
    ]:
        if any(kw in text_lower for kw in cat_keywords):
            category = cat
            break

    # Severity
    severity_keywords = {
        "critical": ["ejecutado", "masacre", "decapitado", "enfrentamiento armado", "fosa", "cuerpo sin vida"],
        "high": ["detenido", "decomiso", "incautación", "fentanilo", "narcobloqueo", "quema", "incendio"],
        "medium": ["bloqueo", "extorsión", "amenaza", "desaparecido", "secuestro"],
        "low": ["anuncio", "conferencia", "comunicado oficial"],
    }
    severity = "medium"
    for sev, keywords in severity_keywords.items():
        if any(kw in text_lower for kw in keywords):
            severity = sev
            break

    return {"category": category, "severity": severity}


def generate_report() -> str:
    """Generate Telegram intelligence summary."""
    conn = get_db()
    cursor = conn.execute(
        """SELECT channel, COUNT(*) as cnt,
                  SUM(CASE WHEN severity IN ('critical','high') THEN 1 ELSE 0 END) as sig
           FROM posts GROUP BY channel ORDER BY sig DESC"""
    )
    channel_stats = cursor.fetchall()

    cursor2 = conn.execute(
        """SELECT text_content, channel, posted_at, severity FROM posts
           WHERE severity IN ('critical','high') ORDER BY posted_at DESC LIMIT 15"""
    )
    sig_posts = cursor2.fetchall()
    conn.close()

    lines = [
        f"# Telegram Intelligence Summary — {datetime.date.today().isoformat()}",
        "",
        "## Channel Activity",
    ]
    for ch, cnt, sig in channel_stats:
        lines.append(f"- **{ch}**: {cnt} posts ({sig} significant)")

    lines.append("")
    lines.append("## Significant Posts (Critical/High)")
    for text, ch, ts, sev in sig_posts:
        lines.append(f"- [{sev}] {ch}: {text[:120]}...")
        if len(text) > 120:
            lines.append(f"  (truncated, {len(text)} chars)")

    lines.append("")
    lines.append("---")
    lines.append("Source: Public Telegram channels via t.me/s/ web preview")
    lines.append("⚠️ Only public channels — no cartel-affiliated private channels.")
    lines.append("Channels monitored: " + ", ".join(CHANNELS.keys()))

    memo_path = EXPORT_DIR / f"telegram-intel-{datetime.date.today().isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines))
    return str(memo_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Telegram Channel Monitor")
    parser.add_argument("--fetch", action="store_true", help="Fetch channel posts")
    parser.add_argument("--report", action="store_true", help="Generate intel memo")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        total = 0
        for channel_name, info in CHANNELS.items():
            print(f"  {channel_name}...")
            posts = fetch_channel_public(info["username"])
            conn = get_db()
            for p in posts:
                classification = classify_post(p.get("text", ""))
                conn.execute(
                    "INSERT OR IGNORE INTO posts (id, channel, posted_at, text_content, category, severity) VALUES (?, ?, ?, ?, ?, ?)",
                    (p["id"], p["channel"], p.get("posted_at", ""), p.get("text", "")[:2000],
                     classification["category"], classification["severity"]),
                )
                total += 1
            conn.commit()
            conn.close()
            sig = sum(1 for p in posts if classify_post(p.get("text", ""))["severity"] in ("critical", "high"))
            print(f"    {len(posts)} posts ({sig} significant)")
        print(f"\nTotal: {total} posts fetched")

    if args.report:
        path = generate_report()
        print(f"Report: {path}")


if __name__ == "__main__":
    main()
