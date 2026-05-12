#!/usr/bin/env python3
"""
Routing scanner — audits which models are ACTUALLY being used vs configured.

Shows the gap between ORCHESTRATION.md policy and operational reality.

Usage:
    python3 scripts/routing_scanner.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Policy from ORCHESTRATION.md
POLICY = {
    "tier_1_strategic": "anthropic/claude-opus-4.7 (via OpenRouter) — exec summary + red-team",
    "tier_2_regional": "deepseek/deepseek-v4-flash (DeepSeek Direct API) — 6 regional analyses",
    "tier_3_conversational": "deepseek/deepseek-v4-flash (DeepSeek Direct API) — all chat, tools, memory",
    "fallback_chain": ["deepseek-chat", "deepseek-v4-pro", "myclaw/minimax-m2.7"],
    "openrouter_policy": "enabled for Tier-1 strategic analysis (Opus 4.7) + specialist models (image gen, video, TTS). Never route DeepSeek models through OpenRouter.",
}


def scan_production_routing() -> list[dict]:
    """Scan all production scripts for actual model/provider usage."""
    findings = []
    script_dir = REPO_ROOT / "scripts"
    
    for py_file in sorted(script_dir.glob("*.py")):
        content = py_file.read_text()
        # Find model assignments
        for m in re.finditer(r'--model\s+[\'"]([^\'"]+)[\'"]', content):
            findings.append({
                "file": py_file.name,
                "type": "model",
                "value": m.group(1),
                "line_content": content[max(0, m.start()-30):m.end()+30].strip(),
            })
        for m in re.finditer(r'--provider\s+[\'"]([^\'"]+)[\'"]', content):
            findings.append({
                "file": py_file.name,
                "type": "provider",
                "value": m.group(1),
                "line_content": content[max(0, m.start()-30):m.end()+30].strip(),
            })
        # Also find model= in kwargs
        for m in re.finditer(r'model\s*=\s*[\'"]([^\'"]+)[\'"]', content):
            if m.group(1) not in [f["value"] for f in findings if f["type"] == "model"]:
                findings.append({
                    "file": py_file.name,
                    "type": "model (kwarg)",
                    "value": m.group(1),
                    "line_content": content[max(0, m.start()-30):m.end()+30].strip(),
                })

    return findings


def check_skill_routing() -> list[dict]:
    """Check which skills use which models."""
    findings = []
    # Check orchestrate.py for actual cron routing
    orch_file = REPO_ROOT / "skills" / "daily-intel-brief" / "scripts" / "orchestrate.py"
    if orch_file.exists():
        content = orch_file.read_text()
        for m in re.finditer(r'--model\s+[\'"]?([^\'"\s]+)[\'"]?', content):
            findings.append({
                "file": "orchestrate.py (CRON PRODUCTION)",
                "type": "model",
                "value": m.group(1),
            })
        for m in re.finditer(r'--provider\s+[\'"]?([^\'"\s]+)[\'"]?', content):
            findings.append({
                "file": "orchestrate.py (CRON PRODUCTION)",
                "type": "provider",
                "value": m.group(1),
            })
        # Check for --tier2-model flag
        for m in re.finditer(r'--tier2-model\s+[\'"]?([^\'"\s]+)[\'"]?', content):
            findings.append({
                "file": "orchestrate.py (CRON — tier2)",
                "type": "model",
                "value": m.group(1),
            })
        # Check for argparse default values
        for m in re.finditer(r'default=[\'"]?([^\'"\s)}]+)[\'"]?', content):
            val = m.group(1)
            # Filter to model-like values (contain slash or model name patterns)
            if '/' in val and not val.startswith('anthropic') and not val.startswith('deepseek'):
                continue
            if val in ('anthropic/claude-opus-4.7', 'deepseek/deepseek-v4-flash',
                       'deepseek/deepseek-v4-pro', 'openrouter'):
                ftype = 'model' if val.startswith('anthropic') or val.startswith('deepseek') else 'provider'
                findings.append({
                    "file": "orchestrate.py (argparse default)",
                    "type": ftype,
                    "value": val,
                })

    return findings


def main() -> int:
    print("=" * 60)
    print("ROUTING AUDIT — Policy vs Reality")
    print("=" * 60)

    print("\n## ORCHESTRATION.md Policy")
    for k, v in POLICY.items():
        print(f"  {k}: {v}")

    print("\n## Actual Production Routing (cron pipeline)")
    findings = check_skill_routing()
    for f in findings:
        print(f"  {f['file']}: {f['type']}={f['value']}")

    print("\n## Script-level Model References")
    findings = scan_production_routing()
    if findings:
        for f in findings:
            print(f"  {f['file']}: {f['type']}={f['value']}")
    else:
        print("  (none detected)")

    print("\n## Policy Violations")
    violations = []
    all_findings = findings + check_skill_routing()
    # Group by file to pair models with their providers
    for f in all_findings:
        val = f["value"]
        ftype = f.get("type", "")
        fname = f.get("file", "")
        
        if ftype == "provider" and val == "openrouter":
            # Check if this provider is paired with a DeepSeek model (violation)
            # or with Opus/Claude (allowed per policy)
            peer_models = [
                x["value"] for x in all_findings
                if x.get("file") == fname and x.get("type", "") in ("model",)
            ]
            # Only flag as violation if ALL peer models are DeepSeek
            # (if mixed, assume tiered routing with separate providers at runtime)
            non_deepseek = [m for m in peer_models if "deepseek" not in m.lower()]
            if non_deepseek and all("deepseek" in m.lower() for m in peer_models if m not in non_deepseek):
                # Mixed — non-DeepSeek (Opus) uses OpenRouter, DeepSeek uses Direct
                pass
            elif peer_models and all("deepseek" in m.lower() for m in peer_models):
                violations.append(f"  ⚠️  DeepSeek model routed through OpenRouter in {fname} — use DeepSeek Direct API")
            else:
                # No models detected or mixed — assume OK
                pass
        elif ftype == "provider" and val not in ("deepseek", "openrouter"):
            violations.append(f"  ⚠️  Unrecognized provider in {fname}: {val}")

    if not violations:
        print("  ✅ No routing policy violations detected")
    else:
        for v in violations:
            print(v)

    print("\n## Summary")
    cron_providers = set(f["value"] for f in check_skill_routing() 
                         if f["type"] == "provider")
    cron_models = set(f["value"] for f in check_skill_routing() 
                      if f["type"] == "model")
    print(f"  Cron provider: {', '.join(sorted(cron_providers))}")
    print(f"  Cron models: {', '.join(sorted(cron_models))}")
    
    # Check tier consistency against policy
    policy_models = {
        POLICY['tier_1_strategic'].split(' ')[0],
        POLICY['tier_2_regional'].split(' ')[0],
        POLICY['tier_3_conversational'].split(' ')[0],
    }
    # Filter out known fallback/resilience models
    policy_models = {m for m in policy_models if m.startswith('anthropic') or m.startswith('deepseek')}
    
    if cron_models.issubset(policy_models | set(POLICY['fallback_chain'])):
        print(f"\n  ✅ Routing consistent with policy")
    else:
        extra = cron_models - policy_models - set(POLICY['fallback_chain'])
        print(f"\n  ⚠️  ROUTING DRIFT: {extra} not in policy tiers or fallback chain")
        print(f"     Action: Update ORCHESTRATION.md to include these models, or remove from cron")

    return 0


if __name__ == "__main__":
    sys.exit(main())
