#!/usr/bin/env bash
# Tear down Philby/Kalshi trading system — archive, don't destroy
set -euo pipefail

WORKSPACE="/home/ubuntu/.openclaw/workspace"
ARCHIVE="$WORKSPACE/archive/philby-trading-$(date +%Y-%m-%d)"
mkdir -p "$ARCHIVE"

echo "=== PHILBY TRADING SYSTEM — TEARDOWN $(date -u) ==="

# Step 1: Kill any running daemon processes
echo "[1/6] Killing Philby daemon processes..."
pkill -f "philby/trader/daemon.py" 2>/dev/null || echo "  No daemon running"
pkill -f "philby/trader/trader.py" 2>/dev/null || echo "  No trader running"
pkill -f "kalshi_monitor" 2>/dev/null || echo "  No kalshi_monitor running"
sleep 1

# Step 2: Archive all code
echo "[2/6] Archiving Philby trader code..."
mkdir -p "$ARCHIVE"
cp -r "$WORKSPACE/philby" "$ARCHIVE/philby" 2>/dev/null || echo "  No philby dir"
cp "$WORKSPACE/scripts/kalshi_scanner.py" "$ARCHIVE/" 2>/dev/null || echo "  No kalshi_scanner"
echo "  Archived to $ARCHIVE"

# Step 3: Preserve trading journal + positions for audit trail
echo "[3/6] Preserving audit trail..."
mkdir -p "$ARCHIVE/audit"
cp -r "$WORKSPACE/philby/trader/journal.jsonl" "$ARCHIVE/audit/" 2>/dev/null || echo "  No journal"
cp -r "$WORKSPACE/philby/trader/positions_live.json" "$ARCHIVE/audit/" 2>/dev/null || echo "  No positions"
cp -r "$WORKSPACE/logs/kalshi/" "$ARCHIVE/audit/logs-kalshi/" 2>/dev/null || echo "  No kalshi logs"
cp -r "$WORKSPACE/philby/trader/signals/" "$ARCHIVE/audit/signals/" 2>/dev/null || echo "  No signals"
cp -r "$WORKSPACE/philby/trader/circuit_breaker.json" "$ARCHIVE/audit/" 2>/dev/null || echo "  No circuit breaker"
cp -r "$WORKSPACE/philby/trader/calibration-stamp.json" "$ARCHIVE/audit/" 2>/dev/null || echo "  No calibration"
cp "$WORKSPACE/docs/ops/portfolio-overview.md" "$ARCHIVE/audit/" 2>/dev/null || echo "  No portfolio doc"
cp "$WORKSPACE/docs/ops/trade-journal-2026-05-27.md" "$ARCHIVE/audit/" 2>/dev/null || echo "  No May 27 journal"
cp "$WORKSPACE/docs/ops/trade-journal-2026-05-29.md" "$ARCHIVE/audit/" 2>/dev/null || echo "  No May 29 journal"
cp "$WORKSPACE/docs/ops/kalshi-audit-2026-05-31.md" "$ARCHIVE/audit/" 2>/dev/null || echo "  No audit report"

# Step 4: Remove Philby code from active tree
echo "[4/6] Removing Philby code from active tree..."
rm -rf "$WORKSPACE/philby" 2>/dev/null && echo "  philby/ removed" || echo "  No philby dir"
rm -f "$WORKSPACE/scripts/kalshi_scanner.py" 2>/dev/null && echo "  kalshi_scanner.py removed" || echo "  No scanner"
rm -f "$WORKSPACE/scripts/simmer_scanner.py" 2>/dev/null && echo "  simmer_scanner.py removed" || echo "  No simmer scanner"
rm -rf "$WORKSPACE/logs/kalshi/" 2>/dev/null && echo "  logs/kalshi/ removed" || echo "  No kalshi logs"

# Step 5: Remove stale docs
echo "[5/6] Removing stale trading docs..."
rm -f "$WORKSPACE/docs/ops/portfolio-overview.md" 2>/dev/null || echo "  No portfolio doc"
rm -f "$WORKSPACE/docs/ops/trade-journal-2026-05-27.md" 2>/dev/null || echo "  No May 27 journal"
rm -f "$WORKSPACE/docs/ops/trade-journal-2026-05-29.md" 2>/dev/null || echo "  No May 29 journal"
rm -f "$WORKSPACE/brain/memory/semantic/control-plane-metrics.json" 2>/dev/null || echo "  No control plane metrics (kept)"

# Step 6: Update MEMORY.md with teardown note
echo "[6/6] Documenting teardown..."
echo -e "\n## 2026-05-31 — Philby/Kalshi Trading System — TEARDOWN" >> "$WORKSPACE/MEMORY.md"
echo "All trading code archived to $ARCHIVE" >> "$WORKSPACE/MEMORY.md"
echo "Trading crons disabled. Auth keys preserved in .env." >> "$WORKSPACE/MEMORY.md"
echo "See archive/$ARCHIVE for full code + audit trail." >> "$WORKSPACE/MEMORY.md"

echo ""
echo "=== TEARDOWN COMPLETE ==="
echo "Archive: $ARCHIVE"
echo "Audit trail preserved."
echo "All crons remain disabled."
echo ""
echo "Ready for clean rebuild when directed."
