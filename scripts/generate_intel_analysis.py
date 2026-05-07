#!/usr/bin/env python3
"""
Generate a structured intelligence analysis from this week's intel emails
using DeepSeek V4 Pro, then email it to Roderick via Gmail.
"""
import os, sys, json, urllib.request, base64

def load_dotenv(path=".env"):
    """Load env vars from .env file"""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

def read_intel_emails(directory="/tmp/intel_emails"):
    """Read and concatenate all intel email files"""
    import glob
    files = sorted(glob.glob(f"{directory}/*.txt"))
    combined = []
    for f in files:
        with open(f, "r", encoding="utf-8", errors="replace") as fp:
            content = fp.read()
        combined.append(f"\n{'='*80}\nSOURCE: {os.path.basename(f)}\n{'='*80}\n")
        combined.append(content[:8000])
        combined.append("\n[--- end excerpt ---]\n")
    return "".join(combined)

def call_deepseek(prompt, api_key):
    """Call DeepSeek V4 Pro"""
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",  # v4 pro
        "messages": [
            {"role": "system", "content": "You are a senior intelligence analyst producing a structured weekly assessment. Write in clear, calibrated prose with proper tradecraft terminology."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
        "temperature": 0.3
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    print("Calling DeepSeek V4 Pro...", file=sys.stderr)
    resp = urllib.request.urlopen(req, timeout=300)
    result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"]

def send_email(to, subject, body_html, api_key):
    """Send email via Gmail API through Maton gateway"""
    body = f"""From: trevor.mentis@gmail.com
To: {to}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/html; charset="UTF-8"

<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: #f5f5f0; padding: 24px;">
<div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
<div style="background: #161616; color: #c9a84c; padding: 24px 32px;">
<h1 style="margin: 0; font-size: 20px; letter-spacing: 1px; text-transform: uppercase;">Weekly Intelligence Synthesis</h1>
<p style="margin: 6px 0 0; color: #7a8a3c; font-size: 12px; letter-spacing: 2px; text-transform: uppercase;">Generated from ISW / CTP / Cipher Brief / Foreign Policy / CISA</p>
</div>
<div style="padding: 32px;">
{body_html}
</div>
<div style="padding: 8px 32px 24px; border-top: 1px solid #eee;">
<p style="color: #888; font-size: 11px;">TREVOR — Threat Research and Evaluation Virtual Operations Resource</p>
<p style="color: #888; font-size: 11px;">Sources: Intelligence-labeled Gmail inbox (ISW, CTP, Cipher Brief, Foreign Policy, CISA) | Generated {__import__('datetime').date.today().isoformat()}</p>
</div>
</div>
</body>
</html>"""

    raw = base64.urlsafe_b64encode(body.encode()).decode()
    payload = json.dumps({"raw": raw}).encode()

    req = urllib.request.Request(
        "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    print(f"Email sent: {result.get('id', 'unknown')}", file=sys.stderr)

def main():
    # Load credentials
    load_dotenv()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    maton_key = os.environ.get("MATON_API_KEY", "")

    if not deepseek_key or not maton_key:
        print("ERROR: Missing API keys", file=sys.stderr)
        sys.exit(1)

    # Read intel content
    print("Reading intel emails...", file=sys.stderr)
    intel_content = read_intel_emails()

    # Truncate if needed
    MAX_INPUT = 120000
    if len(intel_content) > MAX_INPUT:
        intel_content = intel_content[:MAX_INPUT] + "\n\n[... truncated ...]"

    print(f"Intel content: {len(intel_content)} chars", file=sys.stderr)

    # Build the structured analysis prompt
    prompt = f"""You are a senior intelligence analyst (TREVOR — Threat Research and Evaluation Virtual Operations Resource). 
Analyze the following collection of intelligence emails from this week (May 4-7, 2026) and produce a structured analytic assessment.

The source emails are from: ISW (Institute for the Study of War), CTP (Critical Threats Project), The Cipher Brief, Foreign Policy, and CISA.

Your analysis should cover:

1. **Executive Summary** — 3-5 paragraph synthesis of the most significant developments
2. **Regional Breakdown**:
   - Europe (Russia-Ukraine war: ceasefire dynamics, resettlement strategy)
   - Middle East (Iran war: military operations, diplomatic maneuvers, UAE strikes)
   - Indo-Pacific (Korea: nuclear arsenal expansion; Japan-China tensions)
   - Cyber/Security (CISA vulnerabilities, critical infrastructure)
3. **Key Judgments** — Calibrated probability assessments for the week ahead
4. **Cross-cutting Themes** — Patterns that emerge across multiple theaters
5. **Intelligence Gaps** — What's notable by its absence
6. **Analytic Method** — Sherman Kent-style: weigh evidence, distinguish between fact and assessment

Tone: Professional, direct, calibrated. Use proper intelligence tradecraft language.
Format: Use markdown headers for sections. Keep paragraphs tight and evidence-based.

Here is the intelligence content:

{intel_content}

Produce the analysis now.
"""

    # Generate analysis with DeepSeek V4 Pro
    analysis = call_deepseek(prompt, deepseek_key)
    
    # Save locally
    with open("exports/weekly-intel-synthesis-2026-05-07.md", "w") as f:
        f.write(analysis)
    print(f"Analysis saved to exports/weekly-intel-synthesis-2026-05-07.md", file=sys.stderr)

    # Convert markdown to simple HTML for email
    import re
    html_body = analysis
    html_body = re.sub(r'^### (.+)$', r'<h3 style="color:#c9a84c;margin-top:24px;">\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2 style="color:#161616;margin-top:28px;border-bottom:1px solid #eee;padding-bottom:8px;">\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^# (.+)$', r'<h1 style="color:#161616;margin-top:32px;">\1</h1>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^(\d+)\. (.+)$', r'<li>\1. \2</li>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'<li>(.+)</li>\n<li>', r'<li>\1</li>\n<li>', html_body)
    html_body = re.sub(r'(<li>.*?</li>\n)+', r'<ul style="padding-left:20px;line-height:1.6;">\g<0></ul>', html_body, flags=re.DOTALL)
    html_body = html_body.replace('\n\n', '</p><p style="line-height:1.6;color:#333;">')
    html_body = '<p style="line-height:1.6;color:#333;">' + html_body + '</p>'
    html_body = html_body.replace('</p><p style="line-height:1.6;color:#333;"><ul', '<ul').replace('</ul><p style="line-height:1.6;color:#333;">', '</ul>')

    # Send email
    print("Sending email to roderick.jones@gmail.com...", file=sys.stderr)
    send_email(
        to="roderick.jones@gmail.com",
        subject="Weekly Intelligence Synthesis — May 4-7, 2026",
        body_html=html_body,
        api_key=maton_key
    )

    print("Done!", file=sys.stderr)

if __name__ == "__main__":
    main()
