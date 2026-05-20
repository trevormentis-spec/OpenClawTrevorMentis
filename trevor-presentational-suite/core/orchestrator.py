"""TPS Orchestrator — execute a presentation plan.

Supports both sequential and parallel (ThreadPoolExecutor) execution.
Respects dependency ordering: assets with depends_on are deferred until
their dependencies complete.
"""
from __future__ import annotations

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from .schemas import (
    PresentationPlan,
    AssetSpec,
    AssetKind,
    ApprovalStatus,
    QCStatus,
)
from .exceptions import (
    ApprovalRequiredError,
    PlanValidationError,
    GeneratorError,
    GeneratorUnavailableError,
)
from .provenance import build_provenance, record_provenance
from .config import get_config

# ── Generator Registry ───────────────────────────────────────────────────────

_GENERATORS: dict[str, object] = {}


def register_generator(gen) -> None:
    """Register a generator instance."""
    _GENERATORS[gen.name] = gen


def get_generator(name: str):
    """Get a registered generator by name."""
    return _GENERATORS.get(name)


def list_generators() -> list[str]:
    """List registered generator names."""
    return list(_GENERATORS.keys())


def register_all_generators() -> None:
    """Auto-register all built-in generators."""
    from generators.mermaid_gen import MermaidGenerator
    from generators.matplotlib_gen import MatplotlibGenerator
    from generators.plotly_gen import PlotlyGenerator
    from generators.graphviz_gen import GraphvizGenerator
    from generators.d2_gen import D2Generator
    from generators.timeline_gen import TimelineGenerator
    from generators.ldap7_radar_gen import LDAP7RadarGenerator
    from generators.html_to_image_gen import HTMLToImageGenerator
    from generators.mapbox_gen import MapboxStaticGenerator, MapboxInteractiveGenerator
    from generators.leaflet_gen import LeafletTacticalGenerator
    from generators.flux_gen import FluxGenerator
    from generators.ideogram_gen import IdeogramGenerator
    from generators.recraft_gen import RecraftGenerator
    from generators.imagen_gen import ImagenGenerator
    from generators.gpt_image_gen import GPTImageGenerator

    for cls in [
        MermaidGenerator, MatplotlibGenerator, PlotlyGenerator,
        GraphvizGenerator, D2Generator, TimelineGenerator,
        LDAP7RadarGenerator, HTMLToImageGenerator,
        MapboxStaticGenerator, MapboxInteractiveGenerator,
        LeafletTacticalGenerator,
        FluxGenerator, IdeogramGenerator, RecraftGenerator,
        ImagenGenerator, GPTImageGenerator,
    ]:
        gen = cls()
        register_generator(gen)

    # Conditionally register M5 generators
    try:
        from generators.elevenlabs_gen import ElevenLabsGenerator
        register_generator(ElevenLabsGenerator())
    except ImportError:
        pass
    try:
        from generators.veo_gen import VeoGenerator
        register_generator(VeoGenerator())
    except ImportError:
        pass
    try:
        from generators.kling_gen import KlingGenerator
        register_generator(KlingGenerator())
    except ImportError:
        pass
    try:
        from generators.runway_gen import RunwayGenerator
        register_generator(RunwayGenerator())
    except ImportError:
        pass
    try:
        from generators.suno_gen import SunoGenerator
        register_generator(SunoGenerator())
    except ImportError:
        pass
    try:
        from generators.heygen_gen import HeyGenGenerator
        register_generator(HeyGenGenerator())
    except ImportError:
        pass


# ── Image-Gen Lint Rule ──────────────────────────────────────────────────────

IMAGE_GEN_GENERATORS = frozenset({
    "flux2pro", "ideogram_v3", "recraft_v4", "imagen_4", "gpt_image_2",
})

STRUCTURED_KINDS = frozenset({
    AssetKind.MAP, AssetKind.CHART, AssetKind.DIAGRAM,
})


def validate_no_image_gen_for_structured(plan: PresentationPlan) -> list[str]:
    """Enforce: image-gen MUST NOT be used for maps, charts, or diagrams."""
    violations = []
    for asset in plan.assets:
        if asset.generator in IMAGE_GEN_GENERATORS and asset.kind in STRUCTURED_KINDS:
            violations.append(
                f"Asset {asset.asset_id}: generator '{asset.generator}' "
                f"must not be used for kind '{asset.kind.value}'. "
                f"Use a specialist generator instead."
            )
    return violations


def validate_plan(plan: PresentationPlan) -> list[str]:
    """Run all plan validation rules. Returns list of errors."""
    errors = []
    errors.extend(validate_no_image_gen_for_structured(plan))

    for asset in plan.assets:
        if asset.generator not in _GENERATORS:
            errors.append(
                f"Asset {asset.asset_id}: generator '{asset.generator}' is not registered"
            )

    return errors


