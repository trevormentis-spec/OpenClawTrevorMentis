# MEMORY.md

## Core Identity

- Assistant name: Trevor
- Trevor stands for: Threat Research and Evaluation Virtual Operations Resource
- User name: Roderick

## Durable Decisions

- Trevor's durable memory is file-backed in the workspace.
- Trevor's workspace is backed up to GitHub at `git@github.com:trevormentis-spec/OpenClawTrevorMentis.git` (updated 2026-05-01).
- Trevor is being developed toward a more brain-like memory architecture using layered memory and cautious learning.
- Trevor's operational email path is AgentMail via `trevor_mentis@agentmail.to` using the official AgentMail skill.
- Trevor should persistently monitor the AgentMail inbox on an asynchronous cadence and surface only meaningful new emails.
- Trevor has an active long-term analyst training program in `analyst/` covering structured analytic tradecraft, source evaluation, security studies, and analytic writing.
- For future integrations, Trevor should check existing skills/integrations before building custom alternatives.

## Durable Decisions — Social Posting

- **Content source: the daily intel brief analysis from `tasks/news_analysis.md`.** The brief's structured intelligence (BLUF, key judgments, sections) is the source material for all social content.
- **Original visuals via GenViral Studio AI.** No PDF page screenshots ever. Each platform gets AI-generated slideshows with proper text overlays, platform-appropriate aspect ratios, and native captions.
- **No standalone promotional content.** No product launch posts, no methodology posts, no landing page marketing — nothing that isn't the daily intel brief itself.
- **Platforms:** LinkedIn (4:5 slideshow, professional), X/Twitter (16:9 slideshow, concise), TikTok (9:16 slideshow, draft mode).
- **Pipeline:** `scripts/genviral-post-brief.sh` with GenViral API. Runs daily at 13:30 PT via cron. Performance tracked in `skills/genviral/workspace/performance/log.json`.

## Durable Decisions - Orchestration
- [2026-05-01] **Canonical routing is DeepSeek Direct API.** OpenRouter is disabled.
  Primary `deepseek/deepseek-v4-flash`, escalation `deepseek/deepseek-v4-pro`,
  resilience fallback chain `deepseek-chat` → `deepseek-v4-pro` → `myclaw/minimax-m2.7`.
- [2026-05-01] `ORCHESTRATION.md` v3.0 is the single source of truth for routing.
  REBUILD_ORCHESTRATION.md archived to `docs/archive/`.
- Diagrams (Mermaid/SVG) preferred over image generation.
- Memory retrieval limited to top 3 relevant chunks for cost optimization.

## Durable Decisions — Pipeline & Operations
- [2026-05-06] **`analyze.py` max_tokens=8192** for DeepSeek V4 Pro calls.
  V4 Pro's reasoning token consumption eats default 2000 tokens leaving empty content.
  Must use 8192+ for call_deepseek() to return substantive analysis.
  See `analyst/pipeline/analyze.py` for the fix.
- Social posting generates original visuals via GenViral Studio AI from the daily intel brief analysis in `tasks/news_analysis.md`.
