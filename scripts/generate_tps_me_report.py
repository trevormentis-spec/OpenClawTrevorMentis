# GATE_EXEMPT: Routes through llm_gate.route() before generation. TPS orchestration pipeline.
#!/usr/bin/env python3
"""Regenerate the Middle East Security Report through the full TPS pipeline.

Uses: planner, orchestrator, generators (mermaid, matplotlib, timeline),
      PDF builder with asset injection, provenance, QC watermark.

Usage:
    python3 scripts/generate_tps_me_report.py                    # Generate
    python3 scripts/generate_tps_me_report.py --send             # + email
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Route through gate ────────────────────────────────────────────────────────
sys.path.insert(0, str(REPO_ROOT))
from analyst.llm_gate import route

ROUTING_LOG = REPO_ROOT / "memory" / "llm-routing-log.jsonl"

metadata = {"target_words": 4000, "scenarios": 3, "audience": "family_office", "has_recommendations": True}
decision = route("flagship_document", metadata)
print(f"ROUTING: {decision.model} via {decision.provider} — ${decision.estimated_cost_usd}")

# Log routing
record = {"model": decision.model, "provider": decision.provider,
    "estimated_cost_usd": decision.estimated_cost_usd, "justification": decision.justification,
    "task_type": "flagship_document", "metadata": metadata,
    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()}
ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(ROUTING_LOG, "a") as f:
    f.write(json.dumps(record) + "\n")

# ── Generate the report content via Opus ──────────────────────────────────────
with open(REPO_ROOT / ".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))
or_key = env.get("OPENROUTER_API_KEY", "")

system = """You are a senior Middle East security analyst. Produce a subscriber-grade assessment.

Title: "Security Situation in the Middle East — May 2026 Assessment"

Structure:
1. BLUF
2. Key Developments (table with Admiralty + Kent)
3. Iran Nuclear & Military Posture
4. Israel Multi-Front Dynamics
5. Gulf Security & Energy
6. Regional Diplomacy & Ceasefire Status
7. Watch Indicators — Next 30 Days
8. Strategic Implications for EM Investors

Style: Every claim sourced. Kent bands. Admiralty ratings. No filler."""

user = """Key data points May 15-20, 2026:
- US-Iran ceasefire holding but fragile — indirect Oman talks ongoing
- Iran warns 'many more surprises' if conflict resumes
- IRGC struck US/Israel-linked groups
- Israel killed Hamas military chief in Gaza; Gaza: 6 killed, 40 injured
- Hezbollah drone attack wounded 3 near Rosh Hanikra
- UAE Barakah nuclear plant drone strike; power restored, IAEA monitoring
- Israel intercepted Gaza flotilla near Cyprus; 400+ detained
- Iran reconstituting military during ceasefire (ISW)
- Hormuz tensions elevated; US held off strike after Gulf allies pressure"""

payload = json.dumps({"model": decision.model,
    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    "max_tokens": 8192, "temperature": 0.3}).encode()

req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
    data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {or_key}",
        "HTTP-Referer": "https://github.com/trevormentis-spec"})
with urllib.request.urlopen(req, timeout=180) as resp:
    data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    print(f"GENERATED: {len(content)} chars, {usage.get('prompt_tokens',0)} in, {usage.get('completion_tokens',0)} out")

md_path = REPO_ROOT / "memory" / "middle-east-report-tps.md"
md_path.write_text(content)

# ── TPS Pipeline ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(REPO_ROOT / "trevor-presentational-suite"))
from core.schemas import IngestedBrief, IngestSection, IngestSource, IngestJudgment, AssetSpec, AssetKind, PresentationPlan, DeliverableKind
from core.planner import plan_from_brief
from core.orchestrator import execute_plan, register_all_generators
from deliverables.pdf_builder import PDFBuilder
from core.style_director import inject_brand_css

print("\n--- TPS: Registering generators ---")
register_all_generators()

# Build IngestedBrief
import re
sections_data = []
current_section = None
for line in content.split('\n'):
    h2 = re.match(r'^## (.+)', line)
    if h2:
        if current_section: sections_data.append(current_section)
        current_section = {'title': h2.group(1), 'body': []}
    elif current_section:
        current_section['body'].append(line)
if current_section: sections_data.append(current_section)

sections = []
for s in sections_data[:10]:
    body = '\n'.join(s['body'][:30])[:2000]
    sections.append(IngestSection(title=s['title'][:80], body=body, judgments=[], sources=[], subsections=[]))

brief = IngestedBrief(title="Middle East Security Situation — May 2026 Assessment", date="2026-05-20",
    word_count=len(content.split()), sections=sections)
print(f"Brief: {brief.title}, {len(brief.sections)} sections")

# Plan
plan = plan_from_brief(brief, max_assets=8)
print(f"Plan: {len(plan.assets)} assets")

for a in plan.assets:
    print(f"  → {a.kind.value} via {a.generator}: \"{a.title[:50]}\"")

# Execute (LIVE — generate actual charts)
import tempfile
_tmp = tempfile.mkdtemp(prefix="tps_me_")
print("\n--- Executing plan (LIVE) ---")
results = execute_plan(plan, output_dir=_tmp, brief_id="me-may-2026")
print(f"Execution: {results.success_count} success, {results.failure_count} failures")
for aid, out in results.outputs.items():
    print(f"  ✅ {aid}: {out[:60]}")

# Build PDF
print("\n--- Building PDF ---")
out_dir = REPO_ROOT / "memory" / "me-tps-report"
out_dir.mkdir(parents=True, exist_ok=True)
pdf_path = out_dir / "middle-east-security-tps.pdf"

builder = PDFBuilder()
builder.build(brief_json={'title': brief.title, 'produced_at': '2026-05-20'}, plan=plan, asset_outputs=results.outputs, provenance_records=[], output_path=str(pdf_path))
print(f"PDF: {pdf_path} ({pdf_path.stat().st_size} bytes)")

# Save generation log
log = {
    "routing": {"model": decision.model, "provider": decision.provider, "cost": decision.estimated_cost_usd},
    "generation": {"chars": len(content), "tokens_in": usage.get("prompt_tokens",0), "tokens_out": usage.get("completion_tokens",0)},
    "plan": {"assets": len(plan.assets), "deliverables": [d.value for d in plan.deliverables]},
    "execution": {"successes": list(results.outputs.keys()), "failures": list(results.errors.keys())},
    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
}
(out_dir / "generation-log.json").write_text(json.dumps(log, indent=2))
print(f"Log: {out_dir}/generation-log.json")

# Email
if "--send" in sys.argv:
    import base64
    from agentmail import AgentMail
    client = AgentMail(api_key=env.get("AGENTMAIL_API_KEY", ""))
    pdf_bytes = pdf_path.read_bytes()
    client.inboxes.messages.send(
        inbox_id="trevor_mentis@agentmail.to", to="roderick.jones@gmail.com",
        subject="Middle East Security — Full TPS Presentation",
        text="Generated through the presentation suite with chart assets.",
        attachments=[{"filename": "middle-east-security-tps.pdf", "content": base64.b64encode(pdf_bytes).decode()}],
    )
    print("Emailed.")
PYEOF