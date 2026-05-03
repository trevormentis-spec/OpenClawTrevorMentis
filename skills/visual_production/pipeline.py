from .router import VisualRouter
from .prompt_builder import build_image_prompt
from .quality_gate import validate_text_output
from .schemas import ProducedVisual

class MagazineVisualProductionSkill:
    def __init__(self, nano_client=None):
        self.router = VisualRouter()
        self.nano_client = nano_client

    def run(self, plan):
        results = []

        for brief in plan.visuals:
            route = self.router.route(brief)

            if route == 'nano':
                prompt = build_image_prompt(brief)
                validate_text_output(prompt)

                image = self.nano_client.generate(prompt) if self.nano_client else prompt

                results.append(
                    ProducedVisual(
                        id=brief.id,
                        title=brief.title,
                        visual_type=brief.visual_type,
                        render_engine='nano_banana',
                        asset_kind='image_prompt' if not self.nano_client else 'image',
                        content=image,
                        caption=brief.thesis
                    )
                )

            elif route == 'svg':
                svg = '<svg width="1200" height="400"><rect width="100%" height="100%" fill="#0A2540"/></svg>'
                results.append(
                    ProducedVisual(
                        id=brief.id,
                        title=brief.title,
                        visual_type=brief.visual_type,
                        render_engine='svg',
                        asset_kind='svg',
                        content=svg
                    )
                )

            else:
                results.append(
                    ProducedVisual(
                        id=brief.id,
                        title=brief.title,
                        visual_type=brief.visual_type,
                        render_engine='hybrid',
                        asset_kind='mixed',
                        content=''
                    )
                )

        return results
