# GATE_EXEMPT: Routes through llm_gate.route() at line 379 before API call. Endpoint URL is for the gate-selected model.
"""TPS Planner — LLM art-director that decomposes briefs into visual primitives.

The planner reads an IngestedBrief, reasons about what visual assets would
best communicate the analysis, and outputs a PresentationPlan with routed
AssetSpecs. It enforces the cardinal rule: image-gen for illustration only,
specialist generators for maps/charts/diagrams.

Uses Claude as the planning LLM via TREVOR's existing llm_gate.py.
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .schemas import (
    IngestedBrief,
    PresentationPlan,
    AssetSpec,
    AssetKind,
    DeliverableKind,
    ApprovalStatus,
)
from .cost_estimator import estimate_plan
from .approval_gate import auto_approve_if_cheap
from .config import get_config
from .exceptions import PlanValidationError


# ── Generator Routing Table ─────────────────────────────────────────────────
# Maps asset kinds to preferred generators (ordered by preference)

ROUTING_TABLE: dict[str, list[str]] = {
    "map": ["mapbox_static", "leaflet", "mapbox_interactive"],
    "diagram": ["mermaid", "d2", "graphviz", "timeline"],
    "chart": ["matplotlib", "plotly", "ldap7_radar"],
    "infographic": ["html_to_png", "recraft_v4", "ideogram_v3"],
    "illustration": ["flux2pro", "recraft_v4", "ideogram_v3", "imagen_4", "gpt_image_2"],
    "table": ["html_to_png", "reportlab_table"],
    "narration": ["elevenlabs", "openai_tts"],
    "video": ["veo_3_1", "kling_3_0", "runway_4_5"],
}

# Image-gen generators that MUST NOT route to structured kinds
IMAGE_GEN_SET = frozenset({
    "flux2pro", "ideogram_v3", "recraft_v4", "imagen_4", "gpt_image_2",
})
STRUCTURED_KINDS = frozenset({"map", "chart", "diagram"})


# ── Few-Shot Examples ───────────────────────────────────────────────────────

FEW_SHOT_EXAMPLES = """
## Example 1: Mexico Political Instability Brief

Input brief summary: "Mexico's political landscape is shifting with CFE energy reform,
cartel dynamics in Bajio region, and upcoming legislative changes."

Output plan:
```json
{
  "assets": [
    {
      "kind": "map",
      "generator": "mapbox_static",
      "title": "Bajio Region Cartel Territorial Control",
      "prompt": "Centered on Guanajuato, Mexico (20.9, -101.2). Markers: Leon (red, high violence), Irapuato (orange, contested), Celaya (red, CJNG stronghold). Zoom 7.",
      "parameters": {"center": [20.9, -101.2], "zoom": 7}
    },
    {
      "kind": "chart",
      "generator": "matplotlib",
      "title": "CFE Revenue vs Subsidy Gap 2020-2026",
      "prompt": "Line chart comparing CFE revenue trajectory against federal subsidy allocation",
      "parameters": {"chart_type": "line", "data_labels": true}
    },
    {
      "kind": "diagram",
      "generator": "mermaid",
      "title": "Escalation Ladder: CFE Reform Scenarios",
      "prompt": "graph TD; A[Status Quo] --> B[Legislative Push]; B --> C{Passes?}; C -->|Yes| D[Implementation]; C -->|No| E[Political Crisis]; D --> F[Rate Hikes]; E --> G[Protests]"
    },
    {
      "kind": "chart",
      "generator": "ldap7_radar",
      "title": "LDAP-7: President Decision Profile",
      "parameters": {"scores": [7, 6, 8, 5, 4, 9, 7], "leader_name": "President"}
    }
  ],
  "deliverables": ["pdf", "exec_card"]
}
```

## Example 2: South China Sea Maritime Assessment

Input brief summary: "Naval buildup around Scarborough Shoal, fishing fleet movements,
and ASEAN diplomatic pressure."

Output plan:
```json
{
  "assets": [
    {
      "kind": "map",
      "generator": "leaflet",
      "title": "South China Sea Naval Positions",
      "prompt": "Interactive dark tactical map centered on SCS. Markers for fleet positions.",
      "parameters": {"center": [14.5, 117.8], "zoom": 6}
    },
    {
      "kind": "diagram",
      "generator": "d2",
      "title": "ASEAN Diplomatic Network: SCS Alliances",
      "prompt": "Philippines -> US: MDT alliance\\nPhilippines -> Japan: Visiting Forces\\nChina -> Cambodia: Belt & Road\\nASEAN -> China: COC Negotiations"
    },
    {
      "kind": "chart",
      "generator": "matplotlib",
      "title": "PLA Navy Ship Deployments 2024-2026",
      "parameters": {"chart_type": "bar"}
    },
    {
      "kind": "illustration",
      "generator": "flux2pro",
      "title": "Cover: Maritime Tensions in the Indo-Pacific",
      "prompt": "Satellite view of contested waters with naval vessels, professional intelligence report style"
    }
  ],
  "deliverables": ["pdf", "briefing_video", "social_pack"]
}
```

