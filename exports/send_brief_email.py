import base64, json, urllib.request, os, sys

api_key = os.environ["MATON_API_KEY"]
pdf_path = "/home/ubuntu/.openclaw/workspace/exports/pdfs/daily-brief-2026-05-01.pdf"

with open(pdf_path, "rb") as f:
    pdf_data = f.read()

pdf_b64 = base64.b64encode(pdf_data).decode()

boundary = "==BOUNDARY_TREVOR_001"

email_body = f"""From: trevor.mentis@gmail.com
To: Roderick.jones@gmail.com
Subject: Daily Intelligence Briefing — 1 May 2026
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{boundary}"

--{boundary}
Content-Type: text/html; charset="UTF-8"

<html>
<body style="font-family: Arial, sans-serif; max-width: 600px;">
<h2 style="color: #1a1a2e;">Daily Intelligence Briefing</h2>
<p style="color: #666; font-size: 14px;">1 May 2026 | TREVOR Assessment</p>
<hr>
<h3 style="color: #c0392b;">BLUF</h3>
<ul>
<li>Operation Epic Fury shifts to maritime blockade; ceasefire fragile</li>
<li>Strait of Hormuz closed; Brent crude at $124.67/bbl</li>
<li>Iran militia activity escalating across 6 countries</li>
<li>Protracted standoff risk increasing without diplomatic off-ramp</li>
<li>Ukraine leveraging crisis for Gulf security partnerships</li>
</ul>
<h3>Key Developments</h3>
<p><b>Middle East:</b> US-Israeli campaign transitioned to blockade enforcement (42 vessels turned back, 200 aircraft, 25 ships). Trump briefed on ground intervention and energy infrastructure strike options.</p>
<p><b>Energy:</b> Strait of Hormuz closure driving oil to multi-year highs. Maritime Freedom Construct proposed but diplomatic buy-in uncertain.</p>
<p><b>Ukraine:</b> Anti-drone specialists deployed to 5 Gulf states; security pacts signed with Saudi Arabia, Qatar, UAE.</p>
<p><b>Indo-Pacific:</b> China patrols near Scarborough Shoal; Trump Beijing visit approaching with Hormuz unresolved.</p>
<p style="color: #666; font-size: 11px;">Full PDF attached. TREVOR | 1 May 2026 20:30 UTC</p>
</body>
</html>

--{boundary}
Content-Type: application/pdf
Content-Disposition: attachment; filename="daily-brief-2026-05-01.pdf"
Content-Transfer-Encoding: base64

{pdf_b64}

--{boundary}--
"""

raw_b64 = base64.urlsafe_b64encode(email_body.encode()).decode()

payload = json.dumps({"raw": raw_b64}).encode()
req = urllib.request.Request(
    "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
    data=payload,
    method="POST"
)
req.add_header("Authorization", f"Bearer {api_key}")
req.add_header("Content-Type", "application/json")

try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    msg_id = result.get("id", "unknown")
    print(f"✅ Email sent! Message ID: {msg_id}")
    print(f"   To: Roderick.jones@gmail.com")
    print(f"   Subject: Daily Intelligence Briefing — 1 May 2026")
    print(f"   Attachment: daily-brief-2026-05-01.pdf")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {e.reason}")
    print(f"Response: {body[:300]}")
except Exception as e:
    print(f"❌ Error: {e}")
