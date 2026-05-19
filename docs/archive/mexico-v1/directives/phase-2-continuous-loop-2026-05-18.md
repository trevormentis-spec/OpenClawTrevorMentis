# Phase 2 — Continuous Learning Loop Architecture

**Effective:** 2026-05-18
**Source:** Phase 1 closed at independent 20/21 on Bajío stress test
**Architect:** Open Claw Mexico desk

---

## PURPOSE

Convert the Mexico desk from request-response (principal asks, agent answers) into a continuously running intelligence desk that generates its own work, directs its own capability growth, and reports weekly on what compounded.

---

## ARCHITECTURE — PLANNER + WORKER + TASKS

### (1) analyst/planner.py

Runs every 30 minutes via cron or daemon loop. Inspects system state. Generates 5-15 tasks per cycle. Writes to analyst/queue/.

State inputs: entity file last_source_date, postdiction outcomes, recent incidents, source registry status, Kalshi/Polymarket drift, subscriber question backlog, yesterday's brief gap-flags, Friday-memo capability-gap list.

Output: task list at analyst/queue/<timestamp>.json with type, priority, estimated_cost, estimated_duration, target, rationale.

### (2) analyst/worker.py

Pulls highest-priority task from queue, executes, logs result, updates state. Loops continuously with backoff.

Per-task pattern: load → check budget → execute → validate → update state → log → mark done/fail → sleep/next.

### (3) analyst/tasks/

Directory of task-type implementations. Each task type = single Python module with plan() and execute() functions.

---

## TASK TYPES — SEED CATALOG (6)

(a) entity_deepening.py — deepens least-recently-deepened entity, weighted by recent-incident relevance. 1500w target. Must pass fabrication_check.py.

(b) cross_source_correlation.py — when 2+ sources report same event, writes synthesis note. Updates source reliability priors.

(c) framework_stress_test.py — runs relevant framework (cartel factional dynamics, huachicoleo, LDAP-7) on each significant incident. Logs capability gaps.

(d) postdiction_sweep.py — resolves expired-horizon judgments using 5-category system. Updates per-region calibration.

(e) source_freshness_scan.py — runs freshness checker. Generates deepening tasks for stale entities.

(f) self_question_generation.py — daily. Generates 3-5 subscriber-grade questions the agent can't currently answer well.

---

## BUDGET

- Planner cycle: ~$0.001 per run (keyword-based state inspection)
- Worker task execution: varies by task type (entity deepening ~$0.005, sweep tasks ~$0.001)
- Weekly compound report: ~$0.01
- Target total: <$2/week in additional API costs

---

## GUARDRAILS

- No task can auto-commit new entity files without fabrication_check.py passing
- No task can modify scope.yaml, ORCHESTRATION.md, or principal-authorized config
- No task can execute external actions (email, social posting, Stripe) — planner-only
- Budget hard cap: $0.50/cycle, $5/week, principal override required beyond
