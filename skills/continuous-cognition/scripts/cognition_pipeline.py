# GATE_EXEMPT: Continuous cognition uses DeepSeek Direct API deliberately — lowest-cost path for 15-min Flash cycles. This is not a gate bypass; it IS the intended routing for Tier-3 cognition.
#!/usr/bin/env python3
"""
Continuous Cognition Pipeline — Trevor

Runs every 10-15 minutes as a background daemon.
Uses DeepSeek Flash for lightweight continuous cognition.
Escalates to Pro/Opus when thresholds are crossed.

Architecture:
  collect_context() → build_flash_input() → call_flash() → 
  parse_response() → update_state() → check_escalation() → 
  execute_escalation() → compact()

Usage:
  python3 cognition_pipeline.py              # One cycle
  python3 cognition_pipeline.py --daemon     # Run continuously
  python3 cognition_pipeline.py --status     # Current state snapshot
"""

import sys
import os
import json
import time
import copy
import signal
import logging
import argparse
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin

import requests

# Add project scripts to path
BASE_DIR = Path(__file__).parent.parent.parent.parent  # workspace root
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR / "skills" / "continuous-cognition" / "scripts"))

from utils import (
    load_state, save_state, snapshot_summary,
    upsert_narrative, update_source_trust, add_weak_signal,
    update_drift, add_escalation, get_pending_escalations,
    resolve_escalation, record_token_spend, would_exceed_budget,
    mark_healthy, mark_error, compact_state,
)
from runtime_lock import RuntimeLock

logger = logging.getLogger("cognition")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [cog] %(message)s", datefmt="%H:%M:%S"
))
logger.addHandler(handler)

PROMPT_PATH = BASE_DIR / "skills" / "continuous-cognition" / "prompts" / "flash_cognition.txt"
CYCLE_INTERVAL = 900  # 15 minutes

# DeepSeek API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL_FLASH = "deepseek-chat"  # v4 Flash
DEEPSEEK_MODEL_PRO = "deepseek-chat"    # Pro — same endpoint, different config
OPUS_MODEL = "anthropic/claude-opus-4.7"  # via OpenRouter


# ── Context Collection ──────────────────────────────────────────────

def collect_recent_context() -> Dict[str, Any]:
    """
    Gather recent intelligence context for the cognition cycle.
    Lightweight — reads file headers/age only, not full content.
    """
    context = {
        "recent_events": [],
        "recent_briefs": [],
        "memory_updates": [],
        "runtime_health": {},
        "collection_status": {},
    }

    # Check for today's brief
    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    brief_dir = BASE_DIR / "analyst" / "outputs"
    if brief_dir.exists():
        for f in sorted(brief_dir.glob("*brief*"), reverse=True)[:3]:
            if f.stat().st_mtime > time.time() - 86400:
                context["recent_briefs"].append({
                    "file": f.name,
                    "age_min": int((time.time() - f.stat().st_mtime) / 60),
                    "size": f.stat().st_size,
                })

    # Check for recent collection output
    tmp_dir = BASE_DIR / "tmp"
    if tmp_dir.exists():
        for f in sorted(tmp_dir.glob("*news*data*"), reverse=True)[:3]:
            if f.stat().st_mtime > time.time() - 86400:
                context["recent_events"].append({
                    "file": f.name,
                    "age_min": int((time.time() - f.stat().st_mtime) / 60),
                    "size": f.stat().st_size,
                })

    # Check pipeline logs
    log_dir = BASE_DIR / "logs"
    pipeline_logs = []
    if log_dir.exists():
        for f in sorted(log_dir.glob("daily-brief-*.log"), reverse=True)[:2]:
            if f.stat().st_mtime > time.time() - 172800:
                pipeline_logs.append(f.name)
    context["pipeline_logs"] = pipeline_logs

    # Runtime health
    health_state = BASE_DIR / "tasks" / "runtime-state.json"
    if health_state.exists():
        try:
            with open(health_state) as f:
                context["runtime_health"] = json.load(f)
        except Exception:
            pass

    # Recent memory changes
    memory_dir = BASE_DIR / "memory"
    if memory_dir.exists():
        recent_mem = sorted(
            memory_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True
        )[:2]
        context["memory_updates"] = [
            {"file": f.name, "age_min": int((time.time() - f.stat().st_mtime) / 60)}
            for f in recent_mem
        ]

    # Email OSINT — read AgentMail/Gmail intel from news_raw.md
    news_raw = BASE_DIR / "tasks" / "news_raw.md"
    if news_raw.exists():
        age_min = int((time.time() - news_raw.stat().st_mtime) / 60)
        if age_min < 1440:  # Only if updated in last 24h
            try:
                text = news_raw.read_text()
                # Extract subject lines (## headers in the markdown)
                import re
                subjects = re.findall(r"^## (.+)$", text, re.MULTILINE)
                context["email_intel"] = {
                    "file": "news_raw.md",
                    "age_min": age_min,
                    "size": len(text),
                    "subjects": subjects[:5],  # Top 5 for prompt brevity
                    "has_useful_intel": any(
                        kw in text.lower()
                        for kw in ["iran", "ukraine", "china", "cartel", "fentanyl",
                                  "hormuz", "nuclear", "oil", "tariff", "drone",
                                  "missile", "ceasefire", "sanctions"]
                    ),
                }
            except Exception:
                context["email_intel"] = {"error": "read_failed"}

    return context


