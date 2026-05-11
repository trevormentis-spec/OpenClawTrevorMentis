# Trevor Architecture Audit vs Hermes Agent

Date: 2026-05-11
Goal: Extract Hermes patterns that improve Trevor without replacing OpenClaw.

## 1. Persistent Memory Architecture

**Hermes:**
- SQLite + FTS5 for full-text session search across all conversations
- Two curated files: MEMORY.md (2,200 chars) + USER.md (1,375 chars)
- Agent self-manages memory via `memory` tool (add/replace/remove)
- Frozen snapshot at session start — preserves prefix cache
- Capacity bar in system prompt shows usage %
- Auto-consolidation when >80% full
- Duplicate prevention built-in
- Security scanning on memory writes
- 8 external memory provider plugins (Honcho, Mem0, etc.)

**Trevor (Current):**
- `brain/` directory with episodic/ (JSONL), semantic/ (markdown), procedural/ (markdown)
- `brain.py recall` / `brain.py synthesize` for retrieval
- MEMORY.md + memory/YYYY-MM-DD.md daily logs
- Heartbeat-cued memory maintenance
- No character limits — can grow unbounded
- No auto-consolidation or capacity awareness
- No duplicate prevention
- No security scanning on memory writes
- No frozen snapshot pattern

**Gap: LOW** — Trevor has working memory, just less disciplined. The brain architecture with layered memory (episodic→semantic→procedural) is actually more sophisticated than Hermes' single-file approach. What's missing is the discipline loop.

## 2. Procedural Memory (Skills)

**Hermes:**
- SKILL.md files with frontmatter (name, description, version, platforms, tags)
- Progressive disclosure: Level 0 (index), Level 1 (view), Level 2 (detail)
- `skill_manage` tool — agent creates/patches/deletes skills autonomously
- Skills = on-demand knowledge documents, not always-loaded
- Compatible with agentskills.io open standard
- Slash command access: /skill-name
- Fallback/conditional activation based on tool availability
- External skill directories (read-only, multi-agent shared)

**Trevor (Current):**
- No procedural memory system at all
- Each complex task solved from scratch
- Lessons learned stored in AGENTS.md as free text
- No skill creation, versioning, or discovery
- Analyst playbooks exist in `analyst/playbooks/` but are human-written, not agent-managed

**Gap: CRITICAL** — This is Trevor's biggest missing capability. Every pipeline fix, every integration, every workflow is solved fresh. There's no learning reuse.

## 3. Self-Improvement Loop

**Hermes:**
- After complex tasks (5+ tool calls): nudge to save as skill
- On user corrections: nudge to update memory
- Periodic nudges during idle time to consolidate memory
- Detects error patterns and saves workarounds
- Skill patching during use (prefers `patch` over `edit` for token efficiency)

**Trevor (Current):**
- Heartbeat-cued maintenance (manual rotation through checklist items)
- Brain promotion (episodic→semantic) via `brain.py promote`
- No automatic nudge on complex task completion
- No error pattern detection for skill creation
- Memory consolidation is manual

**Gap: MEDIUM** — Basic loop exists via heartbeats but is entirely manual. No autonomous trigger.

## 4. Autonomous Self-Maintenance

**Hermes:**
- Cron-scheduled maintenance tasks
- Config validation on every start
- Provider health checks
- Automatic session pruning
- Memory capacity monitoring

**Trevor (Current):**
- Cron-driven maintenance (GitHub backup, skill audit, brain reindex)
- Multiple maintenance cron jobs already exist
- No memory capacity monitoring or auto-consolidation
- No config validation on start

**Gap: LOW** — Cron infrastructure exists, just underutilized for memory maintenance.

## 5. Retrieval-First Workflows

**Hermes:**
- `session_search` tool with FTS5 + LLM summarization
- Memory injected directly into system prompt (no search needed for active facts)
- Session search for "did we discuss X?" queries
- Gemini Flash summarization for search results
- Compression avoids context overflow

**Trevor (Current):**
- `brain.py recall` / `brain.py synthesize` for memory retrieval
- FTS5 index in brain/index/index.json
- Memory_search tool in OpenClaw
- No session_search alternative
- No context compression — grows unbounded

**Gap: LOW-MEDIUM** — Both work. Hermes' frozen snapshot pattern is worth adopting for memory.

## 6. Long-Horizon Agent Continuity

**Hermes:**
- SQLite session lineage tracking (parent/child across compressions)
- Profile isolation (separate HERMES_HOME per profile)
- Session search spans all past conversations
- Skills persist across sessions naturally

**Trevor (Current):**
- OpenClaw session management (no manual lineage)
- brain/ episodic memory logs sessions
- File-backed continuity (MEMORY.md, AGENTS.md, TOOLS.md, USER.md)
- No session lineage tracking

**Gap: NONE** — Trevor's file-based continuity is different but equally effective. OpenClaw handles session management.

## 7. Multi-Agent Orchestration

