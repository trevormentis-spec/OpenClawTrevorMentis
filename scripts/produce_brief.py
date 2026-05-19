#!/usr/bin/env python3
"""Produce subscriber brief through llm_gate routing — used by main thread / orchestrator.

Usage:
    python3 scripts/produce_brief.py --task subscriber_brief --out memory/brief.md
"""
import sys, json, os, urllib.request, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from analyst.llm_gate import route

ROUTING_LOG = pathlib.Path('memory/llm-routing-log.jsonl')

def log_routing(decision, task_type, metadata):
    record = {
        'model': decision.model, 'provider': decision.provider,
        'estimated_cost_usd': decision.estimated_cost_usd,
        'fallback_chain': decision.fallback_chain,
        'justification': decision.justification,
        'task_type': task_type, 'metadata': metadata,
        'quality_gates': decision.quality_gates,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ROUTING_LOG, 'a') as f:
        f.write(json.dumps(record) + '\n')

def call_model(decision, system, user):
    """Call the provider that the gate selected."""
    metadata = {'target_words': len(user.split()), 'scenarios': 0, 'audience': 'family_office', 'audience_family_office': True}
    log_routing(decision, 'subscriber_brief', metadata)
    
    model = decision.model
    provider = decision.provider
    
    if provider == 'openrouter':
        with open('.env') as f:
            for line in f:
                if line.startswith('OPENROUTER_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    break
        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {key}',
                   'HTTP-Referer': 'https://github.com/trevormentis-spec'}
    elif provider == 'deepseek_direct':
        with open('.env') as f:
            for line in f:
                if line.startswith('DEEPSEEK_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    break
        url = 'https://api.deepseek.com/v1/chat/completions'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}
    else:
        raise ValueError(f'Unknown provider: {provider}')
    
    payload = json.dumps({
        'model': model,
        'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
        'max_tokens': 4096,
        'temperature': 0.3,
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {})
    return content, usage


if __name__ == '__main__':
    decision = route('subscriber_brief', {'target_words': 1800, 'scenarios': 0, 
        'audience': 'family_office', 'audience_family_office': True})
    print(json.dumps({'routing': {
        'model': decision.model, 'provider': decision.provider,
        'cost': decision.estimated_cost_usd, 'justification': decision.justification
    }}, indent=2))
