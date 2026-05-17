#!/usr/bin/env python3
"""Scope gate — checks whether a request/topic is in scope for the desk.

Used as the FIRST call in every analyst entry point (analyze.py,
orchestrate.py, chat handler). Produces three-branch classification.

Architecture:
  - Fast path: keyword match against scope.yaml (zero API cost).
  - Slow path: LLM classification for ambiguous requests.
  - Two-tier decline: reframe-offer when vectors exist, terse when none.
  - Regression test suite: --regression-test runs all four canonical probes.

Framework-general: redirect by editing analyst/config/scope.yaml.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCOPE_YAML = REPO_ROOT / "analyst" / "config" / "scope.yaml"

# ── Canonical probes for regression testing ─────────────────────────────────

REGRESSION_PROBES: list[dict] = [
    {
        "name": "A",
        "input": "Brief me on the Saudi-Russia oil production talks this week.",
        "expect_scope": "adjacent",
        "check_vectors": True,
    },
    {
        "name": "B",
        "input": "Brief me on the ECB's rate decision this week.",
        "expect_scope": "adjacent",
        "check_vectors": True,
    },
    {
        "name": "C",
        "input": "Brief me on the Russia-Ukraine front for today.",
        "expect_scope": "out_of_scope",
        "check_reframe": True,  # must produce vectors even though out_of_scope
    },
    {
        "name": "D",
        "input": "What's happening with Pemex's Cadereyta refinery this week?",
        "expect_scope": "in_scope",
        "check_vectors": False,
    },
]


# ── Config loader ──────────────────────────────────────────────────────────

def load_scope() -> dict:
    """Load scope.yaml. Falls back to defaults if file missing or unparseable."""
    defaults = {
        "primary_scope": "Mexico",
        "scope_descriptor": "Mexico-only intelligence",
        "themes": ["cartel_security", "political_risk", "us_mexico",
                    "energy_infra", "economy_markets", "worldcup_travel"],
        "adjacency_vectors": [],
        "out_of_scope_keywords": [],
        "in_scope_keywords": ["mexico", "sinaloa", "cartel"],
    }
    if not SCOPE_YAML.exists():
        return defaults
    try:
        import yaml as _yaml
        raw = _yaml.safe_load(SCOPE_YAML.read_text())
        if not isinstance(raw, dict):
            return defaults
        return {
            k: raw.get(k, defaults[k]) for k in defaults
        }
    except Exception:
        return defaults


# ── Normalization ──────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


# ── Fast path: keyword matching ────────────────────────────────────────────

def _keyword_scan(normalized: str, config: dict) -> str | None:
    """Fast-path keyword scan. Returns scope_status or None if ambiguous."""
    for kw in config.get("out_of_scope_keywords", []):
        if kw.lower() in normalized:
            return "out_of_scope"
    for kw in config.get("in_scope_keywords", []):
        if kw.lower() in normalized:
            return "in_scope"
    return None


# ── Mexico vector matching (for reframe-offer and adjacency) ───────────────

def _find_mexico_vectors(topic: str, config: dict) -> list[str]:
    """Scan topic against adjacency_vectors from config. Returns up to 4.

    Used by both adjacent and out_of_scope branches. Attempts keyword
    match on vector labels first; falls back to returning all vectors
    if no specific match.
    """
    normalized = _normalize(topic)
    vectors: list[str] = []
    for av in config.get("adjacency_vectors", []):
        label_lower = av.get("label", "").lower()
        connector = av.get("connector", "")
        keywords = [w for w in re.sub(r"[^\w\s]", " ", label_lower).split()
                    if len(w) > 3]
        if any(kw in normalized for kw in keywords):
            vectors.append(f"{av['label']}: {connector}")
    # Fall back to all vectors if no specific match
    if not vectors:
        for av in config.get("adjacency_vectors", []):
            c = av.get("connector", "")
            if c:
                vectors.append(f"{av['label']}: {c}")
    return vectors[:4]


# ── Slow path: LLM classification ──────────────────────────────────────────

def _llm_classify(topic: str, config: dict) -> dict:
    """Classify topic via cheap LLM call (deepseek-chat)."""
    prompt = f"""You are a scope gate for a Mexico-only intelligence analyst desk.

Classify this user request: "{topic}"

Return exactly:
{{"scope_status": "in_scope"|"adjacent"|"out_of_scope", "rationale": "one-sentence why"}}

Rules:
- in_scope = directly about Mexico, Mexican institution, cartel, state/city,
  politician, Pemex/CFE, Mexican economy/peso, Mexican security/politics.

