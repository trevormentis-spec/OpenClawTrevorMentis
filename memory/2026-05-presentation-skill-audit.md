# Presentation Capability Audit — 2026-05-18

**Context:** Parallel workstream to Phase 2 live evaluation.
**Objective:** Assess what's available for converting analytical output to subscriber-grade product.

---

## Skill Inventory

| Capability | Tool | State | Notes |
|-----------|------|-------|-------|
| **PDF** | reportlab | WORKING | System package, programmatic PDF generation |
| **PDF** | weasyprint | WORKING | HTML→PDF, good for branded layouts |
| **PDF** | pdf-report skill | INSTALLED-UNREGISTERED | In skills/ directory, not in openclaw.json config. Need registration + testing |
| **DOCX** | python-docx | NOT-AVAILABLE | System package missing. `pip install python-docx` |
| **PPTX** | python-pptx | NOT-AVAILABLE | System package missing. `pip install python-pptx` |
| **XLSX** | openpyxl | NOT-AVAILABLE | System package missing. `pip install openpyxl` |
| **Charts** | matplotlib | WORKING | Used in GSIB pipeline for calibration charts |
| **Charts** | plotly | NOT-AVAILABLE | Would need `pip install plotly`. Interactive preferred over static |
| **Charts** | data-charts-visualization skill | INSTALLED-UNREGISTERED | ClawHub skill for chart generation |
| **Mapping** | folium | NOT-AVAILABLE | Would need `pip install folium`. Interactive Mexico maps |
| **Mapping** | mapbox-geospatial-operations skill | INSTALLED-UNREGISTERED | ClawHub skill, Mapbox MCP server integration |
| **Mapping** | mapbox-data-visualization-patterns skill | INSTALLED-UNREGISTERED | Reference patterns only |
| **Frontend** | landing-page-generator skill | INSTALLED-UNREGISTERED | ClawHub skill, subscriber-facing pages |
| **Frontend** | landing-page-roast skill | INSTALLED-UNREGISTERED | Conversion audit skill |
| **Image gen** | visual_production skill | INSTALLED-UNREGISTERED | OpenRouter image gen via google/gemini-3.1-flash |
| **Image gen** | Pillow | WORKING | Image processing, compositing |
| **Mermaid** | mermaid skill | INSTALLED-UNREGISTERED | Diagram generation |
| **Mermaid** | python bindings | WORKING | @mermaid-js/mermaid-cli via npm |
| **TTS Audio** | system TTS | NOT-AVAILABLE | Need API (OpenAI TTS / ElevenLabs) |
| **Video** | ffmpeg/system | NOT-AVAILABLE | Would need `apt install ffmpeg` + compositing library |

---

## Summary by Category

| Category | Count | Breakdown |
|----------|-------|-----------|
| WORKING | 5 | reportlab, weasyprint, matplotlib, Pillow, mermaid python |
| INSTALLED-UNREGISTERED | 8 | pdf-report, data-charts, mapbox-geospatial, mapbox-viz, landing-page-gen, landing-page-roast, visual_production, mermaid |
| NOT-AVAILABLE | 7 | python-docx, python-pptx, openpyxl, plotly, folium, TTS, video |
| **Total capabilities** | **20** | |

**Key finding:** 5 WORKING capabilities already exist without any new installs. The PDF path weasyprint (HTML→PDF with CSS branding) is the fastest route to subscriber-grade output — zero new dependencies, full visual control via CSS.

---

## Brief JSON Structure (Part B Foundation)

Proposed additive schema alongside existing markdown output:

```json
{
  "brief_id": "bajio-v3-20260518",
  "query_type": "industrial_real_estate",
  "produced_at": "2026-05-18T16:00:00Z",
  "producer": "Open Claw Mexico desk",
  "bluf": "The Bajío corridor faces acute energy-infrastructure constraints...",
  
  "sections": [
    {
      "id": "section_1",
      "title": "12-Month Security & Political Risk",
      "subsections": [
        {
          "id": "section_1_1",
          "title": "Guanajuato sub-corridor",
          "narrative": "...",
          "judgments": [
            {
              "claim": "At least one major industrial park experiences temporary shutdown due to cartel violence",
              "kent_band": "Probable",
              "kent_pct_range": [50, 60],
              "source": "El Financiero",
              "admiralty": "B2"
            }
          ],
          "subscriber_action": "Do not commit new capital to Guanajuato until Q4 2026",
          "geographic": {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [...]},
            "properties": {
              "risk_level": 4,
              "risk_dimensions": ["cartel_violence", "extortion"],
              "energy_infra_score": 2
            }
          }
        }
      ]
    }
  ],
  
  "watch_items": [...],
  "trade_positions": [
    {
      "instrument": "KXTARIFFRATEPRC",
      "strike": ">9%",
      "price": 0.13,
      "recommendation": "buy",
      "sizing_usd": 100000,
      "rationale": "Most liquid, core USMCA tariff hedge"
    }
  ],
  "gaps": [...],
  "action_lines": [...],
  "meta": {
    "sources_cited": ["El Financiero", "CONAGUA", "CFE"],
    "total_judgments": 12,
    "avg_confidence": 0.65
  }
}
```

**Implementation:** Add `--json-output` flag to the brief generation pipeline. The LLM already produces structured JSON for adjacent briefs — extend the schema to include judgments, geography, and trade positions. Markdown remains the primary output; JSON is additive.
