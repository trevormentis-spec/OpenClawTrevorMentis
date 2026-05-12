#!/usr/bin/env python3
"""Generate fresh theatre assessment markdowns using DeepSeek V4 Pro with retrieval-conditioned prompting.

Sources raw intelligence emails from Gmail (label: Intelligence) and produces
TREVOR's own structured assessments conditioned on prior memory, narrative
continuity, calibration feedback, and adaptation flags.
"""
import os, sys, json, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from deepseek_client import DeepSeekClient
from trevor_config import WORKSPACE, THEATRES
from trevor_log import get_logger
from trevor_memory import MemoryStore

sys.path.insert(0, str(SKILL_ROOT / 'scripts'))
from _fetch_intel_emails import fetch_emails

log = get_logger("generate_assessments")
ASSESS_DIR = SKILL_ROOT / 'assessments'


def load_previous_assessment(theatre_key):
    """Extract BLUF and Key Judgments from the previous edition."""
    path = ASSESS_DIR / f"{theatre_key}.md"
    if not path.exists():
        return {"bluf": "", "key_judgments": ""}
    
    content = path.read_text()
    lines = content.split('\n')
    bluf = []
    kj = []
    in_bluf = False
    in_kj = False
    
    for line in lines:
        if 'Bottom Line Up Front' in line:
            in_bluf = True
            continue
        if 'Key Judgments' in line:
            in_bluf = False
            in_kj = True
            continue
        if in_bluf and line.strip() and not line.startswith('#'):
            bluf.append(line)
        if in_kj and line.strip() and not line.startswith('#'):
            kj.append(line)
        if in_kj and line.startswith('##') and 'Key Judgments' not in line:
            break
    
    return {
        "bluf": '\n'.join(bluf[:10])[:2000],
        "key_judgments": '\n'.join(kj[:10])[:2000],
    }


def load_kalshi_prices():
    """Get latest Kalshi scan data."""
    exports_dir = WORKSPACE / 'exports'
    scans = sorted(exports_dir.glob('kalshi-scan-*.md'))
    if scans:
        return scans[-1].read_text()[:4000]
    return ""


def format_source_text(emails):
    """Format raw intel emails into source text for the prompt."""
    if not emails:
        return "No new intelligence reports for this theatre in the current cycle."
    
    parts = []
    for e in emails:
        parts.append(f"=== SOURCE: {e['source']} ===")
        parts.append(f"Subject: {e['subject']}")
        parts.append(f"Date: {e['date']}")
        parts.append(e['body'][:5000])
        parts.append("")
    
    return '\n'.join(parts)


