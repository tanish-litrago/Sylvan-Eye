# Sylvan Eye — Handoff Record

Purpose: a running record so any new session (or Claude instance) can pick up the project without re-asking. Update this file at the end of each phase. **Never put API keys or credentials in this file.**

Last updated: 2026-10-02 (end of Phase 2, start of Phase 3)

---

## 1. What the project is

Sylvan Eye recommends plants/trees for afforestation at a given location. It combines satellite imagery (what's there now) with soil and climate data (what the environment supports), picks suitable plants with rules/ML, and optionally explains the result in plain language.

**Core design principle:** decision and explanation are separate. The rule/ML layer decides suitability from real data. An LLM may only *explain* the shortlist, never decide it (same pattern as the YouTube Transcript Summarizer project).

## 2. Architecture (four layers)

1. **Satellite Image Layer** — Sentinel-2 via Google Earth Engine: land cover, vegetation density, seasonality, terrain.
2. **Environmental Data Layer** — soil, climate, air quality.
3. **Matching Layer** — rules and/or lightweight ML against a plant requirement database. Not an LLM.
4. **Explanation Layer** — LLM, local inference, **swappable plugin, off by default**. v1 ships with structured shortlist output only.

## 3. v1 scope

One location in → data fetch → terrain extraction → ranked plant shortlist out. No accounts, no growth tracking, no multi-region comparison. Simple coordinate form for the UI.

Future: plant-care advice, multi-region comparison, larger-scale planning.

## 4. Decisions made

| Area | Decision |
|---|---|
| Language | Python, in a venv, deps in `requirements.txt` |
| Cost | Free tools only (user constraint) |
| Build style | Hands-on, user wants to understand every decision |
| Imagery | Google Earth Engine primary; provider interface kept swappable so a Copernicus direct-download backend can be added later |
| Earth Engine | Project `sylvan-eye`, noncommercial, **Community tier** (150 EECU-hours, no billing account) |
| Soil | Via Earth Engine (SoilGrids REST API is paused by ISRIC). Tries SoilGrids community assets first, falls back to OpenLandMap |
| Climate | Open-Meteo (free, no key) |
| Air quality | OpenAQ v3 (free key in env var `OPENAQ_API_KEY`) |
| Plant DB | Flat JSON/CSV, 20-30 plants for v1 |
| Matching | Simple threshold rules first; user also wants ML in this layer eventually |
| LLM | Local inference, swappable, off by default |
| Imagery summary method | Median composite for NDVI; **per-pixel 90th percentile across images for water (NDWI)**; per-pixel p10/p90 for seasonal NDVI range |
| Water class name | Renamed to `water_or_wet_surface` because the signal cannot tell small ponds from seasonally damp bare ground |

## 5. Build phases and status

| Phase | Goal | Status |
|---|---|---|
| 1 | Data pipeline: all four sources fetch for one hardcoded location | **Done** (4/4) |
| 2 | Terrain/vegetation extraction from satellite image → structured data | **Done** (with documented limits, see section 8) |
| 3 | Plant requirement database (20-30 plants) | **Next** |
| 4 | Rule-based matching layer | Not started |
| 5 | LLM explanation layer (plugin) | Not started |
| 6 | Integration + basic UI | Not started |
| 7 | Testing across multiple regions | Not started |

## 6. Files

- `phase1_data_pipeline.py` — four fetchers + a runner that reports X/4. Functions: `get_sentinel2_data`, `get_soil_data`, `get_openmeteo_data`, `get_openaq_data`.
- `phase2_terrain_extraction.py` — `get_terrain_data(lat, lon, radius_m=1000)` returns NDVI, NDWI (p90), seasonal NDVI (p10, p90, range, big-swing fraction), land-cover fractions, elevation, slope. Tunable thresholds sit at the top of the file: `NDWI_WATER=0.0`, `NDVI_SPARSE=0.2`, `NDVI_DENSE=0.5`, `SEASONAL_SWING=0.25`.
- `requirements.txt` — `requests`, `earthengine-api`.
- `.gitignore` — must include `venv/`, `.env`, `__pycache__/`.

Repo: github.com/tanish-litrago/Sylvan-Eye

## 7. Test locations and results

Phase 1 (Bilaspur city centre, 22.0797, 82.1409):
- Soil (OpenLandMap fallback): pH 7.58, organic carbon 10 g/kg, clay 33.4%, sand 37.9%.
- Open-Meteo: current conditions only (~27 °C, humidity ~70-76%).
- OpenAQ: station "Mangala, Bilaspur - CECB" about 1 km away (metadata only).

Phase 2 terrain extraction, four test points (1 km radius unless noted; imagery 2025, ~41-42 low-cloud images; Jul-Sep have no usable images):

| | City centre | Fadhakhar Park | Khapri farmland | NTPC Sipat ash dyke |
|---|---|---|---|---|
| Coordinates | 22.0797, 82.1409 | 22.042991, 82.173492 | 22.033592, 82.265111 | 22.079370, 82.281826 (400 m radius) |
| Mean NDVI | 0.265 | 0.469 | 0.288 | 0.037 |
| NDVI dry p10 / peak p90 | 0.196 / 0.348 | 0.279 / 0.648 | 0.178 / 0.443 | -0.09 / 0.115 |
| NDVI range | 0.152 | 0.369 | 0.264 | 0.204 |
| Big-swing area | 11.1% | 84.4% | 44.3% | 28.4% |
| Water or wet surface | 0.3% | 0.1% | 3.2% | 59.8% (suspect) |
| Bare or built-up | 44.6% | 2.0% | 4.8% | 40.2% |
| Sparse veg or crops | 45.3% | 58.0% | 86.9% | 0.0% |
| Dense vegetation | 9.9% | 39.9% | 5.1% | 0.0% |
| Elevation / slope | 269 m / 2.95° | 267 m / 2.74° | 269 m / 2.45° | 273 m / 3.0° |

Notes on the points:
- City centre: matches satellite view; a small pond was missed until the NDWI method changed (median hid it; its NDWI was positive only in Jan-Feb).
- Park: high seasonal swing comes from deciduous trees/grass, not crops.
- Khapri: fallow/harvested cropland with small fields, tanks, scattered trees. Not degraded land, despite being picked as a test of it.
- Ash dyke (NTPC Sipat "Rakhad Dam"): never greens up (peak NDVI 0.115). The 59.8% water figure is not trustworthy, see section 8.

## 8. Known issues and caveats

**Terrain layer**
- **Swing alone does not mean cropland.** Deciduous trees swing as much as crops. Working hypothesis (3-4 points only, not validated): low dry floor + big swing = cropland; high dry floor + big swing = deciduous trees/grass; low floor + low peak + small swing = never-green ground (barren, roofs, ash); high floor + small swing = evergreen.
- **Water class cannot separate small ponds from seasonally damp bare ground.** On the ash dyke, NDWI and MNDWI rose and fell together (negative Oct-Feb, peak Apr-May at ~0.11 NDWI / 0.16 MNDWI, no images Jul-Sep). Those values overlap the park-area pond (0.14-0.18), so no single NDWI threshold separates them. MNDWI did not fix it. For planting both are excluded land, so the label was widened to `water_or_wet_surface`. Possible later cross-check: JRC Global Surface Water in Earth Engine (asset ID and small-pond resolution not yet verified).
- **Bare and built-up are merged**, and mixed 10 m pixels push built-up edges into "sparse vegetation or crops". A built-up index (NDBI) or ESA WorldCover (separate built-up/bare/cropland classes; asset ID not yet verified) could help later.
- **No monsoon imagery.** The <20% cloud filter drops Jul-Sep, so peak greenness of kharif crops is partly missing and swing is conservative. Proper cloud masking (Sentinel-2 scene classification band) would fix this.
- NDVI/NDWI thresholds are hand-tuned starting points validated on only a few points. They have not been checked on truly degraded natural land (no such test site yet: gullies, quarries, rocky ground).

**Soil**
- **Soil data is only valid on natural ground.** At industrial, ash, mined or filled land, OpenLandMap/SoilGrids describe natural soil that isn't there, so the numbers are meaningless. The matching layer needs a way to flag such land (low NDVI + industrial context) instead of trusting soil values.
- SoilGrids community assets returned masked (None) values at the test point even over a 500 m buffer; cause unknown. OpenLandMap fallback works but is a 2018 dataset at 250 m; record the source name in any output.
- OpenLandMap sand and organic-carbon asset IDs were written from memory, not verified against the catalog (pH and clay were verified). They returned plausible values.

**Climate and air quality**
- Open-Meteo currently returns only current weather and a 7-day forecast. Plant matching needs long-term climate (annual rainfall, temperature range, dry-season length): switch to the historical archive endpoint before Phase 4.
- OpenAQ returns station metadata, not measurements. Air quality is the weakest input for plant suitability; treat as optional context, not a matching rule.

**Other**
- Earth Engine prints a feedback-survey line on init; harmless.

## 9. Security notes

- OpenAQ key lives only in the `OPENAQ_API_KEY` environment variable.
- Earth Engine credentials are cached locally by `earthengine authenticate`, outside the repo.
- Before every commit: run `git status` and confirm no keys, `.env`, or `venv/` are staged. If a key is ever committed, rotate it immediately.

## 10. Working preferences

- Direct, plain communication.
- Free-only tooling.
- Explain the *why* of each decision; user wants to build it hands-on rather than receive a finished black box.
- Confirm important decisions with the user before locking them in.
- Verify against reality (satellite view) rather than trusting a number; several of this phase's fixes came from the user's screenshots.

## 11. Next steps

1. **Phase 3: plant requirement database.** Define fields (pH range, annual rainfall range, temperature range, soil texture tolerance, water need, drought/waterlogging tolerance, sun, deciduous/evergreen) and fill 20-30 well-documented plants/trees relevant to central India / Chhattisgarh first. Record the source for every plant's values.
2. Switch Open-Meteo to historical climate averages (needed by Phase 4).
3. Decide how the matching layer should treat low-confidence or excluded land (water/wet surface, built-up, active cropland, ash/industrial) rather than recommending plants there.
4. Later/optional: find a true degraded natural-land test site; monsoon cloud masking; WorldCover or JRC water cross-check.