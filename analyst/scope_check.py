#!/usr/bin/env python3
"""Scope gate — checks whether a request/topic is in scope for the desk.

Used as the FIRST call in every analyst entry point (analyze.py,
orchestrate.py, chat handler). Declines out-of-scope requests with
a structured response and offers Mexico-vector reframes for adjacent
topics.

Architecture:
  - Fast path: keyword match against scope.yaml (zero API cost).
  - Slow path: LLM classification for ambiguous requests.
  - Output: dict with scope_status, rationale, and mexico_vectors.

Usage:
    python3 scope_check.py --topic "Brief me on Russia-Ukraine"
    python3 scope_check.py --topic "What's happening with Pemex refining margins?"

    # As an importable module:
    from analyst.scope_check import check_scope
    result = check_scope("Brief me on Sinaloa cartel violence")
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCOPE_YAML = REPO_ROOT / "analyst" / "config" / "scope.yaml"
DECLINE_TEMPLATE = """\
Open Claw Mexico is scoped to {scope_descriptor}. {topic_label}
reaches Mexico through {n} vectors moving today:

{vectors}

Want any of those framings? If you have a specific Mexico question
I should be answering, ask that instead.\
"""


# ── Config loader ──────────────────────────────────────────────────────────

def load_scope() -> dict:
    """Load scope.yaml. Falls back to defaults if file missing or unparseable.

    Returns a dict with keys: primary_scope, scope_descriptor, themes,
    adjacency_vectors, out_of_scope_keywords, in_scope_keywords.
    """
    defaults = {
        "primary_scope": "Mexico",
        "scope_descriptor": "Mexico-only intelligence",
        "themes": ["cartel_security", "political_risk", "us_mexico",
                    "energy_infra", "economy_markets", "worldcup_travel"],
        "adjacency_vectors": [
            {"key": "brent-pemex",
             "label": "Oil prices / Pemex spread",
             "connector": "Brent/WTI moves affect Pemex spreads and the peso."},
        ],
        "out_of_scope_keywords": [],
        "in_scope_keywords": ["mexico", "sinaloa", "cartel"],
    }

    if not SCOPE_YAML.exists():
        return defaults

    try:
        # Use yaml if available, otherwise simple key:value scanner
        import yaml as _yaml
        raw = _yaml.safe_load(SCOPE_YAML.read_text())
        if not isinstance(raw, dict):
            return defaults
        return {
            "primary_scope": raw.get("primary_scope", defaults["primary_scope"]),
            "scope_descriptor": raw.get("scope_descriptor", defaults["scope_descriptor"]),
            "themes": raw.get("themes", defaults["themes"]),
            "adjacency_vectors": raw.get("adjacency_vectors", defaults["adjacency_vectors"]),
            "out_of_scope_keywords": raw.get("out_of_scope_keywords", defaults["out_of_scope_keywords"]),
            "in_scope_keywords": raw.get("in_scope_keywords", defaults["in_scope_keywords"]),
        }
    except Exception:
        return defaults


# ── Fast path: keyword matching ────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = re.sub(r"[^\w\s]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keyword_scan(normalized: str, config: dict) -> str | None:
    """Fast-path keyword scan. Returns scope_status or None if ambiguous."""
    # Check blocklist first (unambiguous out-of-scope)
    for kw in config.get("out_of_scope_keywords", []):
        if kw.lower() in normalized:
            return "out_of_scope"

    # Check in-scope keywords (unambiguous in-scope)
    for kw in config.get("in_scope_keywords", []):
        if kw.lower() in normalized:
            return "in_scope"

    # Ambiguous — needs LLM
    return None


# ── Slow path: LLM classification ──────────────────────────────────────────

def _llm_classify(topic: str, config: dict) -> dict:
    """Classify topic via cheap LLM call (deepseek-v4-flash)."""
    prompt = f"""You are a scope gate for a Mexico-only intelligence analyst desk.

Classify this user request: "{topic}"

Return exactly one JSON object with two fields:
{{"scope_status": "in_scope"|"adjacent"|"out_of_scope", "rationale": "one-sentence why"}}

Rules:
- "in_scope" = directly about Mexico, Mexican institutions, cartels, Mexican states, 
  US-Mexico relations, Pemex, Mexican politics, Mexican economy, Mexican security.
  ANY mention of Mexico, a Mexican state/city, a Mexican institution, a cartel,
  a Mexican politician, or a Mexico-specific issue = in_scope.
- "adjacent" = the topic is not about Mexico but has a current, specific connection
  to Mexico. Examples: global oil prices (Pemex), fentanyl precursor chemicals from 
  China (Mexican cartel labs), US tariffs (Mexico trade), migration through Mexico,
  Ukraine wheat prices (Mexican tortilla prices), Russian fertilizer (Mexican ag).
- "out_of_scope" = no substantive Mexico connection. Pure Russia-Ukraine front
  reporting, China-Taiwan military balance, Israel-Gaza, African security, European
  politics, Asian regional security, global finance etc = out_of_scope.

