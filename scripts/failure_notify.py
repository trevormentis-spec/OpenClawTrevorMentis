"""Send a failure notification email when the daily brief pipeline fails."""
import urllib.request, json, base64, sys

api_key = sys.argv[1] if len(sys.argv) > 1 else ""
date_utc = sys.argv[2] if len(sys.argv) > 2 else "unknown"
rc = sys.argv[3] if len(sys.argv) > 3 else "unknown"
log_path = sys.argv[4] if len(sys.argv) > 4 else "unknown"

subject = f"TREVOR Daily Brief -- FAILED -- {date_utc}"
body = f"""The daily brief pipeline failed on {date_utc} (rc={rc}).

Check the log at: {log_path}

TREVOR Automation"""

email = f"""From: trevor.mentis@gmail.com
To: roderick.jones@gmail.com
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/plain; charset="UTF-8"

{body}"""

raw = base64.urlsafe_b64encode(email.encode()).decode()
req = urllib.request.Request(
    "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
    data=json.dumps({"raw": raw}).encode(),
    method="POST",
)
req.add_header("Authorization", f"Bearer {api_key}")
req.add_header("Content-Type", "application/json")
try:
    urllib.request.urlopen(req, timeout=30)
    print("Failure notification sent to Roderick")
except Exception as e:
    print(f"Could not send failure notification: {e}")