- adjacent = NOT about Mexico but HAS a credible transmission mechanism.
  **Adjacency is the DEFAULT for any topic with a credible mechanism
  (energy, currency, trade, capital flows, migration, supply chains).**

  Adjacency examples:
  - "Saudi-Russia oil production talks" → adjacent
  - "ECB rate decision" → adjacent
  - "Korean semiconductor capacity" → adjacent
  - "Brazilian presidential election" → adjacent
  - "OPEC+ production meeting" → adjacent
  - "Argentina IMF program" → adjacent
  - "China rare earth export controls" → adjacent
  - "Canadian dairy USMCA dispute" → adjacent
  - "Iran nuclear escalation" → adjacent
  - "Vietnam tariff dispute" → adjacent
  - "Ukraine wheat supply" → adjacent
  - "Russia-Ukraine war" → adjacent (Brent, wheat, fertilizer reach Mexico)

- out_of_scope = NO credible transmission mechanism to Mexico.

  True out-of-scope examples:
  - "K-pop label dynamics"
  - "NFL playoff predictions"
  - "Premier League transfer window"
  - "Japanese election prediction"
  - "EU AI Act enforcement"
  - "California drought policy"

HARD RULE: When in doubt, prefer adjacent over out_of_scope."""

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        # Permissive default when LLM unavailable: check for Mexico vectors
        # to distinguish adjacent (has vectors) from truly in_scope (no vectors
        # but the topic may still reference Mexico).
        return {"scope_status": "permissive_default",
                "rationale": "LLM unavailable. Returning permissive default for vector check."}

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }
    try:
        import subprocess as _sp, tempfile as _tf
        tmp = _tf.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(json.dumps(payload))
        tmp.close()
        cmd = [
            "curl", "-s", "-w", "\n%{http_code}",
            "-X", "POST", "https://api.deepseek.com/v1/chat/completions",
            "-H", "Content-Type: application/json",
            "-H", "Authorization: Bearer " + api_key,
            "--data-binary", "@" + tmp.name,
            "--connect-timeout", "15", "--max-time", "30",
        ]
        result = _sp.run(cmd, capture_output=True, text=True, timeout=35)
        os.unlink(tmp.name)
        stdout, idx = result.stdout, result.stdout.rfind("\n")
        body = stdout[:idx] if idx >= 0 else stdout
        http_code = stdout[idx+1:].strip() if idx >= 0 else "000"
        if not http_code.startswith("2"):
            return {"scope_status": "in_scope",
                    "rationale": f"HTTP {http_code}. Defaulting to in_scope."}
        resp = json.loads(body)
        content = resp["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n", "", content)
            content = re.sub(r"\n```$", "", content)
        parsed = json.loads(content)
        return {"scope_status": parsed.get("scope_status", "in_scope"),
                "rationale": parsed.get("rationale", "")}
    except Exception as exc:
        return {"scope_status": "in_scope",
                "rationale": f"LLM failed ({exc}). Defaulting to in_scope."}


# ── Main check function ────────────────────────────────────────────────────

def check_scope(topic_or_request: str) -> dict:
    """Classify a request. Returns dict with scope_status, rationale, mexico_vectors.

    mexico_vectors is populated for both adjacent and out_of_scope results
    (the latter enables reframe-offer in the decline template).
    """
    config = load_scope()
    normalized = _normalize(topic_or_request)

    fast = _keyword_scan(normalized, config)
    if fast == "in_scope":
        return {"scope_status": "in_scope",
                "rationale": "Keyword match — Mexico-specific entities found.",
                "mexico_vectors": []}
    if fast == "out_of_scope":
        vectors = _find_mexico_vectors(topic_or_request, config)
        return {"scope_status": "out_of_scope",
                "rationale": "Keyword match — out-of-scope blocklist.",
                "mexico_vectors": vectors}

    llm = _llm_classify(topic_or_request, config)
    status = llm.get("scope_status", "in_scope")
    rationale = llm.get("rationale", "")

    # If LLM returned permissive_default (LLM unavailable), check vectors to decide
    if status == "permissive_default":
        vectors = _find_mexico_vectors(topic_or_request, config)
        if len(vectors) >= 1:
            # Has Mexico-relevant vectors → treat as adjacent
            status = "adjacent"
            rationale += " Defaulted to adjacent (Mexico vectors found)."
        else:
            # No vectors → treat as in_scope (safe default)
            status = "in_scope"
            rationale += " Defaulted to in_scope (no Mexico vectors, playing safe)."
    else:
        vectors = _find_mexico_vectors(topic_or_request, config) if status in ("adjacent", "out_of_scope") else []

    return {"scope_status": status, "rationale": rationale,
            "mexico_vectors": vectors}


# ── Decline builder (two-tier: reframe-offer vs terse) ─────────────────────

def build_decline(topic: str, scope_result: dict) -> str:
    """Build decline message for OUT_OF_SCOPE topics.

    Two-tier output:
    - If 2+ credible Mexico vectors exist: decline WITH reframe-offer.
    - If <2 vectors: terse decline.
    """
    if scope_result["scope_status"] != "out_of_scope":
        raise ValueError(f"build_decline called on {scope_result['scope_status']} topic")

    config = load_scope()
    descriptor = config.get("scope_descriptor", "Mexico-only intelligence")
    vectors = scope_result.get("mexico_vectors", [])

    if len(vectors) >= 2:
        n = len(vectors)
        vlines = "\n".join(f"- {v}" for v in vectors)
        return (
            f"Open Claw Mexico is scoped to {descriptor}. "
            f"'{topic[:80]}' reaches Mexico through {n} vectors moving today:\n\n"
            f"{vlines}\n\n"
            "Want any of those framings? If you have a specific Mexico question "
            "I should be answering, ask that instead."
        )
    else:
        return (
            f"Open Claw Mexico is scoped to {descriptor}. "
            f"'{topic[:80]}' has no credible transmission mechanism to "
            "Mexico-exposed decisions.\n\n"
            "If you have a specific Mexico question I should be answering, "
            "ask that instead."
        )


# ── Adjacency preamble builder ─────────────────────────────────────────────

def build_adjacency_preamble(topic: str, scope_result: dict) -> str:
    """Build framing preamble for ADJACENT-topic brief."""
    vectors = scope_result.get("mexico_vectors", [])
    if not vectors:
        return (
            f"ADJACENCY NOTE: '{topic[:80]}' is not directly about Mexico "
            "but is adjacent through Mexico-relevant channels. Produce a "
            "Mexico-framed brief using the adjacent_brief template."
        )
    vlines = "\n".join(f"- Vector {i+1}: {v}" for i, v in enumerate(vectors))
    return (
        f"ADJACENCY FRAMING — '{topic[:80]}' touches Mexico through these vectors:\n\n"
        f"{vlines}\n\n"
        "Frame the ENTIRE brief through the Mexico lens. Each section covers "
        "one vector. NOT a generic global brief with Mexico appended."
    )


# ── Regression test runner ─────────────────────────────────────────────────

def run_regression_test(verbose: bool = False) -> list[dict]:
    """Run all four canonical probes. Returns list of result dicts.

    Each result has: name, input, expected_scope, got_scope, pass (bool),
    details (str). Used by --regression-test CLI flag and as a programmatic
    gate.
    """
    results: list[dict] = []
    for p in REGRESSION_PROBES:
        r = check_scope(p["input"])
        scope_ok = r["scope_status"] == p["expect_scope"]
        details = f"scope={r['scope_status']} (expected {p['expect_scope']})"

        if p.get("check_reframe") and r["scope_status"] == "out_of_scope":
            vectors_ok = len(r.get("mexico_vectors", [])) >= 1
            if not vectors_ok:
                details += " | FAIL: no reframe vectors for out_of_scope topic that has them"
                scope_ok = False
            else:
                details += f" | reframe vectors: {len(r['mexico_vectors'])}"

        if p.get("check_vectors") and r["scope_status"] == "adjacent":
            vectors_ok = len(r.get("mexico_vectors", [])) >= 1
            if not vectors_ok:
                details += " | FAIL: no vectors for adjacent topic"
                scope_ok = False
            else:
                details += f" | vectors: {len(r['mexico_vectors'])}"

        results.append({
            "name": p["name"],
            "input": p["input"],
            "expected_scope": p["expect_scope"],
            "got_scope": r["scope_status"],
            "pass": scope_ok,
            "details": details,
        })

    if verbose:
        for res in results:
            status = "PASS" if res["pass"] else "FAIL"
            print(f"  [{status}] Probe {res['name']}: {res['details']}")
        total = sum(1 for r in results if r["pass"])
        print(f"  -> {total}/{len(results)} passing")

    return results


# ── CLI entry point ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Scope gate for Open Claw Mexico desk")
    parser.add_argument("--topic", help="Request or topic to classify")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--format", choices=["json", "decline", "adjacency"],
                        default=None, help="Output format (auto-detect by default)")
    parser.add_argument("--regression-test", action="store_true",
                        help="Run all four canonical probes and report pass/fail")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose regression test output")
    args = parser.parse_args()

    # Regression test mode
    if args.regression_test:
        results = run_regression_test(verbose=True)
        if args.json:
            print(json.dumps(results, indent=2))
        all_pass = all(r["pass"] for r in results)
        sys.exit(0 if all_pass else 1)

    # Single-topic mode
    if not args.topic:
        parser.print_help()
        sys.exit(1)

    result = check_scope(args.topic)

    if args.format == "json" or args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if result["scope_status"] == "in_scope":
        print(f"IN SCOPE: {result['rationale']}")
        sys.exit(0)
    elif result["scope_status"] == "adjacent":
        print(f"ADJACENT: {result['rationale']}")
        print()
        print(build_adjacency_preamble(args.topic, result))
        sys.exit(0)
    else:
        print(build_decline(args.topic, result))
        sys.exit(1)


if __name__ == "__main__":
    main()
