# Self-Improvement Nudge System

Adopted from Hermes Agent: after complex tasks, Trevor should save what it learned
as a skill or memory entry.

## Nudge Triggers

1. **Complex task completion** — 5+ tool calls in a single turn with a successful outcome
2. **User correction** — When Roderick corrects an approach, save the correction
3. **New integration** — When a new API/script/skill is wired up, document it as a skill
4. **Error recovery** — When a non-trivial error is solved, save the resolution

## Nudge Actions

| Trigger | Action | Location |
|---------|--------|----------|
| Complex task | Create/update a skill file | `skills/trevor/<category>/<name>.md` |
| User correction | Update MEMORY.md or brain semantic | `brain/memory/semantic/` |
| New integration | Create skill with procedure | `skills/trevor/integration/<name>.md` |
| Error recovery | Save to brain episodic | `brain/memory/episodic/` |

## Implementation

The heartbeat check should run:
```
python3 brain/scripts/brain.py nudge-check
```

Which looks at the last session's tool call count, any errors, and prompts
the creation of skills for significant work.
