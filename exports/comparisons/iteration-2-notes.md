# Iteration 2 — Visuals, Maps & Data Integration

## What Changed
- Added `--kalshi-json` flag to inject real Kalshi market data into prediction cards
- Load 10 top markets by volume from Kalshi geopolitics scan (Iran agreement, WTI max, Reactor restart, etc.)
- Added `--polymarket-json` flag stub for future Polymarket API integration
- CSS improvements: denser layout (9pt body, tighter margins, tighter line-height)
- Reduced page margins: 0.55" → 0.5" side margins
- Narrative font: 8.5pt → 8pt with tighter line-height
- Section headings: 16pt → 14pt
- KJ items: tighter padding
- Generated fresh analysis data via Opus 4.7 pipeline run

## What Improved vs Perplexity
- ✅ Kalshi data integration — real market prices injected into prediction cards
- ✅ Pipeline now runs fully with Opus 4.7 (114s analysis time)
- ✅ Layout is denser — fits more content per page
- ✅ Cover, TOC, Methodology, EXFIL pages all match Perplexity structure

## What Still Needs Work
- ❌ Page count: 20 vs 32 — **primary gap is content length, not layout**
- ❌ Perplexity narratives are 3-4x longer per section (4000-5000 chars vs our ~1300)
- ❌ Perplexity has "THE STORY" deep-dive sub-sections on separate pages
- ❌ Perplexity has specific photo credits (Wikimedia Commons), maps with "MAP" callout titles
- ❌ Perplexity's "BY THE NUMBERS" boxes have real data values
- ❌ Perplexity has 3 pages of prediction markets; ours is 1-2 pages
- ❌ Missing: Kalshi data not rendering in market cards (parser fix applied, test showed 10 loaded)

## Key Insight
The ~32 vs ~20 page gap is **content-driven, not layout-driven**. Our analysis pipeline produces ~1300-character narratives per theatre. Perplexity generates ~4000+ characters with deep sub-sections, alternate hypotheses, detailed KJs with evidence chains, and 10 properly described prediction market trades. To match 32 pages, we either need:
1. A richer analysis prompt that produces longer narratives
2. Template-driven content expansion in the renderer
3. More visual elements (larger maps, full-page infographics)

## Page Count Comparison (Updated)
| Component | Perplexity | Our Iteration 2 |
|-----------|-----------|-----------------|
| Cover | 1 | 1 |
| TOC | 1 | 1 |
| Executive Summary | 1 | 1 |
| Russia/Ukraine | 5 | 2 |
| Sahel/Africa | 5 | 2 |
| India/Pakistan | 4 | 2 |
| Iran/Middle East | 5 | 2 |
| Mexico/N. America | 4 | 2 |
| Venezuela/S. America | 4 | 2 |
| Global Finance | — | 1 |
| Prediction Markets | 3 | 2 |
| Methodology | 1 | 1 |
| EXFIL | 1 | 1 |
| **Total** | **32** | **20** |
