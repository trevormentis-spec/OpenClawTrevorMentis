---
name: continuous-cognition
description: Lightweight persistent cognition layer. DeepSeek Flash runs every 15 minutes to summarize events, update confidence state, detect anomalies, evolve source trust, and maintain situational awareness. Escalates to Pro/Opus when thresholds are crossed. No recursive loops, no endless reflection.
metadata:
  author: Trevor
  version: "1.0.0"
  displayName: Continuous Cognition
  difficulty: advanced
---

# Continuous Cognition

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  COGNITION DAEMON (every 15 min)                     │
│                                                      │
│  collect_context() → build_flash_input()             │
│       │                                              │
│       ▼                                              │
│  DeepSeek Flash (cheap, $0.14/M)                     │
│       │                                              │
│       ▼                                              │
│  parse_response() → update_state() → compact()       │
│       │                                              │
│       ▼                                              │
│  check_escalation()                                  │
│    ├── no change → wait 15 min                       │
│    ├── confidence >15pt swing → DeepSeek Pro ($0.44/M)│
│    └── multi-narrative shift → Opus ($5/M)          │
└──────────────────────────────────────────────────────┘
```

## Cognition State

Persistent JSON at `state/cognition_state.json`:

```json
{
  "active_narratives": { "narrative_id": { "confidence": 65, "trend": "upward", ... } },
  "source_trust": { "source_id": { "admiralty": "A2", "track_record": 0.85 } },
  "weak_signals": [ { "signal": "...", "strength": 0.3 } ],
  "narrative_drift": { "id": { "direction": "sideways", "magnitude": 0.0 } },
  "escalation_queue": [ { "level": "pro", ... } ],
  "token_economics": { "total_spent_cents": 0.0 }
}
```

## Cadence

| Component | Interval | Model | Cost/Cycle | Daily Cost |
|---|---|---|---|---|
| Flash cognition | 15 min | DeepSeek Flash | ~$0.0005 | ~$0.05 |
| Pro escalation | on demand (< 2/day) | DeepSeek Pro | ~$0.01 | ~$0.02 |
| Opus escalation | rare | Claude Opus | ~$0.08 | < $0.10 |
| **Total** | | | | **< $0.17/day** |

## Escalation Thresholds

**DeepSeek Pro (daily limit: 2):**
- KJ confidence swings >15 points in one cycle
- New evidence contradicts ALL active narratives
- Weak signal strength >0.7 probability
- Two conflicting A-rated sources

**Claude Opus (rare):**
- 3+ narratives shift simultaneously by >15 points
- Pro analysis reveals genuine strategic crossroads

## Bounded Growth

- Max 20 active narratives (oldest archived)
- Max 50 weak signals (lowest-strength pruned)
- Max 100 source trust entries
- Signals decay to zero after 7 days
- Narratives stale >14 days archived
- Token budget: $0.20/day hard cap

## Operational Safeguards

- RuntimeLock: prevents overlapping daemon instances
- Skip at 90%+ disk usage
- Skip if daily budget exceeded
- Skip if no DeepSeek API key
- 60s timeout on Flash API calls
- Non-blocking: failures don't cascade
- No recursive cognition loops
- State file backed by atomic write (tmp + rename)

## Files

```
skills/continuous-cognition/
├── SKILL.md
├── config.yaml                    # Thresholds, cadence, routing
├── state/
│   └── cognition_state.json       # Persistent state (gitignored)
├── scripts/
│   ├── cognition_pipeline.py      # Main daemon
│   └── utils.py                   # State management utilities
└── prompts/
    └── flash_cognition.txt        # Flash instruction set
```
