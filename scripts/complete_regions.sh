#!/bin/bash
# Complete remaining analysis regions via direct curl
set -uo pipefail

REPO=/home/ubuntu/.openclaw/workspace
WD=/home/ubuntu/trevor-briefings/2026-05-27
LOG=$REPO/logs/complete-regions-$(date -u +%Y-%m-%d).log

source $REPO/.env 2>/dev/null
KEY="$DEEPSEEK_API_KEY"
export KEY

echo "=== $(date -u) ===" | tee -a $LOG

# Remaining regions: south_east_asia, oceania, east_asia, south_asia, prediction_markets
for region in south_east_asia oceania east_asia south_asia prediction_markets; do
    if [ -f "$WD/analysis/${region}.json" ]; then
        echo "[SKIP] $region already exists" | tee -a $LOG
        continue
    fi
    
    echo "--- $region ---" | tee -a $LOG
    
    # Build prompt and payload
    python3 "$REPO/scripts/build_region_payload.py" "$region" "$WD" /tmp/payload_${region}.json 2>&1 | tee -a $LOG
    
    payload_size=$(wc -c < /tmp/payload_${region}.json)
    echo "[$region] payload=$payload_size bytes" | tee -a $LOG
    
    # Call API - try up to 2 times
    success=0
    for attempt in 1 2; do
        echo "[$region] attempt $attempt" | tee -a $LOG
        
        result=$(timeout 180 curl -s -w "\n%{http_code}" --max-time 180 \
            -X POST "https://api.deepseek.com/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $KEY" \
            --data-binary @/tmp/payload_${region}.json 2>&1)
        
        http_code=$(echo "$result" | tail -1)
        body=$(echo "$result" | sed '$d')
        
        if [ "$http_code" = "200" ]; then
            # Extract content and validate JSON
            echo "$body" | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
content = data['choices'][0]['message']['content']
print(f'Content: {len(content)} chars, finish={data[\"choices\"][0][\"finish_reason\"]}')
try:
    pj = json.loads(content)
    pj['model_used'] = 'deepseek/deepseek-v4-pro'
    json.dump(pj, open('$WD/analysis/${region}.json', 'w'), indent=2)
    print(f'SAVED: $WD/analysis/${region}.json')
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f'INVALID JSON: {e}')
    # Try to extract JSON from the response
    import re
    m = re.search(r'\{.*\}', content, re.DOTALL)
    if m:
        try:
            pj = json.loads(m.group())
            pj['model_used'] = 'deepseek/deepseek-v4-pro'
            json.dump(pj, open('$WD/analysis/${region}.json', 'w'), indent=2)
            print(f'EXTRACTED and SAVED')
            sys.exit(0)
        except:
            print(f'Could not extract valid JSON')
    sys.exit(1)
" 2>&1 | tee -a $LOG
            
            if [ $? -eq 0 ]; then
                success=1
                break
            fi
        else
            echo "[$region] HTTP $http_code" | tee -a $LOG
        fi
    done
    
    if [ $success -eq 0 ]; then
        echo "[$region] FAILED after 2 attempts" | tee -a $LOG
    fi
    
    rm -f /tmp/payload_${region}.json
done

echo "=== ALL COMPLETE $(date -u) ===" | tee -a $LOG
