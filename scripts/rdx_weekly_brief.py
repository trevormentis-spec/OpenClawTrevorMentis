#!/usr/bin/env python3
"""
RDX/C4 Weekly Brief — automated production pipeline.

Runs all collectors, compiles data, generates report via Opus 4.7,
humanizes, sends to roderick.jones@gmail.com.

Schedule: weekly (default Monday 08:00 PT)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import base64
import email.mime.text

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "analyst" / "knowledge" / "rdx_c4_supply" / "data_feeds"

env = open(REPO_ROOT / ".env").read()
env_vars = {}
for line in env.split("\n"):
    if "=" in line:
        k, v = line.strip().split("=", 1)
        env_vars[k] = v.strip().strip("'\"")


def log(msg):
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[rdx-weekly {ts}] {msg}", file=sys.stderr, flush=True)


def run(cmd, timeout=180):
    """Run a shell command and return output."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, **env_vars})
    if result.returncode != 0:
        log(f"  WARNING: '{' '.join(cmd[:3])}' exited {result.returncode}: {result.stderr[:100]}")
    return result.stdout


def load(prefix):
    files = sorted(DATA_DIR.glob(f"{prefix}-*.json"), reverse=True)
    if files:
        try:
            return json.loads(files[0].read_text())
        except:
            return {}
    return {}


def build_data_packet() -> str:
    """Gather all collector data into a prompt for Opus."""
    gdelt = load("gdelt-sweep")
    jobs = load("job-signals")
    pats = load("patents")
    trade = load("trade-remedy")
    car = load("car-reports")
    epa = load("epa-tri")
    osint = load("osint-events")

    gdelt_articles = gdelt.get("articles", []) if isinstance(gdelt, dict) else []
    job_signals = jobs.get("signals", []) if isinstance(jobs, dict) else []
    trade_actions = trade.get("actions", []) if isinstance(trade, dict) else []
    car_reports = car.get("reports", []) if isinstance(car, dict) else []
    epa_facilities = epa.get("facilities", []) if isinstance(epa, dict) else []
    osint_events = osint.get("events", []) if isinstance(osint, dict) else []

    packet = f"""Current date: {dt.date.today().isoformat()}
Previous report date: {(dt.date.today() - dt.timedelta(days=7)).isoformat()}

MARKET CONTEXT:
- Global RDX market: projected $13.77B by 2029, 5.7% CAGR
- Annual production: 60,000+ metric tons
- Demand drivers: Ukraine artillery consumption, Asia-Pacific mining, insensitive munitions migration
- European nitrocellulose gap: 4,500-10,000 t/y output vs 20,000 t target
- Holston Army Ammunition Plant (Tennessee) is sole US RDX/HMX producer
- Nitro-Chem (Poland) is sole NATO TNT producer

SIGNALS THIS CYCLE:

1. GDELT NEWS ({len(gdelt_articles)} articles):
{chr(10).join(f"   - {a.get('title','')[:100]}" for a in (gdelt_articles if isinstance(gdelt_articles, list) else [])[:10]) or '   - None found'}

2. JOB POSTINGS (hiring = expansion):
{chr(10).join(f"   - {s['query']}: {'active hiring' if s.get('status') == 'active_hiring' else 'static'}" for s in job_signals) or '   - None found'}

3. PATENTS (R&D direction):
{chr(10).join(f"   - {p['title'][:100]}" for p in pats.get('patents', [])[:5]) or '   - None found'}

4. TRADE REMEDIES (precursor supply chain):
{chr(10).join(f"   - {a.get('source','')}: {a.get('title','')[:80]}" for a in (trade_actions if isinstance(trade_actions, list) else [])[:5]) or '   - None found'}

5. CONFLICT ARMAMENT RESEARCH (munitions tracing):
{chr(10).join(f"   - {r.get('title','')[:100]}" for r in (car_reports if isinstance(car_reports, list) else [])[:5]) or '   - None found'}

6. EPA TOXICS RELEASE INVENTORY (production proxy):
{chr(10).join(f"   - {f.get('facility','')}: {f.get('status','')}" for f in epa_facilities) or '   - None found'}

7. RUSSIAN PLANT OSINT EVENTS:
{chr(10).join(f"   - {e.get('channel','')}: {e.get('producer','')}" for e in (osint_events if isinstance(osint_events, list) else [])[:5]) or '   - None found'}

PRODUCER TRACKER:
- Holston AAP (USA): sole US RDX/HMX producer. BAE Systems GOCO contract through 2033. Modernization underway.
- Eurenco Bergerac (France): European RDX anchor. Restarted line for Ukraine demand.
- Nitro-Chem (Poland): sole NATO TNT. $310M US contract for 18,000t through 2029.
- Chemring Nobel (Norway): RDX, HMX, PETN.
- Rheinmetall Varpalota (Hungary): new plant commissioning.
- Hanwha (South Korea): major Asian producer.
- Solar Industries (India): expanding industrial and military output.
- Sverdlov Plant (Russia): damaged by strike April 30, 2026.
- Bryansk Chemical (Russia): struck May 2026.
- JSC Promsintez (Russia): struck March 28, 2026."""

    return packet


