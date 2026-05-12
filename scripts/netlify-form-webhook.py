#!/usr/bin/env python3
"""
Netlify form submission webhook → AgentMail routing.
Receives Netlify form POSTs and forwards subscriber data to the intel brief pipeline.

Netlify configuration:
  Settings → Forms → Form notifications → "Send POST to URL"
  URL: https://<your-host>/api/netlify-form
  (Or deploy this as a serverless function)

For local/test usage: pipe the Netlify form payload to this script via stdin.
"""

import os
import sys
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ── Configuration ──
AGENTMAIL_TO = "trevor_mentis@agentmail.to"  # Inbox for subscriber routing
SUBSCRIBER_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "exports/subscribers.json"
)
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs"
)
PORT = int(os.environ.get("WEBHOOK_PORT", "8899"))

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SUBSCRIBER_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "netlify-webhook.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("netlify-webhook")


def send_agentmail_notification(email: str, name: str = "", message: str = ""):
    """
    Send a notification to the Trevor inbox via AgentMail API.
    Uses the AgentMail REST API directly.
    """
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key:
        log.warning("AGENTMAIL_API_KEY not set — cannot forward notification")
        return

    import urllib.request

    subject = f"New landing page subscriber: {email}"
    body = (
        f"New subscriber from landing page\n\n"
        f"Email: {email}\n"
        f"Name: {name or '(not provided)'}\n"
        f"Message: {message or '(none)'}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n\n"
        f"Action: Add to newsletter list and send welcome/intro brief."
    )

    payload = json.dumps({
        "to": AGENTMAIL_TO,
        "subject": subject,
        "body": body
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.agentmail.to/v1/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            log.info(f"AgentMail notification sent: {result.get('id', 'unknown')}")
            return result
    except Exception as e:
        log.error(f"AgentMail send failed: {e}")
        return None


def save_subscriber(data: dict):
    """Append subscriber to local JSON file."""
    subscribers = []
    if os.path.exists(SUBSCRIBER_FILE):
        with open(SUBSCRIBER_FILE, "r") as f:
            try:
                subscribers = json.load(f)
            except json.JSONDecodeError:
                subscribers = []
    
    subscribers.append({
        **data,
        "captured_at": datetime.utcnow().isoformat() + "Z"
    })
    
    with open(SUBSCRIBER_FILE, "w") as f:
        json.dump(subscribers, f, indent=2)
    
    log.info(f"Subscriber saved ({len(subscribers)} total)")


class WebhookHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Netlify form POSTs."""
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        # Parse form data (Netlify sends application/x-www-form-urlencoded)
        try:
            # Try JSON first
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Parse URL-encoded form
            import urllib.parse
            form_str = body.decode("utf-8")
            parsed = urllib.parse.parse_qs(form_str)
            data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        
        log.info(f"Form submission received: {json.dumps(data, default=str)[:200]}")
        
        # Extract contact fields (Netlify form standard fields)
        email = data.get("email", data.get("form-name", ""))
        name = data.get("name", "")
        message = data.get("message", "")
        
        if not email:
            self._respond(400, "Missing email field")
            return
        
        # Save locally
        save_subscriber({"email": email, "name": name, "message": message})
        
        # Forward to AgentMail
        send_agentmail_notification(email, name, message)
        
        self._respond(200, {"status": "ok", "message": "Subscriber recorded"})
    
    def do_GET(self):
        self._respond(200, {"status": "alive", "service": "Netlify form webhook"})
    
    def _respond(self, code: int, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
    
    def log_message(self, format, *args):
        log.info(f"{self.client_address[0]} - {format % args}")


def run_server():
    """Run the webhook server."""
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    log.info(f"Netlify webhook server running on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        run_server()
    else:
        # Stdin mode — read a single form submission from stdin
        payload = sys.stdin.read()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            import urllib.parse
            data = dict(urllib.parse.parse_qsl(payload))
        
        email = data.get("email", "unknown@test.com")
        name = data.get("name", "")
        message = data.get("message", "")
        
        save_subscriber(data)
        send_agentmail_notification(email, name, message)
        print(json.dumps({"status": "ok", "email": email}))
