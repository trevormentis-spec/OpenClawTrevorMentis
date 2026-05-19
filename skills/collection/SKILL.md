---
name: trevor-web-collection
description: |
  Use for any collection task that involves extracting structured data from a website.
  Always prefer programmatic API access (openweb spec → reverse-engineered API → window globals → DOM scrape, in that order).
  Trigger on: "collect from <site>", "pull data from <url>", "scrape", "monitor <web platform>",
    "get the latest <articles|posts|data> from <site>", "fetch <resource> from <site>",
    "load <site> <content>", "search <site> for <query>",
    "pull <site>", "get <site> <section>", "extract <data> from <site>".
metadata:
  version: "1.0.0"
  openclaw:
    requires:
      bins: [openweb, node, python3, uv]
      env: [ANTHROPIC_API_KEY, OPENWEB_HOME]
---

# TREVOR Web Collection — OpenWeb + Reverse-API-Engineer

**Collection hierarchy (always follow this order):**

```
openweb API spec (94 sites) → reverse-engineered API spec → window globals → DOM scrape
```

## Step 1 — Check openweb built-ins

List available sites:
```bash
npx @openweb-org/openweb sites | grep -i <site>
```

If found, call directly:
```bash
npx @openweb-org/openweb <site> <operation> '<params>'
```

Structured JSON out. Done. No DOM interaction required.

**Supported operations per site:**
```bash
npx @openweb-org/openweb <site>     # shows available operations + schema
```

### Auth handling
openweb resolves cookies, JWT, CSRF chains, and exchange protocols automatically. If the site requires login, openweb uses a managed Chrome session for auth bootstrap, then switches to HTTP for data collection. You never touch tokens manually.

---

## Step 2 — Reverse-engineer (site not in openweb)

If the target site is not in openweb's built-in list, generate a spec:

### 2a — Capture HAR traffic for one representative action

```bash
cd skills/collection/reverse-api-engineer
uv run reverse-api-engineer agent --url <target-url>
```

This launches a Playwright browser. Navigate to the site, perform ONE representative user action (search, view profile, load feed), then close the browser. The tool captures all network traffic as HAR.

### 2b — Generate API client + spec

```bash
uv run reverse-api-engineer engineer --run <latest-run-id>
```

Claude analyzes the HAR and emits:
- **(a)** A runnable API client script `~/.reverse-api-engineer/scripts/<run>/generated_script.py`
- **(b)** An openweb-compatible site spec stub in `skills/collection/_specs/<site>/`

### 2c — Test the generated client

```bash
cd skills/collection/reverse-api-engineer
uv run reverse-api-engineer run <run-id>
```

If the client works (returns structured data), proceed to 2d. If not, capture additional HAR traces covering edge cases (pagination, auth refresh, error responses) and re-run the engineer step.

### 2d — Register the spec for future use

```bash
mkdir -p skills/collection/_specs/<site>
cp ~/.reverse-api-engineer/scripts/<run>/generated_spec.json skills/collection/_specs/<site>/spec.json
cp ~/.reverse-api-engineer/scripts/<run>/generated_script.py skills/collection/_specs/<site>/client.py
```

Once registered, future collection from this site goes through Step 1 (check openweb built-ins, then check _specs).

---

## Step 3 — Fallback to DOM/browser automation

Only if Steps 1 and 2 both fail — site has no API, HAR confirms API is dead, or site uses aggressive anti-bot that blocks both approaches — fall back to:

- **Claude for Chrome** (browser automation via extension)
- **Playwright** (programmatic browser automation)
- **Puppeteer** (headless Chrome)

Log the reason for fallback in the output record (see BigQuery section).

---

## Blockers — Explicit Handling

### PII filters on browser extensions
When a browser extension blocks visible data (e.g., LinkedIn PII filters on extension-based collection):
- **Do not** try to bypass the extension — that route is blocked by design
- **Route through openweb's HTTP transport** instead. openweb calls the site's own API endpoints directly, bypassing DOM-layer PII filters entirely
- If openweb doesn't have the site, generate an API spec via reverse-api-engineer (Step 2) that targets the raw API endpoints rather than the rendered page

### Infinite scroll
Infinite scroll is a DOM-level pattern. The underlying API is almost always paginated via cursor or offset:
1. Open the browser DevTools Network tab
2. Scroll once — capture the XHR/fetch call that loads the next page
3. Identify the pagination parameter (`cursor`, `offset`, `page`, `after`, `since_id`)
4. Replay programmatically: increment the cursor/offset parameter and call the same endpoint
5. openweb specs handle this natively — the spec includes pagination cursors as call parameters

### WebSocket apps
For sites that use WebSockets (real-time feeds, chat, streaming data):
1. Capture WebSocket frames during a session using HAR recording
2. Identify the message protocol (JSON-RPC, custom binary framing, etc.)
3. Build a minimal WebSocket client that connects to the same endpoint and subscribes to the relevant message types
4. Register the WebSocket client as part of the site spec
5. The reverse-api-engineer tool can generate WebSocket client code; if it misses, write the client manually in Python using `websockets` library

---

## BigQuery Pipeline

Every successful collection call must emit a JSON record appended to the existing GDELT/GKG-adjacent collection table:

