#!/usr/bin/env python3
"""Process remaining regions via OpenRouter (reliable connectivity)."""
import json, subprocess, re
from pathlib import Path

WORKSPACE = Path('/home/ubuntu/.openclaw/workspace')
WD = Path('/home/ubuntu/trevor-briefings/2026-05-27')
LOG = WORKSPACE / 'logs/openrouter-regions-2026-05-27.log'
logf = open(LOG, 'a')

KEY = ''
for line in open(WORKSPACE / '.env'):
    if line.startswith('OPENROUTER_API_KEY'):
        KEY = line.split('=', 1)[1].strip().strip("'\"").strip()
        break

md = (WORKSPACE / 'skills/daily-intel-brief/references/deepseek-prompts.md').read_text()
m = re.search(r'```\n(.*?)```', md, re.DOTALL)
sys_p = m.group(1).strip() if m else ''
parts = md.split('## Regional Analyst Prompt')
rt = parts[1].split('```')[1].strip() if len(parts) > 1 and '```' in parts[1] else ''
incs = json.load(open(WD / 'raw/incidents.json')).get('incidents', [])

ad = WD / 'analysis'
ad.mkdir(exist_ok=True)

TODO = [
    ('oceania', 'Oceania', 'OCE'),
    ('east_asia', 'East Asia', 'EAS'),
    ('south_asia', 'South Asia', 'SAS'),
    ('prediction_markets', 'Prediction Markets', 'PRD'),
]

for snake, label, short in TODO:
    if (ad / f'{snake}.json').exists():
        continue
    
    ri = [i for i in incs if i.get('region') == snake]
    user = rt.replace('{date_utc}', '2026-05-27')
    user = user.replace('{region_label}', label)
    user = user.replace('{region_snake}', snake)
    user = user.replace('{region_short}', short)
    user = user.replace('{incidents_json_for_region}', json.dumps(ri, indent=2))
    user = user.replace('{low_incident_warning}', '')
    user = user.replace('{iw_board}', 'No standing I&W board.')
    user += '\n\nIMPORTANT: Output ONLY valid JSON. No other text.'

    # Truncate if needed
    for t in [14000, 12000, 10000, 8000, 6000, 4000]:
        u2 = user[:t] + '\n\n[DATA TRUNCATED]' if len(user) > t else user
        payload_test = json.dumps({
            'model': 'deepseek/deepseek-v4-pro',
            'messages': [{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': u2}]
        })
        if len(payload_test.encode()) <= 25000:
            user = u2
            break

    payload = {
        'model': 'deepseek/deepseek-v4-pro',
        'messages': [{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': user}],
        'temperature': 0.3,
        'max_tokens': 16384,
    }

    tmp = Path(f'/tmp/or_{snake}.json')
    tmp.write_text(json.dumps(payload))
    sz = tmp.stat().st_size
    
    msg = f'[{snake}] {len(ri)} incs, payload={sz} bytes'
    print(msg, flush=True)
    logf.write(msg + '\n')
    logf.flush()

    for attempt in range(2):
        try:
            r = subprocess.run([
                'curl', '-s', '-w', '\n%{http_code}',
                '-X', 'POST', 'https://openrouter.ai/api/v1/chat/completions',
                '-H', 'Content-Type: application/json',
                '-H', f'Authorization: Bearer {KEY}',
                '-H', 'HTTP-Referer: https://github.com/trevormentis-spec',
                '-H', 'X-Title: TREVOR Intel Brief',
                '--data-binary', f'@{tmp}',
                '--connect-timeout', '15',
                '--max-time', '120',
            ], capture_output=True, text=True, timeout=130)

            out = r.stdout
            idx = out.rfind('\n')
            http = out[idx + 1:].strip() if idx >= 0 else '000'
            body = out[:idx] if idx >= 0 else out

            if http.startswith('2'):
                data = json.loads(body)
                content = data['choices'][0]['message']['content']
                try:
                    pj = json.loads(content)
                    pj['model_used'] = 'deepseek/deepseek-v4-pro'
                    (ad / f'{snake}.json').write_text(json.dumps(pj, indent=2))
                    ok = f'[{snake}] OK: {len(content)} chars, finish={data["choices"][0]["finish_reason"]}'
                    print(ok, flush=True)
                    logf.write(ok + '\n')
                    logf.flush()
                    break
                except json.JSONDecodeError:
                    err = f'[{snake}] invalid JSON ({len(content)} chars)'
                    print(err, flush=True)
                    logf.write(err + '\n')
                    logf.flush()
            else:
                err = f'[{snake}] HTTP {http}: {body[:200]}'
                print(err, flush=True)
                logf.write(err + '\n')
                logf.flush()
        except subprocess.TimeoutExpired:
            tm = f'[{snake}] TIMEOUT attempt {attempt+1}'
            print(tm, flush=True)
            logf.write(tm + '\n')
            logf.flush()
        except Exception as e:
            exc = f'[{snake}] {type(e).__name__}: {e}'
            print(exc, flush=True)
            logf.write(exc + '\n')
            logf.flush()

    tmp.unlink(missing_ok=True)

done = 'ALL REGIONS COMPLETE'
print(done, flush=True)
logf.write(done + '\n')
logf.close()
