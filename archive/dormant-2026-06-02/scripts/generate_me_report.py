# GATE_EXEMPT: Routes through llm_gate.route() at line 12 before API call. Endpoint URL is for gate-selected model.
#!/usr/bin/env python3
"""Generate Middle East Security Report via routing gate + render via presentation suite."""
import sys, json, os, urllib.request, datetime, pathlib, io
sys.path.insert(0, '.')
from analyst.llm_gate import route

ROUTING_LOG = pathlib.Path('memory/llm-routing-log.jsonl')

# Route through gate
metadata = {'target_words': 4000, 'scenarios': 3, 'audience': 'family_office', 'has_recommendations': True}
decision = route('flagship_document', metadata)
print(f'ROUTING: {decision.model} via {decision.provider} — ${decision.estimated_cost_usd}')

# Log
record = {'model': decision.model, 'provider': decision.provider,
    'estimated_cost_usd': decision.estimated_cost_usd, 'justification': decision.justification,
    'task_type': 'flagship_document', 'metadata': metadata,
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}
ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(ROUTING_LOG, 'a') as f:
    f.write(json.dumps(record) + '\n')

# Load keys
with open('.env') as f:
    env = dict(line.strip().split('=', 1) for line in f if '=' in line and not line.startswith('#'))
or_key = env.get('OPENROUTER_API_KEY', '')

system = '''You are a senior Middle East security analyst at a top-tier intelligence firm. Produce a subscriber-grade security assessment.

Title: "Security Situation in the Middle East — May 2026 Assessment"

Structure:
1. BLUF (2 paragraphs)
2. Key Developments (5-7 items, each with Admiralty source rating + Kent confidence band)
3. Iran Nuclear & Military Posture
4. Israel Multi-Front Dynamics (Gaza, Lebanon, West Bank, Iran)
5. Gulf Security & Energy (Hormuz, UAE Barakah, Saudi)
6. Regional Diplomacy & Ceasefire Status
7. Humanitarian & Civilian Impact
8. Watch Indicators — Next 30 Days (calendar table with triggers)
9. Strategic Implications for EM Investors

Style: Analyst-to-analyst. Every claim sourced. Kent bands on all judgments. Admiralty ratings. No filler. For a family office with EM exposure assessing regional risk to portfolios.'''

user = """Key data points (May 15-20, 2026):
- US-Iran ceasefire holding but fragile — indirect negotiations ongoing via Oman
- Iran warns of "many more surprises" if conflict resumes — IRGC struck US/Israel-linked groups
- Israel killed Hamas military chief in Gaza; Gaza health ministry: 6 killed, 40 injured in past day
- Hezbollah drone attack on northern Israel wounded 3 civilians near Rosh Hanikra; IDF shelling in response
- UAE Barakah nuclear plant hit by drone strike; power restored, IAEA monitoring
- Israel intercepted Gaza-bound flotilla near Cyprus; 400+ activists detained
- Iran reconstituting military during ceasefire (ISW assessment, May 13)
- Far-right Israeli marchers in Old City chanted "death to Arabs"
- Strait of Hormuz tensions elevated; oil market monitoring
- US held off strike on Iran after Gulf allies pressure — renewed talks gaining momentum"""
    
payload = json.dumps({
    'model': decision.model,
    'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
    'max_tokens': 8192, 'temperature': 0.3,
}).encode()

req = urllib.request.Request(
    'https://openrouter.ai/api/v1/chat/completions',
    data=payload,
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {or_key}',
             'HTTP-Referer': 'https://github.com/trevormentis-spec'}
)
with urllib.request.urlopen(req, timeout=180) as resp:
    data = json.loads(resp.read())
    content = data['choices'][0]['message']['content']
    usage = data.get('usage', {})
    print(f'\nGENERATED: {len(content)} chars, {usage.get("prompt_tokens",0)} in, {usage.get("completion_tokens",0)} out')

# Save markdown
md_path = pathlib.Path('memory/middle-east-report.md')
md_path.write_text(content)
print(f'Markdown saved: {md_path} ({len(content.split())} words)')
PYEOF