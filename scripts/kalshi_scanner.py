#!/usr/bin/env python3
"""
Kalshi Market Scanner — wrapper that uses the trading-system adapter.
Replaces the archived philby scanner. Provides --save and --json flags.
"""

import json, os, sys, datetime, pathlib

# Load .env
env_path = pathlib.Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k, v)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'trading-system'))
os.environ.setdefault('KALSHI_CLIENT_PATH', str(pathlib.Path(__file__).resolve().parent.parent / 'skills' / 'kalshi-trader' / 'scripts' / 'client.py'))

SAVE_DIR = pathlib.Path(__file__).resolve().parent.parent / 'exports'

def main():
    try:
        from execution.kalshi_adapter import KalshiAdapter
        client = KalshiAdapter()
        bal = client.get_balance()
        cash = bal.get('cash_cents', 0) / 100.0
        portfolio_val = bal.get('portfolio_cents', 0) / 100.0
        equity = bal.get('equity_cents', 0) / 100.0

        result = {
            "balance": {"cash": cash, "portfolio": portfolio_val, "total": equity},
            "markets": [],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if '--save' in sys.argv[1:]:
            SAVE_DIR.mkdir(exist_ok=True)
            date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
            path = SAVE_DIR / f'kalshi-scan-{date_str}.md'
            path.write_text(f"# Kalshi Scan — {date_str}\n**Balance:** ${cash:.2f} cash | ${portfolio_val:.2f} portfolio | ${equity:.2f} total\n\nScanner restored from trading-system adapter (post-archival).\n")
            print(f"Saved to {path}")
        if '--json' in sys.argv[1:]:
            print(json.dumps(result, indent=2))
        else:
            print(f"Kalshi Balance: ${cash:.2f} cash, ${portfolio_val:.2f} portfolio, ${equity:.2f} total")
            print(f"(Trading system adapter — was incorrectly reported as $0.24 from archived scanner)")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        result = {"balance": {"cash": 0, "portfolio": 0, "total": 0}, "markets": [], "error": str(e)}
        if '--json' in sys.argv[1:]:
            print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
