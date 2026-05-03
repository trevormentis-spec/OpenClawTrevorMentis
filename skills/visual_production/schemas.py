from dataclasses import dataclass
from typing import List, Dict, Literal

@dataclass
class SourceContent:
    title: str
    body: str

@dataclass
class VisualBrief:
    id: str
    visual_thesis: str
    visual_type: Literal["escalation_chain", "map", "infographic", "dashboard"]
    output_mode: Literal["nano", "svg", "hybrid"]
    elements: List[str]

@dataclass
class VisualProductionPlan:
    title: str
    visuals: List[VisualBrief]

@dataclass
class ProducedVisual:
    id: str
    type: str
    output_path: str
