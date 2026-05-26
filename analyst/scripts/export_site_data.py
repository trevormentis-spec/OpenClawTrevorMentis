#!/usr/bin/env python3
"""
Export KJ feed + calibration data for the public website.
Copies to exports/kj-feeds/ and generates a calibration.json for the site.

Usage:
  python3 export_site_data.py         # Generates all site data
  python3 export_site_data.py --deploy # Also writes to deploy directory
"""

import sys
import os
import json
import shutil
import logging
import datetime
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("site-export")
logger.setLevel(logging.WARNING)

WORKSPACE = Path(__file__).parent.parent.parent
EXPORT_DIR = WORKSPACE / "exports" / "kj-feeds"

CALIBRATION_SRC = WORKSPACE / "brain" / "memory" / "semantic" / "calibration-tracking.json"
CALIBRATION_DST = EXPORT_DIR / "calibration.json"
FEED_SRC = EXPORT_DIR / "kj-feed-latest.json"
DEPLOY_DIR = None  # Set by --deploy flag


def export_feed() -> bool:
    """Ensure KJ feed exists at export location."""
    if not FEED_SRC.exists():
        logger.warning("No KJ feed found — generating")
        result = subprocess.run(
            [sys.executable, str(WORKSPACE / "analyst" / "scripts" / "kj_feed.py")],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            logger.error(f"Feed generation failed: {result.stderr}")
            return False
    return True


def export_calibration() -> bool:
    """Copy calibration data to export directory, stripping internal fields."""
    if not CALIBRATION_SRC.exists():
        logger.warning("No calibration data found")
        return False

    try:
        with open(CALIBRATION_SRC) as f:
            cal = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read calibration: {e}")
        return False

    # Create a clean public version
    public_cal = {
        "total_judgments": cal.get("total_judgments", 0),
        "correct": cal.get("correct", 0),
        "incorrect": cal.get("incorrect", 0),
        "confirmed": cal.get("confirmed", 0),
        "disconfirmed": cal.get("disconfirmed", 0),
        "unresolved": cal.get("unresolved", 0),
        "expired_no_resolution": cal.get("expired_no_resolution", 0),
        "by_confidence_band": {},
        "by_region": {},
        "daily_scores": [],
        "overconfidence_flags": cal.get("overconfidence_flags", []),
        "last_updated": cal.get("last_updated", datetime.datetime.now(datetime.UTC).isoformat()),
    }

    # Clean by_confidence_band — only include bands with data
    for band, data in cal.get("by_confidence_band", {}).items():
        clean = {
            "total": data.get("total", 0),
            "correct": data.get("confirmed", data.get("correct", 0)),
            "incorrect": data.get("disconfirmed", data.get("incorrect", 0)),
        }
        if clean["total"] > 0:
            public_cal["by_confidence_band"][band] = clean

    # Clean by_region
    for region, data in cal.get("by_region", {}).items():
        clean = {
            "total": data.get("total", 0),
            "correct": data.get("confirmed", data.get("correct", 0)),
            "incorrect": data.get("disconfirmed", data.get("incorrect", 0)),
            "confirmed": data.get("confirmed", 0),
            "disconfirmed": data.get("disconfirmed", 0),
        }
        if clean["total"] > 0:
            public_cal["by_region"][region] = clean

    # Clean daily_scores
    for day in cal.get("daily_scores", []):
        clean = {
            "date": day.get("date", "?")[:10],
            "total": day.get("total", 0),
            "confirmed": day.get("confirmed", 0),
            "disconfirmed": day.get("disconfirmed", 0),
            "unresolved": day.get("unresolved", 0),
        }
        public_cal["daily_scores"].append(clean)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CALIBRATION_DST, "w") as f:
        json.dump(public_cal, f, indent=2)

    logger.info(f"Calibration exported: {CALIBRATION_DST}")
    return True


def deploy(deploy_path: str) -> bool:
    """Copy all site assets to the deploy directory."""
    deploy_dir = Path(deploy_path) / "data"
    deploy_dir.mkdir(parents=True, exist_ok=True)

    # Copy KJ feed
    if FEED_SRC.exists():
        shutil.copy2(FEED_SRC, deploy_dir / "kj-feed-latest.json")
        logger.info(f"Copied KJ feed to {deploy_dir}")

    # Copy calibration
    if CALIBRATION_DST.exists():
        shutil.copy2(CALIBRATION_DST, deploy_dir / "calibration.json")
        logger.info(f"Copied calibration to {deploy_dir}")

    # Copy HTML pages
    for page in ["brief.html", "calibration.html"]:
        src = EXPORT_DIR / page
        if src.exists():
            shutil.copy2(src, deploy_dir.parent / page)
            logger.info(f"Copied {page} to {deploy_dir.parent}")

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Export site data")
    parser.add_argument("--deploy", type=str, help="Deploy directory path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.INFO)

    ok = True
    ok &= export_feed()
    ok &= export_calibration()

    if args.deploy:
        ok &= deploy(args.deploy)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
