#!/usr/bin/env python3
"""
Deliver the daily GSIB brief as a clean email with prediction markets and suggested trades.
No PDF. No graphics. No GenViral imagery. Just intelligence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
from zoneinfo import ZoneInfo

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEFINGS_DIR = pathlib.Path.home() / "trevor-briefings"
EXPORTS_DIR = REPO_ROOT / "exports"
CALIBRATION_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
TRADE_ENGINE = REPO_ROOT / "scripts" / "trade_engine.py"

TICKER_LABELS = {
    "KXUSAIRANAGREEMENT": "US-Iran Agreement", "KXPAHLAVIVISITA": "Pahlavi Visit to Iran",
    "KXWTIMAX": "Brent > $X", "KXREACTOR": "Iran Reactor Attack",
    "KXTRUMPIRAN": "Trump Iran Strike", "KXIRANDEMOCRACY": "Iran Democracy",
    "KXIRANEMBASSY": "Iran Embassy Attack", "KXELECTIRAN": "Iran Election",
    "KXWTIMIN": "Brent < $X",
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[deliver {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict | list:
    if path.exists():
        try: return json.loads(path.read_text())
        except Exception: return {}
    return {}


def parse_kalshi_scan(kalshi_file: pathlib.Path) -> list[dict]:
    """Parse Kalshi scan markdown into structured market data."""
    if not kalshi_file.exists():
        log(f"Kalshi scan not found: {kalshi_file}")
        return []
    markets = []
    for line in kalshi_file.read_text().split("\n"):
        parts = line.strip().split()
        # Cols: Series(0) YesBid(1) YesAsk(2) NoBid(3) NoAsk(4) Spread(5) Volume(6) Expiry(7)
        if len(parts) >= 8 and parts[0].startswith("KX"):
            try:
                b, a = parts[1].replace("$",""), parts[2].replace("$","")
                v = parts[6].replace(",","").replace("$","")
                markets.append({"ticker": parts[0], "label": TICKER_LABELS.get(parts[0], parts[0]),
                    "mid": round((float(b)+float(a))/2, 2) if b != "--" and a != "--" else None,
                    "volume": int(v) if v != "--" and v != "0.00" else 0,
                    "expiry": parts[7]})
            except (ValueError, IndexError): continue
    return markets


def build_prediction_market_section(markets: list[dict], limit: int = 15) -> str:
    if not markets: return ""
    mkts = sorted([m for m in markets if m.get("volume",0) > 0], key=lambda m: m["volume"], reverse=True)[:limit]
    if not mkts: return ""
    lines = ["","="*60,"PREDICTION MARKETS (Kalshi)","="*60,"",
             f"  {'Market':35s} {'Yes':8s} {'Volume':12s} {'Expiry':12s}","  "+"-"*65]
    for m in mkts:
        label = m["label"][:33]
        yes = f"${m['mid']:.2f}" if m["mid"] else "--"
        vol = f"${m['volume']:,}" if m["volume"] > 0 else "--"
        lines.append(f"  {label:35s} {yes:8s} {vol:12s} {m['expiry'][:10]:12s}")
    lines.append("")
    return "\n".join(lines)


def build_suggested_trades(judgments: list[dict], markets: list[dict], date_str: str) -> str:
    lines = ["","="*60,"SUGGESTED TRADES (Intel x Market Cross-Reference)","="*60,""]
    if not judgments or not markets or not TRADE_ENGINE.exists():
        lines.append("Trade suggestion engine unavailable.")
        return "\n".join(lines)

    payload = {"judgments": [{"statement":kj.get("statement",""),"region":kj.get("drawn_from_region","?"),
        "band":kj.get("sherman_kent_band","?"),"probability_pct":kj.get("prediction_pct",50)}
        for kj in judgments],
        "markets": [{"ticker":m["ticker"],"label":m.get("label",m["ticker"]),
        "market_price_cents":int(m["mid"]*100) if m["mid"] else None,"volume":m["volume"]}
        for m in markets if m.get("mid")]}

    tmp = REPO_ROOT/"tmp"; tmp.mkdir(exist_ok=True)
    pf = tmp/"trade-payload.json"
    pf.write_text(json.dumps(payload), encoding="utf-8")
    try:
        r = subprocess.run(["python3",str(TRADE_ENGINE),str(pf)], capture_output=True, text=True, timeout=90, cwd=str(REPO_ROOT))
        t = r.stdout.strip()
        if t and "NO TRADES" not in t:
            lines.append(t); lines.append(""); lines.append("*Trades are analytical suggestions, not financial advice.*")
        else:
            lines.append("No actionable divergences identified between intelligence judgments and current market pricing at this time.")
    except Exception as e:
        log(f"Trade engine failed: {e}")
        lines.append("Trade suggestion engine unavailable.")
    finally:
        if pf.exists(): pf.unlink()
    return "\n".join(lines)


def build_email_body(date_str: str, exec_data: dict, kalshi_file: pathlib.Path, cal_data: dict | None = None) -> str:
    bluf = exec_data.get("bluf", "")
    context = exec_data.get("context_paragraph", "")
    judgments = exec_data.get("five_judgments", [])
    markets = parse_kalshi_scan(kalshi_file)

    lines = ["="*60, f"GLOBAL SECURITY & INTELLIGENCE BRIEF", f"{date_str}", "="*60, "", "BLUF", "-"*20, ""]
    for chunk in bluf.split(". "):
        chunk = chunk.strip()
        if chunk:
            if not chunk.endswith("."): chunk += "."
            lines.append(f"  {chunk}"); lines.append("")
    lines.append("")

    if context:
        sentences = [s.strip() + "." for s in context.split(". ") if s.strip() and not s.strip().endswith(".")]
        sentences = [s for s in sentences if len(s) > 5]
        if not sentences:
            sentences = [context]
        para = []
        for i, s in enumerate(sentences):
            if s: para.append(s)
            if len(para) >= 3 or i == len(sentences) - 1:
                lines.append("  " + " ".join(para)); lines.append(""); para = []

    if judgments:
        lines.append("KEY JUDGMENTS"); lines.append("-"*20); lines.append("")
        for kj in judgments:
            r = kj.get("drawn_from_region","??").upper()
            s = kj.get("statement","")
            b = kj.get("sherman_kent_band","?")
            p = kj.get("prediction_pct","?")
            lines.append(f"  [{r}]"); lines.append(f"  {s}"); lines.append(f"  -> Confidence: {b} ({p}% / 7d)"); lines.append("")

    if cal_data and cal_data.get("total_judgments",0) > 0:
        t, c, inc, un = cal_data["total_judgments"], cal_data.get("correct",0), cal_data.get("incorrect",0), cal_data.get("unresolved",0)
        r = c + inc  # resolved = correct + incorrect; exclude unresolved from accuracy
        if r > 0:
            acc = round(c / r * 100, 1)
            lines.append(f"  Calibration: {c}/{r} resolved correct ({acc}%) | {inc} incorrect | {un} pending (unresolvable <7d)"); lines.append("")
        elif t > 0:
            lines.append(f"  Calibration: {t} judgments tracked, none resolved yet (predictions need 7d to verify)"); lines.append("")

    pm = build_prediction_market_section(markets)
    if pm: lines.append(pm)
    lines.append(build_suggested_trades(judgments, markets, date_str))
    lines.extend(["","-"*60,"Prepared by TREVOR Intelligence","Prediction market data from Kalshi. Not financial advice.",""])
    return "\n".join(lines)


def send_email(subject: str, body: str) -> bool:
    send_script = REPO_ROOT / "skills" / "agentmail" / "scripts" / "send_email.py"
    if not send_script.exists(): return False
    body_file = REPO_ROOT / "tmp" / "brief-email-body.txt"
    REPO_ROOT.joinpath("tmp").mkdir(exist_ok=True)
    body_file.write_text(body, encoding="utf-8")
    try:
        r = subprocess.run(["python3",str(send_script),"--inbox","trevor_mentis@agentmail.to",
            "--to","roderick.jones@gmail.com","--subject",subject,"--text",body_file.read_text(encoding="utf-8")],
            capture_output=True, text=True, timeout=60, cwd=str(REPO_ROOT))
        log(f"Email sent: {subject}" if r.returncode == 0 else f"Email failed: {r.stderr[:200]}")
        return r.returncode == 0
    except Exception as e:
        log(f"Email error: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="", help="Date YYYY-MM-DD (default: today)")
    parser.add_argument("--send", action="store_true", help="Send via AgentMail (default: print to stdout)")
    args = parser.parse_args()

    date_str = args.date or dt.datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    exec_file = (BRIEFINGS_DIR / date_str / "analysis" / "exec_summary.json")
    if not exec_file.exists():
        log(f"ERROR: exec_summary.json not found at {exec_file}"); return 1

    exec_data = load_json(exec_file)
    if not exec_data: return 1

    kalshi_files = sorted(EXPORTS_DIR.glob(f"kalshi-scan-*.md"), reverse=True)
    kalshi_file = kalshi_files[0] if kalshi_files else pathlib.Path("/dev/null")
    cal_data = load_json(CALIBRATION_FILE) if CALIBRATION_FILE.exists() else None

    log(f"Building brief email for {date_str}")
    body = build_email_body(date_str, exec_data, kalshi_file, cal_data)
    subject = f"Global Security & Intelligence Brief - {date_str}"

    if args.send:
        return 0 if send_email(subject, body) else 1
    else:
        print(body); log(f"Body: {len(body)} chars"); return 0

if __name__ == "__main__":
    sys.exit(main())
