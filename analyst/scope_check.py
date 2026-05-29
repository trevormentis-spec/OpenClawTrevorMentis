# GATE_EXEMPT: scope_check uses scope_classifier task type via llm_gate. Endpoint URL is for the gate-selected model call.
#!/usr/bin/env python3
"""Scope gate — checks whether a request/topic is in scope for the active assignment.

Used as the FIRST call in every analyst entry point. Produces three-branch classification:
in_scope / adjacent / out_of_scope.

Architecture:
  - Fast path: keyword match against topic config (zero API cost).
  - Slow path: LLM classification for ambiguous requests.
  - Two-tier decline: reframe-offer when vectors exist, terse when none.

Domain-general: reads scope from config/topics/<active-topic>/topic.yaml.
Falls back to analyst/config/scope.yaml for backward compatibility.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any, Optional


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS_DIR = REPO_ROOT / "config" / "topics"
LEGACY_SCOPE_YAML = REPO_ROOT / "analyst" / "config" / "scope.yaml"
ACTIVE_ASSIGNMENTS = REPO_ROOT / "config" / "active-assignments.yaml"


# ── Config loader ──────────────────────────────────────────────────────────

def _get_active_topic_slug() -> Optional[str]:
    """Get the primary active topic slug from active-assignments.yaml."""
    if not ACTIVE_ASSIGNMENTS.exists():
        return None
    try:
        text = ACTIVE_ASSIGNMENTS.read_text()
        # Simple YAML extraction for assignments list
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- topic:"):
                return line.split(":", 1)[1].strip()
        return None
    except Exception:
        return None


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for flat configs (no nested structures beyond lists)."""
    result = {}
    current_key = None
    current_list = None
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list is not None:
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if ":" in stripped and not stripped.startswith("-"):
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if current_list is not None:
                result[current_key] = current_list
                current_list = None
            if val:
                result[key] = val
                current_key = key
            else:
                current_key = key
                current_list = []
    if current_list is not None:
        result[current_key] = current_list
    return result


def load_scope(topic_slug: Optional[str] = None) -> dict:
    """Load scope configuration for the active topic.

    Priority:
    1. config/topics/<topic_slug>/topic.yaml (if topic specified or active)
    2. analyst/config/scope.yaml (legacy fallback)
    3. Permissive defaults (no scope restriction)
    """
    defaults = {
        "primary_scope": "general",
        "scope_description": "general intelligence analysis",
        "themes": [],
        "adjacency_vectors": [],
        "out_of_scope_keywords": [],
        "in_scope_keywords": [],
        "blocklist": [],
    }

    # Determine which topic to load
    if topic_slug is None:
        topic_slug = _get_active_topic_slug()

    # Try topic-specific config
    if topic_slug:
        topic_yaml = TOPICS_DIR / topic_slug / "topic.yaml"
        if topic_yaml.exists():
            try:
                raw = _parse_simple_yaml(topic_yaml.read_text())
                return {
                    "primary_scope": raw.get("primary_scope", raw.get("name", topic_slug)),
                    "scope_description": raw.get("scope_description", raw.get("description", "")),
                    "themes": raw.get("themes", []),
                    "adjacency_vectors": raw.get("adjacency_vectors", []),
                    "out_of_scope_keywords": raw.get("blocklist", []),
                    "in_scope_keywords": raw.get("in_scope_keywords", []),
                    "blocklist": raw.get("blocklist", []),
                    "topic_slug": topic_slug,
                }
            except Exception:
                pass

    # Try legacy scope.yaml
    if LEGACY_SCOPE_YAML.exists():
        try:
            import yaml as _yaml
            raw = _yaml.safe_load(LEGACY_SCOPE_YAML.read_text())
            if isinstance(raw, dict):
                return {k: raw.get(k, defaults[k]) for k in defaults}
        except ImportError:
            # No yaml module — try simple parsing
            try:
                raw = _parse_simple_yaml(LEGACY_SCOPE_YAML.read_text())
                return {k: raw.get(k, defaults[k]) for k in defaults}
            except Exception:
                pass
        except Exception:
            pass

    return defaults


# ── Normalization ──────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


# ── Fast path: keyword matching ────────────────────────────────────────────

def _keyword_scan(normalized: str, config: dict) -> str | None:
    """Fast-path keyword scan. Returns scope_status or None if ambiguous."""
    for kw in config.get("out_of_scope_keywords", []) + config.get("blocklist", []):
        if isinstance(kw, str) and kw.lower() in normalized:
            return "out_of_scope"
    for kw in config.get("in_scope_keywords", []):
        if isinstance(kw, str) and kw.lower() in normalized:
            return "in_scope"
    return None