## Routing Rules (ENFORCED)
1. Maps → mapbox_static, leaflet, mapbox_interactive (NEVER image-gen)
2. Diagrams → mermaid, d2, graphviz, timeline (NEVER image-gen)
3. Charts → matplotlib, plotly, ldap7_radar (NEVER image-gen)
4. Infographics → html_to_png preferred, image-gen acceptable for artistic infographics
5. Illustrations → image-gen generators (flux2pro, ideogram_v3, etc.)
6. Tables → html_to_png, reportlab_table (NEVER image-gen)
7. Narration → elevenlabs, openai_tts
8. Video → veo_3_1, kling_3_0, runway_4_5
"""


# ── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an intelligence report art director. You receive a structured
intelligence brief and decompose it into visual primitives for production.

Your output is a JSON object with "assets" (list of asset specs) and "deliverables"
(list of deliverable types).

ROUTING RULES (CRITICAL — violations cause system errors):
- Maps MUST use: mapbox_static, leaflet, or mapbox_interactive
- Diagrams MUST use: mermaid, d2, graphviz, or timeline
- Charts MUST use: matplotlib, plotly, or ldap7_radar
- Tables MUST use: html_to_png or reportlab_table
- Illustrations MAY use: flux2pro, recraft_v4, ideogram_v3, imagen_4, gpt_image_2
- Narration MUST use: elevenlabs or openai_tts
- Video MUST use: veo_3_1, kling_3_0, or runway_4_5

NEVER route maps, charts, diagrams, or tables to image-gen generators.

For each asset, provide:
- kind: map|diagram|chart|infographic|illustration|table|narration|video
- generator: one of the approved generators for that kind
- title: human-readable title
- prompt: generator-specific content (Mermaid code for mermaid, map description for mapbox, etc.)
- parameters: generator-specific params (chart_type, center coords, zoom, etc.)

Aim for 3-8 assets per brief. Every brief should have at least one map (if geographic),
one diagram showing relationships/processes, and one chart showing trends/comparisons.

Output ONLY valid JSON. No markdown fences, no explanation.
""" + FEW_SHOT_EXAMPLES


def _build_brief_summary(brief: IngestedBrief) -> str:
    """Compress an IngestedBrief into a concise prompt for the LLM."""
    parts = []
    parts.append(f"Title: {brief.title}")
    if brief.bluf:
        parts.append(f"BLUF: {brief.bluf}")

    if brief.headline_judgments:
        parts.append("Key Judgments:")
        for j in brief.headline_judgments[:5]:
            kent = f" [{j.kent_band}]" if j.kent_band else ""
            parts.append(f"  - {j.claim}{kent}")

    if brief.sections:
        parts.append("Sections:")
        for s in brief.sections:
            parts.append(f"  - {s.title}")
            if s.subsections:
                for ss in s.subsections[:3]:
                    parts.append(f"    - {ss.title}")

    if brief.watch_items:
        parts.append("Watch Items:")
        for w in brief.watch_items[:3]:
            parts.append(f"  - {w.indicator}")

    if brief.trade_positions:
        parts.append("Trade Positions:")
        for t in brief.trade_positions[:3]:
            parts.append(f"  - {t.instrument}: {t.recommendation}")

    if brief.gaps:
        parts.append("Gaps:")
        for g in brief.gaps[:3]:
            parts.append(f"  - {g.description}")

    # Geographic context
    geo_sections = [s for s in brief.sections if s.geographic]
    if geo_sections:
        parts.append("Geographic Context:")
        for s in geo_sections[:3]:
            if s.geographic:
                parts.append(f"  - {s.title}: {json.dumps(s.geographic)}")

    return "\n".join(parts)


def _parse_plan_json(raw: str) -> dict:
    """Parse LLM output JSON, handling common formatting issues."""
    text = raw.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    return json.loads(text)


def _validate_routing(assets: list[dict]) -> list[str]:
    """Validate that no image-gen is routed to structured kinds."""
    errors = []
    for i, a in enumerate(assets):
        kind = a.get("kind", "")
        gen = a.get("generator", "")
        if kind in STRUCTURED_KINDS and gen in IMAGE_GEN_SET:
            errors.append(
                f"Asset {i} ({a.get('title', '')}): "
                f"image-gen '{gen}' cannot be used for kind '{kind}'"
            )
    return errors