def _read_file_preview(path: Path, max_chars: int = 2000) -> str:
    """Read the beginning of a file for context."""
    try:
        return path.read_text()[:max_chars]
    except Exception:
        return ""


# ── Flash Input Construction ────────────────────────────────────────

def build_flash_input(state: dict, context: dict) -> str:
    """Build the Flash API message from state + context."""

    # Summarize narratives for Flash
    narratives_summary = []
    for nid, n in state.get("active_narratives", {}).items():
        narratives_summary.append(
            f"  {nid}: confidence={n['confidence']}% trend={n['trend']} "
            f"evidence_for={len(n.get('evidence',{}).get('for',[]))} "
            f"evidence_against={len(n.get('evidence',{}).get('against',[]))} "
            f"catalysts={n.get('catalysts',[])}"
        )

    # Summary of recent events
    events_summary = []
    ev = context.get("recent_events", [])
    if ev:
        events_summary.append(f"Recent intelligence files: {len(ev)}")
        for e in ev[:3]:
            events_summary.append(f"  {e['file']} ({e['age_min']}m old)")

    briefs = context.get("recent_briefs", [])
    if briefs:
        events_summary.append(f"Recent brief outputs: {len(briefs)}")
        for b in briefs[:2]:
            events_summary.append(f"  {b['file']} ({b['age_min']}m old)")

    # Memory updates
    mem = context.get("memory_updates", [])
    if mem:
        events_summary.append(f"Memory changes: {len(mem)}")
        for m in mem:
            events_summary.append(f"  {m['file']} ({m['age_min']}m old)")

    # Source trust
    trust = state.get("source_trust", {})
    trust_summary = [f"{len(trust)} tracked sources"]

    # Weak signals
    signals = state.get("weak_signals", [])
    active_signals = [s for s in signals if s.get("strength", 0) > 0.1]
    signals_summary = f"{len(active_signals)} active weak signals"

    # Read the prompt template
    prompt = _read_file_preview(PROMPT_PATH)

    # Build input
    input_text = (
        f"## PREVIOUS_STATE\n\n"
        f"Cycle: {state['cycle']}\n"
        f"Narratives:\n" + "\n".join(narratives_summary[-10:]) + "\n\n"  # Last 10
        f"Source trust: {trust_summary[0]}\n"
        f"Weak signals: {signals_summary}\n\n"
        f"## NEW_EVENTS\n\n" + "\n".join(events_summary) + "\n\n"
        f"## MEMORY_UPDATES\n\n" + "\n".join(events_summary[-3:]) + "\n\n"
        f"## RUNTIME_HEALTH\n\n"
        f"Disk: {context.get('runtime_health', {}).get('disk', {}).get('usage_pct', '?')}%\n"
        f"Monitor: {context.get('runtime_health', {}).get('processes', {}).get('monitor', '?')}\n"
        f"Risk: {context.get('runtime_health', {}).get('risk', '?')}\n"
    )

    # Add email OSINT intel if available
    email_intel = context.get("email_intel", {})
    if email_intel and not email_intel.get("error"):
        subjects = email_intel.get("subjects", [])
        input_text += (
            f"\n## EMAIL_OSINT\n\n"
            f"Source: {email_intel.get('file', 'news_raw.md')} "
            f"({email_intel.get('age_min', '?')}m old, "
            f"{email_intel.get('size', 0)} bytes)\n"
        )
        if subjects:
            input_text += "Recent intel subjects:\n"
            for s in subjects:
                input_text += f"  - {s}\n"
        if email_intel.get("has_useful_intel"):
            input_text += "Contains desk-relevant intel — consider updating narrative confidence.\n"

    return prompt + "\n\n" + input_text


# ── DeepSeek Flash Call ─────────────────────────────────────────────