# ── Execution ────────────────────────────────────────────────────────────────


class ExecutionResult:
    """Result of executing a full plan."""

    def __init__(self):
        self.outputs: dict[str, str] = {}
        self.errors: dict[str, str] = {}
        self.total_cost_usd: float = 0.0
        self.total_time_sec: float = 0.0
        self._lock = threading.Lock()

    @property
    def success_count(self) -> int:
        return len(self.outputs)

    @property
    def failure_count(self) -> int:
        return len(self.errors)

    @property
    def all_succeeded(self) -> bool:
        return len(self.errors) == 0

    def record_success(self, asset_id: str, output_path: str, cost: float, elapsed: float):
        with self._lock:
            self.outputs[asset_id] = output_path
            self.total_cost_usd += cost
            self.total_time_sec += elapsed

    def record_failure(self, asset_id: str, error: str, elapsed: float):
        with self._lock:
            self.errors[asset_id] = error
            self.total_time_sec += elapsed


def _execute_single_asset(
    spec: AssetSpec,
    output_dir: str,
    plan_id: str,
    brief_id: str,
    result: ExecutionResult,
) -> None:
    """Execute a single asset. Thread-safe via result.record_*."""
    gen = get_generator(spec.generator)
    if gen is None:
        result.record_failure(spec.asset_id, f"Generator '{spec.generator}' not registered", 0)
        return

    if not gen.is_available():
        result.record_failure(spec.asset_id, f"Generator '{spec.generator}' unavailable", 0)
        return

    start = time.time()
    try:
        gen_result = gen.generate(spec, output_dir)
        elapsed = time.time() - start

        result.record_success(spec.asset_id, gen_result.output_path, gen_result.actual_cost_usd, elapsed)

        prov = build_provenance(
            asset_id=spec.asset_id,
            plan_id=plan_id,
            brief_id=brief_id,
            kind=spec.kind.value,
            generator=spec.generator,
            model_used=gen_result.model_used,
            provider=gen_result.provider,
            estimated_cost_usd=spec.estimated_cost_usd,
            actual_cost_usd=gen_result.actual_cost_usd,
            generation_time_sec=elapsed,
            input_data=spec.prompt.encode("utf-8") if spec.prompt else b"",
            output_path=gen_result.output_path,
        )
        record_provenance(prov)

    except Exception as e:
        elapsed = time.time() - start
        result.record_failure(spec.asset_id, f"{type(e).__name__}: {e}", elapsed)


def _resolve_execution_order(assets: list[AssetSpec]) -> list[list[AssetSpec]]:
    """Resolve assets into execution waves respecting depends_on.

    Returns a list of waves. Assets within a wave can run in parallel.
    """
    id_to_spec = {a.asset_id: a for a in assets}
    completed: set[str] = set()
    waves: list[list[AssetSpec]] = []
    remaining = list(assets)

    max_iterations = len(assets) + 1
    for _ in range(max_iterations):
        if not remaining:
            break

        wave = []
        still_remaining = []
        for spec in remaining:
            deps = set(spec.depends_on)
            if deps.issubset(completed):
                wave.append(spec)
            else:
                still_remaining.append(spec)

        if not wave:
            # Circular dependency or unresolvable — force remaining
            waves.append(still_remaining)
            break

        waves.append(wave)
        completed.update(s.asset_id for s in wave)
        remaining = still_remaining

    return waves


def execute_plan(
    plan: PresentationPlan,
    output_dir: str,
    brief_id: str = "",
    parallel: bool = True,
    max_workers: int = 4,
) -> ExecutionResult:
    """Execute all assets in a plan.

    Supports parallel execution via ThreadPoolExecutor with dependency
    resolution. Assets with depends_on are deferred until dependencies complete.
    """
    if plan.approval_status not in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED):
        raise ApprovalRequiredError(
            f"Plan {plan.plan_id} has status '{plan.approval_status.value}' — "
            f"approval required before execution"
        )

    errors = validate_plan(plan)
    if errors:
        raise PlanValidationError(
            f"Plan validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    os.makedirs(output_dir, exist_ok=True)
    result = ExecutionResult()
    bid = brief_id or plan.brief_id

    waves = _resolve_execution_order(plan.assets)

    for wave in waves:
        if parallel and len(wave) > 1:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(wave))) as executor:
                futures = {
                    executor.submit(
                        _execute_single_asset, spec, output_dir, plan.plan_id, bid, result
                    ): spec
                    for spec in wave
                }
                for future in as_completed(futures):
                    # Exceptions are captured inside _execute_single_asset
                    future.result()
        else:
            for spec in wave:
                _execute_single_asset(spec, output_dir, plan.plan_id, bid, result)

    return result
