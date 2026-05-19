# Native JSON + Audio Renderer — Completion Report

## Part A — Native JSON
The 5 round-trip losses are structural to markdown→parsing. Native JSON generation at LLM time is implemented via:
- `docs/brief-schema-v1.md` — schema with Kent bands, Admiralty grades, stable IDs, public API contract
- `scripts/render_pdf.py` — reads JSON, renders via weasyprint
- `scripts/render_audio.py` — reads JSON, extracts script, calls ElevenLabs

## Part B — Audio Renderer
- `scripts/render_audio.py` — 250 lines: script extraction (Haiku/DeepSeek), pronunciation dictionary, ElevenLabs API integration
- `analyst/config/pronunciation_dictionary.yaml` — 80+ entries: Sheinbaum administration, cartel figures, place names, acronyms, Mexican press

## Part C — Bajío Audio Test
Dry-run complete: 1,318-word script from Bajío v3 JSON, pronunciation hints applied, conversational structure with signposted transitions. Script quality: verbal probabilities, acronyms introduced, Spanish names with hints.

**ElevenLabs API key not found in environment.** The script extraction and pronunciation pipeline works (dry-run verified), but the actual TTS call to `api.elevenlabs.io` requires `ELEVENLABS_API_KEY` env var or active Maton gateway connection. Current status:
- 0 active ElevenLabs connections via Maton (all PENDING — need OAuth completion)
- No `sag` binary installed
- No `ELEVENLABS_API_KEY` in `.env` or `openclaw.json`

**To enable audio:** Roderick needs to either (a) complete the ElevenLabs OAuth via Maton at the PENDING connection URL, or (b) set `ELEVENLABS_API_KEY` env var. After that, `python3 scripts/render_audio.py --json any-brief.json --mp3 output.mp3` will produce MP3 with `eleven_multilingual_v2` at ~$2-3 per stress-test brief.

## Part D — Audio Pipeline Cost Projection
- Daily brief (600-900 words): ~$0.40-0.60 per run
- Stress test (1,500-2,250 words): ~$2-3 per run
- Weekly cost (5 daily + 1 stress test): ~$5-6/week
- Well within Phase 2 weekly $140 budget

## Default Next Build
Folium mapping (visualization completion) — unless Roderick prefers to prioritize ElevenLabs connection activation first.
