# Visual Specification — Daily Intel Brief

What each figure in the daily product must show. The visuals subagent
implements; this is the contract.

## Regional maps (×5)

One per geographic region. Not for Global Finance.

- **Aspect:** 3:2 landscape, 1200 × 800 px.
- **Tile source:** Mapbox Streets v12 (preferred) or OSM (fallback).
- **Bounding box:** union of incident points + 5° pad, capped at
  `regions.json` → `bbox_caps`.
- **Pins:** one per geocoded incident, colour-coded by category:
  - kinetic: `#dc2626` (red)
  - cyber: `#ea580c` (orange)
  - political: `#2563eb` (blue)
  - economic: `#16a34a` (green)
  - humanitarian: `#9333ea` (purple)
  - maritime: `#0d9488` (teal)
  - aviation: `#1e3a8a` (navy)
  - other: `#6b7280` (grey)
- **Pin label:** last four chars of incident ID (e.g. "0014"). The
  briefing prose can then reference "(see pin 0014)".
- **Caption (in PDF, not on the image):** "{Region label} — {N}
  incidents in 24 hours to {DTG} UTC. Pins colour-coded by category."
- **Always include:** north arrow (top-right corner, small), scale bar
  (bottom-left, 200 km reference).

If a region has zero geocoded incidents, omit the figure entirely (do
not ship a blank map). The assembler reads `manifest.json` and skips
missing regions cleanly.

## Global Finance chart panel (×1)

A single 2×2 panel image, 1600 × 1200 px, replacing the map slot for
the Global Finance section.

- **Top-left — G10 FX heatmap (% change vs USD):**
  EUR, GBP, JPY, CHF, CAD, AUD, NZD, NOK, SEK, plus DXY.
  Window: today's change. Colour scale diverging (red negative, green
  positive).

- **Top-right — Equity index sparklines, 30 days, normalised to 100:**
  S&P 500, STOXX 600, Nikkei 225, Hang Seng, Bovespa.
  Last close annotated.

- **Bottom-left — Commodities, 30 days, normalised to 100:**
  Brent crude, WTI crude, Henry Hub gas, gold (XAU), copper (HG).

- **Bottom-right — 10y sovereign yields, level (bp):**
  US, Germany, Japan, UK. Last close annotated.

- **Caption:** "Global Finance — markets snapshot {DTG} UTC. Sources:
  ECB SDW (FX, EUR yields), US Treasury (UST yields), EIA (energy),
  index providers (equities)."

If ChartGen is available (`CHARTGEN_API_KEY` set), submit the panel as
a single ChartGen dashboard request — output is one composed image.
Otherwise, build with matplotlib (script in `scripts/build_visuals.py`),
2×2 subplots, sans-serif, no gridlines on the heatmap, faint gridlines
elsewhere.

## Relationships diagram (×1, sometimes)

A single Mermaid `graph LR` for the most active region of the day.
**Skip if the active region has fewer than three named actors** — a
two-node graph isn't a diagram.

- **Theme:** dark, transparent background (`-t dark -b transparent -s 2`).
- **Node shape:** rounded rectangles for actors, diamonds for events.
- **Edge labels:** verb describing the relationship ("struck",
  "intercepted", "claimed", "denied", "deployed").
- **Layout:** left-to-right (`graph LR`).
- **Caption:** "{Region label} — actor / event relationships, last 24h
  to {DTG} UTC. Solid edges = observed; dashed edges = claimed."

Save as `visuals/relationships_<region>.png`. Include `kind:
"relationships"` in the manifest with `region` set.

## Cover page banner (no separate file)

The cover banner is rendered by the PDF template, not the visuals
subagent. The template uses:

- Top: classification banner ("UNCLASSIFIED // FOR OFFICIAL USE — TREVOR
  DAILY"), red on white.
- Title: "TREVOR DAILY INTELLIGENCE BRIEF".
- Subtitle: "{Long date} — DTG {YYYYMMDDThhmmZ}".
- BLUF block (drawn from `exec_summary.json`).

If the principal wants a custom banner image, drop a PNG at
`assets/banner.png` and the template will use it instead of the text
banner. The skill ships without one — text is fine.

## On consistency

The principal sees the same shape every day. That's the point of the
daily product. Do not let one of the five maps become "but today we
went 4×3" or "we had three subplots not four for the finance panel" —
the visual consistency is what makes the daily *recognisable*. If the
data won't fit the standard layout, fix the data filter, not the
layout.

## On accessibility

- No information conveyed by colour alone. Pin labels carry the
  incident ID; legend carries the category names.
- Charts have textual axis labels and a written caption.
- Diagrams have edge labels.

This is for the principal's later reuse — quotes, screenshots,
forwarded slides — not just the rendered PDF.
