#!/usr/bin/env bash
# Trevor v2 Bootstrap — brings a clean MyClaw instance to operational state.
#
# Usage:
#   bash deployment/bootstrap.sh
#
# Prerequisites:
#   - MyClaw instance running
#   - Python 3.10+
#   - .env file with required keys (copy from deployment/.env.example)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG="$REPO_ROOT/logs/bootstrap.log"

mkdir -p "$REPO_ROOT/logs"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"
}

error() {
    log "ERROR: $*"
    exit 1
}

log "=== Trevor v2 Bootstrap ==="
log "Repo root: $REPO_ROOT"

# ── Step 1: Check Python ────────────────────────────────────────────────
log "Checking Python..."
PYTHON=$(command -v python3 || true)
if [ -z "$PYTHON" ]; then
    error "Python 3 not found. Install Python 3.10+ and try again."
fi
PY_VERSION=$($PYTHON --version 2>&1)
log "Python: $PY_VERSION"

# ── Step 2: Check .env ──────────────────────────────────────────────────
log "Checking .env..."
if [ ! -f "$REPO_ROOT/.env" ]; then
    error ".env not found. Copy deployment/.env.example to .env and fill in API keys."
fi

# Check required keys
REQUIRED_KEYS=(DEEPSEEK_API_KEY)
OPTIONAL_KEYS=(OPENROUTER_API_KEY ELEVENLABS_API_KEY AGENTMAIL_API_KEY)
MISSING=0

for key in "${REQUIRED_KEYS[@]}"; do
    if ! grep -q "^${key}=.\+" "$REPO_ROOT/.env" 2>/dev/null; then
        log "MISSING (required): $key"
        MISSING=1
    fi
done

if [ "$MISSING" -eq 1 ]; then
    error "Required API keys missing from .env. See deployment/.env.example."
fi

for key in "${OPTIONAL_KEYS[@]}"; do
    if ! grep -q "^${key}=.\+" "$REPO_ROOT/.env" 2>/dev/null; then
        log "WARNING (optional): $key not set — some features will be unavailable"
    fi
done

# ── Step 3: Python dependencies ─────────────────────────────────────────
log "Checking Python dependencies..."

# Core dependencies (standard library — no install needed)
# Optional: weasyprint for PDF rendering
if $PYTHON -c "import weasyprint" 2>/dev/null; then
    log "weasyprint: available"
else
    log "WARNING: weasyprint not available — PDF rendering disabled"
    log "Install: pip3 install weasyprint"
fi

# ── Step 4: Directory structure ─────────────────────────────────────────
log "Ensuring directory structure..."
mkdir -p "$REPO_ROOT/memory"
mkdir -p "$REPO_ROOT/logs"
mkdir -p "$REPO_ROOT/exports/pdfs"
mkdir -p "$REPO_ROOT/exports/images"
mkdir -p "$REPO_ROOT/exports/social"
mkdir -p "$REPO_ROOT/config/topics"
mkdir -p "$REPO_ROOT/data"
mkdir -p "$REPO_ROOT/tmp"

# ── Step 5: Brain runtime ──────────────────────────────────────────────
log "Checking brain runtime..."
if [ -f "$REPO_ROOT/brain/scripts/brain.py" ]; then
    log "Brain runtime: present"
    # Rebuild index if needed
    if [ ! -f "$REPO_ROOT/brain/index/index.json" ]; then
        log "Building brain index..."
        $PYTHON "$REPO_ROOT/brain/scripts/brain.py" reindex 2>/dev/null || log "Brain reindex skipped (may need data)"
    fi
else
    log "WARNING: brain runtime not found at brain/scripts/brain.py"
fi

# ── Step 6: Smoke tests ────────────────────────────────────────────────
log "Running smoke tests..."
SMOKE_PASS=0
SMOKE_FAIL=0

# Test LLM gate
if $PYTHON -c "from analyst.llm_gate import route; d = route('daily_ingestion', {}); assert d.model" 2>/dev/null; then
    log "  LLM gate: PASS"
    ((SMOKE_PASS++))
else
    log "  LLM gate: FAIL"
    ((SMOKE_FAIL++))
fi

# Test cost ledger
if $PYTHON -c "from analyst.cost_ledger import CostLedger; l = CostLedger(); l.check_budget()" 2>/dev/null; then
    log "  Cost ledger: PASS"
    ((SMOKE_PASS++))
else
    log "  Cost ledger: FAIL"
    ((SMOKE_FAIL++))
fi

# Test topic onboarding
if $PYTHON -c "from analyst.topic_onboarding import list_topics; list_topics()" 2>/dev/null; then
    log "  Topic onboarding: PASS"
    ((SMOKE_PASS++))
else
    log "  Topic onboarding: FAIL"
    ((SMOKE_FAIL++))
fi

# Test scope check
if $PYTHON -c "from analyst.scope_check import check_scope; check_scope('test query')" 2>/dev/null; then
    log "  Scope check: PASS"
    ((SMOKE_PASS++))
else
    log "  Scope check: FAIL"
    ((SMOKE_FAIL++))
fi

log "Smoke tests: $SMOKE_PASS passed, $SMOKE_FAIL failed"

# ── Step 7: Report ─────────────────────────────────────────────────────
log ""
log "=== Bootstrap Complete ==="
log "Passed: $SMOKE_PASS smoke tests"
if [ "$SMOKE_FAIL" -gt 0 ]; then
    log "Failed: $SMOKE_FAIL smoke tests — check log for details"
    log "Run: bash deployment/health-check.sh for full diagnostics"
fi
log ""
log "Next steps:"
log "1. Run: bash deployment/health-check.sh"
log "2. Onboard a topic: python3 analyst/topic_onboarding.py --topic 'Your Topic'"
log "3. Start cron pipeline (if applicable)"
log ""
log "Log saved to: $LOG"
