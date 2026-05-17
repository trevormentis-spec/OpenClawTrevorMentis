#!/usr/bin/env python3
"""Analyst worker for the Daily Intel Brief.

Reads WORKING_DIR/raw/incidents.json, calls the DeepSeek Direct API
(model: deepseek/deepseek-v4-pro per ORCHESTRATION.md escalation tier)
once per region plus one executive-summary call plus one red-team call,
and writes WORKING_DIR/analysis/{region}.json + exec_summary.json +
red_team.md.

Implements agents/analyst.md.

Usage:

    python3 scripts/analyze.py --working-dir <wd> \\
        --prompts skills/daily-intel-brief/references/deepseek-prompts.md \\
        --regions skills/daily-intel-brief/references/regions.json \\
        [--model deepseek/deepseek-v4-pro] [--mock]

`--mock` returns canned analytical JSON without calling the API, so the
rest of the pipeline can be exercised when DEEPSEEK_API_KEY is unset.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any

DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com")
DEEPSEEK_PATH = "/v1/chat/completions"

OPENROUTER_BASE = "https://openrouter.ai/api"
OPENROUTER_PATH = "/v1/chat/completions"

REGIONS_ORDER = [
    "europe", "asia", "middle_east",
    "north_america", "south_central_america", "global_finance",
]

REGION_LABEL = {
    "europe": "Europe",
    "asia": "Asia",
    "middle_east": "Middle East",
    "north_america": "North America",
    "south_central_america": "South & Central America (incl. Caribbean)",
    "global_finance": "Global Finance",
}

REGION_SHORT = {
    "europe": "EU", "asia": "AS", "middle_east": "ME",
    "north_america": "NA", "south_central_america": "SC", "global_finance": "FIN",
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[analyze {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def split_prompts(prompts_md: str) -> dict[str, str]:
    """Pull the four named prompt blocks out of references/deepseek-prompts.md.

    The file uses '## <name>' section headers with fenced code blocks.
    We grab the first fenced block under each section.
    """
    sections: dict[str, str] = {}
    headers = list(re.finditer(r"^## (.+)$", prompts_md, flags=re.MULTILINE))
    for i, h in enumerate(headers):
        name = h.group(1).strip()
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(prompts_md)
        block = prompts_md[start:end]
        m = re.search(r"```(?:[a-zA-Z0-9]+)?\n(.*?)```", block, flags=re.DOTALL)
        if m:
            sections[name] = m.group(1).strip()
    return sections


def call_deepseek(model: str, system: str, user: str,
                  temperature: float = 0.3, max_tokens: int = 8192,
                  json_mode: bool = True,
                  provider: str = "deepseek") -> str:
    """Call DeepSeek/OpenRouter via curl subprocess (avoids Python SSL hangs)."""
    import subprocess, tempfile, json as _json, os as _os
    
    # Get API key
    if provider == "openrouter":
        api_key = _os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        base_url = "https://openrouter.ai/api"
        api_model = model
        extra_headers = [
            "-H", "HTTP-Referer: https://github.com/trevormentis-spec",
            "-H", "X-Title: TREVOR Intel Brief",
        ]
    else:
        api_key = _os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set")
        base_url = "https://api.deepseek.com"
        api_model = model.split("/", 1)[-1] if "/" in model else model
        extra_headers = []
    
    # Build payload dict
    payload = {
        "model": api_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    # Write payload to temp file (avoids shell escaping issues)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    tmp.write(_json.dumps(payload))
    tmp.close()
    
    try:
        # Build curl command
        cmd = [
            "curl", "-s", "-w", "\n%{http_code}",
            "-X", "POST", f"{base_url}/v1/chat/completions",
            "-H", "Content-Type: application/json",
            "-H", "Authorization: Bearer " + api_key,
        ] + extra_headers + [
            "--data-binary", "@" + tmp.name,
            "--connect-timeout", "60",
            "--max-time", "300",
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=310)
        
        stdout = result.stdout
        # Split on newline - last line is HTTP status code
        idx = stdout.rfind("\n")
        if idx >= 0:
            http_code = stdout[idx+1:].strip()
            body = stdout[:idx]
        else:
            http_code = "000"
            body = stdout
        
        if not http_code.startswith("2"):
            err = result.stderr[:300] if result.stderr else body[:300]
            raise RuntimeError(f"HTTP {http_code}: {err}")
        
        response_data = _json.loads(body)
        return response_data["choices"][0]["message"]["content"]
    except subprocess.TimeoutExpired:
        raise RuntimeError("curl timed out after 310s")
    except Exception as e:
        if "HTTP" in str(e):
            raise
        raise RuntimeError(f"API call failed: {e}")
    finally:
        try:
            _os.unlink(tmp.name)
        except:
            pass
def build_collection_quality(region_snake: str, incidents: list[dict],
                               collection_state: dict | None = None,
                               behavioral_state: dict | None = None) -> str:
    """Build collection quality + behavioral constraints for a region.
    
    If behavioral_state is provided, it emits HARD constraints on what
    confidence bands the model may use, maximum percentages, and mandatory
    caveats. This is the behavioral adaptation bridge — it changes what
    the model can output, not just what it's told.
    """
    region_incidents = [i for i in incidents if i.get("region") == region_snake]
    inc_count = len(region_incidents)
    
    # Count unique sources
    all_sources = set()
    for inc in region_incidents:
        for s in inc.get("sources", []):
            name = s.get("name", "") if isinstance(s, dict) else str(s)
            all_sources.add(name)
    source_count = len(all_sources)
    
    # Get region cap from collection state
    region_cap = 8
    collection_gaps = []
    if collection_state:
        caps = collection_state.get("per_region_cap", {})
        region_cap = caps.get(region_snake, 8)
        gaps = collection_state.get("identified_gaps", [])
        for g in gaps:
            if region_snake in g:
                collection_gaps.append(g)
    
    # --- BEHAVIORAL ADAPTATION: Hard constraints from behavioral state ---
    # These override the descriptive guidance below
    constraints = {}
    if behavioral_state:
        constraints = behavioral_state.get("per_region_constraints", {}).get(region_snake, {})
    
    # Assess collection quality (descriptive)
    if inc_count == 0:
        coverage = "NONE"
        diversity = "N/A (no incidents)"
        quality = "CRITICAL GAP"
        descriptive_guidance = "No incidents collected for this region. You CANNOT produce a meaningful assessment. State the gap explicitly."
    elif inc_count <= 2 or source_count <= 1:
        coverage = "THIN"
        diversity = "LOW" if source_count <= 1 else "MODERATE"
        quality = "LOW"
        descriptive_guidance = "Thin collection coverage. Collection limitation noted."
    elif inc_count <= 5 or source_count <= 2:
        coverage = "MODERATE"
        diversity = "MODERATE"
        quality = "MODERATE"
        descriptive_guidance = "Moderate collection coverage."
    else:
        coverage = "FULL"
        diversity = "HIGH" if source_count >= 4 else "MODERATE"
        quality = "HIGH"
        descriptive_guidance = "Good collection coverage with diverse sources."
    
    lines = [
        f"Region: {REGION_LABEL.get(region_snake, region_snake)}",
        f"Incidents collected: {inc_count}",
        f"Unique sources: {source_count}",
        f"Collection intensity cap: {region_cap}",
        f"Coverage: {coverage}",
        f"Source diversity: {diversity}",
        f"Collection quality: {quality}",
        f"",
        f"Descriptive guidance: {descriptive_guidance}",
    ]
    
    # Behavioral adaptation: emit HARD CONSTRAINTS if available
    # These change what the model is ALLOWED to output
    if constraints:
        available = constraints.get("available_bands", [])
        max_pct = constraints.get("max_confidence_pct", 95)
        max_ss = constraints.get("max_single_source_pct", 70)
        aggression = constraints.get("forecasting_aggression", "standard")
        caveats = constraints.get("mandatory_caveats", [])
        
        lines.append(f"")
        lines.append(f"<<< HARD CONSTRAINTS — MUST FOLLOW >>>")
        lines.append(f"Available confidence bands (ONLY these): {', '.join(available)}")
        lines.append(f"Max confidence percentage: {max_pct}%")
        lines.append(f"Max single-source percentage: {max_ss}%")
        lines.append(f"Forecasting aggression: {aggression}")
        if caveats:
            lines.append(f"Mandatory caveats (must include):")
            for c in caveats:
                lines.append(f"  - {c}")
        lines.append("<<< END HARD CONSTRAINTS >>>")
    
    if collection_gaps:
        lines.append(f"Collection gaps: {'; '.join(collection_gaps)}")
    
    return "\n".join(lines)


def regional_prompt(template: str, region_snake: str, incidents: list[dict],
                    iw_board_md: str, date_utc: str,
                    collection_state: dict | None = None,
                    behavioral_state: dict | None = None,
                    prediction_market_data: str = "No prediction market data available.",
                    standing_assessment: str = "No previous standing assessment available.") -> tuple[str, str]:
    region_label = REGION_LABEL[region_snake]
    short = REGION_SHORT[region_snake]
    incidents_for_region = [i for i in incidents if i.get("region") == region_snake]
    coll_quality = build_collection_quality(region_snake, incidents, collection_state, behavioral_state)
    user = (template
            .replace("{region_label}", region_label)
            .replace("{region_snake}", region_snake)
            .replace("{region_short}", short)
            .replace("{date_utc}", date_utc)
            .replace("{incidents_json_for_region}",
                     json.dumps(incidents_for_region, indent=2))
            .replace("{iw_board_markdown_or_none}",
                     iw_board_md or "No standing I&W board for this region.")
            .replace("{prediction_market_data}", prediction_market_data)
            .replace("{standing_assessment}", standing_assessment)
            .replace("{collection_quality_markdown}", coll_quality))
    # the system prompt is shared (defined in references/deepseek-prompts.md)
    return user, short


def exec_prompt(template: str, regional_payloads: dict[str, dict],
                date_utc: str, collection_state: dict | None = None,
                behavioral_state: dict | None = None) -> str:
    user = template.replace("{date_utc}", date_utc)
    
    # Build collection quality summary from either behavioral state or raw collection state
    if behavioral_state:
        constraints = behavioral_state.get("per_region_constraints", {})
        quality_lines = ["PER-REGION CONFIDENCE CONSTRAINTS (hard limits):"]
        for r, c in sorted(constraints.items()):
            label = REGION_LABEL.get(r, r)
            bands = ", ".join(c.get("available_bands", []))
            max_pct = c.get("max_confidence_pct", 95)
            aggression = c.get("forecasting_aggression", "standard")
            quality_lines.append(f"  {label}: bands=[{bands}], max={max_pct}%, aggression={aggression}")
            for caveat in c.get("mandatory_caveats", []):
                quality_lines.append(f"    CAVEAT: {caveat}")
        coll_summary = "\n".join(quality_lines)
        user = template.replace("{collection_quality_summary}", coll_summary)
    elif collection_state:
        caps = collection_state.get("per_region_cap", {})
        quality_lines = ["COLLECTION QUALITY BY REGION:"]
        for r, cap in sorted(caps.items()):
            label = REGION_LABEL.get(r, r)
            quality_lines.append(f"  {label}: intensity_cap={cap}")
        coll_summary = "\n".join(quality_lines)
        user = template.replace("{collection_quality_summary}", coll_summary)
    else:
        # Remove placeholder if no state
        user = template.replace("{collection_quality_summary}", "")
    
    for snake, payload in regional_payloads.items():
        user = user.replace(
            "{" + snake + "_json}",
            json.dumps(payload, indent=2),
        )
    return user


def red_team_prompt(template: str, region_label: str, kj: dict,
                    narrative: str, date_utc: str) -> str:
    return (template
            .replace("{date_utc}", date_utc)
            .replace("{region_label}", region_label)
            .replace("{kj_id}", kj.get("id", "<unknown>"))
            .replace("{kj_statement}", kj.get("statement", ""))
            .replace("{kj_band}", kj.get("sherman_kent_band", ""))
            .replace("{kj_pct}", str(kj.get("prediction_pct", "?")))
            .replace("{kj_evidence_ids}", ", ".join(kj.get("evidence_incident_ids", [])))
            .replace("{kj_single_source}", "yes" if kj.get("single_source_basis") else "no")
            .replace("{regional_narrative}", narrative or ""))


def find_iw_board(repo_root: pathlib.Path, region_snake: str) -> str:
    candidate = repo_root / "analyst" / "iw-boards" / f"{region_snake}.md"
    if candidate.exists():
        return candidate.read_text()
    return ""


def mock_regional(region_snake: str, incidents: list[dict], date_utc: str) -> dict:
    short = REGION_SHORT[region_snake]
    incs = [i for i in incidents if i.get("region") == region_snake]
    ev_ids = [i["id"] for i in incs[:2]] or [f"i-mock-0000"]
    bands = [
        ("highly likely", 78),
        ("likely", 60),
        ("even chance", 50),
        ("unlikely", 30),
    ]
    band_pick = bands[hash(region_snake) % len(bands)]
    return {
        "region": region_snake,
        "as_of_utc": f"{date_utc}T06:00:00Z",
        "incident_count": len(incs),
        "narrative": (
            f"Mock narrative for {REGION_LABEL[region_snake]}. "
            "Two paragraphs would normally synthesise the day's incidents, "
            "cite the higher-rated sources, and connect the development to "
            "the principal's standing equities. This stub exists so the "
            "downstream pipeline can render."
        ),
        "key_judgments": [
            {
                "id": f"KJ-{short}-1",
                "statement": (
                    f"Mock judgment 1 for {REGION_LABEL[region_snake]}: "
                    "an observable forward-looking event would be stated here."),
                "sherman_kent_band": band_pick[0],
                "prediction_pct": band_pick[1],
                "horizon_days": 7,
                "evidence_incident_ids": ev_ids,
                "single_source_basis": True if band_pick[1] <= 70 else False,
                "confidence_in_judgment": "moderate",
                "what_would_change_it": [
                    "softener: contradicting wire from an A-rated source",
                    "tightener: corroborating event in the next 24-48h",
                ],
            },
            {
                "id": f"KJ-{short}-2",
                "statement": (
                    f"Mock judgment 2 for {REGION_LABEL[region_snake]}: "
                    "a second forward-looking call, distinct from #1."),
                "sherman_kent_band": "even chance",
                "prediction_pct": 50,
                "horizon_days": 7,
                "evidence_incident_ids": ev_ids,
                "single_source_basis": False,
                "confidence_in_judgment": "low",
                "what_would_change_it": [
                    "softener: a credible de-escalation signal from a primary",
                    "tightener: a second confirming incident",
                ],
            },
        ],
        "scenarios": None,
        "red_team_target_kj": f"KJ-{short}-1",
    }


def mock_exec(regional: dict[str, dict], date_utc: str) -> dict:
    five = []
    for snake in REGIONS_ORDER:
        if snake not in regional:
            continue
        kjs = regional[snake].get("key_judgments") or []
        if not kjs:
            continue
        kj = kjs[0]
        five.append({
            "id": f"EXEC-{len(five)+1}",
            "statement": kj["statement"],
            "sherman_kent_band": kj["sherman_kent_band"],
            "prediction_pct": kj["prediction_pct"],
            "horizon_days": kj["horizon_days"],
            "drawn_from_region": snake,
            "drawn_from_kj_id": kj["id"],
        })
        if len(five) >= 5:
            break
    return {
        "as_of_utc": f"{date_utc}T06:00:00Z",
        "bluf": (
            "Mock BLUF: a calibrated one-sentence headline judgment "
            "covering the most decision-relevant overnight development."),
        "context_paragraph": (
            "Mock context paragraph. Two to three sentences naming what "
            "is new in the last 24 hours, why it matters today, and what "
            "the principal should watch for."),
        "five_judgments": five,
    }


def parse_json_strict(text: str) -> dict:
    """DeepSeek json_mode usually returns clean JSON; be tolerant anyway."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--regions", required=True)
    parser.add_argument("--model", default="deepseek/deepseek-v4-flash")
    parser.add_argument("--tier2-model", default="deepseek/deepseek-v4-flash", help="Tier-2 fast model for regional analysis (default: DeepSeek V4 Flash)")
    parser.add_argument("--provider", choices=["deepseek", "openrouter"], default="deepseek",
                        help="API provider to route through (default: deepseek)")
    parser.add_argument("--recall", default="",
                        help="path to brain-recall.md with prior memory context")
    parser.add_argument("--procedural", default="",
                        help="path to procedural-memory.md with learned procedures")
    parser.add_argument("--collection-state", default="",
                        help="path to collection-state.json for confidence conditioning")
    parser.add_argument("--calibration", default="",
                        help="path to calibration-tracking.json for calibration feedback")
    parser.add_argument("--behavioral-state", default="",
                        help="path to behavioral-state.json for hard behavioral constraints (overrides individual --collection-state and --calibration)")
    parser.add_argument("--self-assessment", default="",
                        help="path to self-assessment-injection.md for system health feedback")
    parser.add_argument("--scope-topic", default="Mexico daily intelligence brief",
                        help="topic to validate against scope gate; default treats pipeline as Mexico-scoped")
    parser.add_argument("--mock", action="store_true",
                        help="return canned analysis without calling the API")
    args = parser.parse_args()

    # ── Scope gate — first check ──
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
        from analyst.scope_check import check_scope, build_decline, build_adjacency_preamble
        scope_result = check_scope(args.scope_topic)
        if scope_result["scope_status"] == "out_of_scope":
            log(f"SCOPE GATE: topic '{args.scope_topic}' is out_of_scope. Aborting.")
            log(f"Decline: {build_decline(args.scope_topic, scope_result)}")
            return 0  # non-fatal
        elif scope_result["scope_status"] == "adjacent":
            preamble = build_adjacency_preamble(args.scope_topic, scope_result)
            log(f"SCOPE GATE: topic '{args.scope_topic}' is adjacent (not direct).")
            log(f"Adjacency framing: {preamble[:200]}...")
            log("Proceeding with Mexico-scoped analysis using adjacent_brief.md template.")
        else:
            log(f"SCOPE GATE: topic '{args.scope_topic}' confirmed in_scope.")
    except ImportError:
        log("SCOPE GATE: analyst.scope_check not available — skipping scope validation.")
    except Exception as exc:
        log(f"SCOPE GATE: check failed ({exc}) — proceeding permissively.")

    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    repo_root = wd  # used for IW boards; if running in repo, override below
    # Heuristic: if invoked from repo, ORCHESTRATION.md exists at parents
    for cand in [wd, *wd.parents]:
        if (cand / "ORCHESTRATION.md").exists():
            repo_root = cand
            break

    incidents_path = wd / "raw" / "incidents.json"
    if not incidents_path.exists():
        log("FATAL: incidents.json missing; run collector first")
        return 2
    incidents_payload = load_json(incidents_path)
    incidents = incidents_payload.get("incidents", [])
    date_utc = incidents_payload.get("generated_at_utc", "")[:10] or \
               dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    prompts = split_prompts(pathlib.Path(args.prompts).read_text())
    system = prompts.get("System message (used for every regional + exec call)", "")

    # Step 0a — inject brain recall into system prompt (if available)
    if args.recall and os.path.exists(args.recall):
        recall_text = pathlib.Path(args.recall).read_text().strip()
        if recall_text:
            recall_block = (
                "\n\n### === MEMORY CONTEXT FROM PRIOR BRIEFS ===\n"
                "The following is retrieved from Trevor's memory store. "
                "Use it to maintain continuity with previous assessments — "
                "carry forward unresolved narratives, reference prior judgments "
                "where relevant, and avoid contradicting prior analysis without "
                "explicitly noting the change.\n\n"
                + recall_text +
                "\n\n=== END MEMORY CONTEXT ==="
            )
            system = system + recall_block
            log(f"injected brain recall ({len(recall_text)} chars) into system prompt")

    # Step 0d — initialize behavioral state container (must be before any usage)
    behavioral_state = None
    collection_state = None
    if args.behavioral_state and os.path.exists(args.behavioral_state):
        try:
            behavioral_state = json.loads(pathlib.Path(args.behavioral_state).read_text())
            log(f"loaded behavioral state — {len(behavioral_state.get('per_region_constraints', {}))} regions constrained")
        except Exception as exc:
            log(f"behavioral state load failed ({exc}) — falling back to individual state")

    if behavioral_state is None:
        if args.collection_state and os.path.exists(args.collection_state):
            try:
                collection_state = json.loads(pathlib.Path(args.collection_state).read_text())
                log(f"loaded collection state ({len(collection_state)} keys) for confidence conditioning")
            except Exception as exc:
                log(f"collection state load failed ({exc}) — confidence conditioning disabled")

    # Step 0e — inject calibration feedback into system prompt
    # If behavioral state is loaded, use its calibration directives (they are the compiled version)
    if behavioral_state:
        # Behavioral state already contains compiled calibration + collection + event directives
        cal_dirs = behavioral_state.get("calibration_directives", {})
        cal_parts = ["\n\n### === CALIBRATION FEEDBACK (from behavioral state) ==="]

        overall = cal_dirs.get("overall", {})
        total = overall.get("total_judgments", 0)
        if total > 0:
            cal_parts.append(
                f"\nOverall: {overall.get('correct', 0)}/{total} correct "
                f"({overall.get('accuracy_pct', 0)}%). Posture: {overall.get('posture', 'hold_bands')}."
            )

        # Concrete per-band downshift directives (from compile_calibration_directives.py)
        band_directives = cal_dirs.get("band_directives", [])
        if band_directives:
            cal_parts.append("\nBand-level adjustments (mandatory):")
            for bd in band_directives:
                cal_parts.append(
                    f"  • '{bd['band']}' is {int(bd['accuracy']*100)}% accurate over "
                    f"{bd['samples']} judgments → use '{bd['use_instead']}' instead."
                )

        if overall.get("unresolved", 0) > 10:
            cal_parts.append(
                f"\n⚠ {overall['unresolved']}/{total} judgments unresolved. "
                "High uncertainty environment — restrict top confidence bands."
            )

        if overall.get("overconfidence_regions"):
            cal_parts.append(
                f"\n⚠ Overconfidence detected in: "
                f"{', '.join(overall['overconfidence_regions'])}. "
                "Widen bands by one notch for these regions/themes."
            )

        cal_parts.append("\n\n=== END CALIBRATION FEEDBACK ===")
        cal_block = "\n".join(cal_parts)
        
        insert_point = system.find("Discipline:")
        if insert_point >= 0:
            system = system[:insert_point] + cal_block + "\n\n" + system[insert_point:]
            log(f"injected behavioral calibration feedback ({len(cal_block)} chars)")
        else:
            system = system + cal_block
            log(f"injected behavioral calibration feedback at end")
    elif args.calibration and os.path.exists(args.calibration):
        try:
            cal_data = json.loads(pathlib.Path(args.calibration).read_text())
            cal_parts = ["\n\n### === CALIBRATION FEEDBACK ==="]
            
            # Check for overconfidence flags
            flags = cal_data.get("overconfidence_flags", [])
            if flags:
                cal_parts.append("\nOverconfidence signals detected in recent assessments:")
                for f in flags:
                    cal_parts.append(
                        f"  • {f.get('region','?')}: {f.get('band','?')} at {f.get('pct','?')}% "
                        f"with limited sources ({f.get('sources','?')}) — "
                        f"{f.get('flag','widen bands')}"
                    )
                cal_parts.append(
                    "\nAction: Widen confidence bands by one level for the flagged regions. "
                    "Instead of 'highly likely', use 'likely'. Instead of 'likely', use 'even chance'. "
                    "Narrow bands require diverse, multi-source confirmation."
                )
            
            # Check per-band calibration
            bands = cal_data.get("by_confidence_band", {})
            for band_name, stats in bands.items():
                if stats.get("total", 0) >= 3 and stats.get("correct", 0) == 0:
                    cal_parts.append(
                        f"\n  ⚠ Band '{band_name}' has {stats['total']} judgments with zero confirmed correct. "
                        f"Avoid this band until calibration improves."
                    )
            
            # Running accuracy summary
            total = cal_data.get("total_judgments", 0)
            if total > 0:
                correct = cal_data.get("correct", 0)
                incorrect = cal_data.get("incorrect", 0)
                pct = round(correct / max(total, 1) * 100, 1)
                cal_parts.append(
                    f"\nRunning calibration: {correct}/{total} correct ({pct}%). "
                    f"{incorrect} incorrect, {total - correct - incorrect} unresolved."
                )
            
            cal_parts.append("\n\n=== END CALIBRATION FEEDBACK ===")
            cal_block = "\n".join(cal_parts)
            
            insert_point = system.find("Discipline:")
            if insert_point >= 0:
                system = system[:insert_point] + cal_block + "\n\n" + system[insert_point:]
                log(f"injected calibration feedback ({len(cal_block)} chars) into system prompt")
            else:
                system = system + cal_block
                log(f"injected calibration feedback at end ({len(cal_block)} chars)")
        except Exception as exc:
            log(f"calibration feedback failed to load ({exc}) — continuing without")

    # Step 0e — inject self-assessment feedback (if critical issues found)
    if args.self_assessment and os.path.exists(args.self_assessment):
        sa_text = pathlib.Path(args.self_assessment).read_text().strip()
        if sa_text and "CRITICAL" in args.self_assessment.upper():
            # Only inject if file has actual content
            pass
        if sa_text and len(sa_text) > 50:
            system = system + "\n\n" + sa_text
            log(f"injected self-assessment feedback ({len(sa_text)} chars) into system prompt")

    # Step 0c — inject procedural memory (learned procedures) into system prompt
    if args.procedural and os.path.exists(args.procedural):
        proc_text = pathlib.Path(args.procedural).read_text().strip()
        if proc_text:
            system = system + "\n\n" + proc_text
            log(f"injected procedural memory ({len(proc_text)} chars) into system prompt")



    regional_template = prompts.get("Regional Analyst Prompt", "")
    exec_template = prompts.get("Executive Summary Prompt", "")
    red_team_template = prompts.get("Red Team Prompt", "")
    if not (system and regional_template and exec_template and red_team_template):
        log("FATAL: prompt templates missing in deepseek-prompts.md")
        return 2

    analysis_dir = wd / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Tiered model routing: cheap model for regional data synthesis, frontier for strategy
    tier1_model = args.model       # e.g., anthropic/claude-opus-4.7 — exec summary + red team
    tier2_model = args.tier2_model  # e.g., deepseek/deepseek-v4-pro — regional analysis
    # Tier-2 ALWAYS uses DeepSeek Direct API (never route DeepSeek through OpenRouter)
    tier2_provider = "deepseek"
    log(f"Tiered routing: 6 regions → {tier2_model.split('/')[-1]} (tier-2 via {tier2_provider}), "
        f"exec+redteam → {tier1_model.split('/')[-1]} (tier-1 via {args.provider})")

    regional_payloads: dict[str, dict] = {}
    for region in REGIONS_ORDER:
        log(f"analysing {region} (tier-2)")
        if args.mock:
            payload = mock_regional(region, incidents, date_utc)
        else:
            iw_md = find_iw_board(repo_root, region)
            user, _short = regional_prompt(regional_template, region,
                                           incidents, iw_md, date_utc,
                                           collection_state=collection_state,
                                           behavioral_state=behavioral_state)
            try:
                content = call_deepseek(tier2_model, system, user, provider=tier2_provider)
                payload = parse_json_strict(content)
            except Exception as exc:
                log(f"tier-2 attempt failed for {region}: {exc}; retrying with strict prompt")
                strict_system = system + (
                    "\n\nIMPORTANT: respond ONLY with a valid JSON object. "
                    "No prose, no markdown fences."
                )
                content = call_deepseek(tier2_model, strict_system, user, provider=tier2_provider)
                payload = parse_json_strict(content)
        (analysis_dir / f"{region}.json").write_text(json.dumps(payload, indent=2))
        regional_payloads[region] = payload

    log(f"composing executive summary (tier-1)")
    if args.mock:
        exec_payload = mock_exec(regional_payloads, date_utc)
    else:
        user = exec_prompt(exec_template, regional_payloads, date_utc,
                               collection_state=collection_state,
                               behavioral_state=behavioral_state)
        content = call_deepseek(tier1_model, system, user, provider=args.provider)
        exec_payload = parse_json_strict(content)
    (analysis_dir / "exec_summary.json").write_text(
        json.dumps(exec_payload, indent=2))

    # Red-team — uses tier-1 for better adversarial reasoning
    log("running red-team pass (tier-1)")
    target_region = max(REGIONS_ORDER,
                       key=lambda r: regional_payloads[r].get("incident_count", 0))
    target_payload = regional_payloads[target_region]
    target_kj_id = target_payload.get("red_team_target_kj")
    target_kj = next((k for k in target_payload.get("key_judgments", [])
                      if k.get("id") == target_kj_id),
                     (target_payload.get("key_judgments") or [{}])[0])
    if args.mock:
        red_md = (
            f"# Red-Team Note — {REGION_LABEL[target_region]} — {target_kj.get('id')}\n\n"
            "Mock red-team. The strongest alternative would argue [...]. "
            "Two underweighted incident-set items: [...]. Two outside-set items: [...]. "
            "Probability of alternative: even chance.\n\n"
            "**Verdict: The original judgment holds with the assigned band.**\n"
        )
    else:
        user = red_team_prompt(red_team_template, REGION_LABEL[target_region],
                               target_kj, target_payload.get("narrative", ""),
                               date_utc)
        red_md = call_deepseek(tier1_model, system, user, json_mode=False,
                               temperature=0.4, provider=args.provider)
    (analysis_dir / "red_team.md").write_text(red_md)

    log(f"wrote 7 analysis files to {analysis_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
