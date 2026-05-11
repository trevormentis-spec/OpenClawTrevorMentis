#!/usr/bin/env python3
"""
context_compressor.py — Prevents context overflow by summarizing mid-conversation turns.

Monitors context usage and when it exceeds a threshold (default 75% of model limit),
summarizes the middle 50% of conversation turns into a compact block.
Preserves decisions, facts, and pending work — drops verbose tool output.

Usage:
    python3 scripts/context_compressor.py --check <session_log>
    python3 scripts/context_compressor.py --compress <session_log> --output <summary_file>
    python3 scripts/context_compressor.py --status
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import datetime

REPO = pathlib.Path(__file__).resolve().parent.parent
EPISODIC_DIR = REPO / "brain" / "memory" / "episodic"
COMPRESSED_DIR = REPO / "brain" / "compressed"

# Model context limits (tokens)
MODEL_LIMITS = {
    "deepseek/deepseek-v4-flash": 200_000,
    "deepseek/deepseek-v4-pro": 1_000_000,
    "deepseek/deepseek-chat": 131_072,
    "anthropic/claude-opus-4.7": 200_000,
}

# Compression threshold
COMPRESS_THRESHOLD = 0.75  # 75% of model limit

# Rough token estimation (chars / 4)
CHARS_PER_TOKEN = 4


def log(msg):
    print(f"[compress] {msg}", file=sys.stderr)


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return len(text) // CHARS_PER_TOKEN


def get_recent_session_logs(count: int = 3) -> list[dict]:
    """Read recent episodic session logs."""
    sessions = []
    if EPISODIC_DIR.exists():
        files = sorted(EPISODIC_DIR.glob("*.jsonl"), reverse=True)[:count]
        for f in files:
            try:
                data = f.read_text(encoding="utf-8")
                sessions.append({
                    "file": str(f),
                    "lines": [json.loads(l) for l in data.strip().split("\n") if l],
                    "raw": data,
                })
            except Exception as e:
                log(f"  Error reading {f}: {e}")
    return sessions


def estimate_context_usage(sessions: list[dict], model: str = "deepseek/deepseek-v4-flash") -> dict:
    """Estimate current context usage vs model limit."""
    total_chars = sum(len(s.get("raw", "")) for s in sessions)
    total_tokens = estimate_tokens(str(sessions))
    limit = MODEL_LIMITS.get(model, 200_000)
    usage_pct = min(100, int(total_tokens / limit * 100))
    
    return {
        "model": model,
        "limit_tokens": limit,
        "estimated_tokens": total_tokens,
        "usage_pct": usage_pct,
        "needs_compression": usage_pct >= COMPRESS_THRESHOLD * 100,
        "session_count": len(sessions),
    }


def compress_session(sessions: list[dict]) -> str:
    """Compress session content into a summary block."""
    summary_parts = []
    
    for session in sessions:
        source = pathlib.Path(session["file"]).stem
        lines = session["lines"]
        
        # Extract key decisions, facts, and actions
        decisions = []
        facts = []
        errors = []
        tools_used = set()
        
        for line in lines:
            content = str(line.get("content", line.get("text", "")))
            action = str(line.get("action", line.get("type", "")))
            
            # Track tool usage
            if "tool" in action.lower() or "exec" in action.lower() or "function" in action.lower():
                tools_used.add(action[:50])
            
            # Extract salient content patterns
            if any(kw in content for kw in ["decision", "decided", "chose", "going with"]):
                decisions.append(content[:150])
            elif any(kw in content for kw in ["error", "failed", "exception"]):
                errors.append(content[:150])
            elif any(kw in content for kw in ["fact:", "note:", "remember", "lesson"]):
                facts.append(content[:150])
        
        summary_parts.append(f"--- Session: {source} ---")
        summary_parts.append(f"Lines: {len(lines)} | Tools: {len(tools_used)}")
        if decisions:
            summary_parts.append(f"Decisions: {'; '.join(decisions[:3])}")
        if facts:
            summary_parts.append(f"Facts: {'; '.join(facts[:3])}")
        if errors:
            summary_parts.append(f"Issues: {'; '.join(errors[:2])}")
        summary_parts.append("")
    
    if not summary_parts:
        return "No compressible content found."
    
    return "═══ COMPRESSED SESSION (auto-summarized) ═══\n" + "\n".join(summary_parts)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Context compressor for Trevor")
    parser.add_argument("--check", action="store_true", help="Check context usage")
    parser.add_argument("--compress", action="store_true", help="Compress recent sessions")
    parser.add_argument("--model", type=str, default="deepseek/deepseek-v4-flash",
                       help="Model name for context limit lookup")
    parser.add_argument("--output", type=str, default=None,
                       help="Output file for compressed summary")
    parser.add_argument("--status", action="store_true", help="Show compression status")
    args = parser.parse_args()
    
    sessions = get_recent_session_logs(5)
    
    if args.check or args.status:
        usage = estimate_context_usage(sessions, args.model)
        print(f"Model: {usage['model']} ({usage['limit_tokens']:,} token limit)")
        print(f"Estimated usage: {usage['estimated_tokens']:,} tokens ({usage['usage_pct']}%)")
        print(f"Sessions: {usage['session_count']}")
        if usage['needs_compression']:
            print(f"\n⚠️  Above {int(COMPRESS_THRESHOLD*100)}% threshold — compression recommended")
        else:
            print(f"\n✅ Below {int(COMPRESS_THRESHOLD*100)}% threshold — no compression needed")
        return 0 if not usage['needs_compression'] else 1
    
    if args.compress:
        result = compress_session(sessions)
        if args.output:
            out_path = pathlib.Path(args.output).expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result)
            log(f"Compressed summary saved to {out_path}")
        else:
            print(result)
        return 0
    
    # Default: check
    usage = estimate_context_usage(sessions, args.model)
    print(f"Context: {usage['usage_pct']}% | {usage['estimated_tokens']:,}/{usage['limit_tokens']:,} tokens")
    if usage['needs_compression']:
        print("Compression recommended. Run with --compress to generate summary.")
    return 0 if not usage['needs_compression'] else 1


if __name__ == "__main__":
    sys.exit(main())
