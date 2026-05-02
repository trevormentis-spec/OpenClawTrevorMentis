# Playbook: Daily Cadence

The end-to-end daily run, time-budgeted. Run the orchestrator once per
day at the agreed hour. If you blow past the budget on any phase, cut —
do not let the brief become a project.

---

## Schedule (default 06:30 local)

| Phase                                  | Wall clock     | Cumulative |
|----------------------------------------|----------------|------------|
| Step 0 — frame + brain recall          | 5 min          | 0:05       |
| Step 1 — collector                     | 25 min         | 0:30       |
| Step 2 — analyst (parallel with Step 3)| 30 min         | 1:00       |
| Step 3 — visuals                       | 25 min         | 1:00       |
| Step 4 — quality gates                 | 10 min         | 1:10       |
| Step 5 — assemble PDF + DOCX           | 5 min          | 1:15       |
| Step 6 — archive + deliver             | 5 min          | 1:20       |

Target: 80 minutes from kick-off to delivery. Hard ceiling: 2 hours.
Past 2 hours, ship what you have and note the slip in the daily memo —
the principal is on a ground truth that the brief lands by 08:00.

---

## When to skip a step

- **Step 3 (visuals) entirely:** acceptable if visuals tooling is broken
  and a fix would push past the 2-hour ceiling. Mark sections with "[map
  unavailable today]". Open a brain note to investigate.
- **Step 4 red-team:** never. Even on a slow news day, the red-team is
  structural discipline. A 100-word red-team beats a skipped one.
- **Step 6 delivery:** acceptable if the principal has indicated they
  are unavailable today (e.g. travel without secure email). Archive
  locally and resume tomorrow.

---

## When to escalate the daily into a special

See `playbooks/escalation-criteria.md`.

---

## Failure modes seen in early runs

1. **Collector over-pulls.** Spends 45 minutes finding a 12th Lebanon
   incident. Push back: 5–8 per region, then stop.
2. **Analyst over-judges.** Returns 4 KJs per region "because the day
   was rich". The principal wanted three. Force the count.
3. **Visuals subagent retries Mapbox indefinitely** when the token is
   missing. Fail-fast on the env check at Step 0; do not let visuals
   take the run hostage.
4. **Calibration drift.** The first week's predictions all sit in 80–95%.
   The analyst's prompt has the calibration discipline section; refer
   the analyst back to it explicitly when you see this happen.
5. **Length creep.** The third regional section is suddenly three pages.
   The assembler will refuse to render past the cap; the analyst should
   tighten its narrative.

---

## On the cron

Recommended cron:

```
30 6 * * * cd $REPO_ROOT && \
    DEEPSEEK_API_KEY=$(cat ~/.openclaw/secrets/deepseek) \
    MAPBOX_TOKEN=$(cat ~/.openclaw/secrets/mapbox 2>/dev/null) \
    CHARTGEN_API_KEY=$(cat ~/.openclaw/secrets/chartgen 2>/dev/null) \
    AGENTMAIL_API_KEY=$(cat ~/.openclaw/secrets/agentmail) \
    python3 skills/daily-intel-brief/scripts/orchestrate.py \
    >> ~/trevor-briefings/log.txt 2>&1
```

Per `AGENTS.md` heartbeat-vs-cron guidance: this is a cron task because
timing matters (the principal wants it by 08:00) and it should run in
isolation from the main session history.

---

## Weekly hygiene (Friday afternoon)

- Walk through the week's `~/trevor-briefings/<date>/analysis/red_team.md`
  files. Promote any standing red-team challenge to a permanent I&W
  board entry.
- Update `analyst/meta/sources.json` with any new durable source the
  collector found.
- Refresh the brain index (`brain/scripts/brain.py reindex`).

## Monthly hygiene (last Friday of the month)

- Score every prediction made in the previous month against what
  actually happened. Compute Brier score per region; print on the
  next month's first daily cover.
- Walk source list; downgrade or remove stale sources.
- Walk standing I&W boards; retire indicators that have not moved in
  90 days.