When in doubt, err toward "adjacent" — the scope gate is permissive, not strict.
It's better to offer a reframe than to dismiss a request that could reach Mexico."""
    
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return {
            "scope_status": "in_scope",  # permissive default on API failure
            "rationale": "Cannot classify — LLM API unavailable. Defaulting to in_scope.",
        }

    payload = {
        "model": "deepseek-chat",  # cheapest option for classification
        "messages": [
            {"role": "system", "content": "You are a classification gate. Return only valid JSON."},
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
            "--connect-timeout", "15",
            "--max-time", "30",
        ]
        result = _sp.run(cmd, capture_output=True, text=True, timeout=35)
        os.unlink(tmp.name)

        stdout = result.stdout
        idx = stdout.rfind("\n")
        body = stdout[:idx] if idx >= 0 else stdout
        http_code = stdout[idx+1:].strip() if idx >= 0 else "000"

        if not http_code.startswith("2"):
            return {
                "scope_status": "in_scope",
                "rationale": f"LLM classify returned HTTP {http_code}. Defaulting to in_scope.",
            }

        resp = json.loads(body)
        choice = resp["choices"][0]
        content = choice["message"]["content"]

        # Handle potential markdown-wrapped JSON
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n", "", content)
            content = re.sub(r"\n```$", "", content)

        parsed = json.loads(content)
        return {
            "scope_status": parsed.get("scope_status", "in_scope"),
            "rationale": parsed.get("rationale", ""),
        }

    except Exception as exc:
        return {
            "scope_status": "in_scope",
            "rationale": f"LLM classify failed ({exc}). Defaulting to in_scope.",
        }


# ── Main check function ────────────────────────────────────────────────────

def check_scope(topic_or_request: str) -> dict:
    """Check if a request is within the desk's scope.

    Returns dict with:
        scope_status: "in_scope" | "adjacent" | "out_of_scope"
        rationale: str
        mexico_vectors: list[str]  # 2-4 Mexico-connecting vectors, only for adjacent
    """
    config = load_scope()
    normalized = _normalize(topic_or_request)

    # Fast path: keyword scan
    fast_result = _keyword_scan(normalized, config)
    if fast_result == "in_scope":
        return {
            "scope_status": "in_scope",
            "rationale": "Keyword match — topic directly references Mexico or Mexico-specific entities.",
            "mexico_vectors": [],
        }
    if fast_result == "out_of_scope":
        return {
            "scope_status": "out_of_scope",
            "rationale": "Keyword match — topic matches out-of-scope blocklist.",
            "mexico_vectors": [],
        }

    # Slow path: LLM classification
    llm_result = _llm_classify(topic_or_request, config)
    status = llm_result.get("scope_status", "in_scope")
    rationale = llm_result.get("rationale", "LLM classification — permissive default.")

    # Build Mexico vectors if adjacent
    vectors = []
    if status == "adjacent":
        # Find matching vectors from config by scanning the topic against labels
        normalized_lower = normalized
        for av in config.get("adjacency_vectors", []):
            label_lower = av.get("label", "").lower()
            connector = av.get("connector", "")
            # Check if any key terms from the vector appear in the topic
            keywords = re.sub(r"[^\w\s]", " ", label_lower).split()
            keywords = [k for k in keywords if len(k) > 3]
            if any(kw in normalized_lower for kw in keywords):
                vectors.append(f"{av.get('label', 'Unknown')}: {connector}")
        
        # If no specific vectors matched, include all generic ones
        if not vectors:
            for av in config.get("adjacency_vectors", []):
                connector = av.get("connector", "")
                if connector:
                    vectors.append(f"{av.get('label', 'Unknown')}: {connector}")
        
        # Limit to 4 vectors
        vectors = vectors[:4]

    return {
        "scope_status": status,
        "rationale": rationale,
        "mexico_vectors": vectors,
    }


# ── Decline message builder ────────────────────────────────────────────────

def build_decline(topic: str, scope_result: dict) -> str:
    """Build the decline-and-reframe message.

    Uses the DECLINE_TEMPLATE with scope config and dynamic vectors.
    """
    config = load_scope()
    scope_descriptor = config.get("scope_descriptor", "Mexico-only intelligence")

    if scope_result["scope_status"] == "in_scope":
        raise ValueError("build_decline called on in_scope topic — use normal handler")

    if scope_result["scope_status"] == "adjacent":
        vectors = scope_result.get("mexico_vectors", [])
        if not vectors:
            # Fallback: offer generic adjacency prompt
            return (
                f"Open Claw Mexico is scoped to {scope_descriptor}. "
                f"'{topic}' is adjacent but I don't see a live Mexico vector today.\n\n"
                "If you have a specific Mexico question I should be answering, ask that instead."
            )

        n = len(vectors)
        vector_lines = "\n".join(f"- {v}" for v in vectors)

        return DECLINE_TEMPLATE.format(
            scope_descriptor=scope_descriptor,
            topic_label=topic[:80],
            n=n,
            vectors=vector_lines,
        )

    # out_of_scope
    return (
        f"Open Claw Mexico is scoped to {scope_descriptor}. "
        f"'{topic[:80]}' is out of scope.\n\n"
        "If you have a specific Mexico question I should be answering, ask that instead."
    )


# ── CLI entry point ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Scope gate for Open Claw Mexico desk")
    parser.add_argument("--topic", required=True, help="The request or topic to classify")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of decline message")
    args = parser.parse_args()

    result = check_scope(args.topic)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if result["scope_status"] == "in_scope":
        print(f"IN SCOPE: {result['rationale']}")
        sys.exit(0)
    else:
        print(build_decline(args.topic, result))
        sys.exit(1)


if __name__ == "__main__":
    main()