def _fix_routing(assets: list[dict]) -> list[dict]:
    """Auto-fix routing violations by substituting the preferred generator."""
    fixed = []
    for a in assets:
        kind = a.get("kind", "")
        gen = a.get("generator", "")
        if kind in STRUCTURED_KINDS and gen in IMAGE_GEN_SET:
            # Substitute with first preferred generator for this kind
            preferred = ROUTING_TABLE.get(kind, [])
            if preferred:
                a["generator"] = preferred[0]
        fixed.append(a)
    return fixed


def plan_from_brief(
    brief: IngestedBrief,
    deliverables: Optional[list[str]] = None,
    max_assets: int = 8,
    auto_approve_free: bool = True,
) -> PresentationPlan:
    """Generate a PresentationPlan from an IngestedBrief using the LLM planner.

    Falls back to rule-based planning if LLM is unavailable.

    Args:
        brief: Parsed TREVOR brief.
        deliverables: Requested deliverable types (default: ["pdf"]).
        max_assets: Maximum number of assets to plan.
        auto_approve_free: Auto-approve if total cost is $0.

    Returns:
        PresentationPlan ready for cost estimation and approval.
    """
    if deliverables is None:
        deliverables = ["pdf"]

    brief_summary = _build_brief_summary(brief)

    # Try LLM-based planning first
    plan_json = None
    try:
        plan_json = _llm_plan(brief_summary, max_assets)
    except Exception:
        pass

    if plan_json is None:
        # Fall back to rule-based planning
        plan_json = _rule_based_plan(brief, max_assets)

    # Parse assets
    raw_assets = plan_json.get("assets", [])

    # Enforce routing rules
    raw_assets = _fix_routing(raw_assets)
    violations = _validate_routing(raw_assets)
    if violations:
        raise PlanValidationError(
            "Routing violations after fix: " + "; ".join(violations)
        )

    # Build AssetSpecs
    assets = []
    for a in raw_assets[:max_assets]:
        try:
            kind = AssetKind(a.get("kind", "diagram"))
        except ValueError:
            kind = AssetKind.DIAGRAM

        spec = AssetSpec(
            asset_id=a.get("asset_id", str(uuid4())[:8]),
            kind=kind,
            generator=a.get("generator", ROUTING_TABLE.get(kind.value, ["mermaid"])[0]),
            title=a.get("title", "Untitled"),
            prompt=a.get("prompt", ""),
            parameters=a.get("parameters", {}),
        )
        assets.append(spec)

    # Build deliverable list
    del_kinds = []
    for d in deliverables:
        try:
            del_kinds.append(DeliverableKind(d))
        except ValueError:
            pass
    if not del_kinds:
        del_kinds = [DeliverableKind.PDF]

    # Also add any deliverables from LLM output
    for d in plan_json.get("deliverables", []):
        try:
            dk = DeliverableKind(d)
            if dk not in del_kinds:
                del_kinds.append(dk)
        except ValueError:
            pass

    plan = PresentationPlan(
        brief_id=brief.brief_id or str(uuid4())[:12],
        assets=assets,
        deliverables=del_kinds,
        style_brief=plan_json.get("style_brief", ""),
    )

    # Estimate costs
    cost_est = estimate_plan(plan)

    # Auto-approve free plans
    if auto_approve_free and cost_est.total_cost_usd == 0.0:
        plan.approval_status = ApprovalStatus.AUTO_APPROVED
    elif not cost_est.requires_approval:
        plan.approval_status = ApprovalStatus.AUTO_APPROVED

    return plan


def _llm_plan(brief_summary: str, max_assets: int) -> dict:
    """Call LLM to generate a plan. Routes through TREVOR's llm_gate for Opus 4.7."""
    try:
        trevor_root = Path(__file__).resolve().parent.parent.parent
        sys.path.insert(0, str(trevor_root))
        
        # Route through gate for model selection
        from analyst.llm_gate import route
        gating = route("flagship_document", {"target_words": len(brief_summary.split()), "scenarios": 0})
        model = gating.model

        user_prompt = (
            f"Create a presentation plan for the following intelligence brief. "
            f"Maximum {max_assets} assets.\n\n{brief_summary}"
        )

        # Call via OpenRouter (supports all model formats)
        import urllib.request
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
            "max_tokens": 4096,
            "temperature": 0.3,
        }).encode()
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/trevormentis-spec"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        text = data["choices"][0]["message"]["content"]
        return _parse_plan_json(text)
    except Exception as exc:
        pass

    raise RuntimeError("LLM planning unavailable")


