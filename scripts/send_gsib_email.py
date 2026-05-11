#!/usr/bin/env python3
"""
Send GSIB PDF via MATON API (Gmail proxy). Clean version.
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import formatdate

# Load .env
env_path = os.path.expanduser("~/.openclaw/workspace/.env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k] = v

MATON_KEY = os.environ.get("MATON_API_KEY", "")
PDF_PATH = os.path.expanduser("~/trevor-briefings/2026-05-10/final/GSIB-2026-05-10-v15.pdf")

if not MATON_KEY:
    sys.exit("ERROR: No MATON_API_KEY found")
if not os.path.exists(PDF_PATH):
    sys.exit(f"ERROR: PDF not found at {PDF_PATH}")

with open(PDF_PATH, "rb") as f:
    pdf_data = f.read()
print(f"PDF: {len(pdf_data)} bytes ({len(pdf_data)//1024} KB)", file=sys.stderr)

# Build multipart message
msg = MIMEMultipart("mixed")
msg["From"] = "trevor.mentis@gmail.com"
msg["To"] = "roderick.jones@gmail.com"
msg["Subject"] = "GSIB Daily Brief — 10 May 2026 (v15 — LLM-Map Edition)"
msg["Date"] = formatdate(localtime=True)

# Plain text body
body_text = """Roderick,

Attached is today's Global Security & Intelligence Brief (GSIB) for 10 May 2026.

This edition features LLM-informed theatre maps designed by Claude Opus 4.7 — each map was designed to illuminate the specific geographic story of its region:

• Europe — Three Vectors: Russian Strike Tempo (108 drones), US Drawdown (5,000 troops from Germany), Belarus Watch
• Asia — Pre-Summit Positioning: Trump-China visit horizon / Allied hedging (Japan-Australia industrialisation)
• Middle East — The Hormuz Toll Trap: Iran's rial-denominated shipping toll / US sanctions threat / Israeli strike geometry
• North America — The Substitution Map: Venezuelan barrels (1.23M bpd) replacing Iranian barrels under blockade
• S. & C. America — Distributed Stress: Cuba sanctions escalation / Brazil northeast flooding
• Global Finance — Hormuz Chokepoint × Oil Major Strategy × Memory Bottleneck

26 pages, 6 theatres, 10 Kalshi prediction market trade cards, 3 analytic charts.

— Trevor (🤖)
Threat Research and Evaluation Virtual Operations Resource
"""
msg.attach(MIMEText(body_text, "plain"))

# PDF attachment
part = MIMEBase("application", "pdf")
part.set_payload(pdf_data)
encoders.encode_base64(part)
part.add_header("Content-Disposition", "attachment", filename="GSIB-2026-05-10-v15.pdf")
msg.attach(part)

# Encode to base64url for Gmail API
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

# Send via MATON API
url = "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send"
req = urllib.request.Request(
    url,
    data=json.dumps({"raw": raw}).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {MATON_KEY}",
        "Content-Type": "application/json",
    },
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
        print(f"✅ Email sent! Message ID: {result.get('id', 'unknown')}", file=sys.stderr)
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP Error {e.code}: {body}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
