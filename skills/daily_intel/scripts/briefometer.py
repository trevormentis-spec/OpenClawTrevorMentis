#!/usr/bin/env python3
"""📊 Briefometer — Multi-axis measurement system for the daily intel brief.

Tracks and scores improvement across three axes:
  1. VISUAL QUALITY  — maps, photos, infographics, layout
  2. CONTENT QUALITY — assessments: depth, sourcing, estimative language
  3. PREDICTIVE ACCURACY — Brier scores for Key Judgments over time

Usage:
  python3 briefometer.py              # Full measurement run
  python3 briefometer.py --dashboard  # Show historical dashboard
  python3 briefometer.py --kjs        # Elicit/record a Key Judgment
  python3 briefometer.py --calibrate  # Show calibration curve
"""
import os, sys, json, re, datetime, math, subprocess
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSESS_DIR = SKILL_ROOT / 'assessments'
IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
INFO_DIR = SKILL_ROOT / 'infographics'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
EXPORTS_DIR = Path.home() / '.openclaw' / 'workspace' / 'exports'
from trevor_config import WORKSPACE, THEATRE_KEYS as THEATRES

MEASUREMENT_LOG = CRON_DIR / 'measurement_log.json'
KJ_LOG = CRON_DIR / 'key_judgments.json'


# ═══════════════════════════════════════════════════════════
# AXIS 1: VISUAL QUALITY
# ═══════════════════════════════════════════════════════════