def _rule_based_plan(brief: IngestedBrief, max_assets: int) -> dict:
    """Deterministic fallback planner when LLM is unavailable.

    Generates a reasonable plan based on brief structure:
    - Has geographic sections → map
    - Has judgments → kent bar chart
    - Has sections → process diagram
    - Has watch items → timeline
    - Has trade positions → comparison chart
    - Always → cover illustration
    """
    assets = []

    # 1. Geographic map if applicable
    geo_sections = [s for s in brief.sections if s.geographic]
    if geo_sections and len(assets) < max_assets:
        geo = geo_sections[0].geographic or {}
        assets.append({
            "kind": "map",
            "generator": "mapbox_static",
            "title": f"Geographic Overview: {geo_sections[0].title}",
            "prompt": f"Map for {geo_sections[0].title}",
            "parameters": {
                "center": geo.get("center", [0, 0]),
                "zoom": geo.get("zoom", 5),
            },
        })

    # 2. Kent probability chart from judgments
    if brief.headline_judgments and len(assets) < max_assets:
        labels = [j.claim[:40] for j in brief.headline_judgments[:7]]
        # Map kent bands to numeric scores
        kent_scores = {
            "almost_certain": 9.5, "highly_likely": 8.5, "likely": 7.5,
            "probable": 6.5, "even_chance": 5.0, "unlikely": 3.5,
            "highly_unlikely": 2.0, "remote": 1.0,
        }
        values = [
            kent_scores.get(j.kent_band, 5.0)
            for j in brief.headline_judgments[:7]
        ]
        bands = [j.kent_band for j in brief.headline_judgments[:7]]
        assets.append({
            "kind": "chart",
            "generator": "matplotlib",
            "title": "Key Judgments: Confidence Distribution",
            "prompt": "Horizontal bar chart of judgment confidence bands",
            "parameters": {
                "chart_type": "kent_bar",
                "labels": labels,
                "values": values,
                "kent_bands": bands,
            },
        })

    # 3. Process/escalation diagram from sections
    if brief.sections and len(assets) < max_assets:
        section_titles = [s.title for s in brief.sections[:5]]
        mermaid_code = "graph TD\n"
        for i, t in enumerate(section_titles):
            node = t.replace(" ", "_")[:20]
            if i == 0:
                mermaid_code += f"    {node}[{t}]\n"
            else:
                prev = section_titles[i - 1].replace(" ", "_")[:20]
                mermaid_code += f"    {prev} --> {node}[{t}]\n"

        assets.append({
            "kind": "diagram",
            "generator": "mermaid",
            "title": "Analysis Structure",
            "prompt": mermaid_code,
        })

    # 4. Watch items timeline
    if brief.watch_items and len(assets) < max_assets:
        events = [
            {"date": "", "label": w.indicator, "kent_band": ""}
            for w in brief.watch_items[:8]
        ]
        assets.append({
            "kind": "diagram",
            "generator": "timeline",
            "title": "Indicators & Warnings Timeline",
            "prompt": "",
            "parameters": {"events": events},
        })

    # 5. Trade positions comparison
    if brief.trade_positions and len(assets) < max_assets:
        labels = [t.instrument[:30] for t in brief.trade_positions[:6]]
        values = [t.sizing_usd or 0 for t in brief.trade_positions[:6]]
        assets.append({
            "kind": "chart",
            "generator": "matplotlib",
            "title": "Trade/Hedge Position Sizing",
            "prompt": "Bar chart of position sizes",
            "parameters": {
                "chart_type": "bar",
                "labels": labels,
                "values": values,
            },
        })

    # 6. LDAP-7 if brief mentions a leader
    if len(assets) < max_assets:
        leader_name = brief.title.split(":")[0] if ":" in brief.title else brief.title
        assets.append({
            "kind": "chart",
            "generator": "ldap7_radar",
            "title": f"LDAP-7: {leader_name}",
            "prompt": "",
            "parameters": {
                "scores": [5, 5, 5, 5, 5, 5, 5],
                "leader_name": leader_name,
            },
        })

    # 7. Cover illustration
    if len(assets) < max_assets:
        assets.append({
            "kind": "illustration",
            "generator": "flux2pro",
            "title": f"Cover: {brief.title}",
            "prompt": (
                f"Professional intelligence report cover illustration for: {brief.title}. "
                f"Abstract, data-driven aesthetic. Dark background with accent lighting."
            ),
        })

    return {
        "assets": assets,
        "deliverables": ["pdf"],
    }
