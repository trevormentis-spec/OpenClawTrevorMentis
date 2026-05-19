#!/usr/bin/env python3
"""Send skill audit report via AgentMail."""
import os
import sys
from agentmail import AgentMail

api_key = os.getenv("AGENTMAIL_API_KEY", "am_us_inbox_fa0e0d2ddaa2a10b824d2af2416767fca38983e70e16972e953677d902ac41ed")
client = AgentMail(api_key=api_key)

# Load the report
report_path = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit-2026-05-19.md")
with open(report_path) as f:
    report = f.read()

# Build executive summary for the email body
text_body = """Daily Skill Security Audit Report — 2026-05-19

EXECUTIVE SUMMARY
=================
Total Skills Scanned: 125
Total Findings: 175
Approved: 112
Caution: 1
Reject: 12

REJECTED SKILLS:
- OpenClawTrevorMentis (56 critical) — credential_paths, crypto_miner findings in audit docs
- api-gateway (1 critical) — credential path ref in SKILL.md
- chartgen-ai (5 critical) — credential path refs in JS config
- daily-intel-brief (2 critical) — .env paths in scripts
- genviral (2 critical) — ~/.config/env/global.env refs
- gmail (1 critical) — Bearer token ref in SKILL.md
- gog-myclaw (2 critical) — ~/.config/gogcli/credentials.json refs
- skill-scanner (8 critical) — scanner's own detection patterns flagged as threats
- social-post (36 critical) — hardcoded .env paths, Farcaster private keys
- stripe-api (1 critical) — Bearer token ref in SKILL.md
- video-translation (1 critical) — API key ref in SKILL.md
- whatsapp-business (1 critical) — Bearer token ref in SKILL.md

CAUTION SKILLS:
- trevor-methodology (1 high) — RegExp .exec() call flagged as eval_exec

NOTES:
- Most "credential_paths" findings are documentation references or legitimate env var reads.
- The skill-scanner flags itself because its threat patterns reference ~/.ssh, xmrig, /etc/systemd, etc.
- social-post has genuine concerns with hardcoded absolute .env paths and exposed private keys in scripts.

Full report saved locally at exports/skill-audit-2026-05-19.md
"""

html_body = "<pre>" + text_body.replace("\n", "<br>") + "</pre>"

# Also attach the full report content
report_truncated = report[:50000]  # limit size

# Send via trevor_mentis@agentmail.to
try:
    result = client.inboxes.messages.send(
        inbox_id="trevor_mentis@agentmail.to",
        to="roderick.jones@gmail.com",
        subject="[Security Audit] Daily Skill Scanner Report — 2026-05-19",
        text=text_body + "\n\n---\nFull report attached below.\n\n" + report_truncated,
        html=f"<html><body><pre>{text_body}</pre><hr><pre>{report_truncated}</pre></body></html>",
    )
    print(f"EMAIL_SENT:{result}")
except Exception as e:
    print(f"EMAIL_ERROR:{e}", file=sys.stderr)
    sys.exit(1)
