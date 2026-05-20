# Build Readiness — Trevor Presentational Suite v2

**Date:** 2026-05-20 16:30 UTC
**Environment:** Docker container, Linux 6.8.0, Node v22.22.2, 1.7 GB free

---

## 1. Ready Now — Stages Whose Prerequisites Are All Present

| Stage | Stage | Depends On | Status |
|-------|-------|-----------|--------|
| 1 | Cover/illustration | GENVIRAL_API_KEY (2323 credits) | ✅ Ready |
| 2 | Charts & diagrams | matplotlib, mmdc/mermaid.ink | ✅ Ready |
| 3 | Static maps | MAPBOX_TOKEN, Mapbox API | ✅ Ready |
| 4a | Narration script | DEEPSEEK_API_KEY (DeepSeek Flash) | ✅ Ready |
| 4b | Narration audio | ELEVENLABS_API_KEY (in .env) | ✅ Ready (tested: HTTP 402, degraded to silence) |
| 5 | Video composite | ffmpeg, Pillow | ✅ Ready |
| — | Vision QC | Opus 4.7 via OpenRouter | ✅ Ready |
| — | Integration CLI | All stage scripts | ✅ Ready |

**Key APIs verified reachable:**
- GenViral: 2,323 credits, small plan ✅
- OpenRouter (Opus 4.7): endpoint reachable ✅
- Mapbox: HTTP 200, free tier ✅
- DeepSeek: HTTP 200, direct API ✅
- ElevenLabs: endpoint reachable, HTTP 402 on generation (needs credits) ⚠️

**Binaries:**
ffmpeg ✅, ffprobe ✅, python3 ✅, node ✅, npm ✅, weasyprint ✅, tesseract ✅, pdftoppm ✅, mmdc ✅

---

## 2. Needs Operator Action — Stages Blocked on Missing Keys

| Stage | Primitive | Missing Key | Suggested Action |
|-------|-----------|-----------|-----------------|
| 4b | Narration audio | ElevenLabs credits | Top up ElevenLabs account (current key works but HTTP 402 — pay-as-you-go or $5/mo subscription) |
| 6 | Avatar video | `HEYGEN_API_KEY` + `HEYGEN_AVATAR_ID` | Create HeyGen account ($24/mo starter plan) and create an avatar. Provide key + avatar ID. |
| 7 | Scene video | `KLING_API_KEY` or `GOOGLE_VERTEX_PROJECT` | For Kling 3.0: sign up at fal.ai, get API key ($0.12/sec). For Veo 3.1: set up GCP Vertex AI. |
| — | Direct Anthropic API | `ANTHROPIC_API_KEY` (direct) | Current key fails auth. Must route through OpenRouter (already working). Not blocking. |
| — | OpenAI images/TTS | `OPENAI_API_KEY` | Only needed as ElevenLabs substitute. Not blocking — GenViral covers Stage 1. |

**All above batched here — never mid-build asks.**

---

## 3. Will Install During Build

| Package | For | How |
|---------|-----|-----|
| `anthropic` (pip) | Opus 4.7 SDK for vision QC | Already available via OpenRouter REST — no install needed |
| `openai-whisper` (pip) | Audio transcription for video verification | Install during Stage 5 verification |
| `pymupdf` (pip) | PDF page rendering for QC | Install during PDF assembly if needed |

---

## Design Summary

| Rule | Implementation |
|------|---------------|
| Rule-based routing | 10-line if/elif dictionary in stage2_charts.py |
| One provider per primitive | GenViral → images, Mapbox → maps, ElevenLabs → audio, ffmpeg → video |
| No FastAPI/SQL | State in manifest.json, cache as content-hashed files |
| Cost ceilings | `--budget` flag, per-asset hard limits in trevor_present.py |
| Self-test at startup | Every stage checks prereqs, logs "STAGE N DISABLED: reason" |
| Opus 4.7 scope | Content generation (narration scripts), vision QC — never routing |
| Verification | Phase A (programmatic), Phase B (Opus 4.7 vision) |
