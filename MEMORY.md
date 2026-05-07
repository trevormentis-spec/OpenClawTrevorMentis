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

- **⚠️ BINDING RULE: Only the daily intel brief from Gmail.** The source PDF is in Gmail, labeled "Important Myclaw use this". Always fetch the most recent one with this label for ALL social posts. No exceptions.
- **Content source: daily intel brief PDF from Gmail, period.** The brief content can go on any platform — LinkedIn, X/Twitter, TikTok, and Moltbook — but the content itself must originate from the Gmail PDF.
- **No standalone promotional content.** No product launch posts, no methodology posts, no landing page marketing — nothing that isn't the daily intel brief itself.
- Use pdftotext for content extraction; pdftoppm for page images.
- Do not use cached/stale images from exports/images/.
- The social posting pipeline must source content exclusively from the Gmail PDF, not from `tasks/news_analysis.md` or any other local file.

## Durable Decisions - Orchestration
- [2026-05-01] **Canonical routing is DeepSeek Direct API.** OpenRouter is disabled.
  Primary `deepseek/deepseek-v4-flash`, escalation `deepseek/deepseek-v4-pro`,
  resilience fallback chain `deepseek-chat` → `deepseek-v4-pro` → `myclaw/minimax-m2.7`.
- [2026-05-01] `ORCHESTRATION.md` v3.0 is the single source of truth for routing.
  REBUILD_ORCHESTRATION.md archived to `docs/archive/`.
- Diagrams (Mermaid/SVG) preferred over image generation.
- Memory retrieval limited to top 3 relevant chunks for cost optimization.
