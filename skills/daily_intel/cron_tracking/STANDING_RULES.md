# Standing Rules — Improvement Daemon

## Cron Schedule (set via `openclaw cron add`)

| Schedule | Job | Description |
|---|---|---|
| Daily 16:00 PT | `Improvement Daemon — daily pipeline` | Full enrichment → generation → quality → measurement → distribution |
| Hourly | `Improvement Daemon — hourly market check` | Kalshi significant move detection, no delivery |
| Weekly Sun 04:00 PT | `Improvement Daemon — weekly analytics` | Trend analysis, calibration, diversity report |

## Pipeline Components

### Phase 1: Enrichment (pre-generation)
1. `story_tracker.py --diff` — compare today's signatures vs yesterday, flag stalled stories
2. `daily_enrichment.py` — source freshness check, Kalshi integration, stale story instructions
3. `kalshi_scanner.py --save` — fresh prediction market data

### Phase 2: Generation
4. `generate_assessments.py` — theatre assessments (consumes enrichment report)
5. `refresh_imagery.py` — story-relevant photos, 50m maps with ISW-style symbology, contextual infographics
6. `build_pdf.py` — assemble final PDF

### Phase 3: Quality & Measurement
7. `quality_audit.py` — validate all assets
8. `briefometer.py` — 4-axis measurement (visual, content, PDF, predictive)
9. `story_tracker.py --save` — record today's state

### Phase 4: Distribution
10. Copy PDF to exports/pdfs/
11. Deploy to landing page (GitHub Pages)
12. Post to Moltbook (if configured)
13. Email via AgentMail (if configured)

### Phase 5: Improvement
14. Generate daily improvement report → `cron_tracking/daily_report_*.json`
15. Log to `cron_tracking/daemon_run.log`

## Self-Improvement Loop

### Auto-fix (runs automatically on failure)
- Missing assessment → create placeholder
- No PDF → attempt rebuild
- Empty image dir → regenerate imagery
- Build failure → retry once

### Story Freshness (daily)
- 80%+ signature overlap with yesterday → STALLED → inject "deepen analysis" instruction
- New signatures → DEVELOPING → normal coverage
- No previous data → EMERGING → full treatment

### Measurement Trend (weekly)
- Visual quality tracked via briefometer Axis 1
- Content quality tracked via briefometer Axis 2
- Predictive calibration tracked via Brier score
- Story freshness tracked via delta detection

## Quality Thresholds

| Metric | Target | Action if below |
|---|---|---|
| Photo size | >100KB each | Re-download from Wikipedia |
| Map size | >60KB each | Regenerate with higher DPI |
| Infographic size | >25KB each | Add more market data |
| PDF size | 1.5-4MB | Check image counts |
| PDF images | >20 embedded | Check build pipeline |
| Assessment words | >2000 per theatre | Flag for expansion |
| Assessment sources | >4 per theatre | Recommend new sources |
| Source diversity | >2 categories | Seek official/academic sources |
| Estimative language | >4 terms per theatre | Flag for richer KJs |
| Stall ratio | <80% overlap | Flag for story refresh |

## Commands

```bash
# Full daily pipeline
python3 scripts/improvement_daemon.py --daily

# Check status
python3 scripts/improvement_daemon.py --status

# Weekly analytics
python3 scripts/improvement_daemon.py --weekly

# Auto-fix issues
python3 scripts/improvement_daemon.py --auto-fix

# Record a Key Judgment
python3 scripts/briefometer.py --kjs

# Full dashboard
python3 scripts/briefometer.py --dashboard
```
