#!/usr/bin/env python3
"""Generate fresh theatre assessment markdowns using DeepSeek V4 Pro.

Sources raw intelligence emails from Gmail (label: Intelligence) and produces
TREVOR's own structured assessments — not a rewrite of ISW/CTP analysis.

Pipeline:
  1. Fetch raw intel emails from Gmail by label
  2. Route to correct theatre (Europe, Middle East, etc.)
  3. Feed raw source text into DeepSeek V4 Pro with TREVOR's analytic method
  4. Write structured markdown assessments with calibrated judgments
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
    """Build the DeepSeek V4 Pro prompt with memory-conditioned retrieval."""
    
    # Memory context: prior narratives, KJs, trade theses, unresolved questions
    mem_bluf = memory_context.get("prior_narrative", "") if memory_context else ""
    mem_kjs = memory_context.get("prior_kjs", "") if memory_context else ""
    mem_unresolved = memory_context.get("unresolved_questions", "") if memory_context else ""
    mem_trade = memory_context.get("prior_trade_theses", "") if memory_context else ""
    mem_drift = memory_context.get("narrative_drift", "") if memory_context else ""
    
    prompt = f"""You are TREVOR — Threat Research and Evaluation Virtual Operations Resource — a senior intelligence analysis system.

You are producing YOUR OWN strategic assessment for the "{theatre_title}" theatre.
This is TREVOR's analysis, not a summary of any other source.

DATE: {datetime.date.today().isoformat()}

--- INTELLIGENCE SOURCE MATERIAL (GMAIL "INTELLIGENCE" LABEL) ---
The following are raw intelligence emails that have been collected for this theatre.
Assess them critically — weigh source credibility, look for corroboration and contradiction.

{source_text}

--- NARRATIVE CONTINUITY (memory retrieval) ---
Prior BLUF: {mem_bluf[:1000]}
Prior Key Judgments: {mem_kjs[:1000]}
Unresolved questions from prior runs: {mem_unresolved[:800]}
Prior trade theses: {mem_trade[:800]}

--- NARRATIVE DRIFT DETECTION ---
{mem_drift[:800]}

Apply structured analytic techniques:
- **Narrative Continuity:** Have narratives changed since the last assessment? If not, require fresh sourcing.
- **ACH (Analysis of Competing Hypotheses):** Identify 2-3 alternative explanations for the key development
- **Source Credibility Weighting:** Rate each source (1-5) for reliability and relevance
- **Indicator Validation:** Track whether previous indicators were confirmed or refuted
- **Calibrated Probability:** Use Sherman Kent ranges (e.g., "moderate confidence [55-75%]")

--- PREDICTION MARKET DATA ---
{kalshi_data[:2000]}

PRODUCE A COMPLETE ASSESSMENT WITH THESE SECTIONS:

# [Headline — TREVOR's own lead story for this theatre today]

**Date:** {datetime.date.today().isoformat()}
**Classification:** TREVOR — OPEN SOURCE STRATEGIC ASSESSMENT
**Region:** {theatre_title}

**Bottom Line Up Front** (3-5 paragraphs — TREVOR's synthesized judgment from the raw source material. What changed? What's the key takeaway? What does TREVOR think?)

## Key Judgments (numbered with calibrated confidence, e.g., "moderate-to-high confidence [60-80%]")

## Discussion (detailed analysis citing specific source material — <super>1</super>, <super>2</super> markers)

## Alternative Analysis (counter-thesis — what would change TREVOR's mind)

## Predictive Judgments (30-60-90 day projections with probability ranges)

## Indicators to Watch (specific, falsifiable events)

## Implications

## Source Assessment (rate the quality and coverage of the raw intelligence received this cycle)

## Sources (numbered with published-URL attribution where available)

Write in TREVOR's voice: direct, calibrated, evidence-driven, professional intelligence tradecraft.
"""
    return prompt


def generate_assessments(source_data, kalshi_data):
    """Generate all theatre assessments from raw source material."""
    system = "You are TREVOR, a senior intelligence analysis system. Produce YOUR OWN structured assessment from the raw source material provided. Apply ACH, source credibility weighting, and Sherman Kent calibrated probabilities. Never say you cannot access external information — you already have the source material in the prompt."
    
    def generate_one(theatre):
        key = theatre['key']
        print(f"Generating {key}...", flush=True)
        
        # Retrieve memory context for this theatre
        try:
            mem = MemoryStore()
            prior_narr = mem.get_previous_narrative(key, days=30) or ""
            prior_kjs_raw = mem.get_prior_judgment(key)
            prior_kjs = json.dumps([j.get("content","")[:200] for j in prior_kjs_raw]) if prior_kjs_raw else ""
            
            # Search for unresolved questions and trade theses
            unresolved_raw = mem.search("unresolved question", collection="narrative", region=key, top_k=3)
            unresolved = json.dumps([r.get("content","")[:200] for r in unresolved_raw]) if unresolved_raw else ""
            
            trade_raw = mem.search("trade thesis", collection="trade_thesis", region=key, top_k=3)
            trade = json.dumps([r.get("content","")[:200] for r in trade_raw]) if trade_raw else ""
            
            # Check narrative drift from story_tracker
            drift = ""
            drift_file = SKILL_ROOT / 'cron_tracking' / 'story_delta.json'
            if drift_file.exists():
                try:
                    dd = json.loads(drift_file.read_text())
                    for d in dd.get("diffs", []):
                        if d.get("region") == key and d.get("status") == "stale":
                            drift = f"⚠ Stale: same lead narrative for {d.get('days_same', '?')} days. Require fresh framing."
                except: pass
            
            mem.close()
        except Exception:
            prior_narr = ""
            prior_kjs = ""
            unresolved = ""
            trade = ""
            drift = ""
        
        memory_context = {
            "prior_narrative": prior_narr,
            "prior_kjs": prior_kjs,
            "unresolved_questions": unresolved,
            "prior_trade_theses": trade,
            "narrative_drift": drift,
        }
        
        prev = load_previous_assessment(key)
        emails = source_data.get(key, [])
        source_text = format_source_text(emails)
        prompt = build_prompt(key, theatre['title'], prev, source_text, kalshi_data, memory_context)
        
        client = DeepSeekClient(timeout=120)
        try:
            content = client.chat(prompt, system=system)
            out_path = ASSESS_DIR / f"{theatre['key']}.md"
            with open(out_path, 'w') as f:
                f.write(content)
            print(f"  OK: {len(content)} chars -> {out_path.name}", flush=True)
            return {"theatre": theatre['key'], "status": "ok", "chars": len(content), "sources": len(emails)}
        except Exception as e:
            print(f"  FAIL: {theatre['key']} — {e}", flush=True)
            return {"theatre": theatre['key'], "status": "failed", "error": str(e)}
    
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(generate_one, t) for t in THEATRES]
        for future in as_completed(futures):
            results.append(future.result())
    
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
        print(f"  {r['theatre']}: {r['chars']} chars ({r['sources']} source emails)", flush=True)
    for r in failures:
        print(f"  {r['theatre']}: ERROR - {r.get('error','?')}", flush=True)
    
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