def score_visual_quality(date_str=None):
    """Score visual quality across all image types.

    Returns dict of theatre -> {photo, map, infographic, total} scores.
    """
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    results = {}
    overall = {"photo": 0, "map": 0, "infographic": 0, "total": 0}

    for idx, theatre in enumerate(THEATRES, 1):
        scores = {}

        # Photo
        photo = IMAGES_DIR / f"{date_str}_{theatre}.jpg"
        if photo.exists():
            sz = os.path.getsize(photo)
            from PIL import Image
            img = Image.open(photo)
            w, h = img.size
            # Score: 0-10 based on size + resolution
            sz_score = min(10, sz // 20000)  # 200KB = 10pts
            res_score = min(5, w // 400)     # 2000px = 5pts
            scores["photo"] = sz_score + res_score
        else:
            scores["photo"] = 0

        # Map
        map_f = MAPS_DIR / f"{idx:02d}_{theatre}.png"
        if map_f.exists():
            sz = os.path.getsize(map_f)
            from PIL import Image
            img = Image.open(map_f)
            w, h = img.size
            sz_score = min(10, sz // 5000)   # 50KB = 10pts
            res_score = min(5, w // 200)     # 1200px = 6pt cap
            scores["map"] = sz_score + min(5, res_score)
        else:
            scores["map"] = 0

        # Infographic
        info_f = INFO_DIR / f"{idx:02d}_{theatre}.png"
        if info_f.exists():
            sz = os.path.getsize(info_f)
            sz_score = min(10, sz // 2000)   # 20KB = 10pts
            scores["infographic"] = sz_score
        else:
            scores["infographic"] = 0

        scores["total"] = sum(scores.values())
        results[theatre] = scores

        for k in overall:
            if k == "total":
                continue
            overall[k] += scores.get(k, 0)

    overall["total"] = sum(v for k, v in overall.items() if k != "total")
    return {"theatres": results, "overall": overall}


# ═══════════════════════════════════════════════════════════
# AXIS 2: CONTENT QUALITY
# ═══════════════════════════════════════════════════════════

def score_content_quality():
    """Score assessment content across multiple factors.

    Metrics:
    - Depth: word count per assessment
    - Structure: number of sections/headings
    - Sourcing: number of unique named sources cited
    - Estimative language: proper use of calibrated language
    - Diversity: range of source types (news, academic, official)
    - Readability: Flesch-like score for intelligence writing
    """
    results = {}
    overall = {
        "depth": 0, "structure": 0, "sourcing": 0,
        "estimate": 0, "diversity": 0, "total": 0
    }

    source_types = {
        "news": ["bbc", "cnn", "reuters", "ap ", "nyt ", "washington post", "axios",
                 "al jazeera", "npr", "bloomberg", "wsj", "financial times",
                 "the diplomat", "kyiv post", "turkish", "tass"],
        "academic": ["isw", "critical threats", "csis", "rand", "chatham house",
                     "iiss", "brookings", "aei", "wilson center"],
        "official": ["state department", "pentagon", "white house", "centcom",
                     "treasury", "ofac", "us congress", "un ", "nato", "ecowas",
                     "iaf", "irgc", "mod"],
        "intel": ["shurkin", "acled", "polymarket", "kalshi", "ukmto",
                  "jmic", "stratfor", "janes"],
    }

    estimate_terms = {
        "highly_likely": ["highly likely", "almost certain"],
        "likely": ["likely", "probably", "expected to"],
        "roughly_even": ["roughly even", "about even", "approximately"],
        "unlikely": ["unlikely", "improbable", "probably not"],
        "highly_unlikely": ["highly unlikely", "remote", "almost no chance"],
    }

    for theatre in THEATRES:
        ass = ASSESS_DIR / f"{theatre}.md"
        if not ass.exists():
            results[theatre] = {k: 0 for k in overall}
            continue

        text = ass.read_text()
        scores = {}

        # Depth: word count (target 2000-3500)
        words = len(text.split())
        if words < 1000:
            scores["depth"] = 3
        elif words < 2000:
            scores["depth"] = 6
        elif words < 3500:
            scores["depth"] = 10
        else:
            scores["depth"] = 8

        # Structure: heading density
        headings = len(re.findall(r'^#{1,4}\s', text, re.MULTILINE))
        if headings < 5:
            scores["structure"] = 3
        elif headings < 10:
            scores["structure"] = 6
        elif headings < 20:
            scores["structure"] = 10
        else:
            scores["structure"] = 8

        # Sourcing: count unique named sources
        sources_found = set()
        for stype, keywords in source_types.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    sources_found.add(kw)
        scores["sourcing"] = min(10, len(sources_found))

        # Diversity: how many different source categories
        cats_found = set()
        for stype, keywords in source_types.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    cats_found.add(stype)
                    break
        scores["diversity"] = len(cats_found) * 3  # max 12, capped at 10

        # Estimative language: use of calibrated terms
        est_count = 0
        for category, terms in estimate_terms.items():
            for term in terms:
                est_count += text.lower().count(term)
        if est_count < 3:
            scores["estimate"] = 3
        elif est_count < 6:
            scores["estimate"] = 6
        else:
            scores["estimate"] = 10

        scores["total"] = sum(scores.values())
        results[theatre] = scores

        for k in overall:
            if k == "total":
                continue
            overall[k] += scores.get(k, 0)

    overall["total"] = sum(v for k, v in overall.items() if k != "total")
    return {"theatres": results, "overall": overall}


# ═══════════════════════════════════════════════════════════
# AXIS 3: PREDICTIVE ACCURACY
# ═══════════════════════════════════════════════════════════

def load_kjs():
    """Load the Key Judgment tracking log."""
    if KJ_LOG.exists():
        return json.loads(KJ_LOG.read_text())
    return {"judgments": [], "brier_scores": [], "calibration": {}}


def save_kjs(data):
    """Save the Key Judgment log."""
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    KJ_LOG.write_text(json.dumps(data, indent=2))


def record_kj():
    """Interactive elicitation of a Key Judgment for future verification."""
    print("\n=== Key Judgment Elicitation ===")
    print("Record a prediction so we can score it later.\n")

    theatres_str = ", ".join(f"{i+1}. {t}" for i, t in enumerate(THEATRES))
    print(f"Theatres: {theatres_str}")
    t_idx = input("Theatre number: ").strip()
    try:
        theatre = THEATRES[int(t_idx) - 1]
    except:
        theatre = "unknown"

    kj_text = input("Key Judgment: ").strip()
    if not kj_text:
        print("Cancelled.")
        return

    print("\nProbability (0-100):")
    prob = input("> ").strip()
    try:
        prob = min(100, max(0, int(prob)))
    except:
        prob = 50

    horizon = input("Verification horizon (days, e.g. 30): ").strip()
    try:
        horizon_days = int(horizon)
    except:
        horizon_days = 30

    source = input("Source ref (optional): ").strip()

    judgment = {
        "id": f"KJ-{datetime.date.today().isoformat()}-{len(load_kjs()['judgments']) + 1}",
        "date": datetime.date.today().isoformat(),
        "theatre": theatre,
        "text": kj_text,
        "probability": prob,
        "horizon_days": horizon_days,
        "verify_by": (datetime.date.today() + datetime.timedelta(days=horizon_days)).isoformat(),
        "source": source,
        "outcome": None,  # True/False/None
        "verified_date": None,
    }

    data = load_kjs()
    data["judgments"].append(judgment)
    save_kjs(data)

    print(f"\n✓ Recorded {judgment['id']}: {kj_text} @ {prob}%")
    print(f"  Verify by: {judgment['verify_by']}")


def verify_kj():
    """Verify an open Key Judgment against reality."""
    data = load_kjs()
    pending = [j for j in data["judgments"] if j["outcome"] is None]

    if not pending:
        print("No pending judgments to verify.")
        return

    print(f"\n=== Verify Key Judgments ===")
    print(f"{len(pending)} pending:\n")

    for i, kj in enumerate(pending):
        print(f"[{i+1}] {kj['id']}: {kj['text']}")
        print(f"    Predicted: {kj['probability']}%  |  Theatre: {kj['theatre']}")
        print(f"    Verify by: {kj['verify_by']}  |  Source: {kj.get('source', 'N/A')}")
        print()

    idx = input("Which one to verify? (number or q): ").strip()
    if idx.lower() == 'q':
        return

    try:
        kj = pending[int(idx) - 1]
    except:
        print("Invalid.")
        return

    outcome = input("Outcome (y/n/s for skip): ").strip().lower()
    if outcome == 'y':
        kj["outcome"] = True
    elif outcome == 'n':
        kj["outcome"] = False
    else:
        return

    kj["verified_date"] = datetime.date.today().isoformat()
    save_kjs(data)
    print(f"✓ {kj['id']} verified: {'HIT' if kj['outcome'] else 'MISS'}")

    # Recalculate Brier scores
    calc_brier_scores(data)


def calc_brier_scores(data):
    """Calculate Brier score for all verified judgments.

    Brier score = mean of (prediction - outcome)²
    0 = perfect, 1 = worst
    """
    verified = [j for j in data["judgments"] if j["outcome"] is not None]
    if not verified:
        return

    scores = []
    for kj in verified:
        p = kj["probability"] / 100.0
        o = 1.0 if kj["outcome"] else 0.0
        brier = (p - o) ** 2
        scores.append({
            "id": kj["id"],
            "theatre": kj["theatre"],
            "brier": round(brier, 4),
            "predicted": kj["probability"],
            "outcome": kj["outcome"],
        })

    mean_brier = round(sum(s["brier"] for s in scores) / len(scores), 4)

    data["brier_scores"] = scores
    data["mean_brier"] = mean_brier

    # Calibration bins
    bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    calibration = {}
    for lo, hi in bins:
        in_bin = [j for j in verified if lo <= j["probability"] < hi]
        if in_bin:
            hits = sum(1 for j in in_bin if j["outcome"])
            calibration[f"{lo}-{hi}%"] = {
                "count": len(in_bin),
                "hits": hits,
                "accuracy": round(hits / len(in_bin) * 100, 1),
            }
    data["calibration"] = calibration

    save_kjs(data)


def show_calibration():
    """Show calibration curve."""
    data = load_kjs()
    if not data.get("calibration"):
        print("No calibration data yet. Verify some KJs first.")
        return

    print("\n=== Calibration Curve ===\n")
    print(f"{'Bin':<12} {'Count':<8} {'Hits':<8} {'Accuracy':<10} {'Ideal':<10}")
    print("-" * 50)

    for bin_label, stats in sorted(data["calibration"].items()):
        lo = int(bin_label.split("-")[0])
        hi = int(bin_label.split("%")[0].split("-")[1])
        ideal = (lo + hi) / 2
        acc = stats["accuracy"]
        diff = acc - ideal
        marker = "✓" if abs(diff) < 10 else "△" if abs(diff) < 20 else "✗"
        print(f"{bin_label:<12} {stats['count']:<8} {stats['hits']:<8} {acc:<10.1f} {ideal:<10.1f} {marker}")

    verified = [j for j in data["judgments"] if j["outcome"] is not None]
    print(f"\nMean Brier Score: {data.get('mean_brier', 'N/A')}")
    print(f"Total verified: {len(verified)}")

    # Interpret Brier
    brier = data.get("mean_brier", 1)
    if brier < 0.1:
        print("Grade: A — Excellent calibration")
    elif brier < 0.2:
        print("Grade: B — Good calibration")
    elif brier < 0.3:
        print("Grade: C — Needs improvement")
    else:
        print("Grade: D — Poor calibration (consider recalibration)")


# ═══════════════════════════════════════════════════════════
# PDF QUALITY SCAN
# ═══════════════════════════════════════════════════════════

def score_pdf_quality(date_str=None):
    """Score the PDF document quality."""
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    score = 0

    # Find PDF
    pdf_paths = sorted(EXPORTS_DIR.glob(f"*{date_str}*.pdf"))
    if not pdf_paths:
        pdf_paths = sorted(SKILL_ROOT.glob(f"security_brief_{date_str}.pdf"))
    if not pdf_paths:
        return 0

    pdf = pdf_paths[-1]
    size_kb = os.path.getsize(pdf) // 1024

    # Size score: 1-3MB ideal
    if 1500 <= size_kb <= 4000:
        score += 10
    elif size_kb > 1000:
        score += 7
    else:
        score += 3

    # Count embedded images via pdfimages
    try:
        result = subprocess.run(['pdfimages', '-list', str(pdf)],
                               capture_output=True, text=True, timeout=10)
        img_count = len([l for l in result.stdout.split('\n') if l.strip()]) - 2
        if img_count >= 22:
            score += 10
        elif img_count >= 18:
            score += 7
        elif img_count >= 12:
            score += 4
        else:
            score += 1
    except:
        pass

    # Get page count
    try:
        result = subprocess.run(['pdfinfo', str(pdf)],
                               capture_output=True, text=True, timeout=10)
        pages_match = re.search(r'Pages:\s+(\d+)', result.stdout)
        if pages_match:
            pages = int(pages_match.group(1))
            if 30 <= pages <= 45:
                score += 5
            elif pages >= 20:
                score += 3
            else:
                score += 1
    except:
        pass

    return score


# ═══════════════════════════════════════════════════════════
# MEASUREMENT LOG
# ═══════════════════════════════════════════════════════════

def load_measurements():
    if MEASUREMENT_LOG.exists():
        return json.loads(MEASUREMENT_LOG.read_text())
    return {"runs": [], "trends": {}}


def save_measurement(date_str, visual, content, pdf_score, kj_score=None):
    """Save a measurement snapshot."""
    log = load_measurements()
    entry = {
        "date": date_str,
        "visual": visual,
        "content": content,
        "pdf_quality": pdf_score,
    }
    if kj_score is not None:
        entry["brier"] = kj_score
    log["runs"].append(entry)
    MEASUREMENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    MEASUREMENT_LOG.write_text(json.dumps(log, indent=2))
    return entry


# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════

def show_dashboard():
    """Show full measurement dashboard with trends."""
    log = load_measurements()
    kj_data = load_kjs()

    print("\n" + "=" * 72)
    print("  📊 BRIEFOMETER — Multi-Axis Measurement Dashboard")
    print("=" * 72)

    if not log.get("runs"):
        print("\n  No measurement data yet. Run briefometer.py to collect baseline.")
        return

    # Latest measurement
    latest = log["runs"][-1]

    print(f"\n  Date: {latest['date']}")
    print(f"  {'─' * 60}")
    print(f"  Axis 1 — Visual Quality:     {latest['visual']}/150")
    print(f"  Axis 2 — Content Quality:     {latest['content']}/150")
    print(f"  Axis 3 — PDF Quality:         {latest['pdf_quality']}/25")

    if "brier" in latest:
        brier = latest["brier"]
        grade = "A" if brier < 0.1 else "B" if brier < 0.2 else "C" if brier < 0.3 else "D"
        print(f"  Axis 4 — Predictive (Brier): {brier} ({grade})")

    total = latest.get("visual", 0) + latest.get("content", 0) + latest.get("pdf_quality", 0)
    print(f"\n  COMPOSITE SCORE: {total}/325")

    # Trend
    if len(log["runs"]) >= 2:
        print(f"\n  {'─' * 60}")
        print(f"  TREND (last {len(log['runs'])} runs):")

        # Visual trend
        visual_vals = [r["visual"] for r in log["runs"]]
        v_trend = visual_vals[-1] - visual_vals[0]
        v_dir = "↑" if v_trend > 0 else "↓" if v_trend < 0 else "→"
        print(f"  Visual:    {visual_vals[0]} → {visual_vals[-1]} {v_dir}{abs(v_trend)}")

        # Content trend
        c_vals = [r["content"] for r in log["runs"]]
        c_trend = c_vals[-1] - c_vals[0]
        c_dir = "↑" if c_trend > 0 else "↓" if c_trend < 0 else "→"
        print(f"  Content:   {c_vals[0]} → {c_vals[-1]} {c_dir}{abs(c_trend)}")

        # Composite trend
        comp_vals = [
            r.get("visual", 0) + r.get("content", 0) + r.get("pdf_quality", 0)
            for r in log["runs"]
        ]
        comp_trend = comp_vals[-1] - comp_vals[0]
        comp_dir = "↑" if comp_trend > 0 else "↓" if comp_trend < 0 else "→"
        print(f"  Composite: {comp_vals[0]} → {comp_vals[-1]} {comp_dir}{abs(comp_trend)}")

    # KJ summary
    if kj_data.get("judgments"):
        verified = [j for j in kj_data["judgments"] if j["outcome"] is not None]
        pending = [j for j in kj_data["judgments"] if j["outcome"] is None]
        print(f"\n  Key Judgments: {len(kj_data['judgments'])} total")
        print(f"  Verified: {len(verified)}  |  Pending: {len(pending)}")
        if verified:
            hits = sum(1 for j in verified if j["outcome"])
            print(f"  Hit rate: {hits}/{len(verified)} ({hits/len(verified)*100:.0f}%)")
        if kj_data.get("mean_brier"):
            print(f"  Mean Brier: {kj_data['mean_brier']}")

    print(f"\n  {'─' * 60}")
    print(f"  Run: briefometer.py --kjs to record a Key Judgment")
    print(f"       briefometer.py --calibrate to see calibration curve")
    print(f"       briefometer.py for fresh measurement run")
    print("=" * 72 + "\n")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Briefometer — multi-axis quality measurement")
    parser.add_argument('--dashboard', action='store_true', help='Show measurement dashboard')
    parser.add_argument('--kjs', action='store_true', help='Record a Key Judgment')
    parser.add_argument('--verify', action='store_true', help='Verify a pending Key Judgment')
    parser.add_argument('--calibrate', action='store_true', help='Show calibration curve')
    parser.add_argument('--date', help='Date to measure (default: today)')
    args = parser.parse_args()

    if args.dashboard:
        show_dashboard()
        return

    if args.kjs:
        record_kj()
        return

    if args.verify:
        verify_kj()
        return

    if args.calibrate:
        show_calibration()
        return

    # Full measurement run
    date_str = args.date or datetime.date.today().isoformat()
    print(f"\n📊 Briefometer — Measuring {date_str}")

    # Axis 1: Visual quality
    print("\n  Axis 1: Visual Quality...")
    visual = score_visual_quality(date_str)
    v_total = visual["overall"]["total"]
    print(f"  → {v_total}/150")
    for t in THEATRES:
        t_scores = visual["theatres"].get(t, {})
        print(f"    {t:<16} photo={t_scores.get('photo',0):>2}  map={t_scores.get('map',0):>2}  info={t_scores.get('infographic',0):>2}")

    # Axis 2: Content quality
    print("\n  Axis 2: Content Quality...")
    content = score_content_quality()
    c_total = content["overall"]["total"]
    print(f"  → {c_total}/150")
    for t in THEATRES:
        t_scores = content["theatres"].get(t, {})
        print(f"    {t:<16} depth={t_scores.get('depth',0):>2}  struct={t_scores.get('structure',0):>2}  source={t_scores.get('sourcing',0):>2}  est={t_scores.get('estimate',0):>2}  div={t_scores.get('diversity',0):>2}")

    # Axis 3: PDF quality
    print("\n  Axis 3: PDF Quality...")
    pdf_score = score_pdf_quality(date_str)
    print(f"  → {pdf_score}/25")

    # Axis 4: Predictive (if available)
    kj_data = load_kjs()
    brier = kj_data.get("mean_brier")
    if brier:
        print(f"\n  Axis 4: Predictive (Brier): {brier}")
    else:
        print(f"\n  Axis 4: Predictive — No verified KJs yet (run --kjs to start tracking)")

    # Save measurement
    save_measurement(date_str, v_total, c_total, pdf_score, brier)

    composite = v_total + c_total + pdf_score
    print(f"\n  {'─' * 50}")
    print(f"  COMPOSITE SCORE: {composite}/325")
    print(f"  Saved to measurement_log.json")

    try:
        show_dashboard()
    except:
        pass


if __name__ == "__main__":
    main()
