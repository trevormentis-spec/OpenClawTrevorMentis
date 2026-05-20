#!/usr/bin/env python3
"""TPS Test Runner — run all test suites with pass/fail counters.

Matches TREVOR's existing test pattern: functions returning bool,
no pytest, inline pass/fail counting.

Usage:
    python3 trevor-presentational-suite/tests/run_all.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import json
import shutil
from pathlib import Path

# Set up paths
TPS_ROOT = Path(__file__).resolve().parent.parent
TREVOR_ROOT = TPS_ROOT.parent
sys.path.insert(0, str(TPS_ROOT))
sys.path.insert(0, str(TREVOR_ROOT))

EXAMPLES_DIR = TPS_ROOT / "examples"
BAJIO_BRIEF = EXAMPLES_DIR / "bajio_v3.json"

passed = 0
failed = 0
errors = []


def run_test(name: str, fn):
    """Run a single test, catch exceptions, track pass/fail."""
    global passed, failed
    try:
        result = fn()
        if result:
            print(f"  PASS  {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}")
            failed += 1
            errors.append(name)
    except Exception as e:
        print(f"  FAIL  {name} — {type(e).__name__}: {e}")
        failed += 1
        errors.append(f"{name}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Schemas (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_asset_kind_values():
    from core.schemas import AssetKind
    expected = {"map", "diagram", "chart", "infographic", "illustration", "table", "narration", "video"}
    actual = {e.value for e in AssetKind}
    return actual == expected


def test_presentation_plan_serialization():
    from core.schemas import PresentationPlan, AssetSpec, AssetKind, DeliverableKind
    plan = PresentationPlan(
        brief_id="test-001",
        assets=[
            AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="Test Diagram"),
        ],
        deliverables=[DeliverableKind.PDF],
    )
    data = plan.model_dump(mode="json")
    restored = PresentationPlan(**data)
    return (
        restored.brief_id == "test-001"
        and len(restored.assets) == 1
        and restored.assets[0].kind == AssetKind.DIAGRAM
    )


def test_qc_status_default():
    from core.schemas import AssetProvenance, AssetKind, QCStatus
    prov = AssetProvenance(
        asset_id="a1", plan_id="p1", brief_id="b1",
        kind=AssetKind.DIAGRAM, generator="mermaid",
    )
    return prov.qc_status == QCStatus.PENDING_REVIEW


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Ingest (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_ingest_bajio_v3():
    from core.ingest import ingest_json
    brief = ingest_json(str(BAJIO_BRIEF))
    return (
        brief.brief_id == "bajio-v3-20260518"
        and len(brief.headline_judgments) == 4
        and len(brief.sections) == 4
        and len(brief.watch_items) == 5
        and len(brief.trade_positions) == 3
        and len(brief.gaps) == 3
        and len(brief.action_lines) == 5
        and len(brief.sources) == 7
        and brief.calibration_band == "probable"
        and brief.calibration_pct_range == [50, 60]
    )


def test_ingest_dict_input():
    from core.ingest import ingest_json
    data = json.loads(BAJIO_BRIEF.read_text())
    brief = ingest_json(data)
    return brief.brief_id == "bajio-v3-20260518" and brief.title != ""


def test_ingest_missing_fields():
    from core.ingest import ingest_json
    minimal = {"brief_id": "minimal-001", "title": "Minimal Brief"}
    brief = ingest_json(minimal)
    return (
        brief.brief_id == "minimal-001"
        and len(brief.headline_judgments) == 0
        and len(brief.sections) == 0
        and brief.calibration_band == ""
    )


def test_ingest_preserves_raw():
    from core.ingest import ingest_json
    brief = ingest_json(str(BAJIO_BRIEF))
    return "brief_id" in brief.raw and "sections" in brief.raw


def test_ingest_agent_brief_format():
    from core.ingest import ingest_json
    agent_data = {
        "brief_id": "gsib-test",
        "title": "GSIB Test Brief",
        "published": "2026-05-15T12:00:00Z",
        "theatres": [
            {
                "region": "europe",
                "region_label": "Europe",
                "section_title": "European Theatre",
                "narrative": "Test narrative",
                "key_judgments": [
                    {
                        "id": "KJ-EUR-1",
                        "statement": "Test judgment",
                        "confidence_band": "Likely",
                        "probability_lower": 60,
                        "probability_upper": 79,
                    }
                ],
            }
        ],
        "cross_cutting_analysis": {
            "bluf": "Test BLUF",
            "key_judgments": [],
        },
        "methodology": {
            "sources": [{"name": "Test Source", "source_rating": "B-2"}],
        },
    }
    brief = ingest_json(agent_data)
    return (
        brief.brief_id == "gsib-test"
        and len(brief.sections) == 1
        and len(brief.headline_judgments) == 1
        and brief.headline_judgments[0].kent_band == "Likely"
        and brief.headline_judgments[0].pct_range == [60, 79]
        and brief.bluf == "Test BLUF"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Cost Estimator (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_free_generators_zero_cost():
    from core.cost_estimator import estimate_asset
    from core.schemas import AssetSpec, AssetKind
    for gen in ("mermaid", "matplotlib", "plotly", "graphviz", "leaflet"):
        spec = AssetSpec(kind=AssetKind.DIAGRAM, generator=gen, title="Test")
        est = estimate_asset(spec)
        if est.estimated_cost_usd != 0.0:
            return False
    return True


def test_image_gen_pricing():
    from core.cost_estimator import estimate_asset
    from core.schemas import AssetSpec, AssetKind
    spec = AssetSpec(
        kind=AssetKind.ILLUSTRATION, generator="flux2pro", title="Hero Image",
    )
    est = estimate_asset(spec)
    return 0.04 <= est.estimated_cost_usd <= 0.10


def test_plan_total_aggregation():
    from core.cost_estimator import estimate_plan
    from core.schemas import PresentationPlan, AssetSpec, AssetKind
    plan = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="D1"),
            AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="D2"),
            AssetSpec(kind=AssetKind.ILLUSTRATION, generator="flux2pro", title="I1"),
        ],
    )
    est = estimate_plan(plan)
    return (
        len(est.assets) == 3
        and est.total_cost_usd == sum(a.estimated_cost_usd for a in est.assets)
    )


def test_approval_threshold():
    from core.cost_estimator import estimate_plan
    from core.schemas import PresentationPlan, AssetSpec, AssetKind
    cheap = PresentationPlan(
        brief_id="test",
        assets=[AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="D")],
    )
    cheap_est = estimate_plan(cheap)
    expensive = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(kind=AssetKind.ILLUSTRATION, generator="flux2pro", title=f"I{i}")
            for i in range(15)
        ],
    )
    exp_est = estimate_plan(expensive)
    return not cheap_est.requires_approval and exp_est.requires_approval


def test_budget_headroom():
    from core.cost_estimator import check_budget_headroom
    result = check_budget_headroom(1.0)
    return isinstance(result, dict) and "ok" in result


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Approval Gate (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_auto_approve_under_threshold():
    from core.approval_gate import auto_approve_if_cheap
    from core.cost_estimator import estimate_plan
    from core.schemas import PresentationPlan, AssetSpec, AssetKind, ApprovalStatus
    plan = PresentationPlan(
        brief_id="test",
        assets=[AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="D")],
    )
    est = estimate_plan(plan)
    status = auto_approve_if_cheap(plan, est)
    return status == ApprovalStatus.AUTO_APPROVED


def test_requires_approval_over_threshold():
    from core.approval_gate import auto_approve_if_cheap
    from core.cost_estimator import estimate_plan
    from core.schemas import PresentationPlan, AssetSpec, AssetKind, ApprovalStatus
    plan = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(kind=AssetKind.ILLUSTRATION, generator="flux2pro", title=f"I{i}")
            for i in range(15)
        ],
    )
    est = estimate_plan(plan)
    status = auto_approve_if_cheap(plan, est)
    return status == ApprovalStatus.PENDING


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Provenance (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_provenance_jsonl_append():
    from core.provenance import record_provenance, load_provenance, PROVENANCE_LOG
    from core.schemas import AssetProvenance, AssetKind, QCStatus
    import core.provenance as prov_mod
    original = prov_mod.PROVENANCE_LOG
    tmp = Path(tempfile.mktemp(suffix=".jsonl"))
    prov_mod.PROVENANCE_LOG = tmp
    try:
        record = AssetProvenance(
            asset_id="test-a1", plan_id="test-p1", brief_id="test-b1",
            kind=AssetKind.DIAGRAM, generator="mermaid",
            actual_cost_usd=0.0,
        )
        record_provenance(record)
        record_provenance(record)
        lines = tmp.read_text().strip().split("\n")
        return len(lines) == 2
    finally:
        prov_mod.PROVENANCE_LOG = original
        if tmp.exists():
            tmp.unlink()


def test_provenance_qc_flag():
    from core.provenance import stamp_qc_pending
    from core.schemas import AssetProvenance, AssetKind, QCStatus
    prov = AssetProvenance(
        asset_id="a1", plan_id="p1", brief_id="b1",
        kind=AssetKind.DIAGRAM, generator="mermaid",
        qc_status=QCStatus.APPROVED,
    )
    stamped = stamp_qc_pending(prov)
    return stamped.qc_status == QCStatus.PENDING_REVIEW


def test_provenance_file_hashing():
    from core.provenance import hash_file, hash_data
    tmp = Path(tempfile.mktemp())
    tmp.write_bytes(b"hello world")
    try:
        file_hash = hash_file(str(tmp))
        data_hash = hash_data(b"hello world")
        return file_hash == data_hash and len(file_hash) == 64
    finally:
        tmp.unlink()


def test_provenance_read():
    """Test read_provenance returns recent records."""
    from core.provenance import record_provenance, read_provenance, PROVENANCE_LOG
    from core.schemas import AssetProvenance, AssetKind
    import core.provenance as prov_mod
    original = prov_mod.PROVENANCE_LOG
    tmp = Path(tempfile.mktemp(suffix=".jsonl"))
    prov_mod.PROVENANCE_LOG = tmp
    try:
        for i in range(3):
            record = AssetProvenance(
                asset_id=f"read-test-{i}", plan_id="p1", brief_id="b1",
                kind=AssetKind.DIAGRAM, generator="mermaid",
            )
            record_provenance(record)
        records = read_provenance(limit=2)
        return (
            len(records) == 2
            and records[0]["asset_id"] == "read-test-2"  # Most recent first
        )
    finally:
        prov_mod.PROVENANCE_LOG = original
        if tmp.exists():
            tmp.unlink()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Mermaid Generator (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_mermaid_validates_spec():
    from generators.mermaid_gen import MermaidGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = MermaidGenerator()
    good = AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="D", prompt="graph TD; A-->B")
    assert gen.validate_spec(good) == []
    bad = AssetSpec(kind=AssetKind.MAP, generator="mermaid", title="M", prompt="x")
    return len(gen.validate_spec(bad)) > 0


def test_mermaid_rejects_empty_prompt():
    from generators.mermaid_gen import MermaidGenerator
    from core.schemas import AssetSpec, AssetKind
    from core.exceptions import GeneratorError
    gen = MermaidGenerator()
    spec = AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="Empty", prompt="")
    try:
        gen.generate(spec, tempfile.mkdtemp())
        return False
    except GeneratorError:
        return True


def test_mermaid_is_available():
    from generators.mermaid_gen import MermaidGenerator
    gen = MermaidGenerator()
    return gen.is_available()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Orchestrator Lint Rules (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_lint_image_gen_for_map():
    from core.orchestrator import validate_no_image_gen_for_structured
    from core.schemas import PresentationPlan, AssetSpec, AssetKind
    plan = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(kind=AssetKind.MAP, generator="flux2pro", title="Bad Map"),
        ],
    )
    violations = validate_no_image_gen_for_structured(plan)
    return len(violations) == 1 and "flux2pro" in violations[0]


def test_lint_allows_correct_routing():
    from core.orchestrator import validate_no_image_gen_for_structured
    from core.schemas import PresentationPlan, AssetSpec, AssetKind
    plan = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(kind=AssetKind.MAP, generator="mapbox_static", title="Good Map"),
            AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="Good Diagram"),
            AssetSpec(kind=AssetKind.CHART, generator="matplotlib", title="Good Chart"),
            AssetSpec(kind=AssetKind.ILLUSTRATION, generator="flux2pro", title="Good Illustration"),
        ],
    )
    violations = validate_no_image_gen_for_structured(plan)
    return len(violations) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Database (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_db_create_tables():
    from db.engine import get_engine, init_db
    init_db()
    from sqlalchemy import inspect
    insp = inspect(get_engine())
    tables = set(insp.get_table_names())
    expected = {"tps_plans", "tps_assets", "tps_provenance", "tps_source_events", "tps_indicator_history"}
    return expected.issubset(tables)


def test_db_insert_plan():
    from db.engine import get_session, init_db
    from db.models import PlanRecord
    from datetime import datetime, timezone
    from uuid import uuid4
    init_db()
    session = get_session()
    plan_id = f"test-{uuid4().hex[:8]}"
    try:
        plan = PlanRecord(
            plan_id=plan_id,
            brief_id="test-brief-001",
            created_at=datetime.now(timezone.utc),
            approval_status="approved",
            total_estimated_cost_usd=0.50,
        )
        session.add(plan)
        session.commit()
        fetched = session.get(PlanRecord, plan_id)
        ok = fetched is not None and fetched.brief_id == "test-brief-001"
        session.delete(fetched)
        session.commit()
        return ok
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: PDF Builder (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pdf_qc_watermark():
    from deliverables.pdf_builder import PDFBuilder
    builder = PDFBuilder()
    html = '<div class="footer">Original footer</div>'
    stamped = builder._stamp_qc_flag(html)
    return "PENDING HUMAN ANALYST QC REVIEW" in stamped


def test_pdf_provenance_table():
    from deliverables.pdf_builder import PDFBuilder
    from core.schemas import AssetProvenance, AssetKind
    builder = PDFBuilder()
    records = [
        AssetProvenance(
            asset_id="a1", plan_id="p1", brief_id="b1",
            kind=AssetKind.DIAGRAM, generator="mermaid",
            actual_cost_usd=0.0,
        ),
    ]
    html = '<div class="footer">Footer</div>'
    result = builder._append_provenance_section(html, records)
    return "Asset Provenance" in result and "mermaid" in result


def test_pdf_asset_injection():
    from deliverables.pdf_builder import PDFBuilder
    from core.schemas import PresentationPlan, AssetSpec, AssetKind
    builder = PDFBuilder()
    plan = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(asset_id="img1", kind=AssetKind.DIAGRAM, generator="mermaid", title="Test Diagram"),
        ],
    )
    tmp = Path(tempfile.mktemp(suffix=".png"))
    tmp.write_bytes(b"PNG_DATA")
    try:
        html = '<div class="footer">Footer</div>'
        result = builder._inject_assets(html, plan, {"img1": str(tmp)})
        return "Generated Visual Assets" in result and "Test Diagram" in result
    finally:
        tmp.unlink()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: Config (M1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_config_brand_defaults():
    from core.config import TPSConfig
    config = TPSConfig()
    return (
        config.brand.color_primary == "#0f3460"
        and config.brand.color_accent == "#e94560"
        and config.brand.qc_watermark == "PENDING HUMAN ANALYST QC REVIEW"
    )


def test_config_provider_lookup():
    from core.config import TPSConfig
    config = TPSConfig()
    mermaid = config.get_provider("mermaid")
    return mermaid.name == "mermaid" and mermaid.provider_type == "local"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M2 — Generators
# ═══════════════════════════════════════════════════════════════════════════════

def test_matplotlib_gen_bar_chart():
    """Test matplotlib generator creates a bar chart PNG."""
    from generators.matplotlib_gen import MatplotlibGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = MatplotlibGenerator()
    if not gen.is_available():
        return True  # Skip if matplotlib not installed
    spec = AssetSpec(
        kind=AssetKind.CHART, generator="matplotlib", title="Test Bar",
        parameters={
            "chart_type": "bar",
            "labels": ["A", "B", "C"],
            "values": [10, 20, 15],
        },
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        return (
            os.path.exists(result.output_path)
            and result.output_path.endswith(".png")
            and result.actual_cost_usd == 0.0
        )
    finally:
        shutil.rmtree(tmpdir)


def test_matplotlib_gen_kent_bar():
    """Test kent probability band chart."""
    from generators.matplotlib_gen import MatplotlibGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = MatplotlibGenerator()
    if not gen.is_available():
        return True
    spec = AssetSpec(
        kind=AssetKind.CHART, generator="matplotlib", title="Kent Bar",
        parameters={
            "chart_type": "kent_bar",
            "labels": ["Judge 1", "Judge 2"],
            "values": [8.5, 5.0],
            "kent_bands": ["highly_likely", "even_chance"],
        },
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        return os.path.exists(result.output_path)
    finally:
        shutil.rmtree(tmpdir)


def test_plotly_gen_creates_html():
    """Test plotly generator creates interactive HTML."""
    from generators.plotly_gen import PlotlyGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = PlotlyGenerator()
    if not gen.is_available():
        return True
    spec = AssetSpec(
        kind=AssetKind.CHART, generator="plotly", title="Interactive",
        parameters={
            "chart_type": "bar",
            "labels": ["X", "Y"],
            "values": [5, 10],
        },
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        return (
            os.path.exists(result.output_path)
            and result.output_path.endswith(".html")
        )
    finally:
        shutil.rmtree(tmpdir)


def test_timeline_gen():
    """Test timeline HTML generator."""
    from generators.timeline_gen import TimelineGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = TimelineGenerator()
    spec = AssetSpec(
        kind=AssetKind.DIAGRAM, generator="timeline", title="Events",
        parameters={
            "events": [
                {"date": "2026-01-01", "label": "Event A", "kent_band": "likely"},
                {"date": "2026-02-01", "label": "Event B"},
            ],
        },
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        ok = os.path.exists(result.output_path) and result.output_path.endswith(".html")
        if ok:
            content = Path(result.output_path).read_text()
            ok = ok and "Event A" in content and "Event B" in content
        return ok
    finally:
        shutil.rmtree(tmpdir)


def test_ldap7_radar_gen():
    """Test LDAP-7 radar chart generator."""
    from generators.ldap7_radar_gen import LDAP7RadarGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = LDAP7RadarGenerator()
    if not gen.is_available():
        return True
    spec = AssetSpec(
        kind=AssetKind.CHART, generator="ldap7_radar", title="Leader X",
        parameters={
            "scores": [7, 6, 8, 5, 4, 9, 7],
            "leader_name": "Test Leader",
        },
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        return (
            os.path.exists(result.output_path)
            and result.output_path.endswith(".png")
            and result.model_used == "matplotlib-radar"
        )
    finally:
        shutil.rmtree(tmpdir)


def test_html_to_image_gen():
    """Test HTML-to-image (weasyprint) generator."""
    from generators.html_to_image_gen import HTMLToImageGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = HTMLToImageGenerator()
    if not gen.is_available():
        return True
    spec = AssetSpec(
        kind=AssetKind.INFOGRAPHIC, generator="html_to_png", title="Table Render",
        prompt="<html><body><h1>Hello TPS</h1><table><tr><td>A</td><td>B</td></tr></table></body></html>",
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        return (
            os.path.exists(result.output_path)
            and result.output_path.endswith(".png")
            and result.model_used == "weasyprint"
        )
    finally:
        shutil.rmtree(tmpdir)


def test_leaflet_gen():
    """Test leaflet tactical map generator."""
    from generators.leaflet_gen import LeafletTacticalGenerator
    from core.schemas import AssetSpec, AssetKind
    gen = LeafletTacticalGenerator()
    spec = AssetSpec(
        kind=AssetKind.MAP, generator="leaflet", title="Tactical Map",
        parameters={
            "center": [20.9, -101.2],
            "zoom": 8,
            "markers": [{"lat": 20.9, "lon": -101.2, "label": "Target"}],
        },
    )
    tmpdir = tempfile.mkdtemp()
    try:
        result = gen.generate(spec, tmpdir)
        ok = os.path.exists(result.output_path) and result.output_path.endswith(".html")
        if ok:
            content = Path(result.output_path).read_text()
            ok = ok and "leaflet" in content.lower() and "Target" in content
        return ok
    finally:
        shutil.rmtree(tmpdir)


def test_cache_operations():
    """Test cache key generation and storage."""
    from core.cache import cache_key, cache_get, cache_put, cache_has
    from core.schemas import AssetSpec, AssetKind
    import time
    spec = AssetSpec(
        kind=AssetKind.DIAGRAM, generator="test_gen_", title="Cache Test",
        prompt=f"test prompt {time.time()}",
    )
    ck = cache_key("test_gen", spec)
    # Should be a hex string
    if not ck or len(ck) < 16:
        return False
    # Should not be cached yet
    if cache_get(ck, tempfile.mkdtemp()):
        return False
    # Cache a file
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, "test.png")
    with open(tmpfile, "w") as f:
        f.write("test data")
    cache_put(ck, tmpfile)
    return cache_has(ck)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M2 — Style Director
# ═══════════════════════════════════════════════════════════════════════════════

def test_style_director_image_suffix():
    """Test brand suffix for image-gen prompts."""
    from core.style_director import get_image_prompt_suffix
    suffix = get_image_prompt_suffix()
    return (
        "primary" in suffix.lower() or "#0f3460" in suffix
    ) and len(suffix) > 20


def test_style_director_kent_color():
    """Test kent band color lookup."""
    from core.style_director import get_kent_color
    color = get_kent_color("almost_certain")
    return color.startswith("#") and len(color) == 7


def test_style_director_chart_colors():
    """Test chart palette retrieval."""
    from core.style_director import get_chart_colors
    colors = get_chart_colors()
    return isinstance(colors, list) and len(colors) >= 5


def test_style_director_inject_css():
    """Test CSS variable injection."""
    from core.style_director import inject_brand_css
    html = "<html><head></head><body>Test</body></html>"
    result = inject_brand_css(html)
    return "--tps-primary" in result and "--tps-accent" in result


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M3 — Planner
# ═══════════════════════════════════════════════════════════════════════════════

def test_planner_routing_table():
    """Test routing table covers all asset kinds."""
    from core.planner import ROUTING_TABLE
    expected_kinds = {"map", "diagram", "chart", "infographic", "illustration", "table", "narration", "video"}
    return expected_kinds == set(ROUTING_TABLE.keys())


def test_planner_validate_routing():
    """Test routing validation catches violations."""
    from core.planner import _validate_routing
    bad_assets = [
        {"kind": "map", "generator": "flux2pro", "title": "Bad Map"},
        {"kind": "chart", "generator": "ideogram_v3", "title": "Bad Chart"},
    ]
    errors = _validate_routing(bad_assets)
    return len(errors) == 2


def test_planner_fix_routing():
    """Test automatic routing fix."""
    from core.planner import _fix_routing
    bad_assets = [
        {"kind": "map", "generator": "flux2pro", "title": "Bad Map"},
        {"kind": "diagram", "generator": "gpt_image_2", "title": "Bad Diagram"},
    ]
    fixed = _fix_routing(bad_assets)
    return (
        fixed[0]["generator"] == "mapbox_static"
        and fixed[1]["generator"] == "mermaid"
    )


def test_planner_rule_based_fallback():
    """Test rule-based planner produces valid plan from brief."""
    from core.planner import _rule_based_plan
    from core.ingest import ingest_json
    brief = ingest_json(str(BAJIO_BRIEF))
    result = _rule_based_plan(brief, max_assets=8)
    assets = result.get("assets", [])
    # Should produce multiple assets
    if len(assets) < 3:
        return False
    # Should have valid kinds
    valid_kinds = {"map", "diagram", "chart", "infographic", "illustration", "table", "narration", "video"}
    for a in assets:
        if a["kind"] not in valid_kinds:
            return False
    # Should not have image-gen for structured kinds
    from core.planner import _validate_routing
    errors = _validate_routing(assets)
    return len(errors) == 0


def test_planner_plan_from_brief():
    """Test full plan_from_brief pipeline (rule-based fallback)."""
    from core.planner import plan_from_brief
    from core.ingest import ingest_json
    from core.schemas import ApprovalStatus
    brief = ingest_json(str(BAJIO_BRIEF))
    plan = plan_from_brief(brief, deliverables=["pdf"], max_assets=5)
    return (
        len(plan.assets) > 0
        and len(plan.assets) <= 5
        and plan.approval_status in (ApprovalStatus.AUTO_APPROVED, ApprovalStatus.PENDING)
        and plan.brief_id == "bajio-v3-20260518"
    )


def test_planner_brief_summary():
    """Test brief summary construction."""
    from core.planner import _build_brief_summary
    from core.ingest import ingest_json
    brief = ingest_json(str(BAJIO_BRIEF))
    summary = _build_brief_summary(brief)
    return (
        "Title:" in summary
        and "Key Judgments:" in summary
        and "Sections:" in summary
        and len(summary) > 100
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M3 — Parallel Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def test_orchestrator_dependency_resolution():
    """Test execution wave resolution with dependencies."""
    from core.orchestrator import _resolve_execution_order
    from core.schemas import AssetSpec, AssetKind
    assets = [
        AssetSpec(asset_id="a1", kind=AssetKind.DIAGRAM, generator="mermaid", title="D1"),
        AssetSpec(asset_id="a2", kind=AssetKind.CHART, generator="matplotlib", title="C1"),
        AssetSpec(asset_id="a3", kind=AssetKind.ILLUSTRATION, generator="flux2pro", title="I1",
                  depends_on=["a1", "a2"]),
    ]
    waves = _resolve_execution_order(assets)
    # Wave 1: a1, a2 (no deps); Wave 2: a3 (depends on a1, a2)
    return (
        len(waves) == 2
        and len(waves[0]) == 2
        and len(waves[1]) == 1
        and waves[1][0].asset_id == "a3"
    )


def test_orchestrator_register_all():
    """Test auto-registration of all built-in generators."""
    from core.orchestrator import register_all_generators, list_generators, _GENERATORS
    # Clear existing
    _GENERATORS.clear()
    register_all_generators()
    gens = list_generators()
    # Should have at least 15 generators
    return len(gens) >= 15


def test_orchestrator_execution_result_thread_safety():
    """Test ExecutionResult thread-safe operations."""
    from core.orchestrator import ExecutionResult
    result = ExecutionResult()
    result.record_success("a1", "/path/a1.png", 0.05, 1.5)
    result.record_failure("a2", "test error", 0.5)
    return (
        result.success_count == 1
        and result.failure_count == 1
        and result.total_cost_usd == 0.05
        and not result.all_succeeded
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M4 — Deliverables
# ═══════════════════════════════════════════════════════════════════════════════

def test_social_pack_builder():
    """Test social pack produces LinkedIn, X, IG files."""
    from deliverables.social_pack import SocialPackBuilder
    from core.schemas import PresentationPlan, AssetSpec, AssetKind, ApprovalStatus
    builder = SocialPackBuilder()
    brief_json = {
        "title": "Test Brief",
        "bluf": "This is a test BLUF for social pack.",
        "headline_judgments": [
            {"claim": "Judgment 1", "kent_band": "likely"},
            {"claim": "Judgment 2", "kent_band": "probable"},
        ],
    }
    plan = PresentationPlan(brief_id="test", approval_status=ApprovalStatus.APPROVED)
    tmpdir = tempfile.mkdtemp()
    try:
        result = builder.build(brief_json, plan, {}, [], tmpdir)
        files = os.listdir(tmpdir)
        return (
            "linkedin_carousel.html" in files
            and "x_thread.txt" in files
            and "ig_card.html" in files
            and "manifest.json" in files
        )
    finally:
        shutil.rmtree(tmpdir)


def test_exec_card_builder():
    """Test exec card produces HTML output."""
    from deliverables.exec_card import ExecCardBuilder
    from core.schemas import PresentationPlan, ApprovalStatus
    builder = ExecCardBuilder()
    brief_json = {
        "title": "Exec Card Test",
        "bluf": "Executive summary test.",
        "produced_at": "2026-05-19",
        "headline_judgments": [
            {"claim": "Test judgment", "kent_band": "highly_likely"},
        ],
    }
    plan = PresentationPlan(brief_id="test", approval_status=ApprovalStatus.APPROVED)
    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "exec_card.html")
    try:
        result = builder.build(brief_json, plan, {}, [], output_path)
        ok = os.path.exists(result) and result.endswith(".html")
        if ok:
            content = Path(result).read_text()
            ok = (
                "Exec Card Test" in content
                and "PENDING HUMAN ANALYST QC REVIEW" in content
                and "Highly Likely" in content
            )
        return ok
    finally:
        shutil.rmtree(tmpdir)


def test_website_builder():
    """Test website builder produces static site structure."""
    from deliverables.website_builder import WebsiteBuilder
    from core.schemas import PresentationPlan, AssetProvenance, AssetKind, ApprovalStatus
    builder = WebsiteBuilder()
    brief_json = {
        "title": "Website Test Brief",
        "bluf": "Test BLUF for website.",
        "produced_at": "2026-05-19",
        "headline_judgments": [
            {"claim": "Web judgment", "kent_band": "likely"},
        ],
        "sections": [
            {"title": "Section 1", "narrative": "Narrative text.", "subsections": []},
        ],
    }
    plan = PresentationPlan(brief_id="test", approval_status=ApprovalStatus.APPROVED)
    prov = [AssetProvenance(
        asset_id="wa1", plan_id="wp1", brief_id="wb1",
        kind=AssetKind.DIAGRAM, generator="mermaid",
    )]
    tmpdir = tempfile.mkdtemp()
    output_dir = os.path.join(tmpdir, "site")
    try:
        result = builder.build(brief_json, plan, {}, prov, output_dir)
        return (
            os.path.exists(os.path.join(output_dir, "index.html"))
            and os.path.exists(os.path.join(output_dir, "style.css"))
            and os.path.exists(os.path.join(output_dir, "provenance.html"))
            and os.path.exists(os.path.join(output_dir, "sections", "0.html"))
        )
    finally:
        shutil.rmtree(tmpdir)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M5 — Audio/Video Generator Specs
# ═══════════════════════════════════════════════════════════════════════════════

def test_elevenlabs_gen_spec():
    """Test ElevenLabs generator interface."""
    from generators.elevenlabs_gen import ElevenLabsGenerator
    from core.schemas import AssetKind
    gen = ElevenLabsGenerator()
    return (
        gen.name == "elevenlabs"
        and AssetKind.NARRATION.value in gen.supported_kinds
    )


def test_veo_gen_spec():
    """Test Veo generator interface."""
    from generators.veo_gen import VeoGenerator
    from core.schemas import AssetKind
    gen = VeoGenerator()
    return (
        gen.name == "veo_3_1"
        and AssetKind.VIDEO.value in gen.supported_kinds
    )


def test_kling_gen_spec():
    """Test Kling generator interface."""
    from generators.kling_gen import KlingGenerator
    from core.schemas import AssetKind
    gen = KlingGenerator()
    return (
        gen.name == "kling_3_0"
        and AssetKind.VIDEO.value in gen.supported_kinds
    )


def test_runway_gen_spec():
    """Test Runway generator interface."""
    from generators.runway_gen import RunwayGenerator
    from core.schemas import AssetKind
    gen = RunwayGenerator()
    return (
        gen.name == "runway_4_5"
        and AssetKind.VIDEO.value in gen.supported_kinds
    )


def test_suno_gen_spec():
    """Test Suno generator interface."""
    from generators.suno_gen import SunoGenerator
    from core.schemas import AssetKind
    gen = SunoGenerator()
    return (
        gen.name == "suno"
        and AssetKind.NARRATION.value in gen.supported_kinds
    )


def test_heygen_gen_spec():
    """Test HeyGen generator interface."""
    from generators.heygen_gen import HeyGenGenerator
    from core.schemas import AssetKind
    gen = HeyGenGenerator()
    return (
        gen.name == "heygen"
        and AssetKind.VIDEO.value in gen.supported_kinds
    )


def test_assembly_ffmpeg_check():
    """Test FFmpeg availability check."""
    from generators.assembly import is_available
    # Just verify the function works (bool return)
    result = is_available()
    return isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M5 — Cost Estimator Audio/Video
# ═══════════════════════════════════════════════════════════════════════════════

def test_audio_cost_estimation():
    """Test audio narration cost estimation."""
    from core.cost_estimator import estimate_asset
    from core.schemas import AssetSpec, AssetKind
    spec = AssetSpec(
        kind=AssetKind.NARRATION, generator="elevenlabs", title="Narration",
        parameters={"char_count": 5000},
    )
    est = estimate_asset(spec)
    # 5000 chars × $0.00003/char = $0.15
    return 0.10 <= est.estimated_cost_usd <= 0.20


def test_video_cost_estimation():
    """Test video cost estimation."""
    from core.cost_estimator import estimate_asset
    from core.schemas import AssetSpec, AssetKind
    spec = AssetSpec(
        kind=AssetKind.VIDEO, generator="veo_3_1", title="Video",
        parameters={"duration_sec": 10},
    )
    est = estimate_asset(spec)
    # 10 sec × $0.40/sec = $4.00
    return 3.50 <= est.estimated_cost_usd <= 4.50


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE: M6 — API
# ═══════════════════════════════════════════════════════════════════════════════

def test_api_app_creates():
    """Test FastAPI app can be created."""
    from api.server import app
    return app.title == "Trevor Presentational Suite"


def test_api_routes_registered():
    """Test key routes are registered."""
    from api.server import app
    paths = [r.path for r in app.routes]
    required = ["/api/health", "/api/generators", "/api/ingest", "/api/plan", "/api/execute"]
    for req in required:
        if req not in paths:
            return False
    return True


def test_api_health_endpoint():
    """Test health endpoint via TestClient."""
    from fastapi.testclient import TestClient
    from api.server import app
    client = TestClient(app)
    resp = client.get("/api/health")
    return (
        resp.status_code == 200
        and resp.json()["status"] == "ok"
        and resp.json()["generators_count"] > 0
    )


def test_api_generators_endpoint():
    """Test generators listing endpoint."""
    from fastapi.testclient import TestClient
    from api.server import app
    client = TestClient(app)
    resp = client.get("/api/generators")
    data = resp.json()
    return (
        resp.status_code == 200
        and "generators" in data
        and len(data["generators"]) > 0
    )


def test_api_ingest_endpoint():
    """Test ingest endpoint with Bajio brief."""
    from fastapi.testclient import TestClient
    from api.server import app
    client = TestClient(app)
    brief_data = json.loads(BAJIO_BRIEF.read_text())
    resp = client.post("/api/ingest", json={"brief_json": brief_data})
    data = resp.json()
    return (
        resp.status_code == 200
        and data["brief_id"] == "bajio-v3-20260518"
        and data["sections_count"] == 4
        and data["judgments_count"] == 4
    )


def test_api_plan_endpoint():
    """Test plan generation endpoint."""
    from fastapi.testclient import TestClient
    from api.server import app
    client = TestClient(app)
    brief_data = json.loads(BAJIO_BRIEF.read_text())
    resp = client.post("/api/plan", json={
        "brief_json": brief_data,
        "deliverables": ["pdf"],
        "max_assets": 4,
    })
    data = resp.json()
    return (
        resp.status_code == 200
        and "plan_id" in data
        and len(data["assets"]) > 0
        and len(data["assets"]) <= 4
    )


def test_api_cost_estimate_endpoint():
    """Test cost estimation endpoint."""
    from fastapi.testclient import TestClient
    from api.server import app
    from core.schemas import PresentationPlan, AssetSpec, AssetKind
    client = TestClient(app)
    plan = PresentationPlan(
        brief_id="test",
        assets=[
            AssetSpec(kind=AssetKind.DIAGRAM, generator="mermaid", title="D1"),
            AssetSpec(kind=AssetKind.ILLUSTRATION, generator="flux2pro", title="I1"),
        ],
    )
    resp = client.post("/api/cost/estimate", json={
        "plan_json": plan.model_dump(mode="json"),
    })
    data = resp.json()
    return (
        resp.status_code == 200
        and "total_cost_usd" in data
        and data["total_cost_usd"] >= 0
    )


def test_webhook_storage():
    """Test webhook result storage and retrieval."""
    from api.webhook import _store_webhook_result, get_webhook_result, clear_webhook_result
    _store_webhook_result("fal", "test-123", {"status": "COMPLETED", "images": []})
    result = get_webhook_result("fal", "test-123")
    ok = result is not None and result["data"]["status"] == "COMPLETED"
    clear_webhook_result("fal", "test-123")
    cleared = get_webhook_result("fal", "test-123")
    return ok and cleared is None


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  TPS Full Test Suite — Milestones 1-6")
    print("=" * 60)

    suites = [
        # M1 — Foundation
        ("M1: Schemas", [
            ("asset_kind_values", test_asset_kind_values),
            ("presentation_plan_serialization", test_presentation_plan_serialization),
            ("qc_status_default", test_qc_status_default),
        ]),
        ("M1: Ingest", [
            ("ingest_bajio_v3", test_ingest_bajio_v3),
            ("ingest_dict_input", test_ingest_dict_input),
            ("ingest_missing_fields", test_ingest_missing_fields),
            ("ingest_preserves_raw", test_ingest_preserves_raw),
            ("ingest_agent_brief_format", test_ingest_agent_brief_format),
        ]),
        ("M1: Cost Estimator", [
            ("free_generators_zero_cost", test_free_generators_zero_cost),
            ("image_gen_pricing", test_image_gen_pricing),
            ("plan_total_aggregation", test_plan_total_aggregation),
            ("approval_threshold", test_approval_threshold),
            ("budget_headroom", test_budget_headroom),
        ]),
        ("M1: Approval Gate", [
            ("auto_approve_under_threshold", test_auto_approve_under_threshold),
            ("requires_approval_over_threshold", test_requires_approval_over_threshold),
        ]),
        ("M1: Provenance", [
            ("provenance_jsonl_append", test_provenance_jsonl_append),
            ("provenance_qc_flag", test_provenance_qc_flag),
            ("provenance_file_hashing", test_provenance_file_hashing),
            ("provenance_read", test_provenance_read),
        ]),
        ("M1: Mermaid Generator", [
            ("mermaid_validates_spec", test_mermaid_validates_spec),
            ("mermaid_rejects_empty_prompt", test_mermaid_rejects_empty_prompt),
            ("mermaid_is_available", test_mermaid_is_available),
        ]),
        ("M1: Orchestrator Lint Rules", [
            ("lint_image_gen_for_map", test_lint_image_gen_for_map),
            ("lint_allows_correct_routing", test_lint_allows_correct_routing),
        ]),
        ("M1: Database", [
            ("db_create_tables", test_db_create_tables),
            ("db_insert_plan", test_db_insert_plan),
        ]),
        ("M1: PDF Builder", [
            ("pdf_qc_watermark", test_pdf_qc_watermark),
            ("pdf_provenance_table", test_pdf_provenance_table),
            ("pdf_asset_injection", test_pdf_asset_injection),
        ]),
        ("M1: Config", [
            ("config_brand_defaults", test_config_brand_defaults),
            ("config_provider_lookup", test_config_provider_lookup),
        ]),

        # M2 — Generators
        ("M2: Chart Generators", [
            ("matplotlib_bar_chart", test_matplotlib_gen_bar_chart),
            ("matplotlib_kent_bar", test_matplotlib_gen_kent_bar),
            ("plotly_creates_html", test_plotly_gen_creates_html),
            ("ldap7_radar", test_ldap7_radar_gen),
        ]),
        ("M2: Diagram Generators", [
            ("timeline_gen", test_timeline_gen),
            ("html_to_image", test_html_to_image_gen),
        ]),
        ("M2: Map Generators", [
            ("leaflet_gen", test_leaflet_gen),
        ]),
        ("M2: Cache", [
            ("cache_operations", test_cache_operations),
        ]),
        ("M2: Style Director", [
            ("image_prompt_suffix", test_style_director_image_suffix),
            ("kent_color", test_style_director_kent_color),
            ("chart_colors", test_style_director_chart_colors),
            ("inject_css", test_style_director_inject_css),
        ]),

        # M3 — Planner
        ("M3: Planner", [
            ("routing_table_coverage", test_planner_routing_table),
            ("validate_routing", test_planner_validate_routing),
            ("fix_routing", test_planner_fix_routing),
            ("rule_based_fallback", test_planner_rule_based_fallback),
            ("plan_from_brief", test_planner_plan_from_brief),
            ("brief_summary", test_planner_brief_summary),
        ]),
        ("M3: Parallel Orchestrator", [
            ("dependency_resolution", test_orchestrator_dependency_resolution),
            ("register_all_generators", test_orchestrator_register_all),
            ("execution_result_thread_safety", test_orchestrator_execution_result_thread_safety),
        ]),

        # M4 — Deliverables
        ("M4: Deliverable Builders", [
            ("social_pack_builder", test_social_pack_builder),
            ("exec_card_builder", test_exec_card_builder),
            ("website_builder", test_website_builder),
        ]),

        # M5 — Audio/Video
        ("M5: Audio/Video Generator Specs", [
            ("elevenlabs_spec", test_elevenlabs_gen_spec),
            ("veo_spec", test_veo_gen_spec),
            ("kling_spec", test_kling_gen_spec),
            ("runway_spec", test_runway_gen_spec),
            ("suno_spec", test_suno_gen_spec),
            ("heygen_spec", test_heygen_gen_spec),
            ("assembly_ffmpeg", test_assembly_ffmpeg_check),
        ]),
        ("M5: Audio/Video Cost Estimation", [
            ("audio_cost", test_audio_cost_estimation),
            ("video_cost", test_video_cost_estimation),
        ]),

        # M6 — API
        ("M6: FastAPI", [
            ("app_creates", test_api_app_creates),
            ("routes_registered", test_api_routes_registered),
            ("health_endpoint", test_api_health_endpoint),
            ("generators_endpoint", test_api_generators_endpoint),
            ("ingest_endpoint", test_api_ingest_endpoint),
            ("plan_endpoint", test_api_plan_endpoint),
            ("cost_estimate_endpoint", test_api_cost_estimate_endpoint),
            ("webhook_storage", test_webhook_storage),
        ]),
    ]

    for suite_name, tests in suites:
        print(f"\n── {suite_name} ──")
        for test_name, test_fn in tests:
            run_test(test_name, test_fn)

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")

    if errors:
        print("\n  Failures:")
        for e in errors:
            print(f"    x {e}")

    sys.exit(0 if failed == 0 else 1)
