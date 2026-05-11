#!/usr/bin/env python3
"""Subscriber server — adds signups to Buttondown + notifies Trevor.

Receives POST requests from the landing page form and:
1. Adds the subscriber to Buttondown newsletter
2. Emails Trevor a notification

Run: python3 scripts/subscriber-server.py (port 19877)
"""
import json, os, urllib.request, base64
from http.server import HTTPServer, BaseHTTPRequestHandler

BUTTONDOWN_KEY = os.environ.get("BUTTONDOWN_API_KEY", "")
MATON_KEY = os.environ.get("MATON_API_KEY", "")
NEWSLETTER_ID = "news_3fze7q360q9kmrjsp8fvp6rqmr"

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        name = data.get("name", "N/A")
        email = data.get("email", "N/A")
        edition = data.get("edition", "N/A")
        org = data.get("organization", "N/A")
        source = data.get("source", "landing-page")

        results = []

        # 1. Add to Buttondown
        if BUTTONDOWN_KEY and email and email != "N/A":
            bd_payload = json.dumps({
                "email_address": email,
                "subscriber_type": "regular",
                "notes": f"Source: {source}, Name: {name}, Org: {org}, Edition: {edition}",
                "newsletter": NEWSLETTER_ID,
            }).encode()
            bd_req = urllib.request.Request(
                "https://api.buttondown.com/v1/subscribers",
                data=bd_payload, method="POST",
                headers={
                    "Authorization": f"Token {BUTTONDOWN_KEY}",
                    "Content-Type": "application/json",
                }
            )
            try:
                urllib.request.urlopen(bd_req, timeout=15)
                results.append("buttondown:ok")
                print(f"Buttondown subscriber added: {email}")
            except urllib.error.HTTPError as e:
                err = e.read().decode(errors="replace")[:200]
                if "already" in err.lower():
                    results.append("buttondown:already_exists")
                    print(f"Buttondown: {email} already subscribed")
                else:
                    results.append(f"buttondown:error {e.code}")
                    print(f"Buttondown failed for {email}: {err}")

        # 2. Email notification to Trevor
        subject = f"New GSIB Subscriber: {name} — {email}"
        text = (
            f"New subscriber for Global Security & Intelligence Brief\n\n"
            f"Name:     {name}\nEmail:    {email}\n"
            f"Edition:  {edition}\nOrg:      {org}\n"
            f"Source:   {source}\nButtondown: {'✓' if 'buttondown:ok' in results else 'already subscribed' if 'buttondown:already_exists' in results else 'failed'}\n"
            f"Time:    {__import__('datetime').datetime.utcnow().isoformat()}Z\n"
        )
        raw = f"From: Trevor <trevor.mentis@gmail.com>\nTo: Trevor <trevor.mentis@gmail.com>\nSubject: {subject}\nMIME-Version: 1.0\nContent-Type: text/plain; charset=\"UTF-8\"\n\n{text}"
        raw_b64 = base64.urlsafe_b64encode(raw.encode()).decode()
        payload = json.dumps({"raw": raw_b64}).encode()
        req = urllib.request.Request(
            "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
            data=payload, method="POST",
            headers={"Authorization": f"Bearer {MATON_KEY}", "Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req, timeout=15)
            results.append("email:ok")
        except Exception as e:
            results.append(f"email:error {e}")

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "results": results}).encode())

    def log_message(self, fmt, *args):
        print(f"[subscriber-svc] {fmt % args}")

if __name__ == "__main__":
    port = 19877
    print(f"Subscriber notification server running on port {port}")
    print(f"Buttondown: {'configured' if BUTTONDOWN_KEY else 'MISSING KEY'}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