```json
{
  "source": "wikipedia | reuters | custom_<site>",
  "site_spec_version": "openweb-0.1.6 | rae-<run-id> | manual-v1",
  "method": "openweb | reverse_engineered | dom",
  "nato_admiralty_source_rating": "A | B | C | D | E | F",
  "nato_admiralty_info_rating": "1 | 2 | 3 | 4 | 5 | 6",
  "collected_at": "2026-05-19T17:06:00Z",
  "payload": { "...": "..." }
}
```

**Integration with existing pipeline:**
- Appends to the existing GDELT/GKG-adjacent collection table
- Do NOT create a new table without consulting Roderick
- The wrapper script `scripts/openweb_collect.py` handles record formatting automatically
- Records are written to `tasks/collection_records.jsonl` for pipeline pickup by `collect.py`

## NATO Admiralty Rating — MUST ASSIGN BEFORE WRITE

Every emitted record MUST have non-null `nato_admiralty_source_rating` and `nato_admiralty_info_rating` fields.
If you cannot determine a rating, use the conservative default for the method used.

**Rating assignment rules:**
| Scenario | Source rating | Info rating |
|---|---|---|
| openweb built-in spec (known platform) | B | 2 |
| openweb built-in spec (government/institutional) | A | 2 |
| Reverse-engineered spec (verified API works) | C | 3 |
| Reverse-engineered spec (GraphQL, unverified) | C | 3 |
| DOM scrape (no API available) | D | 4 |
| Window globals extraction | D | 4 |
| User-supplied credentials used | B | 2 |

## PENDING HUMAN ANALYST QC REVIEW

Every collection record must carry this flag. Add it to the payload:
```json
{
  "qc_status": "PENDING_HUMAN_ANALYST_QC_REVIEW",
  ...
}
```
This flag is per-record, not per-report. The analyst reviewing the output is responsible
for verifying source integrity, checking the spec version against the site's current behavior,
and promoting the status to QC_PASS or QC_FAIL.

---

## Failure Modes & Runbook

### Site changes API shape
If a previously working collection starts failing:
1. Re-run reverse-api-engineer to capture new HAR
2. Compare old vs new request/response shapes
3. Update the spec in `skills/collection/_specs/<site>/`
4. Bump the `site_spec_version` in records
5. Run the Eclipse/SPS/NOVA review flag — **site API hardening may signal broader threat posture changes**

### Anti-bot detection escalation
If a site deploys aggressive anti-bot (Cloudflare, DataDome, Akamai) that blocks even API calls:
1. Try openweb's browser-backed fetch (managed Chrome session)
2. If that fails, log as DOM fallback with reason
3. Flag for TREVOR Review — hardened anti-bot on an OSINT-relevant source is itself a signal

### Rate limiting
If 429 received:
1. Respect Retry-After header
2. Log the rate limit event
3. Implement exponential backoff in the wrapper
4. If persistent (>3 consecutive rate limits), flag for human review

---

## Collection Preference — Quick Decision Tree

```
Is site in openweb sites? ──Yes──→ call openweb directly. Done.
        │
        No
        │
        ▼
Run reverse-api-engineer → generates client + spec
        │
        ▼
Does client work? ──Yes──→ register spec → future runs hit openweb
        │
        No
        │
        ▼
Is there an underlying API (found in HAR)? ──Yes──→ hand-write tiny client → register
        │
        No
        │
        ▼
Fall back to Playwright / Claude-for-Chrome DOM automation
```

## Method Downgrade Protocol

When the collection method downgrades (openweb → reverse_engineered → DOM → None):

| Downgrade from | Downgrade to | Action required |
|---|---|---|
| openweb | reverse_engineered | Normal workflow — spec not yet available |
| reverse_engineered | DOM | **⚠️ Trigger Eclipse/SPS/NOVA cross-reference** — site API hardening may be a strategic signal |
| DOM | Failed entirely | Flag for human review — site may be down or blocking |

**Rationale for downgrade→Eclipse/SPS/NOVA:** If a site that previously had a working API
moves it behind aggressive bot detection or removes it entirely, that action may indicate:
- The site detected scanning and hardened its perimeter
- Third-party data access was restricted (regulatory/commercial pressure)
- The site is migrating platforms (legacy API retired before new API is stable)

Any of these is analytically relevant beyond the collection failure. Log the downgrade
reason in the record payload and set `qc_status: DOWNGRADE_REVIEW_NEEDED`.

## Spec Promotion Path

Custom specs live in `skills/collection/_specs/<site>/`. They are NOT auto-registered
in openweb's `src/sites/` directory (which requires a rebuild). The wrapper
`scripts/openweb_collect.py` checks `_specs/` before falling to DOM:

```
openweb sites → miss → check _specs/<site>/ → hit? → use custom spec
                                        → miss? → attempt HAR capture
```

To promote a custom spec into openweb itself would require:
1. Editing `skills/collection/openweb/src/sites/<site>.ts`
2. Running `npm run build`
3. Confirm with Roderick before pushing to public repo

**Do NOT push generated specs to the public openweb repo without Roderick's explicit approval.**
Some collected sites are operationally sensitive — the spec itself can reveal interest.
