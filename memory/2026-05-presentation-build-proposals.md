# Presentation Stack — Priority Build Proposals

**Status:** PARKED for principal review.
**No new skills installed.** Each proposal includes approach, effort, and integration path.

---

## Priority 1 — PDF Renderer

**Approach:** weasyprint (HTML→PDF) with branded CSS. Zero new dependencies.

**Template structure:**
- Cover page: brief title, BLUF, calibration summary, headline judgments (3-5), metadata footer (produced date, sources cited count)
- Section pages: one per section, inline judgment callouts with Kent band color coding (green=highly likely, yellow=probable, red=unlikely)
- Trade positions table: instrument, strike, price, sizing, rationale
- Watch items: per-item with indicator, trigger, signal
- Gap page: explicit gaps with next-step recommendations
- Source/Admiralty footer: full source list with ratings

**Brand assets needed:**
- Color palette: primary (dark teal/navy), accent (amber for warnings, red for risks), neutral (slate)
- Logo/brand mark: Open Claw Mexico
- Font: system sans-serif (inter, system-ui fallback)
- CSS template at `analyst/templates/pdf-brand.css`

**Effort:** 4 hours (CSS + template + integration)
**Build sequence:** CSS template → Python renderer script → brief JSON→PDF pipeline step
**Cost:** $0.00 (no new dependencies)

---

## Priority 2 — Brief JSON Schema

**Approach:** Add `--json-output` flag to brief generation pipeline.

**Implementation:**
- Define complete JSON schema at `analyst/schemas/brief-v1.json`
- LLM generates structured JSON alongside markdown from same call (add JSON schema to system prompt)
- Post-generation: validate JSON against schema (type checking, required fields)
- Save both `.md` and `.json` to output directory
- The JSON becomes the canonical structured data that all renderers read

**Effort:** 2 hours (schema definition + LLM prompt update + validation)
**Cost:** $0.00 (prompt changes only)

---

## Priority 3 — Mapping

**Two options for principal review:**

**Option A — Folium (free, no key):**
- `pip install folium` — zero recurring cost
- GeoJSON from INEGI/Mexican government (free download: state boundaries, municipal boundaries)
- Sub-corridor risk overlays (choropleth by risk level, cartel-presence heatmap, water/grid overlay)
- Export as HTML (interactive) or PNG (static for PDF)
- Effort: 6 hours. Risk: lower quality than Mapbox

**Option B — Mapbox Static API (paid key available):**
- Uses existing Mapbox token (pk. from `.env` — already have it)
- Mapbox Static API renders GeoJSON overlays at server-side quality
- Higher visual quality for subscriber-facing PDFs
- Effort: 4 hours. Risk: API usage costs (pay per tile load ~$0.0005/tile)
- Requires installing Mapbox MCP server (`npx @mapbox/mcp-server`)

**Proposal:** Start with Folium prototype (zero cost, immediate). Upgrade to Mapbox for production if subscriber feedback wants higher visual fidelity.

---

## Priority 4 — PowerPoint Renderer

**Approach:** `pip install python-pptx` + deck template.

**Template structure:**
- Title slide: brief name, date, calibration band
- Slide per section: section title, 3-5 bullet narrative, key judgment callout
- Visualization slides: trade positions table, watch items grid, gap summary
- Closing slide: subscriber action lines, priorities

**Effort:** 3 hours (template + renderer + integration)
**Cost:** $0.00 (new pip package only)
**Note:** Lower priority than PDF + map. PPTX is most useful for family office / institutional subscribers who want to present internally.

---

## Priority 5 — Audio Briefings

**Approach:** OpenAI TTS API ($15/M chars) or ElevenLabs ($5/month base + $0.30/M chars).

**Text pipeline:**
1. Brief JSON → extract BLUF, section narratives, judgments, watch items
2. Script construction: 5-7 min daily (600-900 words), 12-15 min analysis (1500-2000 words)
3. TTS conversion via API call
4. Save as MP3, host for download or embed

**Effort:** 2 hours (script extraction + audio pipeline)
**Cost:** ~$0.10 per daily briefing (OpenAI TTS), ~$5/month base (ElevenLabs)
**Note:** Differentiator for premium tier. Script extraction from JSON is the key overhead — TTS API call is trivial.

---

## Priority 6 — Infographics (Editorial Visuals)

**Approach:** matplotlib + Pillow compositing, generated from brief JSON.

**Outputs:**
- Calibration distribution bar chart
- Sub-corridor risk comparison (5-dimension radar chart)
- Trade position P&L waterfall (if applicable)
- Gap significance matrix

**Effort:** 4 hours (chart templates + data extraction + compositing)
**Cost:** $0.00 (matplotlib + Pillow already WORKING)

---

## Priority 7 — AI Images (Deferred)

**Approach:** visual_production skill via OpenRouter image gen.

**Use cases:** Newsletter masthead illustrations, visual metaphors for key themes. Not core analysis rendering.

**Effort:** 1 hour to wire
**Cost:** ~$0.01-0.05 per image (OpenRouter gemini-3.1-flash)
**Status:** DEFERRED — revisit when newsletter pipeline is live.

---

## Priority 8 — Video (Deferred)

Audio + visuals delivers 80% of value at 20% of cost. Revisit after Parts 1-5 working and subscribers ask.

---

## Build Sequence (Recommended)

| Week | Build | Depends On | Effort |
|------|-------|-----------|--------|
| 1 | Brief JSON schema + LLM prompt update | Nothing | 2h |
| 1 | PDF renderer (weasyprint + CSS) | Brief JSON | 4h |
| 2 | Mapping (Folium prototype) | Brief JSON | 6h |
| 2 | PowerPoint renderer | Brief JSON | 3h |
| 3+ | Audio pipeline | Brief JSON + subscriber signal | 2h |
| TBD | Infographics | Brief JSON | 4h |
| TBD | AI images | Visual production skill | 1h |
| TBD | Video | Audio + subscriber signal | Deferred |

**Total effort (first 3 weeks):** 15 hours across PDF + JSON + mapping + PPTX.
**Total new dependencies:** python-pptx (pip package). Everything else uses existing WORKING tools.
