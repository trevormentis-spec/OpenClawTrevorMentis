"""TPS Briefing Video Builder — full video intelligence briefing.

Assembles generated assets into a structured video:
  1. Title card (5s)
  2. BLUF narration over cover image
  3. Key judgments with supporting visuals
  4. Section-by-section walkthrough
  5. Closing card with QC watermark

Uses FFmpeg assembly module for video composition.
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

from core.schemas import (
    PresentationPlan,
    AssetProvenance,
    AssetKind,
    DeliverableKind,
)
from core.style_director import get_brand
from core.exceptions import GeneratorError
from deliverables.base import BaseDeliverableBuilder
from generators.assembly import (
    is_available as ffmpeg_available,
    AssemblySpec,
    MediaSegment,
    create_title_card,
    assemble,
)


class BriefingVideoBuilder(BaseDeliverableBuilder):
    """Build a full briefing video from generated assets."""

    @property
    def kind(self) -> DeliverableKind:
        return DeliverableKind.BRIEFING_VIDEO

    def build(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
        provenance_records: list[AssetProvenance],
        output_path: str,
    ) -> str:
        if not ffmpeg_available():
            raise GeneratorError(
                "FFmpeg not installed — required for briefing video assembly"
            )

        brand = get_brand()
        title = brief_json.get("title", "Intelligence Brief")
        bluf = brief_json.get("bluf", "")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        segments = []
        narration_path = None
        music_path = None

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Title card
            title_card = os.path.join(tmpdir, "title_card.mp4")
            try:
                create_title_card(
                    text=title,
                    output_path=title_card,
                    duration_sec=5.0,
                    bg_color=f"0x{brand.color_primary.lstrip('#')}",
                )
                segments.append(MediaSegment(
                    path=title_card, media_type="video", label="Title"
                ))
            except Exception:
                pass

            # 2. Collect visual assets as segments
            for asset_id, path in asset_outputs.items():
                if not os.path.exists(path):
                    continue

                # Find the asset spec for context
                asset_spec = None
                for spec in plan.assets:
                    if spec.asset_id == asset_id:
                        asset_spec = spec
                        break

                if path.endswith(('.mp4', '.webm', '.mov')):
                    segments.append(MediaSegment(
                        path=path, media_type="video",
                        label=asset_spec.title if asset_spec else asset_id,
                    ))
                elif path.endswith(('.mp3', '.wav', '.ogg')):
                    # Audio assets: use as narration or music
                    if asset_spec and asset_spec.generator in ("elevenlabs", "openai_tts"):
                        narration_path = path
                    elif asset_spec and asset_spec.generator == "suno":
                        music_path = path
                elif path.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    segments.append(MediaSegment(
                        path=path, media_type="image",
                        duration_sec=5.0,
                        label=asset_spec.title if asset_spec else asset_id,
                    ))

            # 3. Closing card
            closing_card = os.path.join(tmpdir, "closing_card.mp4")
            try:
                create_title_card(
                    text="PENDING HUMAN ANALYST QC REVIEW",
                    output_path=closing_card,
                    duration_sec=3.0,
                    bg_color=f"0x{brand.color_primary.lstrip('#')}",
                    font_size=36,
                )
                segments.append(MediaSegment(
                    path=closing_card, media_type="video", label="QC Card"
                ))
            except Exception:
                pass

            if not segments:
                raise GeneratorError("No visual segments available for video assembly")

            # 4. Assemble
            spec = AssemblySpec(
                segments=segments,
                narration_audio=narration_path,
                background_audio=music_path,
                output_width=1920,
                output_height=1080,
            )

            assemble(spec, output_path)

        return output_path
