#!/usr/bin/env python3
"""
DeepSeek Token & Cost Monitor for Trevor

Tracks DeepSeek API consumption by:
  1. Querying /user/balance for total remaining balance
  2. Parsing OpenClaw session trajectory files for per-session token usage
  3. Storing daily snapshots for historical tracking

Usage:
  python3 deepseek_monitor.py              # Show current dashboard
  python3 deepseek_monitor.py --snapshot    # Record a new balance + usage snapshot
  python3 deepseek_monitor.py --days 7      # Show last 7 days of usage
  python3 deepseek_monitor.py --help        # Full help

Data stored in: brain/memory/semantic/deepseek-usage.json
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Configuration ──────────────────────────────────────────────────────────

API_KEY = "sk-eee491c4ba5d45f8bc3b9d128e8bc894"
BALANCE_URL = "https://api.deepseek.com/user/balance"

WORKSPACE = Path.home() / ".openclaw" / "workspace"
TRACKING_FILE = WORKSPACE / "brain" / "memory" / "semantic" / "deepseek-usage.json"
SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"

# Pricing per 1M tokens (from https://api-docs.deepseek.com/quick_start/pricing)
PRICING = {
    "deepseek/deepseek-v4-flash": {
        "input_cache_hit": 0.0028,
        "input_cache_miss": 0.14,
        "output": 0.28,
        "label": "v4-Flash",
    },
    "deepseek-v4-flash": {
        "input_cache_hit": 0.0028,
        "input_cache_miss": 0.14,
        "output": 0.28,
        "label": "v4-Flash",
    },
    "deepseek/deepseek-v4-pro": {
        "input_cache_hit": 0.003625,
        "input_cache_miss": 0.435,
        "output": 0.87,
        "label": "v4-Pro",
        "note": "75% discount until 2026-05-31",
    },
    "deepseek-v4-pro": {
        "input_cache_hit": 0.003625,
        "input_cache_miss": 0.435,
        "output": 0.87,
        "label": "v4-Pro",
        "note": "75% discount until 2026-05-31",
    },
    "deepseek/deepseek-chat": {
        "input_cache_hit": 0.0028,
        "input_cache_miss": 0.14,
        "output": 0.28,
        "label": "v4-Flash (legacy alias)",
    },
}

# Models that don't use DeepSeek (tracked separately)
OTHER_PROVIDERS = {"gemini-3-flash", "minimax-m2.7", "kimi-k2.5"}

# ── Helpers ────────────────────────────────────────────────────────────────

def fetch_balance():
    """Query DeepSeek balance API. Returns dict or None."""
    req = Request(BALANCE_URL, headers={"Authorization": f"Bearer {API_KEY}"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            balance_infos = data.get("balance_infos", [])
            for bi in balance_infos:
                if bi.get("currency") == "USD":
                    return {
                        "total_balance": float(bi.get("total_balance", 0)),
                        "topped_up_balance": float(bi.get("topped_up_balance", 0)),
                        "granted_balance": float(bi.get("granted_balance", 0)),
                        "is_available": data.get("is_available", False),
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
    except URLError as e:
        return {"error": str(e)}
    return {"error": "No USD balance found"}


def load_tracking():
    """Load stored usage tracking data."""
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "snapshots": [],
        "daily_summaries": {},
        "session_usage": [],
        "last_scan_time": None,
    }


def save_tracking(data):
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKING_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def scan_session_usage(data):
    """Scan OpenClaw session trajectory files for model usage."""
    if not SESSIONS_DIR.exists():
        return data

    last_scan = data.get("last_scan_time")
    if last_scan:
        last_scan_dt = datetime.fromisoformat(last_scan)
    else:
        last_scan_dt = datetime.min.replace(tzinfo=timezone.utc)

    new_sessions = []
    # Scan all trajectory JSONL files in the sessions directory
    traj_files = sorted(SESSIONS_DIR.glob("*.trajectory.jsonl"))
    for traj_file in traj_files:
        # Extract the session key from filename (before .trajectory.jsonl)
        session_key = traj_file.stem.replace(".trajectory", "")
        
        with open(traj_file) as tf:
            for line in tf:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "model.completed":
                    edata = entry.get("data", {})
                    usage = edata.get("usage", {})
                    if usage and usage.get("total", 0) > 0:
                        input_tok = usage.get("input", 0)
                        output_tok = usage.get("output", 0)
                        cache_read = usage.get("cacheRead", 0)
                        # modelId and provider are at the entry top level, not inside data
                        model_id = entry.get("modelId", edata.get("modelId", "unknown"))
                        provider = entry.get("provider", edata.get("provider", "unknown"))
                        is_deepseek = provider == "deepseek" or model_id.startswith("deepseek")
                        
                        # Estimate cost from pricing tables
                        pricing_entry = PRICING.get(model_id, {})
                        if pricing_entry:
                            input_cost = (input_tok / 1_000_000) * pricing_entry["input_cache_miss"]
                            output_cost = (output_tok / 1_000_000) * pricing_entry["output"]
                            estimated_cost = input_cost + output_cost
                        else:
                            estimated_cost = 0.0
                        
                        session_entry = {
                            "session_id": session_key,
                            "timestamp": entry.get("ts", ""),
                            "input_tokens": input_tok,
                            "output_tokens": output_tok,
                            "total_tokens": usage.get("total", 0),
                            "cache_read": cache_read,
                            "cache_write": usage.get("cacheWrite", 0),
                            "estimated_cost": round(estimated_cost, 8),
                            "model": model_id,
                            "provider": provider,
                        }
                        new_sessions.append(session_entry)
                        break

    # Merge with existing, deduplicate by session_id
    existing_ids = {s["session_id"] for s in data.get("session_usage", [])}
    fresh = [s for s in new_sessions if s["session_id"] not in existing_ids]
    fresh.sort(key=lambda x: x["timestamp"])
    data.setdefault("session_usage", []).extend(fresh)
    data["last_scan_time"] = datetime.now(timezone.utc).isoformat()
    return data


def compute_daily_summary(data):
    """Aggregate session usage into daily summaries with cost estimates."""
    daily = {}
    for s in data.get("session_usage", []):
        ts = s.get("timestamp", "")
        try:
            day = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            day = "unknown"

        if day not in daily:
            daily[day] = {
                "sessions": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cache_read": 0,
                "cache_write": 0,
                "cost_usd": 0.0,
                "by_model": {},
            }

        d = daily[day]
        d["sessions"] += 1
        d["input_tokens"] += s.get("input_tokens", 0)
        d["output_tokens"] += s.get("output_tokens", 0)
        d["total_tokens"] += s.get("total_tokens", 0)
        d["cache_read"] += s.get("cache_read", 0)
        d["cache_write"] += s.get("cache_write", 0)
        d["cost_usd"] += s.get("estimated_cost", 0)

        model = s.get("model", "unknown")
        if model not in d["by_model"]:
            d["by_model"][model] = {"sessions": 0, "tokens": 0, "cost": 0.0}
        d["by_model"][model]["sessions"] += 1
        d["by_model"][model]["tokens"] += s.get("total_tokens", 0)
        d["by_model"][model]["cost"] += s.get("estimated_cost", 0)

    data["daily_summaries"] = dict(sorted(daily.items(), reverse=True))
    return data


def record_snapshot(data):
    """Record a new balance + usage snapshot."""
    balance = fetch_balance()
    if "error" in balance:
        return data, f"Error fetching balance: {balance['error']}"

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "balance": balance,
        "total_sessions_tracked": len(data.get("session_usage", [])),
    }

    # Compute cumulative stats
    all_sessions = data.get("session_usage", [])
    if all_sessions:
        snapshot["cumulative"] = {
            "total_sessions": len(all_sessions),
            "total_input_tokens": sum(s.get("input_tokens", 0) for s in all_sessions),
            "total_output_tokens": sum(s.get("output_tokens", 0) for s in all_sessions),
            "total_tokens": sum(s.get("total_tokens", 0) for s in all_sessions),
            "total_cost_usd": round(sum(s.get("estimated_cost", 0) for s in all_sessions), 6),
        }

    data.setdefault("snapshots", []).append(snapshot)
    return data, None


def format_dashboard(data):
    """Render the monitoring dashboard."""
    lines = []
    lines.append("=" * 56)
    lines.append("  DEEPSEEK USAGE MONITOR — Trevor Agent")
    lines.append("=" * 56)
    lines.append("")

    # Current balance
    snapshots = data.get("snapshots", [])
    if snapshots:
        latest = snapshots[-1]
        bal = latest.get("balance", {})
        if "error" not in bal:
            lines.append(f"  💰 Balance:        ${bal.get('total_balance', '?'):>8.2f} USD")
            lines.append(f"     Topped-up:      ${bal.get('topped_up_balance', '?'):>8.2f}")
            lines.append(f"     Granted:        ${bal.get('granted_balance', '?'):>8.2f}")
            lines.append(f"     Last check:     {bal.get('fetched_at', '?')[:19]}")
            lines.append("")

            # Balance trend (last N snapshots)
            if len(snapshots) >= 2:
                prev = snapshots[-2].get("balance", {})
                prev_bal = prev.get("total_balance", 0)
                if prev_bal:
                    diff = float(bal.get("total_balance", 0)) - float(prev_bal)
                    sign = "+" if diff >= 0 else ""
                    pct = (diff / float(prev_bal)) * 100
                    lines.append(f"  📉 Change vs prev: {sign}${diff:.2f} ({sign}{pct:.2f}%)")
                    # Calculate burn rate from snapshots
                    ts_diff = datetime.fromisoformat(latest["timestamp"].replace("Z", "+00:00")) - \
                              datetime.fromisoformat(snapshots[-2]["timestamp"].replace("Z", "+00:00"))
                    hours = ts_diff.total_seconds() / 3600
                    if hours > 0 and diff < 0:
                        daily_burn = abs(diff) / hours * 24
                        lines.append(f"     Burn rate:      ~${daily_burn:.2f}/day")
                        days_left = float(bal.get("total_balance", 0)) / max(daily_burn, 0.01)
                        lines.append(f"     Runway:         ~{days_left:.1f} days")
                lines.append("")
    else:
        lines.append("  💰 Balance:        Not yet fetched")
        lines.append("")

    # Session summary
    sessions = data.get("session_usage", [])
    daily = data.get("daily_summaries", {})
    lines.append(f"  📊 Sessions tracked:  {len(sessions)}")
    lines.append(f"  📅 Days with data:    {len(daily)}")
    lines.append("")

    # Today's usage
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today in daily:
        td = daily[today]
        lines.append(f"  ┌─ Today ({today})")
        lines.append(f"  │  Sessions:       {td['sessions']}")
        lines.append(f"  │  Input tokens:   {td['input_tokens']:>10,}")
        lines.append(f"  │  Output tokens:  {td['output_tokens']:>10,}")
        lines.append(f"  │  Total tokens:   {td['total_tokens']:>10,}")
        lines.append(f"  │  Est. cost:      ${td['cost_usd']:.6f}")
        lines.append("")

    # Last 7 days summary
    week_days = [d for d in sorted(daily.keys(), reverse=True) if d <= today]
    week_days = week_days[:7]
    if week_days:
        lines.append(f"  ┌─ Last {len(week_days)} days")
        wk_sessions = sum(daily[d]["sessions"] for d in week_days)
        wk_tokens = sum(daily[d]["total_tokens"] for d in week_days)
        wk_cost = sum(daily[d]["cost_usd"] for d in week_days)
        lines.append(f"  │  Sessions:       {wk_sessions}")
        lines.append(f"  │  Total tokens:   {wk_tokens:>10,}")
        lines.append(f"  │  Total cost:     ${wk_cost:.4f}")
        lines.append("")

    # Pricing reference (unique models only)
    lines.append("  ┌─ Pricing (per 1M tokens)")
    seen_pricing = set()
    for model in ["deepseek/deepseek-v4-flash", "deepseek/deepseek-v4-pro"]:
        prices = PRICING.get(model, {})
        if not prices:
            continue
        key = f"{prices['input_cache_miss']}|{prices['output']}"
        if key in seen_pricing:
            continue
        seen_pricing.add(key)
        short = model.split("/")[-1]
        note = prices.get("note", "")
        lines.append(f"  │  {short:30s}  Input: ${prices['input_cache_miss']:.4f}  Output: ${prices['output']:.4f}  {note}")
    lines.append("")

    # Models used
    model_counts = {}
    for s in sessions:
        m = s.get("model", "unknown")
        model_counts[m] = model_counts.get(m, 0) + 1
    if model_counts:
        lines.append("  ┌─ Models used")
        for m, c in sorted(model_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  │  {m:35s} {c} sessions")
        lines.append("")

    lines.append("=" * 56)
    lines.append(f"  Data: {TRACKING_FILE}")
    lines.append(f"  Last scan: {data.get('last_scan_time', 'never')[:19]}")
    lines.append("=" * 56)

    return "\n".join(lines)


def format_daily_table(data, days=7):
    """Show a daily breakdown table."""
    daily = data.get("daily_summaries", {})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    dates = sorted([d for d in daily.keys() if d <= today], reverse=True)[:days]
    if not dates:
        return "No daily data yet."

    lines = []
    lines.append(f"{'Date':<12} {'Sessions':>9} {'Input Tokens':>14} {'Output Tokens':>14} {'Total':>14} {'Cost':>10}")
    lines.append("-" * 75)
    for d in dates:
        v = daily[d]
        lines.append(f"{d:<12} {v['sessions']:>9} {v['input_tokens']:>14,} {v['output_tokens']:>14,} {v['total_tokens']:>14,} ${v['cost_usd']:<8.4f}")

    total_s = sum(daily[d]["sessions"] for d in dates)
    total_i = sum(daily[d]["input_tokens"] for d in dates)
    total_o = sum(daily[d]["output_tokens"] for d in dates)
    total_t = sum(daily[d]["total_tokens"] for d in dates)
    total_c = sum(daily[d]["cost_usd"] for d in dates)
    lines.append("-" * 75)
    lines.append(f"{'TOTAL':<12} {total_s:>9} {total_i:>14,} {total_o:>14,} {total_t:>14,} ${total_c:<8.4f}")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DeepSeek Token & Cost Monitor")
    parser.add_argument("--snapshot", action="store_true", help="Record a new balance snapshot")
    parser.add_argument("--days", type=int, default=0, help="Show daily table for N days")
    parser.add_argument("--scan", action="store_true", help="Force re-scan session files")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard (default)")
    args = parser.parse_args()

    data = load_tracking()

    if args.scan or args.snapshot:
        data = scan_session_usage(data)
        data = compute_daily_summary(data)

    if args.snapshot:
        data, err = record_snapshot(data)
        if err:
            print(f"Error: {err}")
            sys.exit(1)
        print(f"✅ Snapshot recorded — balance ${data['snapshots'][-1]['balance']['total_balance']}")
        # Also update TOOLS.md reference
        with open(WORKSPACE / "TOOLS.md") as f:
            tools = f.read()
        print("   (balance data saved to brain/memory/semantic/deepseek-usage.json)")

    if args.days > 0:
        if not args.snapshot and not args.scan:
            # Still need to scan for data if not done above
            data = scan_session_usage(data)
            data = compute_daily_summary(data)
        print(format_daily_table(data, args.days))

    if args.dashboard or not (args.snapshot or args.days):
        if not args.scan and not args.snapshot:
            data = scan_session_usage(data)
            data = compute_daily_summary(data)
        print(format_dashboard(data))

    save_tracking(data)


if __name__ == "__main__":
    main()
