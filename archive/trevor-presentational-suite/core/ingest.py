"""TPS Ingest — parse TREVOR JSON/PDF/markdown into typed IngestedBrief.

This is the bridge between TREVOR's native output and TPS. Handles multiple
JSON formats found in the codebase:
  1. Schema v1.1.0 structured brief (Bajio-style)
  2. Full assessment (key_judgments, pmesii_pt, ach_matrix)
  3. Agent brief (theatres with key_judgments and indicators)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from .exceptions import IngestError
from .schemas import (
    IngestedBrief,
    IngestSection,
    IngestSubsection,
    IngestJudgment,
    IngestSource,
    IngestWatchItem,
    IngestTradePosition,
    IngestGap,
    IngestActionLine,
)


def ingest_json(path_or_data: Union[str, Path, dict]) -> IngestedBrief:
    """Parse a TREVOR brief JSON into an IngestedBrief.

    Accepts a file path (str or Path) or a pre-loaded dict.
    """
    if isinstance(path_or_data, dict):
        raw = path_or_data
    else:
        p = Path(path_or_data)
        if not p.exists():
            raise IngestError(f"File not found: {p}")
        try:
            raw = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            raise IngestError(f"Invalid JSON: {e}") from e

    # Detect format and dispatch
    if "theatres" in raw:
        return _parse_agent_brief(raw)
    if "pmesii_pt" in raw or "ach_matrix" in raw:
        return _parse_full_assessment(raw)
    return _parse_structured_brief(raw)


def ingest_pdf(path: Union[str, Path]) -> IngestedBrief:
    """Extract text from a TREVOR PDF. Stub — deferred to Milestone 2."""
    raise IngestError("PDF ingest not yet implemented (Milestone 2)")


def ingest_markdown(path: Union[str, Path]) -> IngestedBrief:
    """Parse a markdown brief. Stub — deferred to Milestone 2."""
    raise IngestError("Markdown ingest not yet implemented (Milestone 2)")


# ── Private parsers ──────────────────────────────────────────────────────────


def _parse_calibration(cal) -> tuple[str, list[int]]:
    """Extract band and pct_range from calibration field."""
    if isinstance(cal, dict):
        band = cal.get("band", "")
        pct = cal.get("pct_range", [0, 0])
        if isinstance(pct, list) and len(pct) >= 2:
            return band, [int(pct[0]), int(pct[1])]
        return band, [0, 0]
    if isinstance(cal, str):
        return cal, [0, 0]
    return "", [0, 0]


def _parse_source(raw: dict) -> IngestSource:
    """Parse a source reference."""
    return IngestSource(
        id=str(raw.get("id", raw.get("source_id", ""))),
        name=raw.get("name", ""),
        admiralty=raw.get("admiralty", raw.get("source_rating", "")),
        source_type=raw.get("type", raw.get("source_type", "")),
        language=raw.get("language", ""),
        url=raw.get("url", ""),
        themes=raw.get("themes", []),
    )


def _parse_judgment(raw: dict) -> IngestJudgment:
    """Parse a judgment, handling both claim/kent_band and judgment/confidence formats."""
    claim = raw.get("claim", raw.get("judgment", raw.get("statement", "")))
    kent_band = raw.get("kent_band", raw.get("confidence", raw.get("confidence_band", raw.get("band", ""))))
    pct_range = raw.get("pct_range", [0, 0])

    # Handle probability_lower/probability_upper format
    if pct_range == [0, 0]:
        lo = raw.get("probability_lower", 0)
        hi = raw.get("probability_upper", 0)
        if lo or hi:
            pct_range = [int(lo), int(hi)]

    sources_raw = raw.get("sources", [])
    sources = []
    for s in sources_raw:
        if isinstance(s, dict):
            sources.append(_parse_source(s))
        elif isinstance(s, str):
            sources.append(IngestSource(name=s))

    return IngestJudgment(
        id=str(raw.get("id", "")),
        claim=claim,
        kent_band=kent_band,
        pct_range=pct_range if isinstance(pct_range, list) else [0, 0],
        horizon_end=raw.get("horizon_end", raw.get("horizon", "")),
        sources=sources,
        subscriber_action=raw.get("subscriber_action", ""),
    )


def _parse_subsection(raw: dict) -> IngestSubsection:
    """Parse a subsection."""
    judgments = [_parse_judgment(j) for j in raw.get("judgments", [])]
    return IngestSubsection(
        id=str(raw.get("id", "")),
        title=raw.get("title", ""),
        narrative=raw.get("narrative", ""),
        judgments=judgments,
        subscriber_action=raw.get("subscriber_action", ""),
        themes=raw.get("themes", []),
    )


def _parse_section(raw: dict) -> IngestSection:
    """Parse a section with optional subsections."""
    subsections = [_parse_subsection(s) for s in raw.get("subsections", [])]
    judgments = [_parse_judgment(j) for j in raw.get("judgments", [])]
    return IngestSection(
        id=str(raw.get("id", "")),
        title=raw.get("title", ""),
        narrative=raw.get("narrative", ""),
        subsections=subsections,
        judgments=judgments,
        geographic=raw.get("geographic"),
        themes=raw.get("themes", []),
    )


def _parse_structured_brief(raw: dict) -> IngestedBrief:
    """Parse schema v1.1.0 structured brief (Bajio-style)."""
    cal_band, cal_pct = _parse_calibration(raw.get("calibration"))

    headline_judgments = [
        _parse_judgment(j)
        for j in raw.get("headline_judgments", raw.get("judgments", []))
    ]
    sections = [_parse_section(s) for s in raw.get("sections", [])]
    watch_items = [
        IngestWatchItem(
            id=str(w.get("id", "")),
            indicator=w.get("indicator", ""),
            trigger=w.get("trigger", ""),
            signal=w.get("signal", ""),
            upgrade_signal=w.get("upgrade_signal", ""),
            downgrade_signal=w.get("downgrade_signal", ""),
        )
        for w in raw.get("watch_items", [])
    ]
    trade_positions = [
        IngestTradePosition(
            id=str(t.get("id", "")),
            instrument=t.get("instrument", ""),
            instrument_type=t.get("instrument_type", ""),
            strike=str(t.get("strike", "")),
            price=t.get("price"),
            price_as_of=str(t.get("price_as_of", "")),
            recommendation=t.get("recommendation", ""),
            sizing_usd=t.get("sizing_usd"),
            sizing_methodology=t.get("sizing_methodology", ""),
            rationale=t.get("rationale", ""),
            is_proxy=bool(t.get("is_proxy", False)),
        )
        for t in raw.get("trade_positions", [])
    ]
    gaps = [
        IngestGap(
            id=str(g.get("id", "")),
            description=g.get("description", ""),
            impact=g.get("impact", ""),
            next_step=g.get("next_step", ""),
            estimated_cost=g.get("estimated_cost", ""),
            timeline=g.get("timeline", ""),
        )
        for g in raw.get("gaps", [])
    ]
    action_lines = [
        IngestActionLine(
            id=str(a.get("id", "")),
            priority=int(a.get("priority", 3)),
            action=a.get("action", ""),
            timeframe=a.get("timeframe", ""),
            rationale=a.get("rationale", ""),
        )
        for a in raw.get("action_lines", [])
    ]
    sources = [_parse_source(s) for s in raw.get("sources", [])]

    return IngestedBrief(
        brief_id=raw.get("brief_id", ""),
        schema_version=raw.get("schema_version", ""),
        title=raw.get("title", ""),
        query_type=raw.get("query_type", ""),
        produced_at=raw.get("produced_at", ""),
        producer=raw.get("producer", ""),
        bluf=raw.get("bluf", ""),
        calibration_band=cal_band,
        calibration_pct_range=cal_pct,
        headline_judgments=headline_judgments,
        sections=sections,
        watch_items=watch_items,
        trade_positions=trade_positions,
        gaps=gaps,
        action_lines=action_lines,
        sources=sources,
        meta=raw.get("meta", {}),
        generation_metadata=raw.get("generation_metadata", {}),
        raw=raw,
    )


def _parse_full_assessment(raw: dict) -> IngestedBrief:
    """Parse full-assessment.json format with pmesii_pt, ach_matrix, scenarios."""
    brief = _parse_structured_brief(raw)

    # Flatten key_judgments if present (uses different field names)
    if "key_judgments" in raw and not brief.headline_judgments:
        brief.headline_judgments = [
            _parse_judgment(j) for j in raw["key_judgments"]
        ]

    # PMESII-PT dimensions become sections if no sections parsed
    if not brief.sections and "pmesii_pt" in raw:
        pmesii = raw["pmesii_pt"]
        if isinstance(pmesii, dict):
            for dim_name, dim_data in pmesii.items():
                narrative = dim_data if isinstance(dim_data, str) else str(dim_data)
                brief.sections.append(IngestSection(
                    title=f"PMESII-PT: {dim_name.upper()}",
                    narrative=narrative,
                ))

    return brief


def _parse_agent_brief(raw: dict) -> IngestedBrief:
    """Parse agent brief format with theatres and cross_cutting_analysis."""
    # Cross-cutting analysis
    cross = raw.get("cross_cutting_analysis", {})
    bluf = cross.get("bluf", raw.get("bluf", ""))

    # Gather key judgments from cross-cutting and theatres
    all_judgments: list[IngestJudgment] = []
    for kj in cross.get("key_judgments", []):
        all_judgments.append(_parse_judgment(kj))

    # Convert theatres to sections
    sections: list[IngestSection] = []
    for theatre in raw.get("theatres", []):
        subsections = []
        for kj in theatre.get("key_judgments", []):
            all_judgments.append(_parse_judgment(kj))

        section = IngestSection(
            title=theatre.get("section_title", theatre.get("region_label", "")),
            narrative=theatre.get("narrative", theatre.get("story", "")),
        )
        sections.append(section)

    # Methodology metadata
    methodology = raw.get("methodology", {})
    sources = [_parse_source(s) for s in methodology.get("sources", [])]

    return IngestedBrief(
        brief_id=raw.get("brief_id", ""),
        schema_version=raw.get("schema", ""),
        title=raw.get("title", ""),
        produced_at=raw.get("published", raw.get("produced_at", "")),
        bluf=bluf,
        headline_judgments=all_judgments,
        sections=sections,
        sources=sources,
        meta=raw.get("meta", {}),
        raw=raw,
    )
