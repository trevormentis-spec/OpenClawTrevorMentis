#!/usr/bin/env python3
"""Minimal HTTP server that receives subscriber signups and emails Trevor."""
import json, base64, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

MATON_KEY = os.environ.get("MATON_API_KEY", "v2.6nu4_hHJrTgK89bZgm51KLvKHkKptaQUJ-gCUQYtBccrIrto5Orulq6RYk8oE_kqxnj-Aros5JlV0o2D9W4l-usvIRllBBpZ_5jZiD0fyWDQBfzre1IXFEib")

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
        use_case = data.get("use_case", "N/A")
        trial = data.get("trial", "N/A")

        # Email notification to Trevor
        subject = f"New Subscriber: {name} — {edition}"
        text = (
            f"New subscriber for the Global Security & Intelligence Brief\n\n"
            f"Name:       {name}\nEmail:      {email}\n"
            f"Edition:    {edition}\nTrial:      {trial}\n"
            f"Org:        {org}\nUse Case:   {use_case}\n"
            f"Time:       {__import__('datetime').datetime.utcnow().isoformat()}Z\n"
        )

        raw = f"From: Trevor <trevor.mentis@gmail.com>\nTo: Trevor <trevor.mentis@gmail.com>\nSubject: {subject}\nMIME-Version: 1.0\nContent-Type: text/plain; charset=\"UTF-8\"\n\n{text}"
        raw_b64 = base64.urlsafe_b64encode(raw.encode()).decode()

        payload = json.dumps({"raw": raw_b64}).encode()
        req = urllib.request.Request(
            "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
            data=payload, method="POST"
        )
        req.add_header("Authorization", f"Bearer {MATON_KEY}")
        req.add_header("Content-Type", "application/json")
        try:
            urllib.request.urlopen(req, timeout=15)
            print(f"Subscriber notified: {name} <{email}>")
        except Exception as e:
            print(f"Notify failed: {e}")

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def log_message(self, fmt, *args):
        print(f"[subscriber-svc] {fmt % args}")

if __name__ == "__main__":
    port = 19877
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Subscriber notification server running on port {port}")
    server.serve_forever()
