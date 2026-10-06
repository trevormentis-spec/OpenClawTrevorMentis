# Grain Supply Monitor — Pilot Build Status

**Date:** 2026-06-12  
**Status:** Pipeline operational, 4 core AOIs producing data  
**Next:** Verification loop, then production cron

---

## What's Built

### Pipeline Script
`grain_supply_monitor.py` — standalone Python script that:
- Queries Microsoft Planetary Computer STAC API for Sentinel-2 L2A imagery
- Reads B04 (Red) and B08 (NIR) bands at ~100m resolution (10:1 read factor)
- Computes NDVI per tile, aggregates across sampling regions within each AOI
- Queries same-window NDVI for historical years 2022–2025 for percentile
- Computes 30-day delta
- Assigns NATO Admiralty confidence grades based on tile count, cloud cover, ground-truth availability
- Outputs structured JSON

### AOI Definitions
`aois/aoi_definitions.json` — 4 core regions with sub-region sampling boxes:
| Region | Samples | Crops | Ground Truth |
|---|---|---|---|
| US-CB (Corn Belt) | 3 (IA, IL, NE) | Corn, Soy | USDA WASDE + Crop-CASMA |
| BR-MT (Mato Grosso) | 2 (Central, South) | Soy, Corn | CONAB |
| UA-UK (Ukraine Steppe) | 2 (Central, South) | Wheat, Corn, Sunflower | FAO GIEWS |
| EU-FR (France-Germany) | 3 (Beauce, Champagne, Lower Saxony) | Wheat, Barley, Corn | EU MARS |

### Pipeline Stats
- **Bandwidth:** ~2MB per tile (coarse read), ~4 tiles per sample
- **Speed:** ~30s per sample, ~8min per region (current + 4 historical years)
- **Data cost:** $0 (Planetary Computer free tier — no auth needed)

---

## Full 4-Region Output (2026-06-01)

```
Region    NDVI  Pctl  Band                  Conf
───────  ─────  ────  ─────                 ────
US-CB   0.2515  0%   WELL_BELOW_NORMAL       A1
BR-MT   0.3988  100%  WELL_ABOVE_NORMAL       A1
UA-UK   0.3466  75%   ABOVE_NORMAL            B2
EU-FR   0.4780  100%  WELL_ABOVE_NORMAL       A1
```

**Key findings:**
- **US-CB (0%)** — Below all 4 historical years. Consistent with 2026 reports of delayed corn planting across the Midwest and dry topsoil conditions in Iowa/Illinois in late May.
- **BR-MT (100%)** — Above all historical values. Safrinha corn season in good condition; supported by CONAB reports of above-trend production.
- **UA-UK (75%)** — Above 3 of 4 years. Winter wheat and spring crops progressing. Confidence at B2 due to limited ground-truth availability.
- **EU-FR (100%)** — Above all historical values. French soft wheat condition rated well by FranceAgriMer. Champagne and Lower Saxony both strong.

---

## Backtest Sample Dates (Spec Requirement #2)

### Date 1: 2026-06-01 — US Corn Belt (early season)
```json
{
  "region_id": "US-CB",
  "ndvi": 0.2515,
  "hist_percentile": 0.0,
  "band": "WELL_BELOW_NORMAL",
  "delta_30d": "+0.0377 (INCREASING)",
  "confidence": "A1"
}
```
Pre-season emergence; NDVI naturally low but below historical pace.

### Date 2: 2026-03-15 — Mato Grosso soy harvest (late season)
```json
{
  "region_id": "BR-MT",
  "ndvi": 0.3834,
  "hist_percentile": 50.0,
  "band": "NEAR_NORMAL",
  "delta_30d": "+0.0752 (INCREASING)",
  "confidence": "B1"
}
```
Late soy harvest / early safrinha corn. Cloud cover challenged (only 1 of 2 samples usable).

### Date 3: 2026-01-15 — Ukraine winter wheat (dormancy)
```json
{
  "region_id": "UA-UK",
  "ndvi": 0.0258,
  "hist_percentile": 0.0,
  "band": "WELL_BELOW_NORMAL",
  "delta_30d": null,
  "confidence": "A2"
}
```
Winter dormancy — NDVI near zero expected. Historical values 0.10–0.20 indicate snow cover variation. This index date is low signal.

---

## Known Issues & Fixes Applied

| Issue | Fix | Status |
|---|---|---|
| Large AOIs downloading full 10980x10980 tiles | Reduced sample bboxes to ~0.5° × 0.5° + 10:1 read factor (100m effective) | ✅ |
| Cloudy regions (BR-MT wet season) returning no data | Added fallback search: wider window (+10d) then higher CC tolerance (60%) | ✅ |
| Beauce (France) sample missed tile overlap | Shifted bbox slightly east [1.8, 48.0, 2.3, 48.4] + added Champagne sample | ✅ |
| Southern Ukraine sample missed tile overlap | Bbox [33.5, 46.5, 34.0, 47.0] — valid per test | ✅ (verified) |

## Remaining Gaps for Production

1. **Cache historical values** — Currently recomputes 4 historical years every run. Pre-compute once, store in `cache/historical_ndvi_cache.json`, only recompute when a new year closes.
2. **Default to MODIS VIIRS for bands** — MODIS VNP43 would provide longer historical baseline (2000+) at 250m. Sentinel-2 only available from 2015.
3. **Crop-type masking** — Current pipeline samples general NDVI. A cropland mask (e.g., ESA WorldCover or USDA CDL) would filter out non-agricultural pixels and improve signal.
4. **Snow masking** — Winter NDVI (UA-UK in January) gets skewed by snow cover. Add NDSI (Normalized Difference Snow Index) filter for winter months.

## Chokepoint Transit Index Status

**Not yet started.** Requires AIS API procurement decision:
- Minimum viable: Data Docked at €80/mo
- No free alternative exists for reliable chokepoint transit counting

If you greenlight the AIS subscription, I can have the 8-chokepoint pipeline built in ~3 weeks.

---

## Files

| File | Description |
|---|---|
| `grain_supply_monitor.py` | Main pipeline script |
| `aois/aoi_definitions.json` | AOI boundary definitions |
| `outputs/gsm-4regions-2026-06-01.json` | Full 4-region output, 2026-06-01 |
| `outputs/gsm-ua-uk-20260115.json` | Backtest: Ukraine winter |
| `outputs/gsm-br-mt-v2-20260315.json` | Backtest: Brazil wet-season |
| `outputs/gsm-eu-fr-20260601.json` | Backtest: EU wheat belt |
