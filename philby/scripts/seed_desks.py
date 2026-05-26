#!/usr/bin/env python3
"""
seed_desks.py — Philby Desk Seedling.

Adds initial narratives to cognition_state.json for unseeded desks.
Each desk gets 2-3 starter narratives with evidence, catalysts, and source references.

After seeding, the cognition daemon will maintain and evolve these narratives.

Usage:
    python3 philby/scripts/seed_desks.py                           # Seed all unseeded desks
    python3 philby/scripts/seed_desks.py --desk ukraine            # Seed specific desk
    python3 philby/scripts/seed_desks.py --dry-run                 # Preview only
    python3 philby/scripts/seed_desks.py --force                   # Re-seed even if already seeded
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
COGNITION_STATE = REPO / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
PHILBY_CONFIG = REPO / "philby" / "desks" / "philby-config.json"

# Seed narratives by desk
# Each narrative: {id, confidence, trend, evidence_for, evidence_against, catalysts, reasoning, resolution_date}
SEED_NARRATIVES = {
    "north_africa": [
        {
            "id": "north_africa_sahel_insurgency",
            "confidence": 68,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Crisis Group Sahel", "detail": "Jihadi expansion into coastal West Africa accelerating"},
                    {"source": "ACLED data", "detail": "Violent events up 22% YoY in Sahel region"},
                ],
                "against": [
                    {"source": "French drawdown", "detail": "Reduced Western presence creating intelligence gaps"},
                ],
            },
            "catalysts": ["JNIM attacks", "Burkina Faso junta", "Mali-Russia ties"],
            "last_reasoning": "Sahel jihadi groups expand southward into coastal states. French withdrawal reduces ISR coverage. Wagner/RAF presence in Mali/Sahel sustains juntas but does not reduce insurgent capability.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "north_africa_energy_leverage",
            "confidence": 72,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Algeria Sonatrach", "detail": "Gas exports to Southern Europe up 18% in 2026"},
                    {"source": "Egypt LNG", "detail": "Damietta and Idku LNG terminals operating at capacity"},
                ],
                "against": [
                    {"source": "EU diversification", "detail": "Renewables and Norwegian gas reduce dependence on North African supply"},
                ],
            },
            "catalysts": ["EU winter demand", "Algerian production", "Libyan instability"],
            "last_reasoning": "North Africa's role as Europe's alternative gas supplier has structurally increased since 2022. Algeria and Egypt are the key beneficiaries. This gives them diplomatic leverage that persists beyond the immediate energy crisis.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
    ],
    "sub_saharan_africa": [
        {
            "id": "sub_saharan_africa_great_power_competition",
            "confidence": 65,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Russia Africa Corps", "detail": "Russian military deployments expanding across Sahel and Central Africa"},
                    {"source": "China BRI", "detail": "Chinese infrastructure lending to Africa reached new highs in 2025-26"},
                ],
                "against": [
                    {"source": "US strategy", "detail": "US AFRICOM repositioning to counter Russian/Chinese influence"},
                ],
            },
            "catalysts": ["Russia Africa Corps", "China FOCAC", "US counterterrorism"],
            "last_reasoning": "Great-power competition in Sub-Saharan Africa is intensifying as Russia expands military footprint and China deepens economic engagement. The US is repositioning but has lost ground in Sahel states.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "sub_saharan_africa_democratic_backsliding",
            "confidence": 70,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Marshall Center", "detail": "Multiple coup states show no timeline for civilian transition"},
                    {"source": "Election watch", "detail": "Electoral integrity declining in Kenya, Nigeria, DRC"},
                ],
                "against": [
                    {"source": "Regional pushback", "detail": "ECOWAS and AU sanctions regimes maintain pressure on coup juntas"},
                ],
            },
            "catalysts": ["Coup transitions", "Election cycles", "ECOWAS policy"],
            "last_reasoning": "The coup belt across West and Central Africa shows no reversal trend. Juntas consolidate power while ECOWAS sanctions fatigue sets in. Democratic backsliding in previously stable states (Kenya) adds a second vector.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
    ],

    "ukraine": [
        {
            "id": "ukraine_ceasefire_prospects",
            "confidence": 30,
            "trend": "downward",
            "evidence": {
                "for": [
                    {"source": "Oreshnik IRBM deployment", "detail": "Russia using strategic nuclear-capable weapons in theater raises stakes"},
                    {"source": "Prior negotiation patterns", "detail": "Multiple ceasefire attempts failed since 2022"},
                ],
                "against": [
                    {"source": "War fatigue in NATO capitals", "detail": "Political pressure for resolution growing in US and EU"},
                    {"source": "Ukraine signal flexibility", "detail": "Zelensky has indicated openness to negotiated terms"},
                ],
            },
            "catalysts": ["Oreshnik IRBM first use", "NATO summit", "US election cycle"],
            "last_reasoning": "Oreshnik IRBM deployment signals escalation, not de-escalation. Ceasefire unlikely without major battlefield shift or external pressure campaign.",
            "resolution_date": "2026-09-01T14:00:00Z",
        },
        {
            "id": "ukraine_european_security_realignment",
            "confidence": 72,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "NATO force posture", "detail": "Rapid forward deployment to eastern flank confirmed"},
                    {"source": "European defense spending", "detail": "Multiple NATO members exceeding 2% GDP commitment"},
                    {"source": "US troop drawdown reversal", "detail": "Washington signaled commitment to European defense"},
                ],
                "against": [
                    {"source": "Political friction", "detail": "Hungary and Slovakia maintain pro-Russia positions within EU"},
                ],
            },
            "catalysts": ["NATO summit decisions", "European defense industrial base ramp", "US security guarantee reaffirmation"],
            "last_reasoning": "NATO is structurally reinforcing the eastern flank. This is a multi-year trend, not a reversible tactical posture. Hungary/Slovakia are noise, not signal.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "ukraine_energy_infrastructure_strikes",
            "confidence": 78,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "108-drone strike package", "detail": "Largest single drone attack of 2026 hit energy grid"},
                    {"source": "Pattern analysis", "detail": "Winter targeting of thermal and hydro plants consistent"},
                    {"source": "Russian doctrine", "detail": "Energy grid degradation is established Russian strategy"},
                ],
                "against": [
                    {"source": "Ukraine air defense", "detail": "F-16 deliveries and Patriot batteries improving intercept rates"},
                ],
            },
            "catalysts": ["Winter 2026-27 planning", "Air defense deliveries", "Grid resilience investments"],
            "last_reasoning": "Russia has demonstrated willingness to mass drone strikes (108+ per night). Energy grid remains priority target. Ukraine's improved air defense lowers but does not eliminate risk.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
    ],
    "us_china": [
        {
            "id": "us_china_taiwan_tensions",
            "confidence": 48,
            "trend": "stable",
            "evidence": {
                "for": [
                    {"source": "PRC military posture", "detail": "Continued exercises and patrols near Taiwan"},
                    {"source": "Xi warning at summit", "detail": "Direct threat issued during Trump-Xi engagement"},
                ],
                "against": [
                    {"source": "Mutual economic dependency", "detail": "Both sides have strong incentives to avoid conflict"},
                    {"source": "US deterrence posture", "detail": "Public US commitment to Taiwan defense unambiguous"},
                ],
            },
            "catalysts": ["Trump-Xi summit outcomes", "PRC military exercises", "US arms sales to Taiwan"],
            "last_reasoning": "Tensions remain elevated but structurally bounded. Neither side has the appetite or readiness for kinetic conflict. Rhetoric exceeds risk.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "us_china_tech_decoupling",
            "confidence": 82,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Semiconductor export controls", "detail": "US expanding chip equipment restrictions to allies"},
                    {"source": "Tech alliance building", "detail": "Chip 4, US-Japan-Netherlands coordination deepening"},
                    {"source": "China response", "detail": "PRC accelerating domestic semiconductor production"},
                ],
                "against": [
                    {"source": "Implementation gaps", "detail": "Export controls leak through third countries"},
                ],
            },
            "catalysts": ["ASML restrictions", "Huawei sanctions review", "PRC semiconductor investment results"],
            "last_reasoning": "Tech decoupling has passed the point of no return. Export controls expand, domestic production accelerates on both sides. The question is speed, not direction.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "us_china_trade_tariff_escalation",
            "confidence": 55,
            "trend": "stable",
            "evidence": {
                "for": [
                    {"source": "Trump tariff track record", "detail": "First-term tariff escalation pattern is precedent"},
                    {"source": "Campaign rhetoric", "detail": "Renewed tariff threats on campaign trail"},
                ],
                "against": [
                    {"source": "Phase 1 deal structure", "detail": "Mechanisms for de-escalation already exist"},
                    {"source": "Economic costs", "detail": "Tariffs impose measurable domestic costs"},
                ],
            },
            "catalysts": ["US trade representative review", "China currency policy", "Midterm election cycle"],
            "last_reasoning": "Tariff escalation remains a live option but not a certainty. Depends heavily on domestic political calculus and Trump-Xi personal relationship.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
    ],
    "cartel": [
        {
            "id": "mexico_cartel_violence_trend",
            "confidence": 72,
            "trend": "stable",
            "evidence": {
                "for": [
                    {"source": "Homicide data (INEGI)", "detail": "Sustained high homicide rates across cartel-dominated states"},
                    {"source": "Territorial conflict", "detail": "CJNG-Chapitos-Mayo alliance shifting, triggering violence"},
                ],
                "against": [
                    {"source": "Sheinbaum security strategy", "detail": "Harfuch appointment signals professionalized approach"},
                ],
            },
            "catalysts": ["CJNG leadership targeting", "Chapitos extradition", "Sheinbaum policy review"],
            "last_reasoning": "Violence is structural and self-reinforcing. Government capacity to suppress is limited. Harfuch may temporarily reduce strategic violence but not underlying drivers.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "fentanyl_trafficking_disruption",
            "confidence": 32,
            "trend": "stable",
            "evidence": {
                "for": [
                    {"source": "DEA assessments", "detail": "Seizures down, purity up — supply resilient"},
                    {"source": "Production decentralization", "detail": "Sinaloa synthesis spread to multiple states"},
                ],
                "against": [
                    {"source": "US-Mexico cooperation", "detail": "Increased intelligence sharing and joint operations"},
                ],
            },
            "catalysts": ["Precursor chemical controls", "US-Mexico security coordination", "Fentanyl overdose data"],
            "last_reasoning": "Fentanyl supply chains have proven extraordinarily resilient to enforcement. Production methods decentralize faster than interdiction adapts.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "mexico_us_security_cooperation",
            "confidence": 50,
            "trend": "erratic",
            "evidence": {
                "for": [
                    {"source": "Merida Initiative legacy", "detail": "Two-decade cooperation framework exists"},
                    {"source": "Harfuch-US relationship", "detail": "New SSP has strong US law enforcement ties"},
                ],
                "against": [
                    {"source": "Political sovereignty concerns", "detail": "AMLO/Sheinbaum nationalism limits cooperation depth"},
                    {"source": "US policy unpredictability", "detail": "Trump administration threatens unilateral action"},
                ],
            },
            "catalysts": ["Harfuch-LA meetings", "US designation decisions", "Mexican sovereignty debates"],
            "last_reasoning": "Cooperation exists but is fragile. Each US pressure move triggers Mexican nationalist backlash. Pattern is two steps forward, one step back.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
    ],
    "energy": [
        {
            "id": "brent_crude_price_trajectory",
            "confidence": 68,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Hormuz chokepoint risk", "detail": "Iranian sovereignty claims threatening ~20% of global supply"},
                    {"source": "OPEC+ discipline", "detail": "Production cuts maintained despite US pressure"},
                    {"source": "Global demand", "detail": "Demand resilient in India and China"},
                ],
                "against": [
                    {"source": "US strategic release", "detail": "SPR release capability caps extreme upside"},
                    {"source": "Demand destruction risk", "detail": "High prices eventually reduce consumption"},
                ],
            },
            "catalysts": ["Hormuz transit fee imposition", "OPEC+ meeting decisions", "Iran deal resolution"],
            "last_reasoning": "Supply-side risks dominate. Hormuz disruption alone could add $15-20/bbl. OPEC+ has pricing power. Demand side is secondary to supply constraints.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
        {
            "id": "energy_supply_disruption_risk",
            "confidence": 58,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Multiple chokepoints", "detail": "Hormuz, Bab el-Mandeb, and Suez all under elevated threat"},
                    {"source": "Underinvestment", "detail": "Years of underinvestment in production capacity constrains supply"},
                ],
                "against": [
                    {"source": "LNG capacity growth", "detail": "New US and Qatar LNG capacity coming online"},
                    {"source": "Renewables growth", "detail": "Record renewable installations offset some fossil disruption risk"},
                ],
            },
            "catalysts": ["Hormuz escalation", "Houthi Red Sea operations", "Critical energy infrastructure attacks"],
            "last_reasoning": "Chokepoint risk is increasing but not yet realized. The probability of at least one significant supply disruption within 6 months is elevated.",
            "resolution_date": "2026-09-01T14:00:00Z",
        },
        {
            "id": "critical_mineral_supply_chain",
            "confidence": 72,
            "trend": "upward",
            "evidence": {
                "for": [
                    {"source": "Export controls", "detail": "China rare earth export restrictions expanding"},
                    {"source": "US IRA implementation", "detail": "Domestic critical mineral processing investments accelerating"},
                ],
                "against": [
                    {"source": "Processing concentration", "detail": "China controls ~60% of rare earth processing — hard to bypass"},
                ],
            },
            "catalysts": ["Chinese export control changes", "IRA implementation", "New mining project approvals"],
            "last_reasoning": "Critical mineral supply chains are being weaponized as geopolitical leverage. Decoupling is real but takes 5-10 years given processing concentration.",
            "resolution_date": "2026-12-31T14:00:00Z",
        },
    ],
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[seed_desks {ts}] {msg}", file=sys.stderr, flush=True)


def load_state(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "version": 2,
            "cycle": 0,
            "last_run": dt.datetime.now(dt.timezone.utc).isoformat(),
            "active_narratives": {},
            "source_trust": {},
            "weak_signals": [],
            "narrative_drift": {},
            "escalation_queue": [],
            "token_economics": {
                "total_spent_cents": 0,
                "cycles_completed": 0,
                "avg_cost_per_cycle": 0,
                "daily_spent_cents": 0,
            },
            "operational_state": {"healthy": True, "last_error": None},
        }


def save_state(path: pathlib.Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
    log(f"Saved state to {path}")


def load_config(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"desks": {}}


def save_config(path: pathlib.Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))
    log(f"Saved config to {path}")


def seed_desk(state: dict, desk_id: str, narratives: list, config: dict) -> dict:
    """Add seed narratives for a desk to the cognition state."""
    now = dt.datetime.now(dt.timezone.utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    added = 0

    for seed in narratives:
        nid = seed["id"]
        if nid in state.get("active_narratives", {}):
            log(f"  Narrative '{nid}' already exists — skipping")
            continue

        entry = {
            "id": nid,
            "confidence": seed["confidence"],
            "trend": seed["trend"],
            "created": now_str,
            "last_updated": now_str,
            "cycle_created": state.get("cycle", 0),
            "cycle_updated": state.get("cycle", 0),
            "evidence": seed.get("evidence", {"for": [], "against": []}),
            "catalysts": seed.get("catalysts", []),
            "last_reasoning": seed.get("last_reasoning", ""),
            "resolution_date": seed.get("resolution_date"),
        }

        state.setdefault("active_narratives", {})[nid] = entry

        # Add source trust entries for evidence sources
        for dir_key in ["for", "against"]:
            for ev in seed.get("evidence", {}).get(dir_key, []):
                source = ev.get("source", "")
                if source and source not in state.get("source_trust", {}):
                    state.setdefault("source_trust", {})[source] = {
                        "source_id": source,
                        "admiralty": "B2",
                        "track_record": 0.6,
                        "total_assessments": 1,
                        "created": now_str,
                        "last_updated": now_str,
                        "notes": [f"Seeded during Philby desk initialization"],
                    }

        added += 1
        log(f"  Added narrative: {nid} ({seed['confidence']}%)")

    # Mark desk as seeded in config
    if desk_id in config.get("desks", {}):
        config["desks"][desk_id]["seeded"] = True
        log(f"  Desk '{desk_id}' marked as seeded ✅")

    return state


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Philby Desk Seedling")
    parser.add_argument("--desk", default="", help="Seed a specific desk (default: all unseeded)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no changes")
    parser.add_argument("--force", action="store_true", help="Re-seed even if already seeded")
    args = parser.parse_args()

    state = load_state(COGNITION_STATE)
    config = load_config(PHILBY_CONFIG)
    desks_config = config.get("desks", {})

    if args.desk:
        # Seed specific desk
        if args.desk not in SEED_NARRATIVES:
            log(f"ERROR: No seed data for desk '{args.desk}'. Available: {', '.join(SEED_NARRATIVES.keys())}")
            return 1
        targets = {args.desk: SEED_NARRATIVES[args.desk]}
    else:
        # Seed all unseeded desks
        targets = {}
        for did, dconfig in desks_config.items():
            if not dconfig.get("seeded", False) or args.force:
                if did in SEED_NARRATIVES:
                    targets[did] = SEED_NARRATIVES[did]
                else:
                    log(f"  No seed data for desk '{did}' — skipping")

    if not targets:
        log("No desks to seed (all seeded already). Use --desk <id> or --force to re-seed.")
        return 0

    log(f"Seeding {len(targets)} desk(s): {', '.join(targets.keys())}")
    if args.dry_run:
        for did, narratives in targets.items():
            log(f"  [DRY RUN] Would add {len(narratives)} narrative(s) to '{did}'")
        return 0

    for did, narratives in targets.items():
        pre_count = len(state.get("active_narratives", {}))
        state = seed_desk(state, did, narratives, config)
        post_count = len(state["active_narratives"])
        log(f"  Desk '{did}': {pre_count} → {post_count} total narratives")

    # Save updated state
    save_state(COGNITION_STATE, state)
    save_config(PHILBY_CONFIG, config)

    total = sum(len(n) for n in targets.values())
    log(f"✅ Seeded {total} narratives across {len(targets)} desk(s)")
    print(f"✅ Philby desks seeded: {', '.join(targets.keys())} ({total} narratives)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
