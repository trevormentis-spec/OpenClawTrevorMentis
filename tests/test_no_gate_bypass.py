#!/usr/bin/env python3
"""
Regression guard — detects new code paths that bypass llm_gate.

Scans staged files (or all .py files) for:
- Direct URL strings to model provider endpoints outside analyst/llm_clients/
- Hardcoded model name strings as args to API calls
- Imports of model client SDKs outside analyst/llm_clients/
- References to analyst.routing (legacy module)

Files containing 'GATE_EXEMPT:' in the first 5 lines are exempt.

Usage:
    python3 tests/test_no_gate_bypass.py                          # Run on all .py files
    python3 tests/test_no_gate_bypass.py --staged                 # Run on staged files only
    python3 tests/test_no_gate_bypass.py --diff HEAD              # Run on diff against a ref
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Known-legitimate client directories
CLIENT_DIRS = [
    "analyst/llm_clients",
    "skills/collection",
    ".venv",
    "__pycache__",
    "node_modules",
    "tests/",
    "exports/",
    "docs/archive/",
    "docs/",
    "collectors/",
    "tmp_review/",
    "analysis/",
    "tasks/",
]

# API endpoint patterns that should ONLY appear in analyst/llm_clients/
MODEL_ENDPOINT_PATTERNS = [
    r'https://openrouter\.ai/api/v1/chat/completions',
    r'https://api\.deepseek\.com/v1/chat/completions',
    r'https://api\.anthropic\.com/v1/messages',
    r'https://api\.elevenlabs\.io/v1/text-to-speech',
]

# Model name strings that look hardcoded to API calls
HARDCODED_MODEL_PATTERNS = [  # Only flags model strings in API-call context
    r'["\']deepseek/deepseek-v4-flash["\']',
    r'["\']deepseek/deepseek-v4-pro["\']',
    r'["\']anthropic/claude-opus-4\.7["\']',
    r'["\']anthropic/claude-sonnet-4\.5["\']',
    r'["\']deepseek-chat["\']',
]

# Legacy module references
LEGACY_MODULE_PATTERNS = [
    r'from analyst\.routing import',
    r'import analyst\.routing',
]


def is_exempt(filepath: str) -> bool:
    """Check if file has GATE_EXEMPT marker in first 5 lines."""
    path = REPO_ROOT / filepath
    if not path.exists():
        return False
    try:
        for i, line in enumerate(path.open("r")):
            if i > 5:
                break
            if "GATE_EXEMPT:" in line:
                return True
    except Exception:
        pass
    return False


def is_in_client_dir(filepath: str) -> bool:
    """Check if file lives in a legitimate client directory."""
    for cd in CLIENT_DIRS:
        if filepath.startswith(cd):
            return True
    return False


def scan_file(filepath: str) -> list[dict]:
    """Scan a single file for bypass patterns. Returns list of findings."""
    findings = []
    path = REPO_ROOT / filepath
    if not path.exists() or not filepath.endswith(".py"):
        return findings
    if is_exempt(filepath):
        return findings
    if is_in_client_dir(filepath):
        return findings

    try:
        lines = path.open("r").readlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for model endpoint patterns
        for pattern in MODEL_ENDPOINT_PATTERNS:
            if re.search(pattern, stripped):
                findings.append({
                    "file": filepath,
                    "line": i,
                    "pattern": "model_endpoint",
                    "detail": stripped[:100],
                })

        # Check for hardcoded model names — only flag in API-call context
        for pattern in HARDCODED_MODEL_PATTERNS:
            if re.search(pattern, stripped):
                # Only flag if line is in an API-call context
                api_context = any(kw in stripped.lower() for kw in [
                    '"model"', "'model'", 'payload', 'urllib.request', 
                    'requests.', 'curl', '"provider"',
                ])
                if api_context:
                    findings.append({
                        "file": filepath,
                        "line": i,
                        "pattern": "hardcoded_model",
                        "detail": stripped[:100],
                    })

        # Check for legacy module references
        for pattern in LEGACY_MODULE_PATTERNS:
            if re.search(pattern, stripped):
                findings.append({
                    "file": filepath,
                    "line": i,
                    "pattern": "legacy_module",
                    "detail": stripped[:100],
                })

    return findings


def get_staged_files() -> list[str]:
    """Get list of staged Python files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, timeout=10,
        cwd=str(REPO_ROOT),
    )
    return [f for f in result.stdout.strip().split("\n") if f.endswith(".py") and f.strip()]


def get_diff_files(ref: str) -> list[str]:
    """Get files changed in a diff."""
    result = subprocess.run(
        ["git", "diff", ref, "--name-only"],
        capture_output=True, text=True, timeout=10,
        cwd=str(REPO_ROOT),
    )
    return [f for f in result.stdout.strip().split("\n") if f.endswith(".py") and f.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate bypass regression guard")
    parser.add_argument("--staged", action="store_true", help="Check only staged files")
    parser.add_argument("--diff", help="Check files changed in a diff (e.g., HEAD, main)")
    args = parser.parse_args()

    if args.staged:
        files = get_staged_files()
    elif args.diff:
        files = get_diff_files(args.diff)
    else:
        # Walk all .py files
        files = []
        for root, dirs, names in pathlib.Path(REPO_ROOT).walk():
            # Skip excluded dirs
            rel = root.relative_to(REPO_ROOT)
            parts = str(rel).split("/")
            skip = False
            for skip_dir in [".git", ".venv", "__pycache__", "node_modules", 
                           ".local", ".cache", ".npm", "downloads"]:
                if skip_dir in parts:
                    skip = True
                    break
            if skip:
                continue
            for name in names:
                if name.endswith(".py"):
                    rel_path = str(rel / name) if str(rel) != "." else name
                    files.append(rel_path)

    all_findings = []
    for f in files:
        findings = scan_file(f)
        all_findings.extend(findings)

    if all_findings:
        print(f"GATE BYPASS DETECTED: {len(all_findings)} finding(s)")
        print("=" * 60)
        for f in all_findings:
            print(f"  {f['file']}:{f['line']} [{f['pattern']}]")
            print(f"    {f['detail']}")
        print(f"\n{len(all_findings)} bypass(es) found.")
        print("Add '# GATE_EXEMPT: <reason>' to the first 5 lines of exempt files.")
        return 1

    print(f"OK — {len(files)} files scanned, zero bypasses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
