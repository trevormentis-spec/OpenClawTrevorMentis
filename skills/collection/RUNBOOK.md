# TREVOR Web Collection — RUNBOOK

## Failure Modes & Recovery

### 1. Site changes API shape
**Symptoms:** Collection returns empty, 404, or malformed data for a site that previously worked.
**Action:**
1. Re-run `reverse-api-engineer agent` for the affected site
2. `reverse-api-engineer engineer` to generate updated spec
3. Compare old spec (`skills/collection/_specs/<site>/spec.json`) with new output
4. If request shape changed: update client code
5. If response shape changed: update parsing logic
6. Bump `site_spec_version` in collection records
7. **⚠️ Trigger Eclipse/SPS/NOVA review** — API shape changes on an OSINT-relevant source may indicate:
   - Site hardening against automated access (signals broader threat posture shift)
   - Platform migration to new backend (signals investment/priority change)
   - Security incident on the platform (signals data integrity concerns)

### 2. Anti-bot detection escalation (Cloudflare, DataDome, Akamai)
**Symptoms:** HTTP 403/503, CAPTCHA, empty responses with JS challenge content.
**Action:**
1. Retry with openweb's browser-backed fetch (`--transport browser`)
2. If that fails: log as DOM fallback with reason string
3. **⚠️ Flag for TREVOR Review** — hardened anti-bot on an OSINT-relevant source is itself a signal
4. Consider alternative collection methods (RSS, third-party aggregators, manual review)

### 3. Rate limiting (HTTP 429)
**Symptoms:** Consistent 429 responses after a few requests.
**Action:**
1. Check `Retry-After` header; respect it
2. Log the rate limit incident to `tasks/collection_rate_limits.jsonl`
3. Implement exponential backoff: wait 2^n seconds, max 5 retries
4. If persistent (>3 consecutive rate limits across multiple sessions): flag for human review
5. Consider rotating user-agent or introducing longer delays between calls

### 4. Authentication failure
**Symptoms:** 401/403, redirect to login page, empty results requiring auth.
**Action:**
1. Check if openweb's auth bootstrap needs to be re-run (managed Chrome session expired)
2. For reverse-engineered specs: check if session token/cookie has expired
3. Re-authenticate via browser session
4. Update stored credentials (if applicable)

### 5. WebSocket connection failure
**Symptoms:** WebSocket client connects but receives no data, or connection drops.
**Action:**
1. Verify WebSocket endpoint is still active (check with `wscat` or browser DevTools)
2. Re-capture WebSocket frames to check if protocol changed
3. Update WebSocket client code
4. Consider polling fallback if REST endpoint exists

### 6. BigQuery write failure
**Symptoms:** Collection succeeds but record write fails.
**Action:**
1. Check if `tasks/collection_records.jsonl` is writable
2. If file is locked/corrupt, create backup file: `collection_records_fallback.jsonl`
3. Continue with collection — records can be replayed from the JSONL

---

## Collection Method Downgrade Protocol

When a collection method downgrades (e.g., openweb → reverse_engineered → dom):

| Downgrade | Likely Cause | Action Required |
|---|---|---|
| openweb → reverse_engineered | Spec not built yet | Build spec (normal workflow) |
| reverse_engineered → dom | API blocked/removed | Flag for Eclipse/SPS/NOVA review |
| dom → manual | CAPTCHA or JS challenge | Flag for human intervention |
| dom → failed | Site down or permanently locked | Remove from active collection; flag for review |

Any downgrade from `reverse_engineered` to `dom` triggers an automatic Eclipse/SPS/NOVA review flag — the site may be hardening its perimeter, which is analytically relevant beyond the collection failure itself.

---

## Normal Operations

### Daily health check
```bash
# Quick test: 3 representative sites
npx @openweb-org/openweb wikipedia getPageSummary '{"title":"Health"}'
openweb reuters search '{"q":"test"}' 2>/dev/null | head -1
openweb coingecko getPrices '{"ids":"bitcoin"}' 2>/dev/null | head -1
```

### Adding a new site (from scratch)
```bash
# 1. Discover via reverse-api-engineer
cd skills/collection/reverse-api-engineer
uv run reverse-api-engineer agent --url <target-url>
uv run reverse-api-engineer engineer --run <run-id>

# 2. Test
uv run reverse-api-engineer run <run-id>

# 3. Register
mkdir -p ../_specs/<site>
cp ~/.reverse-api-engineer/scripts/<run>/generated_spec.json ../_specs/<site>/spec.json
cp ~/.reverse-api-engineer/scripts/<run>/generated_script.py ../_specs/<site>/client.py
```

### Updating a spec
```bash
# If site API changed, re-run reverse-api-engineer with --diff
cd skills/collection/reverse-api-engineer
uv run reverse-api-engineer agent --url <target-url> --cookie reuse
uv run reverse-api-engineer engineer --run <run-id> --diff ../_specs/<site>/spec.json
```
