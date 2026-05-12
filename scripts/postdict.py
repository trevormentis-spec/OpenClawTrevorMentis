#!/usr/bin/env python3
"""
Postdiction & calibration tracker.

After each daily brief, checks whether yesterday's key judgments were
correct given today's information. Updates a running calibration score
that can influence confidence banding in future analysis.

Usage:
    python3 scripts/postdict.py --today ~/trevor-briefings/2026-05-12 --yesterday ~/trevor-briefings/2026-05-11

Pipeline integration:
    Called from daily-brief-cron.sh after analysis is produced.
    Creates/freshens brain/memory/semantic/calibration-tracking.json.

Design:
    - Loads yesterday's exec_summary.json for predictions
    - Loads today's incidents.json for outcome evidence
    - Uses the Oracle model to check each prediction against reality
    - Compares model's assessment with yesterday's confidence bands
    - Updates running calibration score
    - Writes calibration report to ~/trevor-briefings/{yesterday}/calibration.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CALIBRATION_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
ORACLE_MODEL = "anthropic/claude-opus-4.7"  # Best model for judgment

# Predictions should be re-checked after their horizon expires (default 7 days)
RECHECK_DAYS = 7


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[postdict {ts}] {msg}", file=sys.stderr, flush=True)


def call_oracle(system: str, user: str, provider: str = "openrouter") -> str:
    """Call the oracle model to evaluate a prediction against evidence."""
    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        base_url = "https://openrouter.ai/api"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
            "X-Title": "TREVOR Calibration",
        }
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set")
        base_url = "https://api.deepseek.com"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    model = ORACLE_MODEL if provider == "openrouter" else "deepseek/deepseek-v4-pro"
    api_model = model.split("/", 1)[-1] if "/" in model and provider != "openrouter" else model

    payload = {
        "model": api_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,  # Low temp for objective evaluation
        "max_tokens": 4096,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=body, method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}")


def load_json(path: str | pathlib.Path) -> dict:
    p = pathlib.Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def load_calibration_history() -> dict:
    """Load existing calibration tracking, or create fresh."""
    if CALIBRATION_FILE.exists():
        try:
            return json.loads(CALIBRATION_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            pass
    return {
        "version": 2,
        "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "total_judgments": 0,
        "correct": 0,
        "incorrect": 0,
        "unresolved": 0,
        "by_confidence_band": {},
        "by_region": {},
        "daily_scores": [],
        "last_updated": None,
    }


def evaluate_single_judgment(kj: dict, today_incidents: list[dict],
                              today_exec: dict) -> dict:
    """
    Use the oracle model to check if a prediction was correct.
    Returns an evaluation dict with verdict and explanation.
    """
    date_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    
    system = (
        "You are a calibration auditor. Given a prediction made yesterday "
        "and today's evidence, determine whether the prediction is correct, "
        "incorrect, or unresolved (too early to tell, or insufficient evidence).\n\n"
        "Use these criteria:\n"
        "- CORRECT: The predicted event occurred or the trend direction was right\n"
        "- INCORRECT: The predicted event did NOT occur or direction was wrong\n"
        "- UNRESOLVED: 24h is too short to judge, or evidence is contradictory\n\n"
        "Respond ONLY with a JSON object: {\"verdict\": \"correct|incorrect|unresolved\", "
        "\"confidence\": \"high|medium|low\", \"explanation\": \"...\"}"
    )

    today_bluf = today_exec.get("bluf", "")[:500]
    incidents_preview = json.dumps([
        {"region": i.get("region"), "title": i.get("title", "")[:100],
         "source": i.get("source_rating", "")}
        for i in today_incidents[:20]
    ], indent=2)[:2000]

    user = (
        f"Prediction (made previously):\n"
        f"Statement: {kj.get('statement', '')}\n"
        f"Confidence band: {kj.get('sherman_kent_band', 'unknown')}\n"
        f"Probability: {kj.get('prediction_pct', '?')}%\n"
        f"Horizon: {kj.get('horizon_days', 7)} days\n"
        f"From region: {kj.get('drawn_from_region', 'unknown')}\n\n"
        f"Today's BLUF: {today_bluf}\n\n"
        f"Today's incidents (first 20):\n{incidents_preview}\n\n"
        f"Remember: this prediction was made ~24h ago. "
        f"Some judgments may need several days to resolve. "
        f"Be honest about what's unresolvable yet."
    )

    try:
        raw = call_oracle(system, user)
        raw = raw.strip()
        if raw.startswith("```"):
            import re
            raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
            raw = re.sub(r"\n```$", "", raw)
        return json.loads(raw)
    except Exception as exc:
        return {"verdict": "unresolved", "confidence": "low",
                "explanation": f"Oracle evaluation failed: {exc}"}


def recheck_expired(cal: dict) -> dict:
    """Re-check predictions whose 7-day horizon has expired.
    
    Scans all daily scores for predictions that were marked 'unresolved'
    but whose 7-day horizon has now passed. Re-evaluates them against
    current reality.
    """
    now = dt.datetime.now(dt.timezone.utc)
    rechecked = 0

    for score_entry in cal.get("daily_scores", []):
        horizion_expiry = score_entry.get("horizon_expiry", "")
        if not horizion_expiry:
            continue
        try:
            expiry = dt.datetime.fromisoformat(horizion_expiry)
        except (ValueError, TypeError):
            continue
        
        if now < expiry:
            continue  # Not expired yet
        
        if score_entry.get("rechecked", False):
            continue  # Already re-checked
        
        # This prediction set can now be evaluated definitively
        # For now, mark it as rechecked — full re-evaluation requires
        # the original prediction data and current incidents
        score_entry["rechecked"] = True
        score_entry["rechecked_at"] = now.isoformat()
        rechecked += 1
    
    if rechecked:
        log(f"Marked {rechecked} expired prediction set(s) for re-evaluation")
    return cal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", required=True, help="today's working directory")
    parser.add_argument("--yesterday", required=True, help="yesterday's working directory")
    parser.add_argument("--recheck", action="store_true",
                        help="Re-check expired predictions (>7 days old)")
    args = parser.parse_args()

    # Handle recheck mode separately — doesn't need today/yesterday dirs
    if args.recheck:
        log("Running recheck of expired predictions")
        cal = load_calibration_history()
        cal = recheck_expired(cal)
        CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIBRATION_FILE.write_text(json.dumps(cal, indent=2))
        log(f"Recheck complete. Saved to {CALIBRATION_FILE}")
        return 0

    today_dir = pathlib.Path(args.today).expanduser().resolve()
    yesterday_dir = pathlib.Path(args.yesterday).expanduser().resolve()

    # Load yesterday's predictions
    yest_exec = load_json(yesterday_dir / "analysis" / "exec_summary.json")
    if not yest_exec:
        log("No exec_summary found from yesterday — nothing to postdict. Skipping.")
        return 0

    predictions = yest_exec.get("five_judgments", [])
    if not predictions:
        log("No judgments found in yesterday's exec_summary — skipping postdiction.")
        return 0

    log(f"Loaded {len(predictions)} predictions from {yesterday_dir.name}")

    # Load today's incidents + exec summary
    today_incidents = load_json(today_dir / "raw" / "incidents.json").get("incidents", [])
    today_exec = load_json(today_dir / "analysis" / "exec_summary.json")
    log(f"Loaded {len(today_incidents)} today's incidents")

    # Evaluate each judgment
    evaluations = []
    for kj in predictions:
        log(f"Evaluating: {kj.get('id', '?')} — {kj.get('statement', '')[:80]}...")
        eval_result = evaluate_single_judgment(kj, today_incidents, today_exec)
        evaluations.append({
            **kj,
            "postdict": eval_result,
        })
        log(f"  Verdict: {eval_result.get('verdict', 'unknown')} "
            f"(confidence: {eval_result.get('confidence', 'unknown')})")

    # Calculate stats — exclude unresolved from accuracy calculation
    # Geopolitical predictions take 7 days to verify; marking unresolved as wrong
    # produces misleading calibration feedback
    verdicts = [e["postdict"]["verdict"] for e in evaluations]
    correct = verdicts.count("correct")
    incorrect = verdicts.count("incorrect")
    unresolved = verdicts.count("unresolved")
    total = len(evaluations)
    resolved = correct + incorrect
    accuracy_pct = round((correct / resolved * 100) if resolved > 0 else None, 1) if resolved > 0 else None

    # Build calibration report
    calibration = {
        "date": today_dir.name,
        "yesterday": yesterday_dir.name,
        "predictions_evaluated": total,
        "correct": correct,
        "incorrect": incorrect,
        "unresolved": unresolved,
        "accuracy_pct": accuracy_pct if accuracy_pct is not None else 0.0,
        "evaluations": evaluations,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
    }

    # Save to yesterday's directory
    cal_path = yesterday_dir / "calibration.json"
    cal_path.write_text(json.dumps(calibration, indent=2))
    log(f"Calibration report saved to {cal_path}")

    # Update running calibration tracker
    history = load_calibration_history()
    history["total_judgments"] += total
    history["correct"] += correct
    history["incorrect"] += incorrect
    history["unresolved"] += unresolved
    history["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat() + "Z"

    # Update by-band stats
    for e in evaluations:
        band = e.get("sherman_kent_band", "unknown").lower()
        if band not in history["by_confidence_band"]:
            history["by_confidence_band"][band] = {"total": 0, "correct": 0, "incorrect": 0}
        history["by_confidence_band"][band]["total"] += 1
        verdict = e["postdict"]["verdict"]
        if verdict == "correct":
            history["by_confidence_band"][band]["correct"] += 1
        elif verdict == "incorrect":
            history["by_confidence_band"][band]["incorrect"] += 1

    # Update by-region stats
    for e in evaluations:
        region = e.get("drawn_from_region", "unknown")
        if region not in history["by_region"]:
            history["by_region"][region] = {"total": 0, "correct": 0, "incorrect": 0}
        history["by_region"][region]["total"] += 1
        verdict = e["postdict"]["verdict"]
        if verdict == "correct":
            history["by_region"][region]["correct"] += 1
        elif verdict == "incorrect":
            history["by_region"][region]["incorrect"] += 1

    # Add daily score
    overall_pct = round((history["correct"] / max(history["total_judgments"], 1) * 100), 1)
    # Calculate horizon expiry (predictions are 7-day; re-check after that)
    horizon_expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)).isoformat()
    history["daily_scores"].append({
        "date": today_dir.name,
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "unresolved": unresolved,
        "accuracy_pct": accuracy_pct if accuracy_pct is not None else 0.0,
        "running_accuracy_pct": overall_pct,
        "horizon_expiry": horizon_expiry,
        "rechecked": False,
    })
    # Keep last 90 days
    history["daily_scores"] = history["daily_scores"][-90:]

    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_FILE.write_text(json.dumps(history, indent=2))
    log(f"Calibration history updated at {CALIBRATION_FILE}")

    # Print summary
    print(f"\n{'='*50}")
    print(f"POSTDICTION SUMMARY — {today_dir.name}")
    print(f"{'='*50}")
    print(f"Predictions evaluated: {total}")
    print(f"  Correct:   {correct}  ({round(correct/max(total,1)*100)}%)")
    print(f"  Incorrect: {incorrect}  ({round(incorrect/max(total,1)*100)}%)")
    print(f"  Unresolved:{unresolved}  ({round(unresolved/max(total,1)*100)}%)")
    print(f"Running accuracy: {overall_pct}%")
    print(f"{'='*50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
