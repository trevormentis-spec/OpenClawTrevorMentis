#!/usr/bin/env python3
"""
I&W Feedback Loop — connects postdiction calibration to Philby desk narratives.

Three functions:
  1. Sync I&W board indicators into Philby desk monitoring
  2. Push postdiction calibration results into Philby desk confidence adjustments
  3. Generate testable predictions from I&W boards for postdiction to score

Usage:
    python3 scripts/iw_feedback_loop.py --sync           # Sync I&W → Philby
    python3 scripts/iw_feedback_loop.py --calibrate      # Push calibration → Philby desks
    python3 scripts/iw_feedback_loop.py --all            # Full cycle
"""

import json, os, pathlib, sys, datetime

BASE = pathlib.Path(__file__).resolve().parent.parent
CALIBRATION_FILE = BASE / "brain" / "memory" / "semantic" / "calibration-tracking.json"
PHILBY_CONFIG = BASE / "philby" / "desks" / "philby-config.json"
IANDW_DIR = BASE / "analyst" / "boards"

def log(msg): print(f"[iw-loop {datetime.datetime.now(datetime.UTC).strftime('%H:%M:%S')}] {msg}", flush=True)

def load_json(p):
    try: return json.loads(p.read_text())
    except: return {}

def save_json(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2))

def sync_iw_to_philby():
    """Link I&W board indicators to Philby desk monitoring."""
    philby = load_json(PHILBY_CONFIG)
    boards = sorted(IANDW_DIR.glob("*-iw-board.json"))
    
    if not boards:
        log("No I&W boards found — skipping sync")
        return 0
    
    linked = 0
    for board_path in boards:
        board = load_json(board_path)
        desk_id = board.get("linked_desk", "")
        if desk_id and desk_id in philby.get("desks", {}):
            indicators = board.get("indicators", [])
            active_iw = sum(1 for i in indicators if i.get("status") == "active")
            triggered = sum(1 for i in indicators if i.get("triggered"))
            log(f"  {board['board']}: {len(indicators)} indicators ({active_iw} active, {triggered} triggered)")
            linked += len(indicators)
    
    log(f"Synced {linked} indicators across {len(boards)} boards")
    return linked


def push_calibration_to_desks():
    """Push postdiction calibration accuracy into Philby desk confidence adjustments."""
    cal = load_json(CALIBRATION_FILE)
    philby = load_json(PHILBY_CONFIG)
    
    # Get overall calibration accuracy from resolved judgments
    total = cal.get("total_judgments", 0)
    correct = cal.get("correct", 0)
    incorrect = cal.get("incorrect", 0)
    unresolved = cal.get("unresolved", 0)
    resolved = correct + incorrect
    
    if resolved == 0:
        log("No resolved judgments — no calibration to push")
        return
    
    accuracy_pct = round(correct / resolved * 100, 1) if resolved > 0 else 0
    
    # Map accuracy to calibration adjustment
    # If accuracy < 30%, desks are overconfident — reduce confidence by 5-10pts
    # If accuracy > 70%, desks are well-calibrated — no adjustment needed
    if accuracy_pct < 30:
        adjustment = "reduce_confidence"
        adjustment_pts = 5
        log(f"Calibration {accuracy_pct}% → reducing desk confidence by {adjustment_pts}pts (overconfidence detected)")
    elif accuracy_pct < 50:
        adjustment = "reduce_confidence"
        adjustment_pts = 3
        log(f"Calibration {accuracy_pct}% → reducing desk confidence by {adjustment_pts}pts")
    else:
        adjustment = "no_adjustment"
        adjustment_pts = 0
        log(f"Calibration {accuracy_pct}% → no confidence adjustment needed")
    
    # Write calibration stamp for Philby desks
    stamp = {
        "last_calibration": datetime.datetime.now(datetime.UTC).isoformat(),
        "overall_accuracy_pct": accuracy_pct,
        "resolved_judgments": resolved,
        "total_judgments": total,
        "adjustment": adjustment,
        "adjustment_pts": adjustment_pts,
    }
    
    cal_stamp_path = BASE / "philby" / "trader" / "calibration-stamp.json"
    save_json(cal_stamp_path, stamp)
    log(f"Wrote calibration stamp to {cal_stamp_path}")
    
    # Update each Philby desk's calibration entry
    for desk_id, desk in philby.get("desks", {}).items():
        desk["calibration_adjustment"] = adjustment_pts
        desk["calibration_accuracy_pct"] = accuracy_pct
    
    save_json(PHILBY_CONFIG, philby)
    log(f"Updated {len(philby.get('desks', {}))} desks with calibration data")
    return accuracy_pct


def generate_predictions_from_iw():
    """Generate testable predictions from I&W indicators for postdiction."""
    boards = sorted(IANDW_DIR.glob("*-iw-board.json"))
    predictions = []
    
    for board_path in boards:
        board = load_json(board_path)
        for ind in board.get("indicators", []):
            if ind.get("status") != "active":
                continue
            
            # Each indicator with time_bounds can be a prediction
            time_bounds = ind.get("time_bounds", "7 days")
            try:
                days = int(time_bounds.split()[0])
            except:
                days = 7
            
            predictions.append({
                "source_board": board["board"],
                "indicator_id": ind["id"],
                "indicator": ind["indicator"],
                "hypothesis": ind["hypothesis"],
                "direction": ind["direction"],
                "time_bounds_days": days,
                "status": "pending",
            })
    
    pred_file = BASE / "analyst" / "boards" / "iw-predictions.json"
    existing = load_json(pred_file)
    existing["predictions"] = predictions
    existing["generated"] = datetime.datetime.now(datetime.UTC).isoformat()
    save_json(pred_file, existing)
    log(f"Generated {len(predictions)} testable predictions from I&W boards")
    return predictions


def main():
    import argparse
    parser = argparse.ArgumentParser(description="I&W Feedback Loop")
    parser.add_argument("--sync", action="store_true", help="Sync I&W → Philby")
    parser.add_argument("--calibrate", action="store_true", help="Push calibration → desks")
    parser.add_argument("--predictions", action="store_true", help="Generate predictions from I&W")
    parser.add_argument("--all", action="store_true", help="Full cycle")
    args = parser.parse_args()
    
    if args.all or args.sync:
        log("=== Syncing I&W → Philby ===")
        sync_iw_to_philby()
    
    if args.all or args.calibrate:
        log("=== Pushing calibration → desks ===")
        push_calibration_to_desks()
    
    if args.all or args.predictions:
        log("=== Generating predictions from I&W ===")
        generate_predictions_from_iw()
    
    log("Done.")

if __name__ == "__main__":
    main()
