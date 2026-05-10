#!/usr/bin/env python3
"""Analyst worker for the Daily Intel Brief.

Reads WORKING_DIR/raw/incidents.json, calls the DeepSeek Direct API
(model: deepseek/deepseek-v4-pro per ORCHESTRATION.md escalation tier)
once per region plus one executive-summary call plus one red-team call,
and writes WORKING_DIR/analysis/{region}.json + exec_summary.json +
red_team.md.

Implements agents/analyst.md.

Usage:

    python3 scripts/analyze.py --working-dir <wd> \
        --prompts skills/daily-intel-brief/references/deepseek-prompts.md \
        --regions skills/daily-intel-brief/references/regions.json \
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
    ts = dt.datetime.utcnow().strftime("%H:%M:%S")
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
    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        base_url = OPENROUTER_BASE
        path = OPENROUTER_PATH
        # OpenRouter expects full model name (provider/model)
        api_model = model
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
            "X-Title": "TREVOR Intel Brief",
        }
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set")
        base_url = DEEPSEEK_BASE
        path = DEEPSEEK_PATH
        # DeepSeek uses short model name (strip provider prefix)
        api_model = model.split("/", 1)[-1] if "/" in model else model
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
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
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        base_url + path,
        data=body, method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"{provider.upper()} HTTPError {exc.code}: {exc.read().decode(errors='replace')[:500]}"
        )
    return payload["choices"][0]["message"]["content"]


def regional_prompt(template: str, region_snake: str, incidents: list[dict],
                    iw_board_md: str, date_utc: str) -> tuple[str, str]:
    region_label = REGION_LABEL[region_snake]
    short = REGION_SHORT[region_snake]
    incidents_for_region = [i for i in incidents if i.get("region") == region_snake]
    user = (template
            .replace("{region_label}", region_label)
            .replace("{region_snake}", region_snake)
            .replace("{region_short}", short)
            .replace("{date_utc}", date_utc)
            .replace("{incidents_json_for_region}",
                     json.dumps(incidents_for_region, indent=2))
            .replace("{iw_board_markdown_or_none}",
                     iw_board_md or "No standing I&W board for this region."))
    # the system prompt is shared (defined in references/deepseek-prompts.md)
    return user, short


def exec_prompt(template: str, regional_payloads: dict[str, dict],
                date_utc: str) -> str:
    user = template.replace("{date_utc}", date_utc)
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
    parser.add_argument("--model", default="deepseek/deepseek-v4-pro")
    parser.add_argument("--provider", choices=["deepseek", "openrouter"], default="deepseek",
                        help="API provider to route through (default: deepseek)")
    parser.add_argument("--mock", action="store_true",
                        help="return canned analysis without calling the API")
    args = parser.parse_args()

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
               dt.datetime.utcnow().strftime("%Y-%m-%d")

    prompts = split_prompts(pathlib.Path(args.prompts).read_text())
    system = prompts.get("System message (used for every regional + exec call)", "")
    regional_template = prompts.get("Regional Analyst Prompt", "")
    exec_template = prompts.get("Executive Summary Prompt", "")
    red_team_template = prompts.get("Red Team Prompt", "")
    if not (system and regional_template and exec_template and red_team_template):
        log("FATAL: prompt templates missing in deepseek-prompts.md")
        return 2

    analysis_dir = wd / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    regional_payloads: dict[str, dict] = {}
    for region in REGIONS_ORDER:
        log(f"analysing {region}")
        if args.mock:
            payload = mock_regional(region, incidents, date_utc)
        else:
            iw_md = find_iw_board(repo_root, region)
            user, _short = regional_prompt(regional_template, region,
                                           incidents, iw_md, date_utc)
            try:
                content = call_deepseek(args.model, system, user, provider=args.provider)
                payload = parse_json_strict(content)
            except Exception as exc:
                log(f"first attempt failed for {region}: {exc}; retrying with strict system")
                strict_system = system + (
                    "\n\nIMPORTANT: respond ONLY with a valid JSON object. "
                    "No prose, no markdown fences."
                )
                content = call_deepseek(args.model, strict_system, user, provider=args.provider)
                payload = parse_json_strict(content)
        (analysis_dir / f"{region}.json").write_text(json.dumps(payload, indent=2))
        regional_payloads[region] = payload

    log("composing executive summary")
    if args.mock:
        exec_payload = mock_exec(regional_payloads, date_utc)
    else:
        user = exec_prompt(exec_template, regional_payloads, date_utc)
        content = call_deepseek(args.model, system, user, provider=args.provider)
        exec_payload = parse_json_strict(content)
    (analysis_dir / "exec_summary.json").write_text(
        json.dumps(exec_payload, indent=2))

    # Red-team
    log("running red-team pass")
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
        red_md = call_deepseek(args.model, system, user, json_mode=False,
                               temperature=0.4, provider=args.provider)
    (analysis_dir / "red_team.md").write_text(red_md)

    log(f"wrote 7 analysis files to {analysis_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