def build_prompt(theatre_key, theatre_title, prev, source_text, kalshi_data, memory_context=None):
    """Build prompt conditioned on retrieved memory, calibration, and adaptation state."""
    mem_context = memory_context or {}
    mem_bluf = (mem_context.get("prior_narrative") or "")
    mem_kjs = (mem_context.get("prior_kjs") or "")
    mem_unresolved = (mem_context.get("unresolved_questions") or "")
    mem_trade = (mem_context.get("prior_trade_theses") or "")
    mem_drift = (mem_context.get("narrative_drift") or "")
    has_memory = bool(mem_bluf.strip()) or bool(mem_kjs.strip())

    # Build adaptive continuity instruction
    if has_memory:
        continuity = (
            "--- NARRATIVE CONTINUITY (memory retrieval — active) ---\n"
            f"Prior BLUF (last edition): {mem_bluf[:1200]}\n"
            f"Prior Key Judgments: {mem_kjs[:1000]}\n"
            f"Unresolved questions carried forward: {mem_unresolved[:800]}\n"
            f"Narrative drift status: {mem_drift[:600]}\n"
            "\nSPECIFIC INSTRUCTION: The above is from TREVOR's own prior assessment.\n"
            "- If narratives CHANGED, identify what shifted and why.\n"
            "- If narratives are UNCHANGED, note persistence and require fresh supporting evidence.\n"
            "- If any prior key judgment was wrong, explain how TREVOR's assessment evolved.\n"
            "- Carry forward unresolved questions and attempt to address them.\n"
            "- Do NOT repeat prior framing verbatim. Treat continuity as a constraint, not a template.\n"
        )
    else:
        continuity = (
            "--- NOTE ---\n"
            "No prior TREVOR assessment available for this theatre. First edition.\n"
            "Establish baseline narratives, identify key questions, set estimative benchmarks.\n"
        )

    # Calibration feedback
    cal_feedback = ""
    cal_file = ASSESS_DIR.parent / 'cron_tracking' / 'brier_scores.json'
    if cal_file.exists():
        try:
            cal = json.loads(cal_file.read_text())
            for band, stats in cal.get("by_band", {}).items():
                if stats.get("avg_brier", 0) > 0.25:
                    cal_feedback += (
                        f"[Calibration] '{band}' Brier {stats['avg_brier']:.2f} — "
                        f"use wider probability ranges for this band.\n"
                    )
        except Exception:
            pass

    # Check adaptation flag
    adaptation_flag = os.environ.get("TREVOR_ADAPTATION_FLAG", "")
    adaptation_note = ""
    if adaptation_flag and "stale" in adaptation_flag.lower() and theatre_key in adaptation_flag.lower():
        adaptation_note = (
            "\n*** ADAPTATION FLAG ACTIVE ***\n"
            "Fresh framing required — prior narrative is stale. Do NOT repeat previous structure.\n"
        )
        continuity += adaptation_note

    # Build prompt sections
    prompt = (
        "You are TREVOR — Threat Research and Evaluation Virtual Operations Resource — "
        "a senior intelligence analysis system.\n\n"
        f"You are producing YOUR OWN strategic assessment for \"{theatre_title}\".\n"
        "This is TREVOR's analysis, not a summary of any other source.\n\n"
        f"DATE: {datetime.date.today().isoformat()}\n\n"
        "--- INTELLIGENCE SOURCE MATERIAL ---\n"
        f"{source_text}\n\n"
        f"{continuity}\n"
        f"{cal_feedback}\n"
        "--- PREDICTION MARKET DATA ---\n"
        f"{kalshi_data[:2000]}\n\n"
        "Apply structured analytic techniques:\n"
        "- ACH: Identify 2-3 alternative explanations\n"
        "- Source Credibility Weighting: Rate each source (1-5)\n"
        "- Indicator Validation: Track previous indicators\n"
        "- Calibrated Probability: Sherman Kent ranges\n"
        "- Narrative Continuity: Connect to prior assessments\n\n"
        "PRODUCE A COMPLETE ASSESSMENT:\n\n"
        "# [Headline — lead story for this theatre today]\n\n"
        f"**Date:** {datetime.date.today().isoformat()}\n"
        "**Classification:** TREVOR — OPEN SOURCE STRATEGIC ASSESSMENT\n"
        f"**Region:** {theatre_title}\n\n"
        "**Bottom Line Up Front** (3-5 paragraphs, synthesized judgment)\n\n"
        "## Key Judgments (numbered, calibrated confidence, e.g., moderate-to-high [60-80%])\n\n"
        "## Discussion (detailed analysis with source citations <super>1</super>)\n\n"
        "## Alternative Analysis (would change TREVOR's mind)\n\n"
        "## Predictive Judgments (30-60-90 day projections with probabilities)\n\n"
        "## Indicators to Watch (specific, falsifiable)\n\n"
        "## Implications\n\n"
        "## Source Assessment (quality and coverage of intelligence received)\n\n"
        "## Continuity Check (reference prior narrative: what changed, what was carried forward)\n\n"
        "## Sources\n\n"
        "Write in TREVOR's voice: direct, calibrated, evidence-driven, professional tradecraft.\n"
    )

    log.info(f"Prompt built for {theatre_key}",
             has_memory=has_memory,
             cal_feedback=bool(cal_feedback),
             adaptation_active=bool(adaptation_note),
             prompt_chars=len(prompt))

    return prompt


def retrieve_memory(theatre_key):
    """Retrieve prior narratives, KJs, unresolved questions, and trade theses from FTS5."""
    context = {
        "prior_narrative": "",
        "prior_kjs": "",
        "unresolved_questions": "",
        "prior_trade_theses": "",
        "narrative_drift": "",
    }
    try:
        mem = MemoryStore()
        prior_narr = mem.get_previous_narrative(theatre_key, days=30) or ""
        prior_kjs_raw = mem.get_prior_judgment(theatre_key)
        if prior_kjs_raw:
            context["prior_kjs"] = json.dumps(
                [j.get("content", "")[:200] for j in prior_kjs_raw]
            )
        unresolved_raw = mem.search("unresolved", collection="narrative",
                                     region=theatre_key, top_k=3)
        if unresolved_raw:
            context["unresolved_questions"] = json.dumps(
                [r.get("content", "")[:200] for r in unresolved_raw]
            )
        trade_raw = mem.search("trade thesis", collection="narrative",
                                region=theatre_key, top_k=3)
        if trade_raw:
            context["prior_trade_theses"] = json.dumps(
                [r.get("content", "")[:200] for r in trade_raw]
            )
        # Check narrative drift
        drift_file = SKILL_ROOT / 'cron_tracking' / 'story_delta.json'
        if drift_file.exists():
            try:
                dd = json.loads(drift_file.read_text())
                for d in dd.get("diffs", []):
                    if d.get("region") == theatre_key and d.get("status") == "stale":
                        context["narrative_drift"] = (
                            f"⚠ Stale: same lead narrative for {d.get('days_same', '?')} days. "
                            "Require fresh framing."
                        )
            except Exception:
                pass
        context["prior_narrative"] = prior_narr
        mem.close()
    except Exception as e:
        log.warning(f"Memory retrieval failed for {theatre_key}: {e}")
    return context


