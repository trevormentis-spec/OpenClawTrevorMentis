#!/usr/bin/env python3
"""Send daily skill audit report via AgentMail."""
import os, base64
from agentmail import AgentMail

client = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))

summary_path = os.path.expanduser(
    "~/.openclaw/workspace/exports/skill-audit/skill-audit-summary-2026-05-20.md"
)

with open(summary_path, "rb") as f:
    attachment_content = base64.b64encode(f.read()).decode("utf-8")

text_body = """DAILY SKILL SECURITY AUDIT — 2026-05-20 00:00 UTC
=================================================

79 skills scanned across ~/.openclaw/skills and /usr/lib/node_modules/openclaw/skills

RESULTS:
  ✅ Approved:  71
  ⚠️ Caution:    1  (trevor-methodology — eval_exec in docx-js-template.js)
  ❌ Rejected:   7  (all false-positive credential_paths/crypto_miner hits in documentation)
  ❓ Errors:     0

REJECTED SKILLS:
  • OpenClawTrevorMentis — 56 critical (docs/audit reports referencing ~/.config and scanner pattern descriptions)
  • api-gateway — credential_paths in SKILL.md (Bearer token example)
  • gmail — credential_paths in SKILL.md (Bearer token example)
  • gog-myclaw — credential_paths in SKILL.md (~/.config/gogcli mention)
  • stripe-api — credential_paths in SKILL.md (Bearer token example)
  • video-translation — credential_paths in SKILL.md (Noiz API key setup)
  • whatsapp-business — credential_paths in SKILL.md (Bearer token example)

CAUTION SKILLS:
  • trevor-methodology — eval() usage in pipeline/docx-js-template.js

TOTAL FINDINGS: 97 (56 critical false positives in OpenClawTrevorMentis audit docs,
7 critical in other skill docs, 1 high, 33 medium)

Full report attached.
"""

response = client.inboxes.messages.send(
    inbox_id="trevor_mentis@agentmail.to",
    to=["roderick.jones@gmail.com"],
    subject="🔒 Daily Skill Security Audit — 2026-05-20",
    text=text_body,
    attachments=[{
        "filename": "skill-audit-summary-2026-05-20.md",
        "content": attachment_content,
        "content_type": "text/markdown"
    }]
)

print(f"✅ Email sent! Message ID: {response.message_id}")
print(f"   Thread ID: {response.thread_id}")
