#!/usr/bin/env python3
"""Feed intel into AgentMail inbox using AgentMail SDK."""
import os, datetime, sys
from pathlib import Path

REPO = Path("/home/ubuntu/.openclaw/workspace")
sys.path.insert(0, str(REPO / "skills" / "agentmail" / "scripts"))

try:
    from agentmail import AgentMail
except ImportError:
    print("AgentMail SDK not available — falling back to news_raw.md only")
    AgentMail = None

INTEL_TEXT = """HIGH SIGNAL: Russia Kyiv strikes | Iran nuclear impasse | Hormuz sovereignty

Russia Threatens Systematic Strikes on Kyiv:
- Russian MFA warned of systematic strikes on Ukrainian defense industrial facilities and decision-making centers in Kyiv
- Lavrov personally called Rubio to communicate the threat
- ISW: Putin posturing after Victory Day ceasefire humiliation
- Russia spring-summer offensive stalling; Ukraine drone dominance

Iran Nuclear Negotiations:
- Iran will not commit to HEU removal or enrichment halt
- Trump rejects JCPOA-like deal
- Iran claiming Strait of Hormuz as territorial waters, reframing transit tolls as protection fees
- Contradictory messaging: US claims Tehran agreed; Iran denies

Quad + Xi Pyongyang:
- Quad foreign ministers met in New Delhi (first since 2024)
- Deterioration of Quad strategic value flagged
- Xi preparing Pyongyang visit (first in 7 years) — China nervous about DPRK-Russia axis

Monitoring: Eppendorf (medical ICS), Schneider Electric
"""

SUBJECT = "[TELEGRAM INTEL] Russia Kyiv strikes, Iran nuclear, Quad, Xi-Pyongyang"

# 1. Try AgentMail SDK
sent = False
if AgentMail:
    try:
        api_key = os.environ.get("AGENTMAIL_API_KEY", "")
        if api_key:
            client = AgentMail(api_key=api_key)
            response = client.inboxes.messages.send(
                inbox_id="trevor_mentis@agentmail.to",
                to=["trevor_mentis@agentmail.to"],
                subject=SUBJECT,
                text=INTEL_TEXT,
            )
            print(f"Sent via AgentMail SDK: {response}")
            sent = True
        else:
            print("No AGENTMAIL_API_KEY")
    except Exception as e:
        print(f"AgentMail SDK send failed: {e}")

# 2. Always append to news_raw.md
now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
news_entry = f"""
## Telegram Intel — {now}
**From:** Roderick (Telegram)
**Date:** {now}
**Type:** high_signal

- Russian MFA warned of systematic strikes on Ukrainian defense industrial facilities and decision-making centers in Kyiv — HIGH SIGNAL
- Iran will not commit to HEU removal or enrichment halt. Trump rejects JCPOA-like deal — HIGH SIGNAL
- Iran claiming Strait of Hormuz as territorial waters, reframing transit tolls as protection fees
- Contradictory messaging: US sources claim Tehran agreed to dispose of HEU; Iran denies
- Quad foreign ministers met in New Delhi (first since 2024). Deterioration of Quad strategic value flagged
- Xi preparing Pyongyang visit (first in 7 years) — China nervous about DPRK-Russia axis
- Eppendorf (medical ICS) — monitoring signal
- Schneider Electric — monitoring signal
"""

news_path = REPO / "tasks" / "news_raw.md"
with open(news_path, "a") as f:
    f.write(news_entry)
print(f"Appended to {news_path} ({news_path.stat().st_size} bytes)")

print("Done")
