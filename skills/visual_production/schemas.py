from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

VisualType = Literal[
    "logic_flow",
    "flow_chain",
    "map_plate",
    "matrix",
    "dashboard",
    "timeline",
    "comparison",
    "chart",
]

RenderEngine = Literal["nano_banana", "svg", "html", "hybrid"]

@dataclass
class SourceContent:
    title: str
    body: str
    audience: str = "briefing reader"

@dataclass
class VisualBrief:
    id: str
    title: str
    thesis: str
    visual_type: VisualType
    render_engine: RenderEngine
    flow: List[str] = field(default_factory=list)
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    map_places: List[str] = field(default_factory=list)
    data: List[Dict[str, Any]] = field(default_factory=list)
    caption: str = ""

@dataclass
class VisualProductionPlan:
    title: str
    strategy: str
    visuals: List[VisualBrief]

@dataclass
class ProducedVisual:
    id: str
    title: str
    visual_type: str
    render_engine: str
    asset_kind: str
    content: str
    caption: str = ""