def call_opus(prompt: str) -> str:
    """Generate report via Opus 4.7."""
    key = env_vars.get("OPENROUTER_API_KEY", "")
    if not key:
        log("ERROR: No OPENROUTER_API_KEY")
        return ""

    system = (
        "You are an intelligence analyst writing a weekly market briefing about RDX and C4 explosives. "
        "Write for a general audience. Spell out every acronym on first use. "
        "Use plain, direct language. No jargon. No markdown. "
        "Use === section separators. "
        "Use Sherman Kent probability bands (likely: 55-70%, highly likely: 75-85%) for forward judgments. "
        "Include a sources section listing all data feeds. "
        "Include a 'what to watch' section with 5 specific things."
    )

    user = (
        f"Produce a weekly market briefing on the global RDX and C4 explosives market "
        f"based on the data below. Structure it as:\n\n"
        f"=== EXECUTIVE SUMMARY ===\n"
        f"What changed this week, the most important signal, what it means.\n\n"
        f"=== PRODUCER ACTIVITY ===\n"
        f"Notable events at each major facility.\n\n"
        f"=== SIGNALS & INDICATORS ===\n"
        f"What the data feeds show this week.\n\n"
        f"=== WHAT TO WATCH ===\n"
        f"5 specific things for the next 30 days with probability bands.\n\n"
        f"=== SOURCES ===\n"
        f"List every data feed used.\n\n"
        f"Here is the data:\n\n{prompt}"
    )

    payload = json.dumps({
        "model": "anthropic/claude-opus-4.7",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": 8192,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
            "X-Title": "TrevorIntel",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        log(f"Opus call failed: {e}")
        return ""


def humanize(text: str) -> str:
    """Apply basic humanizer rules."""
    import re
    
    replacements = [
        (r"(?i)\bin order to\b", "to"),
        (r"(?i)\bdue to the fact that\b", "because"),
        (r"(?i)\bat this point in time\b", "now"),
        (r"(?i)\bhas the ability to\b", "can"),
        (r"(?i)\bit is important to note that\b", ""),
        (r"(?i)\bit is worth noting that\b", ""),
        (r"(?i)\badditionally,\s*", ""),
        (r"(?i)\bfurthermore,\s*", ""),
        (r"(?i)\bmoreover,\s*", ""),
        (r"(?i)\bserves? as\b", "is"),
    ]
    
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    
    # Condense double spaces and line breaks
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"\n{4,}", "\n\n", text)
    
    return text


def send_gmail(body: str) -> bool:
    """Send via Gmail API."""
    key = env_vars.get("MATON_API_KEY", "")
    if not key:
        log("ERROR: No MATON_API_KEY")
        return False

    date_str = dt.date.today().strftime("%B %d, %Y")
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["To"] = "roderick.jones@gmail.com"
    msg["From"] = "trevor.mentis@gmail.com"
    msg["Subject"] = f"RDX & C4 Supply Market: Weekly Brief — {date_str}"

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    payload = json.dumps({"raw": raw}).encode("utf-8")

    req = urllib.request.Request(
        "https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            log(f"Sent: {result.get('id', 'unknown')}")
            return True
    except Exception as e:
        log(f"Send failed: {e}")
        return False


def main():
    log("Starting RDX/C4 weekly brief pipeline...")

    # Step 1: Run all collectors
    log("Step 1: Running collectors...")
    run([sys.executable, str(REPO_ROOT / "scripts" / "rdx_collectors.py"), "--all-daily"], timeout=120)
    run([sys.executable, str(REPO_ROOT / "scripts" / "rdx_collectors.py"), "--all-creative"], timeout=120)

    # Step 2: Build data packet
    log("Step 2: Building data packet...")
    data = build_data_packet()
    log(f"  Data packet: {len(data)} chars")

    # Step 3: Generate report via Opus
    log("Step 3: Calling Opus 4.7...")
    report = call_opus(data)
    if not report:
        log("FATAL: Report generation failed")
        sys.exit(1)
    log(f"  Report: {len(report)} chars")

    # Step 4: Humanize
    log("Step 4: Humanizing...")
    report = humanize(report)
    log(f"  Humanized: {len(report)} chars")

    # Step 5: Save
    date_slug = dt.date.today().isoformat()
    out_path = REPO_ROOT / "exports" / f"rdx-weekly-brief-{date_slug}.txt"
    out_path.write_text(report)
    log(f"  Saved: {out_path}")

    # Step 6: Send
    log("Step 5: Sending via Gmail...")
    if send_gmail(report):
        log("✅ Weekly brief delivered")
    else:
        log("❌ Delivery failed")
        sys.exit(1)

    # Step 7: Log to memory
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from scripts.report_memory import log_report
        log_report("rdx_weekly_brief", date_slug, str(out_path),
                   report[:200], len(report.split()), model="opus-4.7",
                   key_judgments=["Weekly RDX/C4 market update compiled from all 16 feeds"])
    except Exception:
        pass


if __name__ == "__main__":
    main()
