# Pipeline Operations

## Daily Brief Pipeline

**Script:** `scripts/daily-text-brief.sh`
**Schedule:** Cron `0 5 * * * @ America/Los_Angeles` (05:00 PT daily)
**Cron ID:** `69d9d778-9de1-4d63-8697-99f0bd13353f`
**Timeout:** 14400s (4 hours)
**Estimated runtime:** 17-25 minutes

### Steps
1. Pre-collection: calibration directives + Kalshi scan
2. Collector: ~96 feeds (50 catalog + ~46 hardcoded)
3. Email intel: Gmail + AgentMail injection
4. Analysis: 10 regions × DeepSeek V4 Pro + exec summary + red team
5. Quality gate: 7 gates (structural, fabrication, themes, calibration, completeness, scope, red-team)
6. Delivery: AgentMail to roderick.jones@gmail.com
7. Postdiction: calibration tracking

### Known Issues
- **GitHub PAT:** Deploy to landing page requires rotating PAT (blocked)
- **Feed rot:** ~60+ dead feeds accumulating in the catalog
- **Calibration:** 0/5 resolution rate on recent predictions
- **QC PARSE_ERROR:** Intermittent quality gate parse failures

### Delivery
- GSIB arrives ~07:00 PT
- 4 Daily Briefings arrive at 08:00 PT
- Cron IDs: GSIB = `250765ae-d951-490c-b3d0-109fca300053`, Briefings = `9ee44803-223c-45cc-ad59-f404919bd5f9`
- Delivery via AgentMail → roderick.jones@gmail.com

## Kalshi Market Scanner

**Script:** `scripts/kalshi_scanner.py`
**Schedule:** Runs as Step 1d in daily brief pipeline
**Output:** `exports/kalshi-scan-YYYY-MM-DD.md`
**Coverage:** 60+ geopolitics series across Iran, Russia-Ukraine, oil/energy, China/Taiwan, etc.

## Source Collection Pipeline

**Catalog:** `analyst/meta/sources_tested.json` (286 working feeds across 10 regions)
**Collector:** `skills/daily-intel-brief/scripts/collect.py` (dynamic catalog + hardcoded feeds)
**Dead-feed cache:** `brain/memory/semantic/dead-feeds.json` (171 pre-populated entries)
**Feed health audit:** `scripts/feed_health_audit.py --catalog`

### Known Issues
- Dead feeds skip after 3 consecutive failures, retest after 48h
- 8s timeout, 1 retry per feed
- South America: 127 working feeds (recently added), rotates 6 per run
