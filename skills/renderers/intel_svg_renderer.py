from typing import Dict, List

class VisualQualityError(Exception):
    pass

class IntelSVGRenderer:
    """Deterministic SVG renderer for intelligence-grade visuals."""

    def render_escalation_chain(self, title: str, steps: List[str]) -> str:
        if not steps or len(steps) < 2:
            raise VisualQualityError("Escalation chain requires at least 2 steps")

        width = 1200
        height = 200 + len(steps) * 120

        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        svg.append('<rect width="100%" height="100%" fill="#0A2540"/>')
        svg.append(f'<text x="50" y="60" fill="white" font-size="36">{title}</text>')

        y = 120
        for i, step in enumerate(steps):
            svg.append(f'<rect x="50" y="{y}" width="900" height="70" rx="12" fill="#1E3A5F"/>')
            svg.append(f'<text x="70" y="{y+45}" fill="white" font-size="20">{i+1}. {step}</text>')

            if i < len(steps) - 1:
                svg.append(f'<line x1="500" y1="{y+70}" x2="500" y2="{y+120}" stroke="white" stroke-width="2"/>')

            y += 120

        svg.append('</svg>')
        return "\n".join(svg)

    def validate_no_raw_code(self, asset_spec: Dict):
        bad_patterns = ["graph TD", "```mermaid", "| Indicator |", "-->" ]
        content = str(asset_spec)
        for pattern in bad_patterns:
            if pattern in content:
                raise VisualQualityError(f"Raw visual code detected: {pattern}")
