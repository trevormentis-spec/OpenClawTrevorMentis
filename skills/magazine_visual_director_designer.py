# DEPRECATED: use skills.visual_production instead

from skills.visual_production.pipeline import MagazineVisualProductionSkill

class MagazineVisualSkill:
    def __init__(self, llm=None):
        self.engine = MagazineVisualProductionSkill()

    def run(self, content):
        raise Exception(
            "MagazineVisualSkill is deprecated. Use skills.visual_production instead."
        )