**Hermes:**
- `delegate_tool.py` — spawn isolated subagents
- Cron jobs run as isolated agent instances
- ACP protocol for IDE integration
- Programmatic Tool Calling collapses multi-step pipelines

**Trevor (Current):**
- `sessions_spawn` for isolated subagents
- Cron system already runs isolated sessions
- Subagent orchestration via sessions_list/kill/send
- No programmatic tool calling equivalent

**Gap: LOW** — OpenClaw's subagent infrastructure is already strong.

## 8. Self-Improving Skills

**Hermes:**
- Create skill after completing complex task
- Patch skill during use (old_string/new_string replacement)
- Skill version tracking
- Skills Hub for sharing/installing community skills
- Skill audit for security scanning

**Trevor (Current):**
- No skill system at all
- No skill sharing capability
- No procedural knowledge reuse

**Gap: CRITICAL** — Doubles down on #2. No skill creation = no learning reuse.

## 9. Failure Recovery

**Hermes:**
- Tool call retry with exponential backoff
- Provider fallback on 429/5xx
- Context compression prevents token overflow
- Atomic session writes with contention handling
- Interruptible tool execution

**Trevor (Current):**
- Provider fallback chain (deepseek-chat → v4-pro → minimax-m2.7)
- Retry on 429 with backoff+jitter
- No context compression — risk of token overflow on long sessions
- No atomic session writes

**Gap: MEDIUM** — Provider resilience exists. Context overflow protection is missing.

## 10. Runtime Observability

**Hermes:**
- Visible tool calls with CLI spinners
- Progress callbacks during tool execution
- Session storage with FTS5 for full audit trail
- Trajectory export for RL training
- Memory capacity indicators in system prompt

**Trevor (Current):**
- OpenClaw tool execution is visible (platform-dependent)
- Cron run history via `openclaw cron runs`
- No structured observability or metrics
- No trajectory export
- No memory capacity awareness

**Gap: MEDIUM** — Basic observability exists via OpenClaw but no structured instrumentation.

## Gap Summary

| Dimension | Gap Severity | Current State |
|-----------|-------------|---------------|
| 1. Persistent memory | LOW | Working brain system, less disciplined |
| 2. Procedural memory (Skills) | CRITICAL | Does not exist |
| 3. Self-improvement loop | MEDIUM | Manual heartbeat maintenance |
| 4. Autonomous maintenance | LOW | Cron infrastructure exists |
| 5. Retrieval-first workflows | LOW-MEDIUM | Both recall and search work |
| 6. Long-horizon continuity | NONE | File-based continuity is effective |
| 7. Multi-agent orchestration | LOW | Sessions_spawn/cron already strong |
| 8. Self-improving skills | CRITICAL | Does not exist |
| 9. Failure recovery | MEDIUM | No context overflow protection |
| 10. Runtime observability | MEDIUM | No structured metrics |

## Ranked Upgrades

| Rank | Upgrade | Impact | Difficulty | Hermes Pattern | Safe? |
|------|---------|--------|------------|----------------|-------|
| 1 | **Skill system**: Create simple SKILL.md-based procedural memory with progressive disclosure | HIGH | EASY | Skills System | ✅ Additive, no existing impact |
| 2 | **Memory freeze**: Add frozen snapshot pattern to memory injection at session start | MEDIUM | EASY | Memory architecture | ✅ Changes nothing existing |
| 3 | **Self-improvement nudge**: After 5+ tool calls, prompt to create skill or update memory | HIGH | EASY | Self-improvement loop | ✅ Prompt-level only |
| 4 | **Skill versioning**: Add version tracking and patch-as-you-go pattern | MEDIUM | EASY | Skill evolution | ✅ Additive file format |
| 5 | **Context compression**: Summarize mid-conversation when context exceeds threshold | MEDIUM | MEDIUM | Context engine | ⚠️ Needs careful testing |
| 6 | **Memory capacity monitoring**: Track memory usage, auto-consolidate at 80% | LOW | EASY | Memory management | ✅ Read-only monitoring |
| 7 | **Runtime metrics**: Structured tool call timing, cost tracking per session | MEDIUM | MEDIUM | Observability | ✅ Additive instrumentation |
| 8 | **Skill sharing**: agentskills.io compatible export/import | LOW | HARD | Skills Hub | ✅ Additive, no existing impact |

## Safe First Steps (Implement Now)

Implementing items 1-4 (all safe, additive, no existing impact).

### Step 1: Skill System

Create a `skills/` directory in workspace, add a SKILL.md format, and add a `skill_manage` tool wrapper.

### Step 2: Memory Freeze

Add a frozen-snapshot memory section to the session context.

### Step 3: Nudge System

Add heartbeat check: did last session have complex work? If yes, prompt to document.

### Step 4: Skill Versioning

Add version and history tracking to SKILL.md files.

Let me implement Step 1 now — the skill system is the highest-impact missing piece.