# ── Vector matching ───────────────────────────────────────────────────────

def _find_topic_vectors(topic: str, config: dict) -> list[str]:
    """Scan topic against adjacency_vectors from config. Returns up to 4."""
    normalized = _normalize(topic)
    vectors: list[str] = []

    for av in config.get("adjacency_vectors", []):
        if isinstance(av, str):
            # Simple string vector
            if any(w in normalized for w in av.lower().split() if len(w) > 3):
                vectors.append(av)
        elif isinstance(av, dict):
            key = av.get("key", "")
            connector = av.get("connector", "")
            label = av.get("label", key)

            label_keywords = [w for w in re.sub(r"[^\w\s]", " ", label.lower()).split()
                             if len(w) > 3]
            if any(kw in normalized for kw in label_keywords):
                vectors.append(f"{label}: {connector}")

    return vectors[:4]


# ── Slow path: LLM classification ──────────────────────────────────────────

def _llm_classify(topic: str, config: dict) -> dict:
    """Classify topic via cheap LLM call (deepseek-chat). Topic-general."""
    scope_name = config.get("primary_scope", "the assigned topic")
    scope_desc = config.get("scope_description", "the current analytical assignment")

    prompt = f"""You are a scope gate for an intelligence analyst desk.
The current assignment is: {scope_name} — {scope_desc}

Classify this user request: "{topic}"

Return exactly:
{{"scope_status": "in_scope"|"adjacent"|"out_of_scope", "rationale": "one-sentence why"}}

Rules:
- in_scope = directly about {scope_name} or its core entities/institutions.
- adjacent = NOT directly about {scope_name} but HAS a credible transmission
  mechanism (energy, currency, trade, capital flows, migration, supply chains,
  political contagion, regulatory precedent, etc.).
  Adjacency is the DEFAULT for any topic with a credible mechanism.
- out_of_scope = NO credible transmission mechanism to {scope_name}.

HARD RULE: When in doubt, prefer adjacent over out_of_scope."""

    # Route through gate for model selection and logging
    try:
        from analyst.llm_gate import route as _gate_route
        _gating = _gate_route("scope_classifier", {"slow_path": True})
        _model = _gating.model
        _provider = _gating.provider
        # Log the routing
        _log_path = REPO_ROOT / "memory" / "llm-routing-log.jsonl"
        _rec = {"model": _model, "provider": _provider,
                "estimated_cost_usd": _gating.estimated_cost_usd,
                "justification": _gating.justification,
                "task_type": "scope_classifier",
                "quality_gates": [],
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path, "a") as _f:
            _f.write(json.dumps(_rec) + "\n")
    except Exception:
        _model = "deepseek-chat"
        _provider = "deepseek"

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return {"scope_status": "needs_human_review",
                "rationale": "LLM unavailable. Fails closed — needs principal review."}

    payload = {
        "model": _model.split("/")[-1] if "/" in _model else _model,
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
            return {"scope_status": "needs_human_review",
                    "rationale": f"HTTP {http_code}. Fails closed — needs principal review."}
        resp = json.loads(body)
        content = resp["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n", "", content)
            content = re.sub(r"\n```$", "", content)
        parsed = json.loads(content)
        return {"scope_status": parsed.get("scope_status", "needs_human_review"),
                "rationale": parsed.get("rationale", "")}
    except Exception as exc:
        return {"scope_status": "needs_human_review",
                "rationale": f"LLM failed ({exc}). Fails closed — needs principal review."}


# ── Main check function ────────────────────────────────────────────────────

def check_scope(topic_or_request: str, topic_slug: Optional[str] = None) -> dict:
    """Classify a request against the active topic scope.

    Returns dict with scope_status, rationale, topic_vectors.
    """
    config = load_scope(topic_slug)
    normalized = _normalize(topic_or_request)

    # Fast path
    fast = _keyword_scan(normalized, config)
    if fast == "in_scope":
        return {"scope_status": "in_scope",
                "rationale": "Keyword match — in-scope entities found.",
                "topic_vectors": []}
    if fast == "out_of_scope":
        vectors = _find_topic_vectors(topic_or_request, config)
        return {"scope_status": "out_of_scope",
                "rationale": "Keyword match — blocklist hit.",
                "topic_vectors": vectors}

    # Slow path
    llm = _llm_classify(topic_or_request, config)
    status = llm.get("scope_status", "in_scope")
    rationale = llm.get("rationale", "")

    vectors = _find_topic_vectors(topic_or_request, config) if status in ("adjacent", "out_of_scope") else []

    return {"scope_status": status, "rationale": rationale,
            "topic_vectors": vectors}


# ── Decline builder ───────────────────────────────────────────────────────

def build_decline(topic: str, scope_result: dict, config: Optional[dict] = None) -> str:
    """Build decline message for OUT_OF_SCOPE topics. Topic-general."""
    if config is None:
        config = load_scope()

    scope_name = config.get("primary_scope", "the assigned topic")
    scope_desc = config.get("scope_description", "current analytical assignment")
    vectors = scope_result.get("topic_vectors", [])

    if len(vectors) >= 2:
        vlines = "\n".join(f"- {v}" for v in vectors)
        return (
            f"Trevor is currently scoped to {scope_name} ({scope_desc}). "
            f"'{topic[:80]}' reaches {scope_name} through {len(vectors)} vectors:\n\n"
            f"{vlines}\n\n"
            "Want any of those framings? If you have a specific question within "
            f"{scope_name} scope, ask that instead."
        )
    else:
        return (
            f"Trevor is currently scoped to {scope_name} ({scope_desc}). "
            f"'{topic[:80]}' has no credible transmission mechanism to "
            f"{scope_name}-exposed decisions.\n\n"
            f"If you have a specific {scope_name} question, ask that instead."
        )


def build_adjacency_preamble(topic: str, scope_result: dict, config: Optional[dict] = None) -> str:
    """Build framing preamble for ADJACENT-topic brief. Topic-general."""
    if config is None:
        config = load_scope()

    scope_name = config.get("primary_scope", "the assigned topic")
    vectors = scope_result.get("topic_vectors", [])

    if not vectors:
        return (
            f"ADJACENCY NOTE: '{topic[:80]}' is not directly about {scope_name} "
            f"but is adjacent through {scope_name}-relevant channels. Produce a "
            f"{scope_name}-framed brief using the adjacent_brief template."
        )
    vlines = "\n".join(f"- Vector {i+1}: {v}" for i, v in enumerate(vectors))
    return (
        f"ADJACENCY FRAMING — '{topic[:80]}' touches {scope_name} through these vectors:\n\n"
        f"{vlines}\n\n"
        f"Frame the ENTIRE brief through the {scope_name} lens. Each section covers "
        f"one vector. NOT a generic global brief with {scope_name} appended."
    )


# ── CLI entry point ────────────────────────────────────────────────────────

def _run_regression_test(topic_slug: str) -> list[dict]:
    """Run regression tests from probes.yaml against the scope check."""
    probes_path = TOPICS_DIR / topic_slug / "probes.yaml"
    if not probes_path.exists():
        return [{"query": "NO PROBES FILE", "expected": "?", "actual": "?", "status": "MISSING_PROBES"}]
    import yaml
    config = yaml.safe_load(probes_path.read_text())
    results = []
    for probe in config.get("probes", []):
        q = probe["query"]
        expected = probe["expected"]
        result = check_scope(q, topic_slug=topic_slug)
        actual = result.get("scope_status", "unknown")
        passed = actual == expected or (expected == "adjacent" and actual in ("adjacent", "in_scope"))
        results.append({"query": q[:60], "expected": expected, "actual": actual, "status": "PASS" if passed else "FAIL"})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Scope gate for Trevor intelligence analyst")
    parser.add_argument("--topic", help="Request or topic to classify")
    parser.add_argument("--topic-slug", help="Override active topic slug")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--regression-test", action="store_true", help="Run regression probes against active topic")
    args = parser.parse_args()

    if args.regression_test:
        slug = args.topic_slug or _get_active_topic_slug()
        if not slug:
            print("{\"status\": \"error\", \"message\": \"No active topic found\"}")
            sys.exit(1)
        results = _run_regression_test(slug)
        passed = sum(1 for r in results if r["status"] == "PASS")
        total = len(results)
        output = {"topic": slug, "total": total, "passed": passed, "results": results}
        if args.json:
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(f"Regression test for topic: {slug}")
            for r in results:
                mark = "✅" if r["status"] == "PASS" else "❌"
                print(f"  {mark} {r['query'][:50]:50s} expected={r['expected']:12s} actual={r['actual']:12s}")
            print(f"\n{passed}/{total} passed")
        sys.exit(0 if passed == total else 1)

    if not args.topic:
        parser.print_help()
        sys.exit(1)

    result = check_scope(args.topic, topic_slug=args.topic_slug)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if result["scope_status"] == "in_scope":
        print(f"IN SCOPE: {result['rationale']}")
    elif result["scope_status"] == "adjacent":
        print(f"ADJACENT: {result['rationale']}")
        print()
        print(build_adjacency_preamble(args.topic, result))
    else:
        print(build_decline(args.topic, result))
        sys.exit(1)


if __name__ == "__main__":
    main()
