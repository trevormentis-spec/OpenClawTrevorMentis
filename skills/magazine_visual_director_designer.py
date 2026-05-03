"""Magazine Visual Director + Designer skill for OpenClaw/MyClaw.

Roles:
- Art Director: chooses what visuals should exist and why.
- Designer: converts visual briefs into renderable asset specs.

Default model routing:
- Art Director: Claude Opus 4.7 via OpenRouter
- Designer: DeepSeek V4 Pro via DeepSeek API
- Critic: DeepSeek V4 Pro via DeepSeek API
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import json
import uuid


DEFAULT_DESIGN_SYSTEM: Dict[str, Any] = {
    "voice": "clear, intelligent, magazine-grade",
    "style": "premium editorial, minimal, information-dense but uncluttered",
    "palette": {
        "ink": "#111827",
        "muted_ink": "#4B5563",
        "paper": "#F8F5EF",
        "white": "#FFFFFF",
        "primary": "#0A2540",
        "accent": "#D97706",
        "grid": "#D1D5DB",
    },
    "rules": [
        "Every visual must answer one editorial question.",
        "Prefer structured graphics over decorative images.",
        "Use image generation only for conceptual illustrations.",
        "Charts and maps need explicit data or must be marked illustrative.",
    ],
}


class VisualType(str, Enum):
    DIAGRAM = "diagram"
    INFOGRAPHIC = "infographic"
    CHART = "chart"
    MAP = "map"
    ILLUSTRATION = "illustration"
    TIMELINE = "timeline"
    TABLE_GRAPHIC = "table_graphic"


class RenderMode(str, Enum):
    SVG = "svg"
    MERMAID = "mermaid"
    CHART_JSON = "chart_json"
    MAP_JSON = "map_json"
    IMAGE_PROMPT = "image_prompt"
    HTML = "html"


@dataclass
class SourceContent:
    title: str
    body: str
    audience: str = "intelligent general reader"
    format: Literal["article", "brief", "report", "script", "unknown"] = "article"
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualBrief:
    id: str
    type: VisualType
    title: str
    editorial_question: str
    purpose: str
    placement: str
    audience_takeaway: str
    complexity: Literal["low", "medium", "high"]
    data_requirements: List[str]
    content_requirements: List[str]
    style_notes: List[str]
    caption_draft: str
    must_not_do: List[str] = field(default_factory=list)


@dataclass
class VisualPlan:
    article_title: str
    visual_strategy: str
    visuals: List[VisualBrief]
    rejected_visuals: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AssetSpec:
    id: str
    brief_id: str
    type: VisualType
    render_mode: RenderMode
    title: str
    caption: str
    spec: Dict[str, Any]
    alt_text: str
    quality_checks: List[str]


@dataclass
class SkillResult:
    plan: VisualPlan
    assets: List[AssetSpec]
    notes: List[str]


class LLMClient:
    ART_DIRECTOR_MODEL = "openrouter/anthropic/claude-opus-4.7"
    DESIGNER_MODEL = "deepseek/deepseek-v4-pro"
    CRITIC_MODEL = "deepseek/deepseek-v4-pro"

    def complete_json(self, *, system: str, user: str, schema_hint: Dict[str, Any], model: str) -> Dict[str, Any]:
        raise NotImplementedError("Wire this method to the OpenClaw/MyClaw model router.")


ART_DIRECTOR_SYSTEM = """You are a magazine art director. Decide which visuals make the piece clearer, sharper, and more memorable. Prefer diagrams, charts, maps, timelines, and structured infographics over generic illustration. Return strict JSON only."""

DESIGNER_SYSTEM = """You are a senior editorial information designer. Convert a structured visual brief into a renderable asset specification. Prefer SVG, Mermaid, chart JSON, map JSON, or HTML for structured visuals. Use image prompts only for conceptual illustrations. Return strict JSON only."""

CRITIC_SYSTEM = """You are a strict magazine design critic. Review for usefulness, clarity, accuracy risk, and editorial quality. Return strict JSON only."""


class MagazineVisualSkill:
    def __init__(self, llm: LLMClient, design_system: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.design_system = design_system or DEFAULT_DESIGN_SYSTEM

    def run(
        self,
        content: SourceContent,
        *,
        max_visuals: int = 3,
        art_director_model: str = LLMClient.ART_DIRECTOR_MODEL,
        designer_model: str = LLMClient.DESIGNER_MODEL,
        run_critic: bool = True,
    ) -> SkillResult:
        plan = self.create_visual_plan(content, max_visuals=max_visuals, model=art_director_model)
        assets = [self.create_asset_spec(b, content, model=designer_model) for b in plan.visuals]
        notes = self.critic_notes(plan, assets, content) if run_critic else []
        return SkillResult(plan=plan, assets=assets, notes=notes)

    def create_visual_plan(self, content: SourceContent, *, max_visuals: int, model: str) -> VisualPlan:
        prompt = {
            "task": "Create a magazine-level visual plan.",
            "content": asdict(content),
            "design_system": self.design_system,
            "max_visuals": max_visuals,
            "return_shape": {
                "article_title": "string",
                "visual_strategy": "string",
                "visuals": [{
                    "id": "v1",
                    "type": "diagram|infographic|chart|map|illustration|timeline|table_graphic",
                    "title": "string",
                    "editorial_question": "string",
                    "purpose": "string",
                    "placement": "string",
                    "audience_takeaway": "string",
                    "complexity": "low|medium|high",
                    "data_requirements": ["string"],
                    "content_requirements": ["string"],
                    "style_notes": ["string"],
                    "caption_draft": "string",
                    "must_not_do": ["string"],
                }],
                "rejected_visuals": [{"idea": "string", "reason": "string"}],
            },
        }
        raw = self.llm.complete_json(system=ART_DIRECTOR_SYSTEM, user=json.dumps(prompt), schema_hint={"type": "VisualPlan"}, model=model)
        return parse_visual_plan(raw)

    def create_asset_spec(self, brief: VisualBrief, content: SourceContent, *, model: str) -> AssetSpec:
        prompt = {
            "task": "Convert this brief into a renderable asset specification.",
            "source_title": content.title,
            "design_system": self.design_system,
            "brief": to_dict(brief),
            "rendering_rules": {
                "diagram": "prefer mermaid or svg",
                "infographic": "prefer svg or html",
                "chart": "prefer chart_json",
                "map": "prefer map_json",
                "illustration": "use image_prompt",
                "timeline": "prefer svg or html",
                "table_graphic": "prefer html or svg",
            },
        }
        raw = self.llm.complete_json(system=DESIGNER_SYSTEM, user=json.dumps(prompt), schema_hint={"type": "AssetSpec"}, model=model)
        return parse_asset_spec(raw)

    def critic_notes(self, plan: VisualPlan, assets: List[AssetSpec], content: SourceContent) -> List[str]:
        prompt = {
            "task": "Flag important issues only.",
            "content_title": content.title,
            "plan": to_dict(plan),
            "assets": [to_dict(a) for a in assets],
        }
        raw = self.llm.complete_json(system=CRITIC_SYSTEM, user=json.dumps(prompt), schema_hint={"type": "CriticNotes"}, model=LLMClient.CRITIC_MODEL)
        return raw.get("notes", [])


class SimpleRenderer:
    def render(self, asset: AssetSpec) -> str:
        if asset.render_mode == RenderMode.MERMAID:
            return "```mermaid\n" + (asset.spec.get("mermaid") or asset.spec.get("code") or "graph TD") + "\n```"
        if asset.render_mode in {RenderMode.CHART_JSON, RenderMode.MAP_JSON}:
            return json.dumps(asset.spec, indent=2)
        if asset.render_mode == RenderMode.IMAGE_PROMPT:
            return asset.spec.get("prompt", json.dumps(asset.spec, indent=2))
        if asset.render_mode == RenderMode.HTML:
            return asset.spec.get("html", f"<figure><h2>{asset.title}</h2><figcaption>{asset.caption}</figcaption></figure>")
        if asset.render_mode == RenderMode.SVG:
            return asset.spec.get("svg", fallback_svg(asset))
        raise ValueError(f"Unsupported render mode: {asset.render_mode}")


def parse_visual_plan(raw: Dict[str, Any]) -> VisualPlan:
    visuals = []
    for i, item in enumerate(raw.get("visuals", []), 1):
        visuals.append(VisualBrief(
            id=item.get("id") or f"v{i}",
            type=VisualType(item["type"]),
            title=item["title"],
            editorial_question=item["editorial_question"],
            purpose=item["purpose"],
            placement=item["placement"],
            audience_takeaway=item["audience_takeaway"],
            complexity=item.get("complexity", "medium"),
            data_requirements=item.get("data_requirements", []),
            content_requirements=item.get("content_requirements", []),
            style_notes=item.get("style_notes", []),
            caption_draft=item.get("caption_draft", ""),
            must_not_do=item.get("must_not_do", []),
        ))
    return VisualPlan(raw.get("article_title", "Untitled"), raw.get("visual_strategy", ""), visuals, raw.get("rejected_visuals", []))


def parse_asset_spec(raw: Dict[str, Any]) -> AssetSpec:
    return AssetSpec(
        id=raw.get("id") or f"asset_{uuid.uuid4().hex[:8]}",
        brief_id=raw["brief_id"],
        type=VisualType(raw["type"]),
        render_mode=RenderMode(raw["render_mode"]),
        title=raw["title"],
        caption=raw.get("caption", ""),
        spec=raw.get("spec", {}),
        alt_text=raw.get("alt_text", ""),
        quality_checks=raw.get("quality_checks", []),
    )


def to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(getattr(obj, k)) for k in obj.__dataclass_fields__}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


def fallback_svg(asset: AssetSpec) -> str:
    title = asset.title.replace("&", "&amp;").replace("<", "&lt;")
    caption = asset.caption.replace("&", "&amp;").replace("<", "&lt;")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <rect width="1200" height="800" fill="#F8F5EF"/>
  <rect x="64" y="64" width="1072" height="672" rx="18" fill="#FFFFFF" stroke="#D1D5DB" stroke-width="2"/>
  <text x="96" y="140" font-family="Inter, Helvetica, Arial" font-size="42" font-weight="700" fill="#111827">{title}</text>
  <text x="96" y="700" font-family="Inter, Helvetica, Arial" font-size="24" fill="#4B5563">{caption}</text>
</svg>'''
