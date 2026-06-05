#!/usr/bin/env python3
"""Send the skill security audit report via AgentMail."""
import os
import sys
import json
import base64
from pathlib import Path

# Add skill-scanner to path
sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/skill-scanner"))

try:
    from agentmail import AgentMail
except ImportError:
    print("Error: agentmail package not found. Install with: pip install agentmail")
    sys.exit(1)

def main():
    api_key = os.getenv('AGENTMAIL_API_KEY')
    if not api_key:
        print("Error: AGENTMAIL_API_KEY not set")
        sys.exit(1)

    # Read the JSON data
    json_path = Path.home() / ".openclaw" / "workspace" / "exports" / "skill-security-audit-2026-05-21.json"
    md_path = Path.home() / ".openclaw" / "workspace" / "exports" / "skill-security-audit-2026-05-21.md"

    if not json_path.exists():
        print("Error: JSON report not found")
        sys.exit(1)

    data = json.loads(json_path.read_text())

    # Build a concise HTML email
    html_parts = [
        "<html><body style='font-family: Arial, sans-serif; max-width: 800px;'>",
        f"<h1>🔒 Daily Skill Security Audit Report</h1>",
        f"<p><strong>Date:</strong> {data['timestamp']}</p>",
        f"<p><strong>Tool:</strong> Skill Scanner v1.0</p>",
        "<hr>",
        "<h2>Executive Summary</h2>",
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse;'>",
        f"<tr><td><strong>Total Skills</strong></td><td>{data['total_skills']}</td></tr>",
        f"<tr><td style='color:green;'>✅ Approved</td><td>{data['approved']}</td></tr>",
        f"<tr><td style='color:orange;'>⚠️ Caution (high-severity)</td><td>{data['caution']}</td></tr>",
        f"<tr><td style='color:red;'>🔴 Rejected (critical-severity)</td><td>{data['rejected']}</td></tr>",
        f"<tr><td>❌ Scan Errors</td><td>{data['errors']}</td></tr>",
        "</table>",
        "<br>",
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse;'>",
        "<tr><th>Severity</th><th>Count</th></tr>",
        f"<tr><td style='color:red;'>Critical</td><td>{data['critical_count']}</td></tr>",
        f"<tr><td style='color:orange;'>High</td><td>{data['high_count']}</td></tr>",
        f"<tr><td style='color:#888;'>Medium</td><td>{data['medium_count']}</td></tr>",
        "</table>",
        "<br><hr>",
        "<h2>⚠️ Notable Findings (After False Positive Analysis)</h2>",
        "<p><em>Most critical/high findings are false positives from regex matching in documentation files. Below are the genuinely notable items:</em></p>",
    ]

    # Real critical findings (not in docs)
    real_critical = 0
    for f in data['findings']:
        if f['severity'] == 'critical':
            ext = Path(f['file']).suffix.lower()
            # Skip if in README/SKILL.md/CHANGELOG.md docs
            fname = Path(f['file']).name.lower()
            if fname in ('readme.md', 'skill.md', 'changelog.md', '_meta.json', 'consolidated_audit_report.md'):
                continue
            if not real_critical:
                html_parts.append("<h3>Critical (Non-Documentation)</h3><ul>")
            html_parts.append(f"<li><strong>{f['skill']}</strong> — <code>{f['file']}:{f['line']}</code><br>"
                              f"Pattern: {f['pattern']} — {f['description']}</li>")
            real_critical += 1

    if real_critical == 0:
        html_parts.append("<p><em>No real critical findings outside documentation.</em></p>")
    else:
        html_parts.append("</ul>")

    # Highlight the most important ones
    html_parts.extend([
        "<hr>",
        "<h2>🔍 Key Items Worth Review</h2>",
        "<ol>",
        "<li><strong>trevor-web-collection</strong> (collection skill): Contains a <code>curl | bash</code> pattern in <code>openweb/install-skill.sh</code> (download_execute), "
        "bulk env var access in <code>reverse-api-engineer/src/reverse_api/cursor_engineer.py</code>, and extensive <code>eval</code>/<code>exec</code> usage across 90+ site adapter files. "
        "This is likely a web scraping framework where some dynamic code execution is expected, but the install script and bulk env access should be reviewed.</li>",
        "<li><strong>daily-intel-brief</strong>: <code>bulk_env_access</code> in <code>scripts/build_pdf.py:330</code> — iterates over <code>os.environ</code>. Verify this is needed.</li>",
        "<li><strong>trevor-methodology</strong>: <code>eval_exec</code> in <code>pipeline/docx-js-template.js:37</code> — verify this is expected template processing.</li>",
        "<li><strong>trevor</strong> workspace skill: <code>credential_paths</code> finding — verify the referenced path is documented, not active.</li>",
        "</ol>",
        "<hr>",
        "<h2>📊 Clean Skills (Top Scorers)</h2>",
        "<p>118 of 133 skills (89%) passed with zero security findings — these are excluded from the detailed breakdown.</p>",
        "<hr>",
        "<h2>📁 False Positive Summary</h2>",
        "<p>The following categories of findings are considered false positives:</p>",
        "<ul>",
        "<li><strong>credential_paths in SKILL.md/README.md/CHANGELOG.md</strong> — Documentation references to <code>.env</code>, <code>~/.config</code>, etc.</li>",
        "<li><strong>skill-scanner self-test</strong> — Scanner flagged its own threat descriptions (reverse_shell, crypto_miner patterns in documentation)</li>",
        "<li><strong>crypto_miner in _meta.json</strong> — Metadata tags describing skill categories</li>",
        "<li><strong>env_scraping with specific os.getenv() calls</strong> — Legitimate API key access patterns</li>",
        "<li><strong>http_post_external in API clients</strong> — Expected behavior for API-wrapping skills</li>",
        "</ul>",
        "<hr>",
        f"<p><small>Full report: {md_path}</small></p>",
        "</body></html>"
    ])

    html_content = "\n".join(html_parts)

    text_parts = [
        "🔒 Daily Skill Security Audit Report",
        f"Date: {data['timestamp']}",
        "",
        "=== EXECUTIVE SUMMARY ===",
        f"Total Skills: {data['total_skills']}",
        f"✅ Approved: {data['approved']}",
        f"⚠️ Caution: {data['caution']}",
        f"🔴 Rejected (critical): {data['rejected']}",
        f"Findings: {data['total_findings']} (Critical: {data['critical_count']}, High: {data['high_count']}, Medium: {data['medium_count']})",
        "",
        "=== NOTABLE FINDINGS ===",
        f"Real critical findings (non-doc): {real_critical}",
        "",
        "Key items for review:",
        "1. trevor-web-collection - download_execute (install-skill.sh), bulk_env_access (cursor_engineer.py), 90+ eval/exec calls in site adapters",
        "2. daily-intel-brief - bulk_env_access in build_pdf.py:330",
        "3. trevor-methodology - eval_exec in docx-js-template.js:37",
        "",
        "118 of 133 skills (89%) passed with zero findings.",
        "",
        f"Full report: {md_path}",
    ]
    text_content = "\n".join(text_parts)

    # Read the full MD report for attachment
    md_content = md_path.read_text()

    # Send
    client = AgentMail(api_key=api_key)

    sender = "trevor_mentis@agentmail.to"
    recipient = "roderick.jones@gmail.com"

    print(f"Sending audit report from {sender} to {recipient}...")

    response = client.inboxes.messages.send(
        inbox_id=sender,
        to=[recipient],
        subject=f"🔒 Skill Security Audit — {data['timestamp']}",
        text=text_content,
        html=html_content,
        attachments=[{
            "filename": f"skill-security-audit-2026-05-21.md",
            "content": base64.b64encode(md_content.encode()).decode(),
            "content_type": "text/markdown"
        }]
    )

    print(f"✅ Email sent! Message ID: {response.message_id}")

if __name__ == "__main__":
    main()
