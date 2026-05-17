# skill-generator

**Status:** active
**Owner:** trevor (self-update loop)
**Added:** 2026-05-17

## Purpose

Close Trevor's autonomous skill-update loop (Loop 5 in
`analyst/directives/2026-05-mexico-pivot.md`). When a capability gap is
identified — by the weekly meta-review, the framework-reflection memo,
or a heartbeat anomaly — this skill drafts a new skill scaffold so the
gap can be filled without principal-side scaffolding.

This is the "I needed a tool that didn't exist, so I built it" loop.

## When to invoke

- After a Friday framework reflection lists a CAPABILITY GAP that maps
  cleanly to a tool (e.g., "cannot OCR Spanish-language PDFs").
- After three or more failures of the same kind in the heartbeat log.
- On explicit principal request: `python3 skills/skill-generator/scripts/generate_skill.py --gap "..."`

## Inputs

| Input | Source |
|-------|--------|
| Gap description | CLI `--gap`, or `analyst/reflections/weekly/*.md` |
| Existing skills inventory | `skills/registry.json` (avoids duplicates) |
| Naming convention | kebab-case, single noun-verb phrase |

## Outputs

Creates:

```
skills/<skill-name>/
  SKILL.md          — purpose, inputs, outputs, when-to-invoke
  scripts/<verb>.py — executable stub (argparse + log + main())
```

And appends a row to `skills/registry.json` so it's discoverable.

## Constraints

- **Never overwrite an existing skill.** Refuse if the directory exists.
- **Stub only.** The generated script raises `NotImplementedError` in
  `main()` until a human (or a follow-up agent invocation) fills it in.
  Bias is toward making the gap visible and reservable, not toward
  shipping unverified code into the autonomous pipeline.
- **Log every generation** to `brain/memory/semantic/skill-generation-log.jsonl`
  so the weekly review can see what was drafted and whether it was completed.

## Limits

This is intentionally a scaffolder, not a code-writer. Trevor's bar for
running new code in the autonomous pipeline is "principal has reviewed
the implementation". The scaffolder gets to the point where Trevor can
say in chat: "Here's the gap; here's the stub I made for it; ready to
fill it in?"