def call_flash(messages: List[dict]) -> Tuple[Optional[dict], float]:
    """
    Call DeepSeek Flash for cognition.
    Returns (parsed_response, cost_cents) or (None, 0) on failure.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.warning("No DEEPSEEK_API_KEY set")
        return None, 0

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL_FLASH,
        "messages": messages,
        "max_tokens": 800,
        "temperature": 0.1,  # Low temperature for consistent cognition
        "stream": False,
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract content
        content = data["choices"][0]["message"]["content"].strip()

        # Parse JSON from response
        # Handle case where Flash wraps in ```json ... ```
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)

        # Cost estimation based on token usage
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        # Flash pricing: $0.14/M input, $0.28/M output
        cost_cents = (prompt_tokens * 0.14 + completion_tokens * 0.28) / 1_000_000 * 100

        return parsed, cost_cents

    except requests.exceptions.Timeout:
        logger.warning("Flash API timeout")
        return None, 0
    except json.JSONDecodeError as e:
        logger.warning(f"Flash returned non-JSON: {e}")
        return None, 0
    except Exception as e:
        logger.warning(f"Flash API error: {e}")
        return None, 0


def call_pro(messages: List[dict]) -> Tuple[Optional[dict], float]:
    """Call DeepSeek Pro for deeper analysis. Same endpoint, higher config."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return None, 0

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL_PRO,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        # Pro pricing: $0.435/M input, $0.87/M output
        cost_cents = (prompt_tokens * 0.435 + completion_tokens * 0.87) / 1_000_000 * 100
        return {"analysis": content, "model": "pro"}, cost_cents
    except Exception as e:
        logger.warning(f"Pro API error: {e}")
        return None, 0


# ── State Update ────────────────────────────────────────────────────

def apply_flash_output(state: dict, flash_output: dict):
    """Apply the Flash cognition output to the state."""
    if not flash_output:
        return

    # Confidence updates
    for update in flash_output.get("confidence_updates", []):
        if not isinstance(update, dict):
            continue
        narrative_id = update.get("narrative")
        if not narrative_id:
            continue
        confidence = update.get("new_confidence", 50)
        trend = update.get("trend", "stable")
        reasoning = update.get("reasoning", "")
        upsert_narrative(
            state, narrative_id, confidence, trend,
            reasoning=reasoning,
        )

    # Source trust updates
    for trust in flash_output.get("source_trust_updates", []):
        source_id = trust.get("source_id")
        if not source_id:
            continue
        update_source_trust(
            state,
            source_id,
            admiralty=trust.get("new_admiralty"),
            track_record=trust.get("track_record"),
            note=trust.get("reason"),
        )

    # Weak signals
    for signal in flash_output.get("weak_signals", []):
        sig = signal.get("signal")
        strength = signal.get("strength", 0.1)
        related = signal.get("related_narratives", [])
        if sig:
            add_weak_signal(state, sig, strength, related)

    # Narrative drift
    for drift in flash_output.get("narrative_drift", []):
        narrative_id = drift.get("narrative")
        if narrative_id:
            update_drift(
                state,
                narrative_id,
                drift.get("direction", "sideways"),
                drift.get("magnitude", 0.0),
            )

    # Escalation
    escalation = flash_output.get("escalation_needed", {})
    level = escalation.get("level", "none")
    if level in ("pro", "opus"):
        reason = escalation.get("reason", "Threshold crossed")
        narrative = escalation.get("narrative", "unknown")
        add_escalation(state, level, narrative, reason)
        logger.info(f"⚠️ Escalation: {level} — {narrative}: {reason}")

    # Memory actions (log them, let runtime handle actual file ops)
    for action in flash_output.get("memory_actions", []):
        if action.get("action") != "none":
            state.setdefault("memory_actions", []).append({
                "action": action["action"],
                "target": action.get("target", ""),
                "reason": action.get("reason", ""),
                "cycle": state["cycle"],
            })

    # Anomalies
    for anomaly in flash_output.get("anomalies", []):
        desc = anomaly.get("description", "")
        severity = anomaly.get("severity", "low")
        if desc:
            state.setdefault("anomalies_detected", []).append({
                "description": desc,
                "severity": severity,
                "cycle": state["cycle"],
                "detected_at": datetime.datetime.now(datetime.UTC).isoformat(),
            })


# ── Escalation Execution ────────────────────────────────────────────

def execute_escalations(state: dict) -> List[str]:
    """Execute pending Pro/Opus escalations."""
    executed = []
    max_per_cycle = 2  # Don't blow budget on escalations
    pending = get_pending_escalations(state)[:max_per_cycle]

    for i, escalation in enumerate(pending):
        level = escalation["level"]
        narrative = escalation["narrative"]

        if level == "pro":
            logger.info(f"→ Calling Pro for: {narrative}")
            pro_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Trevor's deep analysis layer. A threshold was crossed "
                        f"on narrative: {narrative}. "
                        f"Reason: {escalation['reason']}. "
                        "Provide structured analysis: key factors, alternative scenarios, "
                        "and recommended reassessment."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Deep analysis requested for: {narrative}\n"
                        f"Current state: {json.dumps(state.get('active_narratives', {}).get(narrative, {}))}\n"
                        f"Recent escalation reason: {escalation['reason']}\n"
                        "Provide JSON: {assessment, confidence, scenarios: [], key_factors: [], recommendations: []}"
                    ),
                },
            ]
            result, cost = call_pro(pro_messages)
            if result:
                record_token_spend(state, cost)
                # Store Pro analysis in state
                state.setdefault("pro_analyses", []).append({
                    "narrative": narrative,
                    "analysis": result.get("analysis", ""),
                    "cycle": state["cycle"],
                    "cost_cents": cost,
                })
                executed.append(f"pro:{narrative}")
                logger.info(f"  ✅ Pro analysis complete (${cost:.4f})")

        elif level == "opus":
            logger.info(f"→ Escalation to Opus needed for: {narrative}")
            executed.append(f"opus:{narrative}")

        resolve_escalation(state, i)

    return executed


