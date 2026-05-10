# Iteration 1 — Layout & Structure Comparison

## What Changed
- Complete rewrite of `scripts/render_brief_magazine.py` (v4)
- New Perplexity-matching magazine layout structure
- Cover: added BLUF summary text box (matching Perplexity's daily assessment text)
- TOC: added numbering (01-08), region tags, cleaner layout
- Per-section structure:
  - `01 / REGION` section numbering
  - Hero image at top (from AI imagery or map)
  - `▸ Bottom Line Up Front` per section (not just in exec summary)
  - `▸ The Story` narrative label
  - Key Judgments boxes with colored Sherman-Kent band badges
  - `▷ By the Numbers` metric callout boxes (4-column grid)
  - `▷ MAP xxx — territorial & operational picture` callout
  - What Would Change This Assessment indicators
- Running headers (TREVOR / STRATEGIC INTELLIGENCE on left, ISSUE on right)
- Prediction market page with trade cards (BUY/SELL/HOLD badges)
- Methodology page with Sherman Kent estimative language table
- EXFIL final page with key takeaways

## What Improved vs Perplexity
- ✅ Same magazine-style structure (cover → TOC → sections → markets → method → exfil)
- ✅ Section hero images at top (we had them before, now placed like Perplexity)
- ✅ Key Judgments with colored bands (matches Perplexity's approach)
- ✅ BOTTOM LINE UP FRONT per section (matches Perplexity)
- ✅ Methodology with Sherman Kent table (matches Perplexity's estimative language page)
- ✅ Prediction market cards with buy/sell badges
- ✅ Running headers match Perplexity style
- ✅ EXFIL key takeaways page
- ✅ Gold accent color scheme (matches Perplexity's gold)

## What Still Needs Work
- ❌ Page count: 19 vs 32 (need more content density)
- ❌ Our hero images are smaller/lower quality (Perplexity has full-width hero photos)
- ❌ Missing per-section "THE STORY" deep-dive narratives (our narratives are shorter)
- ❌ Missing "BY THE NUMBERS" with real data points (Perplexity has actual data values per section)
- ❌ Prediction market cards need real data from Kalshi/Polymarket
- ❌ Missing maps on most pages (Perplexity has detailed maps for each theatre)
- ❌ Missing infographic data boxes with percentage changes
- ❌ Our typography could match more closely (letter spacing, font sizing)
- ❌ Missing photo credits (Perplexity credits Wikimedia Commons)
- ❌ Section images need to be more relevant (Perplexity uses specific photos for each section)

## Page Count Comparison
| Component | Perplexity | Our Iteration 1 |
|-----------|-----------|-----------------|
| Cover | 1 | 1 |
| TOC | 1 | 1 |
| Executive Summary | 1 | 1 |
| Russia/Ukraine | 3 | 2 |
| Sahel/Africa | 3 | 2 |
| India/Pakistan | 3 | 2 |
| Iran/Middle East | 3 | 2 |
| Mexico/N. America | 3 | 2 |
| Venezuela/S. America | 3 | 2 |
| Global Finance | — | 1 |
| Prediction Markets | 3 | 2 |
| Methodology | 1 | 1 |
| EXFIL | 1 | 1 |
| **Total** | **32** | **19** |

## Next Steps for Iteration 2
1. Run the full pipeline with Opus 4.7 for richer narratives (longer content = more pages)
2. Generate better maps and section images
3. Add real prediction market data from Kalshi scanner
4. Add "By the Numbers" data boxes with real metrics from the analysis
5. Add photo credits for images
6. Improve typography to match Perplexity tighter
