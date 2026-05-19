#!/usr/bin/env bash
# Trevor v2 Backup & Restore — export/import brain state and config.
#
# Usage:
#   bash deployment/backup-restore.sh backup [output-path]
#   bash deployment/backup-restore.sh restore <tarball-path>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ACTION="${1:-help}"
TARGET="${2:-}"

backup() {
    local output="${TARGET:-$REPO_ROOT/exports/trevor-backup-$(date -u +%Y%m%d-%H%M%S).tar.gz}"
    local tmpdir=$(mktemp -d)

    echo "=== Trevor v2 Backup ==="
    echo "Creating backup at: $output"

    # Brain state
    if [ -d "$REPO_ROOT/brain" ]; then
        mkdir -p "$tmpdir/brain"
        cp -r "$REPO_ROOT/brain/memory" "$tmpdir/brain/" 2>/dev/null || true
        cp -r "$REPO_ROOT/brain/meta" "$tmpdir/brain/" 2>/dev/null || true
        # Skip index (rebuilt on restore)
    fi

    # Topic configurations
    if [ -d "$REPO_ROOT/config/topics" ]; then
        mkdir -p "$tmpdir/config"
        cp -r "$REPO_ROOT/config/topics" "$tmpdir/config/"
    fi

    # Active assignments
    cp "$REPO_ROOT/config/active-assignments.yaml" "$tmpdir/config/" 2>/dev/null || true
    cp "$REPO_ROOT/config/budget.yaml" "$tmpdir/config/" 2>/dev/null || true

    # Cost ledger
    mkdir -p "$tmpdir/memory"
    cp "$REPO_ROOT/memory/cost-ledger.jsonl" "$tmpdir/memory/" 2>/dev/null || true
    cp "$REPO_ROOT/memory/llm-routing-log.jsonl" "$tmpdir/memory/" 2>/dev/null || true

    # STATUS history
    cp "$REPO_ROOT/STATUS.md" "$tmpdir/" 2>/dev/null || true

    # Analyst meta
    if [ -d "$REPO_ROOT/analyst/meta" ]; then
        mkdir -p "$tmpdir/analyst/meta"
        cp -r "$REPO_ROOT/analyst/meta" "$tmpdir/analyst/"
    fi

    # Create tarball
    mkdir -p "$(dirname "$output")"
    tar -czf "$output" -C "$tmpdir" .

    rm -rf "$tmpdir"
    echo "Backup created: $output"
    echo "Size: $(du -h "$output" | cut -f1)"
}

restore() {
    if [ -z "$TARGET" ] || [ ! -f "$TARGET" ]; then
        echo "Error: provide path to backup tarball"
        echo "Usage: bash deployment/backup-restore.sh restore <tarball>"
        exit 1
    fi

    echo "=== Trevor v2 Restore ==="
    echo "Restoring from: $TARGET"
    echo ""
    echo "WARNING: This will overwrite existing brain state and config."
    echo "Press Ctrl+C to cancel, or Enter to continue."
    read -r

    local tmpdir=$(mktemp -d)
    tar -xzf "$TARGET" -C "$tmpdir"

    # Restore brain state
    if [ -d "$tmpdir/brain/memory" ]; then
        mkdir -p "$REPO_ROOT/brain/memory"
        cp -r "$tmpdir/brain/memory/"* "$REPO_ROOT/brain/memory/" 2>/dev/null || true
        echo "Restored: brain/memory"
    fi

    if [ -d "$tmpdir/brain/meta" ]; then
        mkdir -p "$REPO_ROOT/brain/meta"
        cp -r "$tmpdir/brain/meta/"* "$REPO_ROOT/brain/meta/" 2>/dev/null || true
        echo "Restored: brain/meta"
    fi

    # Restore config
    if [ -d "$tmpdir/config/topics" ]; then
        mkdir -p "$REPO_ROOT/config/topics"
        cp -r "$tmpdir/config/topics/"* "$REPO_ROOT/config/topics/" 2>/dev/null || true
        echo "Restored: config/topics"
    fi

    for f in active-assignments.yaml budget.yaml; do
        if [ -f "$tmpdir/config/$f" ]; then
            cp "$tmpdir/config/$f" "$REPO_ROOT/config/"
            echo "Restored: config/$f"
        fi
    done

    # Restore memory
    for f in cost-ledger.jsonl llm-routing-log.jsonl; do
        if [ -f "$tmpdir/memory/$f" ]; then
            mkdir -p "$REPO_ROOT/memory"
            cp "$tmpdir/memory/$f" "$REPO_ROOT/memory/"
            echo "Restored: memory/$f"
        fi
    done

    # Restore analyst meta
    if [ -d "$tmpdir/analyst/meta" ]; then
        mkdir -p "$REPO_ROOT/analyst/meta"
        cp -r "$tmpdir/analyst/meta/"* "$REPO_ROOT/analyst/meta/" 2>/dev/null || true
        echo "Restored: analyst/meta"
    fi

    rm -rf "$tmpdir"

    # Rebuild brain index
    if [ -f "$REPO_ROOT/brain/scripts/brain.py" ]; then
        echo "Rebuilding brain index..."
        python3 "$REPO_ROOT/brain/scripts/brain.py" reindex 2>/dev/null || echo "Brain reindex skipped"
    fi

    echo ""
    echo "Restore complete. Run: bash deployment/health-check.sh"
}

case "$ACTION" in
    backup)
        backup
        ;;
    restore)
        restore
        ;;
    *)
        echo "Trevor v2 Backup & Restore"
        echo ""
        echo "Usage:"
        echo "  bash deployment/backup-restore.sh backup [output-path]"
        echo "  bash deployment/backup-restore.sh restore <tarball-path>"
        ;;
esac
