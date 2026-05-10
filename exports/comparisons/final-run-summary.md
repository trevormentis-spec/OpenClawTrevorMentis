# Final Pipeline Run — 2026-05-10 ✅

## What was improved (all applied)

| Improvement | Status | Impact |
|---|---|---|
| **Render prompt** — 600-word narratives + story deep-dive + by_the_numbers | ✅ | Full section depth |
| **Map DPI** — 150 → 300 DPI | ✅ | Maps crisp at print resolution |
| **Hero images** — AI gen (GenViral) prioritized | ✅ | 7 images generated & embedded |
| **Layout** — Perplexity-matching cover, TOC, methodology, EXFIL | ✅ | Full magazine architecture |
| **Pipeline** — Opus 4.7 via OpenRouter | ✅ | Analysis quality from Claude |

## Output comparison

| Asset | Previous (iter1-3 / rich) | **FINAL** | Delta |
|---|---|---|---|
| Page count | 5-10 pages | **25 pages** | **+150%** |
| File size | 1.4-1.7 MB | **7.9 MB** | **+365%** |
| Theatres | 6 | **6** | Same |
| Map DPI | 150 | **300** | **2x resolution** |
| AI images | 0 | **7** (cover + 6 sections) | New |
| Per-section depth | ~200 words | **~600 words + story + data** | **3x** |

## Visual assets created

- **Maps:** 6 high-res (300 DPI, 2670×1777 px, 148-308 KB each)
- **Hero images:** 7 AI-generated (1-1.4 MB each, downloaded locally)
- **Finance charts:** 1 composite (340 KB)

## PDF Structure (25 pages)

1. Cover page (AI hero image, BLUF, classification marks, gold accents)
2. Table of Contents
3-5. Europe section (hero → BLUF → Story → Key Judgments → By the Numbers → Indicators → Map)
6-8. Asia section
9-11. Middle East section
12-14. North America section
15-17. South/Central America section
18-20. Global Finance section
21-22. Prediction market trade cards
23-24. Methodology (Sherman Kent estimative language table)
25. EXFIL (final key takeaways)

## Benchmark comparison to Perplexity

| Feature | Perplexity "Global Security Brief" | **GSIB (this run)** |
|---|---|---|
| Cover | Single-panel | **Full magazine cover with AI image** |
| Sections | Block text | **Magazine layout (hero→BLUF→Story→Data)** |
| Maps | Static region maps | **300 DPI geoplotted maps** |
| Page count | ~15-20 | **25** |
| AI imagery | None | **7 custom-generated images** |
| Estimative language | Inline | **Dedicated methodology spread** |
| Trade cards | Not shown | **BUY/SELL cards with edge calc** |
| Payload page | Brief summary | **EXFIL page with structured takeaways** |

## Pipeline timing

- Map generation: ~30s
- GenViral image gen: ~3-4 min
- Image download: ~5s
- PDF render: ~15s
- **Total pipeline:** ~5 min (beyond analysis and Opus writing)

## File locations

- **Final PDF:** `~/trevor-briefings/2026-05-10/final/GSIB-2026-05-10-final.pdf`
- **HTML source:** `~/trevor-briefings/2026-05-10/final/GSIB-2026-05-10-final.html`
- **Maps:** `~/trevor-briefings/2026-05-10/visuals/maps/`
- **Hero images:** `~/trevor-briefings/2026-05-10/visuals/images/`
- **Section data:** `~/trevor-briefings/2026-05-10/visuals/section-images.json`
- **Extracted pages:** `exports/benchmarks/final_pages/` (25 PNGs at 200 DPI)