def generate_assessments(source_data, kalshi_data):
    """Generate all theatre assessments from raw source material with retrieval conditioning."""
    system = (
        "You are TREVOR, a senior intelligence analysis system. "
        "Produce your own structured assessment from source material provided. "
        "Apply ACH, source credibility weighting, Sherman Kent calibrated probabilities. "
        "If prior memory is provided, maintain continuity and avoid repeating framing."
    )

    def generate_one(theatre):
        key = theatre['key']
        print(f"Generating {key}...", flush=True)

        memory_context = retrieve_memory(key)
        prev = load_previous_assessment(key)
        emails = source_data.get(key, [])
        source_text = format_source_text(emails)
        prompt = build_prompt(key, theatre['title'], prev, source_text, kalshi_data, memory_context)

        client = DeepSeekClient(timeout=180, tier=3)  # Tier 3 — strategic cognition
        try:
            content = client.chat(prompt, system=system)
            out_path = ASSESS_DIR / f"{key}.md"
            out_path.write_text(content if content else "")
            if content:
                print(f"  OK: {len(content)} chars -> {out_path.name}", flush=True)
            else:
                print(f"  EMPTY response for {key}", flush=True)
            return {
                "theatre": key,
                "status": "ok" if content else "empty",
                "chars": len(content or ""),
                "sources": len(emails),
                "memory_conditioned": bool(memory_context["prior_narrative"]),
                "calibration_active": False,
            }
        except Exception as e:
            print(f"  FAIL: {key} — {e}", flush=True)
            return {"theatre": key, "status": "failed", "error": str(e)}

    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(generate_one, t): t for t in THEATRES}
        for future in as_completed(futures):
            results.append(future.result())

    # Summarize retrieval conditioning impact
    conditioned = [r for r in results if r.get("memory_conditioned")]
    print(f"\nRetrieval conditioning: {len(conditioned)}/{len(results)} theatres had prior memory", flush=True)
    for r in conditioned:
        print(f"  {r['theatre']}: conditioned by {r['sources']} source emails, {r['chars']} chars", flush=True)

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate assessments from raw Gmail intel")
    parser.add_argument("--force-fetch", action="store_false", help="Force re-fetch of emails")
    args = parser.parse_args()

    print("=== Fetching raw intelligence from Gmail (label: Intelligence) ===", flush=True)
    source_data = fetch_emails(force_fetch=not args.force_fetch, max_emails=30)

    total_emails = sum(len(v) for v in source_data.values())
    if total_emails == 0:
        print("WARNING: No intel emails found. Using cached/fallback data.", flush=True)

    print(f"Total source emails: {total_emails}", flush=True)
    for theatre, emails in sorted(source_data.items()):
        if emails:
            print(f"  {theatre}: {len(emails)} emails", flush=True)

    print("\nLoading Kalshi data...", flush=True)
    kalshi_data = load_kalshi_prices()
    print(f"Kalshi scan: {len(kalshi_data)} chars", flush=True)

    results = generate_assessments(source_data, kalshi_data)

    successes = [r for r in results if r['status'] == 'ok']
    failures = [r for r in results if r['status'] == 'failed']

    print(f"\n=== Results ===", flush=True)
    print(f"Success: {len(successes)}/{len(results)}", flush=True)
    for r in successes:
        print(f"  {r['theatre']}: {r['chars']} chars ({r['sources']} source emails, memory={r.get('memory_conditioned', False)})", flush=True)
    for r in failures:
        print(f"  {r['theatre']}: ERROR - {r.get('error', '?')}", flush=True)

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
