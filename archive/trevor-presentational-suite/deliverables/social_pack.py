"""TPS Social Pack Builder — LinkedIn carousel, X thread, IG card.

Produces a directory of social-media-ready assets from a TREVOR brief
and its generated visual primitives.
"""
from __future__ import annotations

import os
import json
from typing import Optional

from core.schemas import (
    PresentationPlan,
    AssetProvenance,
    DeliverableKind,
    IngestedBrief,
)
from core.style_director import get_brand, inject_brand_css
from deliverables.base import BaseDeliverableBuilder


class SocialPackBuilder(BaseDeliverableBuilder):
    """Build social media pack: LinkedIn carousel, X thread, IG card."""

    @property
    def kind(self) -> DeliverableKind:
        return DeliverableKind.SOCIAL_PACK

    def build(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
        provenance_records: list[AssetProvenance],
        output_path: str,
    ) -> str:
        os.makedirs(output_path, exist_ok=True)
        brand = get_brand()

        title = brief_json.get("title", "Intelligence Brief")
        bluf = brief_json.get("bluf", "")
        judgments = brief_json.get("headline_judgments", [])

        # 1. LinkedIn Carousel (HTML slides)
        self._build_linkedin_carousel(
            output_path, title, bluf, judgments, asset_outputs, brand
        )

        # 2. X Thread (text file)
        self._build_x_thread(
            output_path, title, bluf, judgments
        )

        # 3. Instagram Card (HTML)
        self._build_ig_card(
            output_path, title, bluf, brand
        )

        # 4. Manifest
        manifest = {
            "deliverable": "social_pack",
            "brief_title": title,
            "files": {
                "linkedin_carousel": "linkedin_carousel.html",
                "x_thread": "x_thread.txt",
                "ig_card": "ig_card.html",
            },
            "asset_count": len(asset_outputs),
            "qc_status": "PENDING HUMAN ANALYST QC REVIEW",
        }
        manifest_path = os.path.join(output_path, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return output_path

    def _build_linkedin_carousel(
        self, output_dir, title, bluf, judgments, asset_outputs, brand
    ):
        """Generate LinkedIn carousel as multi-slide HTML."""
        slides = []

        # Title slide
        slides.append(f"""
        <div class="slide" style="background:{brand.color_primary};color:white;padding:40px;">
            <h1 style="font-size:28px;margin-bottom:20px;">{title}</h1>
            <p style="font-size:16px;opacity:0.9;">{bluf[:200]}</p>
            <div style="margin-top:40px;font-size:12px;opacity:0.6;">
                Trevor Intelligence | PENDING HUMAN ANALYST QC REVIEW
            </div>
        </div>""")

        # Judgment slides (one per judgment, max 5)
        for j in judgments[:5]:
            claim = j.get("claim", j.get("judgment", ""))
            kent = j.get("kent_band", "")
            slides.append(f"""
        <div class="slide" style="background:white;padding:40px;border-left:4px solid {brand.color_accent};">
            <div style="font-size:11px;color:{brand.color_accent};text-transform:uppercase;margin-bottom:12px;">
                Key Judgment — {kent.replace('_', ' ').title() if kent else 'Assessment'}
            </div>
            <p style="font-size:18px;color:{brand.color_body};line-height:1.6;">{claim}</p>
        </div>""")

        # Asset slides
        for asset_id, path in list(asset_outputs.items())[:3]:
            if path.endswith(('.png', '.jpg', '.svg')):
                slides.append(f"""
        <div class="slide" style="background:#F5F3EF;padding:20px;text-align:center;">
            <img src="{path}" style="max-width:100%;max-height:90%;object-fit:contain;" />
        </div>""")

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{font-family:Inter,sans-serif;margin:0;padding:20px;background:#f0f0f0;}}
.slide {{
    width:1200px;height:627px;margin:20px auto;
    display:flex;flex-direction:column;justify-content:center;
    box-sizing:border-box;box-shadow:0 2px 8px rgba(0,0,0,0.15);
}}
h1 {{margin:0;}} p {{margin:0;}}
</style></head><body>
{"".join(slides)}
</body></html>"""

        path = os.path.join(output_dir, "linkedin_carousel.html")
        with open(path, "w") as f:
            f.write(html)

    def _build_x_thread(self, output_dir, title, bluf, judgments):
        """Generate X/Twitter thread as text file."""
        tweets = []

        # Thread opener
        tweets.append(
            f"THREAD: {title}\n\n"
            f"{bluf[:240]}\n\n"
            f"Key findings below"
        )

        # One tweet per judgment
        for i, j in enumerate(judgments[:6], 1):
            claim = j.get("claim", j.get("judgment", ""))
            kent = j.get("kent_band", "")
            band_label = kent.replace("_", " ").title() if kent else ""
            tweet = f"{i}/{len(judgments[:6])} "
            if band_label:
                tweet += f"[{band_label}] "
            tweet += claim[:260]
            tweets.append(tweet)

        # Closer
        tweets.append(
            f"Full analysis available via Trevor Intelligence.\n\n"
            f"PENDING HUMAN ANALYST QC REVIEW"
        )

        thread_text = "\n\n---\n\n".join(tweets)
        path = os.path.join(output_dir, "x_thread.txt")
        with open(path, "w") as f:
            f.write(thread_text)

    def _build_ig_card(self, output_dir, title, bluf, brand):
        """Generate Instagram-format summary card (1080x1080 HTML)."""
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{
    margin:0;padding:0;
    width:1080px;height:1080px;
    font-family:Inter,sans-serif;
    background:linear-gradient(135deg, {brand.color_primary} 0%, {brand.color_body} 100%);
    color:white;
    display:flex;flex-direction:column;justify-content:center;
    padding:80px;box-sizing:border-box;
}}
h1 {{font-size:36px;margin-bottom:24px;line-height:1.3;}}
p {{font-size:18px;opacity:0.85;line-height:1.6;}}
.footer {{
    position:absolute;bottom:40px;left:80px;right:80px;
    font-size:11px;opacity:0.5;
    display:flex;justify-content:space-between;
}}
</style></head><body>
<h1>{title}</h1>
<p>{bluf[:300]}</p>
<div class="footer">
    <span>Trevor Intelligence</span>
    <span>PENDING HUMAN ANALYST QC REVIEW</span>
</div>
</body></html>"""

        path = os.path.join(output_dir, "ig_card.html")
        with open(path, "w") as f:
            f.write(html)
