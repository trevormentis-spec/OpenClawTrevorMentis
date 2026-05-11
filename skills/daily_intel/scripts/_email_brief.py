#!/usr/bin/env python3
"""Email the generated PDF to Roderick via Gmail API.

Usage: python3 _email_brief.py <pdf_path> <issue_number>
Requires MATON_API_KEY in environment.
"""
import os, sys, json, base64, urllib.request, datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: _email_brief.py <pdf_path> [issue_number]", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    issue = sys.argv[2] if len(sys.argv) > 2 else "daily"
    maton_key = os.environ.get("MATON_API_KEY", "")
    
    if not maton_key:
        # Try reading from workspace .env
        from trevor_config import WORKSPACE
        env_path = str(WORKSPACE / ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("MATON_API_KEY="):
                        maton_key = line.strip().split("=", 1)[1]
                        break
    
    if not maton_key:
        print("ERROR: MATON_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    pdf_b64 = base64.b64encode(pdf_data).decode()
    pdf_name = os.path.basename(pdf_path)
    date_str = datetime.date.today().strftime("%d %B %Y")

    # Build email
    boundary = "==TREVOR_INTEL_BOUNDARY=="
    subject = f"Global Security & Intelligence Brief — Issue #{issue} — {date_str}"
    
    body = f"""From: Trevor <trevor.mentis@gmail.com>
To: Roderick Jones <roderick.jones@gmail.com>
Subject: {subject}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=\"{boundary}\"

--{boundary}
Content-Type: text/html; charset="UTF-8"

<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: #f5f5f0; padding: 24px;">
<div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
<div style="background: #161616; color: #c9a84c; padding: 24px 32px;">
<h1 style="margin: 0; font-size: 20px; letter-spacing: 1px; text-transform: uppercase;">Global Security &amp; Intelligence Brief</h1>
<p style="margin: 6px 0 0; color: #7a8a3c; font-size: 12px; letter-spacing: 2px; text-transform: uppercase;">{date_str} — Issue #{issue} — TREVOR Assessment</p>
</div>
<div style="padding: 32px;">
<p style="color: #444; font-size: 14px; line-height: 1.6;">Your daily intelligence assessment is ready.</p>
<p style="color: #444; font-size: 14px; line-height: 1.6;">Full PDF attached — six theatres + global finance with structured analysis, key judgments, and prediction market integration.</p>
<p style="color: #888; font-size: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee;">Six theatres: Europe • Sahel • South Asia • Middle East • North America • South America + Global Finance</p>
<p style="color: #888; font-size: 12px;">TREVOR — Threat Research and Evaluation Virtual Operations Resource</p>
<p style="color: #888; font-size: 12px; margin-top: 8px;">Delivered daily at ~07:00 PT</p>
</div></div>
</body>
</html>

--{boundary}
Content-Type: application/pdf
Content-Disposition: attachment; filename=\"{pdf_name}\"
Content-Transfer-Encoding: base64

{pdf_b64}

--{boundary}--
"""

    raw = base64.urlsafe_b64encode(body.encode()).decode()
    payload = json.dumps({"raw": raw}).encode()

    req = urllib.request.Request(
        "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {maton_key}",
            "Content-Type": "application/json",
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        sent_id = result.get("id", "unknown")
        print(f"Email sent: {sent_id}")
        print(f"To: roderick.jones@gmail.com")
        print(f"Subject: {subject}")
        return 0
    except Exception as e:
        print(f"Email failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