# ── Main Cycle ──────────────────────────────────────────────────────

def run_cognition_cycle(force: bool = False) -> dict:
    """Execute one complete cognition cycle."""
    result = {
        "status": "ok",
        "flash_cost": 0.0,
        "escalation_cost": 0.0,
        "escalations": [],
        "narratives_updated": 0,
        "cycle": 0,
    }

    # Load state
    state = load_state()
    state["cycle"] += 1
    state["last_run"] = datetime.datetime.now(datetime.UTC).isoformat()
    cycle = state["cycle"]

    # Check budget
    if not force and would_exceed_budget(state, estimated_cost_cents=0.5):
        result["status"] = "budget_exceeded"
        logger.info("Skipping: daily budget exceeded")
        return result

    # Collect context
    context = collect_recent_context()

    # Degraded mode check
    if context.get("runtime_health", {}).get("disk", {}).get("usage_pct", 0) >= 90:
        result["status"] = "degraded"
        logger.info("Skipping: degraded mode (disk >= 90%)")
        return result

    # Build Flash input
    flash_input = build_flash_input(state, context)
    messages = [
        {"role": "system", "content": flash_input.split("## PREVIOUS_STATE")[0]},
        {"role": "user", "content": "## PREVIOUS_STATE" + flash_input.split("## PREVIOUS_STATE")[1]},
    ]

    # Call Flash
    flash_output, cost = call_flash(messages)
    result["flash_cost"] = cost

    if flash_output is None:
        mark_error(state, f"Flash API failure (cycle {cycle})")
        save_state(state)
        result["status"] = "flash_error"
        return result

    record_token_spend(state, cost)

    # Apply state update
    narratives_before = len(state["active_narratives"])
    apply_flash_output(state, flash_output)
    result["narratives_updated"] = len(state["active_narratives"]) - narratives_before

    # Maintenance
    archived = compact_state(state)

    # Check and execute escalations
    executed = execute_escalations(state)
    result["escalations"] = executed

    # Mark healthy
    mark_healthy(state)
    save_state(state)

    # Summary
    summary = snapshot_summary(state)
    result["summary"] = summary
    result["cycle"] = cycle

    logger.info(
        f"Cycle {cycle}: ${cost:.4f} | "
        f"{summary['narratives']} narratives | "
        f"{len(executed)} escalations | "
        f"$D{summary.get('total_spent','?')} total"
    )

    return result


# ── Daemon Mode ─────────────────────────────────────────────────────

_running = True


def _handle_shutdown(signum, frame):
    global _running
    logger.info("Shutdown signal received")
    _running = False


def run_daemon(interval: int = CYCLE_INTERVAL):
    """Run continuous cognition daemon."""
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    logger.info(f"Cognition daemon started (interval={interval}s)")

    with RuntimeLock("cognition-daemon", timeout=3600) as lock:
        if not lock.acquired:
            logger.error("Another cognition daemon is running — exiting")
            return

        while _running:
            try:
                result = run_cognition_cycle()
                if result["status"] != "ok":
                    logger.warning(f"Cycle skipped: {result['status']}")
            except Exception as e:
                logger.error(f"Cognition cycle error: {e}")
                mark_error(load_state(), str(e))

            # Sleep interruptibly
            for _ in range(interval):
                if not _running:
                    break
                time.sleep(1)

    logger.info("Cognition daemon stopped")


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Continuous Cognition Pipeline")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=CYCLE_INTERVAL,
                        help="Daemon interval in seconds")
    parser.add_argument("--status", action="store_true", help="Show state snapshot")
    parser.add_argument("--force", action="store_true", help="Run even if budget exceeded")
    parser.add_argument("--once", action="store_true", help="Run one cycle, print result")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.status:
        state = load_state()
        print(json.dumps(snapshot_summary(state), indent=2))
    elif args.once:
        result = run_cognition_cycle(force=True)
        print(json.dumps(result, indent=2, default=str))
    elif args.daemon:
        run_daemon(interval=args.interval)
    else:
        result = run_cognition_cycle(force=args.force)
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
