#!/usr/bin/env bash
# Trevor v2 Health Check — verify all systems operational.
#
# Usage:
#   bash deployment/health-check.sh
#
# Exit codes:
#   0 — all checks pass
#   1 — one or more checks failed

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON=$(command -v python3 || true)

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" -eq 0 ]; then
        echo "  [PASS] $name"
        ((PASS++))
    else
        echo "  [FAIL] $name"
        ((FAIL++))
    fi
}

warn() {
    local name="$1"
    echo "  [WARN] $name"
    ((WARN++))
}

echo "=== Trevor v2 Health Check ==="
echo ""

# ── Environment ─────────────────────────────────────────────────────────
echo "Environment:"
check "Python 3 available" $([ -n "$PYTHON" ] && echo 0 || echo 1)
check ".env exists" $([ -f "$REPO_ROOT/.env" ] && echo 0 || echo 1)

# Check required env vars
if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env" 2>/dev/null || true
    check "DEEPSEEK_API_KEY set" $([ -n "${DEEPSEEK_API_KEY:-}" ] && echo 0 || echo 1)

    if [ -z "${OPENROUTER_API_KEY:-}" ]; then
        warn "OPENROUTER_API_KEY not set (frontier models unavailable)"
    else
        check "OPENROUTER_API_KEY set" 0
    fi

    if [ -z "${ELEVENLABS_API_KEY:-}" ]; then
        warn "ELEVENLABS_API_KEY not set (audio generation unavailable)"
    else
        check "ELEVENLABS_API_KEY set" 0
    fi
fi

echo ""

# ── Core Components ─────────────────────────────────────────────────────
echo "Core Components:"
check "analyst/llm_gate.py exists" $([ -f "$REPO_ROOT/analyst/llm_gate.py" ] && echo 0 || echo 1)
check "analyst/cost_ledger.py exists" $([ -f "$REPO_ROOT/analyst/cost_ledger.py" ] && echo 0 || echo 1)
check "analyst/scope_check.py exists" $([ -f "$REPO_ROOT/analyst/scope_check.py" ] && echo 0 || echo 1)
check "analyst/fabrication_check.py exists" $([ -f "$REPO_ROOT/analyst/fabrication_check.py" ] && echo 0 || echo 1)
check "analyst/themes_preflight.py exists" $([ -f "$REPO_ROOT/analyst/themes_preflight.py" ] && echo 0 || echo 1)
check "analyst/topic_onboarding.py exists" $([ -f "$REPO_ROOT/analyst/topic_onboarding.py" ] && echo 0 || echo 1)
check "analyst/guard_pipeline.py exists" $([ -f "$REPO_ROOT/analyst/guard_pipeline.py" ] && echo 0 || echo 1)

echo ""

# ── Configuration ───────────────────────────────────────────────────────
echo "Configuration:"
check "config/budget.yaml exists" $([ -f "$REPO_ROOT/config/budget.yaml" ] && echo 0 || echo 1)
check "config/llm-routing.yaml exists" $([ -f "$REPO_ROOT/config/llm-routing.yaml" ] && echo 0 || echo 1)
check "config/active-assignments.yaml exists" $([ -f "$REPO_ROOT/config/active-assignments.yaml" ] && echo 0 || echo 1)
check "config/general-skills.yaml exists" $([ -f "$REPO_ROOT/config/general-skills.yaml" ] && echo 0 || echo 1)

echo ""

# ── Brain Runtime ───────────────────────────────────────────────────────
echo "Brain Runtime:"
check "brain/scripts/brain.py exists" $([ -f "$REPO_ROOT/brain/scripts/brain.py" ] && echo 0 || echo 1)
check "brain/memory/ exists" $([ -d "$REPO_ROOT/brain/memory" ] && echo 0 || echo 1)

echo ""

# ── Renderers ───────────────────────────────────────────────────────────
echo "Renderers:"
check "scripts/render_pdf.py exists" $([ -f "$REPO_ROOT/scripts/render_pdf.py" ] && echo 0 || echo 1)
check "scripts/render_audio.py exists" $([ -f "$REPO_ROOT/scripts/render_audio.py" ] && echo 0 || echo 1)

if $PYTHON -c "import weasyprint" 2>/dev/null; then
    check "weasyprint importable" 0
else
    warn "weasyprint not importable (PDF rendering unavailable)"
fi

echo ""

# ── Tests ───────────────────────────────────────────────────────────────
echo "Test Suite:"
if [ -n "$PYTHON" ]; then
    if $PYTHON tests/test_llm_gate.py > /dev/null 2>&1; then
        check "LLM gate tests" 0
    else
        check "LLM gate tests" 1
    fi

    if $PYTHON tests/test_topic_onboarding.py > /dev/null 2>&1; then
        check "Topic onboarding tests" 0
    else
        check "Topic onboarding tests" 1
    fi

    if $PYTHON tests/test_self_improvement.py > /dev/null 2>&1; then
        check "Self-improvement tests" 0
    else
        check "Self-improvement tests" 1
    fi
fi

echo ""

# ── Identity Files ──────────────────────────────────────────────────────
echo "Identity:"
check "SOUL.md exists" $([ -f "$REPO_ROOT/SOUL.md" ] && echo 0 || echo 1)
check "IDENTITY.md exists" $([ -f "$REPO_ROOT/IDENTITY.md" ] && echo 0 || echo 1)
check "AGENTS.md exists" $([ -f "$REPO_ROOT/AGENTS.md" ] && echo 0 || echo 1)
check "USER.md exists" $([ -f "$REPO_ROOT/USER.md" ] && echo 0 || echo 1)
check "ORCHESTRATION.md exists" $([ -f "$REPO_ROOT/ORCHESTRATION.md" ] && echo 0 || echo 1)

echo ""

# ── Summary ─────────────────────────────────────────────────────────────
echo "=== Summary ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Warnings: $WARN"

if [ "$FAIL" -eq 0 ]; then
    echo ""
    echo "  STATUS: HEALTHY"
    exit 0
else
    echo ""
    echo "  STATUS: DEGRADED ($FAIL failures)"
    exit 1
fi
