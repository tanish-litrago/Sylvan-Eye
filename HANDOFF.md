# Sylvan Eye — Handoff Record

Purpose: a running record so any new session (or Claude instance) can pick up the project without re-asking. Update this file at the end of each phase. **Never put API keys or credentials in this file.**

Last updated: 2026-10-09 (Phase 6 web UI: steps 1-6 of 7 written, fixtures/tests/handoff next; earlier: Phase 3 at 26 of 32 species; Phase 4 matcher works live on four sites; Phase 5 explainer run with gemma4:e4b and qwen2.5:7b-instruct)

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
| Plant DB | Flat CSV (`plants.csv`), India-wide mix of trees, every value sourced by URL. Columns `*_opt_*` = the source's typical/"grows best" range, `*_abs_*` = bracketed extremes (optional). Blank cell = not found, never guessed |
| Plant data sources | FAO ECOCROP datasheets where available; otherwise World Agroforestry (Agroforestree Database) species sheets; one USDA Forest Service document (neem); one set of secondary sources (mahua, flagged weak) |
| Cache (2026-10-07) | Cache raw measurements only (terrain 30 days, soil and climate 1 year), never matcher verdicts or LLM text. SQLite by default, Postgres switchable by environment variable. Redis rejected for v1 (separate server, no Windows support, nothing here needs it); revisit only if Phase 6 becomes a multi-user web service with background jobs. CLI: `--refresh`, `--no-cache` |
| Using other LLMs to fill rows | Allowed (user tried Gemini), but every row must carry a source URL and be checked against that page before it goes in. Gemini's 12 rows were checked this way |
| Matching | Simple threshold rules first; user also wants ML in this layer eventually |
| LLM | Local inference, swappable, off by default |
| Imagery summary method | Median composite for NDVI; **per-pixel 90th percentile across images for water (NDWI)**; per-pixel p10/p90 for seasonal NDVI range |
| Matcher tolerances (2026-10-06, chosen by Claude on the user's delegation) | pH within 0.3 of a stated limit = marginal, not excluded (pH is modelled); texture one class away (light/medium/heavy) = marginal, two away = poor; "poor" scores 0.35 (was 0.25, a judgement call); default terrain radius 400 m (was 1000); water or wet surface 20% to 49% = warning, 50% or more = block |
| Water class name | Renamed to `water_or_wet_surface` because the signal cannot tell small ponds from seasonally damp bare ground |
| Phase 6 stack (2026-10-08) | FastAPI backend plus one plain HTML/JS page, no npm or build step. Chosen over Streamlit and Flask+Jinja for hands-on understanding and because the 1-2 minute first run needs an honest wait |
| Phase 6 long run (2026-10-08) | Background job plus polling: `POST /analyze` returns a job id at once, the page polls `GET /jobs/{id}` every 2 s. Chosen over Server-Sent Events and one blocking request. One analysis runs at a time (a lock) because `CACHE_LOG` in `phase4_matcher.py` is a shared module-level list. Redis not needed: single local user, in-process threads |
| Phase 6 layout (2026-10-08) | One page, top to bottom: status banner, warnings (always expanded), tiers (replaced by the block reason when blocked), data limits (always visible), ruled-out list (collapsed, count shown). Tabs and two columns rejected so warnings cannot be skipped |
| Phase 6 tiers (2026-10-08) | No rank numbers shown, because many plants tie on score (a missing value and a marginal fit both score 0.5). Rule layer (`tiers.py`) puts each plant in Strong fit (all four scored factors have data, none marginal or poor), Likely not fully verified (none flagged, some data missing) or Caution (any marginal or poor). Elevation is outside the tiers. An unknown verdict counts as a flag. Alphabetical inside a tier. Decided in Python, never in JavaScript |
| Phase 6 LLM in the UI (2026-10-08) | Template text always shown; the LLM is a separate opt-in button that starts its own job, labelled as LLM-written with the model name and the notes from `explain()`. BUILT (step 6): a second job on the same polling pattern; the page lists two models from `GET /llm/models`; if the checks reject the model's answer the panel says so and shows the template text again; if Ollama is not running the page shows the error message and the template text is untouched; never offered for a blocked location |
| Phase 6 plain-words text (2026-10-09, delegated to Claude) | The fact sheet passed to `build_facts` is in tier order, so the text names strong plants first and says top 8 of N; caution plants therefore do not appear in the text (they do on the page) |
| Phase 6 location entry (2026-10-08) | Paste box for "lat, lon" copied from Google Maps, latitude and longitude fields, a dropdown of the five test sites, radius field (default 400 m, under Advanced), refresh and offline-demo boxes. The result always shows the radius used. No map yet |
| Phase 6 theme (2026-10-08/09) | Palette sampled by hue from the user's red-eyed tree frog photo: skin lime #a8db49, eye orange #e45206, flank blue #4f5f9e, belly #cac3b2, pupil black #100e01. Light theme (white main card, lime header band). The user found the dark leaf greens too dark and then asked to drop leaf greens from the main elements, so only frog colours are used: blue for buttons and information, orange for warnings only, black for text. Colour is never the only signal |

## 5. Build phases and status

| Phase | Goal | Status |
|---|---|---|
| 1 | Data pipeline: all four sources fetch for one hardcoded location | **Done** (4/4) |
| 2 | Terrain/vegetation extraction from satellite image → structured data | **Done** (with documented limits, see section 8) |
| 3 | Plant requirement database (20-30 plants) | **Mostly done**: 26 of 32 species filled, 6 blank (see section 8) |
| 4 | Rule-based matching layer | **Done** (`phase4_matcher.py`); offline demo and live run both work on Bilaspur city centre. Still to do: live runs on other sites and a local-knowledge check |
| 5 | LLM explanation layer (plugin) | **Written, run with both local models on demo and live sites** (`phase5_explainer.py`); guard extended twice after reviewing real outputs; rerun with the updated guard still to do |
| 6 | Integration + basic UI | **In progress, steps 1-6 of 7 written** (tiers, FastAPI skeleton, job layer, form and polling page, results page, LLM opt-in button). Next: step 7 fixtures, tests and handoff. See section 7c and 11 |
| 7 | Testing across multiple regions | Not started |

## 6. Files

- `phase1_data_pipeline.py` — four fetchers + a runner that reports X/4. Functions: `get_sentinel2_data`, `get_soil_data`, `get_openmeteo_data`, `get_openaq_data`.
- `phase2_terrain_extraction.py` — `get_terrain_data(lat, lon, radius_m=1000)` returns NDVI, NDWI (p90), seasonal NDVI (p10, p90, range, big-swing fraction), land-cover fractions, elevation, slope. Tunable thresholds sit at the top of the file: `NDWI_WATER=0.0`, `NDVI_SPARSE=0.2`, `NDVI_DENSE=0.5`, `SEASONAL_SWING=0.25`.
- `plants.csv` — 32 species rows. Columns: common_name, scientific_name, type, leaf_habit, ph/rain/temp each with `_opt_min,_opt_max,_abs_min,_abs_max`, soil_texture (light/medium/heavy/organic, comma separated), source, notes. Rainfall in mm/year, temperature in degrees C. Status: 14 rows have pH, rain and temp typical ranges; 12 are partly filled (mostly missing pH); 6 are blank. Source mix: ECOCROP 8, World Agroforestry 16, USDA Forest Service 1 (neem), secondary sources 1 (mahua).
- `validate_plants.py` — checks `plants.csv` (typical pair filled together, extremes contain the typical range, pH 0-14, plausible values, texture words, source present, no duplicates). Run `python validate_plants.py plants.csv`; currently 0 problems. It cannot catch a number that is plausible but wrong.
- `phase4_inputs.py` — `get_climate_normals` (long-term climate from Open-Meteo archive) and `classify_soil_texture` (clay/sand to light/medium/heavy). Tunable constants at the top.
- `phase4_matcher.py` — `match_plants(env)` and `check_eligibility(terrain)`. Per plant and factor (rainfall, temperature, pH, texture, elevation): good / within_limits / marginal / poor / excluded, or skipped when data is missing (missing counts as neutral 0.5 in the score and lowers confidence). Prints a ranked list with a reason for every plant, plus the ruled-out list and the plants with no data. `python phase4_matcher.py --demo` runs offline on Bilaspur's measured values; without `--demo` it runs the live terrain, soil and climate fetches. The eligibility gate blocks when water/wet surface is 50% or more, and warns for water/wet 20% or more, built-up share, cropland-like seasonality and never-green land. `--brief` prints a short report (env line, terrain summary, warnings, top 10 plants with only their non-good checks, ruled out). Live reports print a one-line terrain summary (radius, land-cover shares, NDVI, swing). pH margin 0.3 and texture adjacency are constants at the top of the file.
- `phase5_explainer.py` — explanation layer, OFF by default. `build_facts()` packs the matcher output into a fact sheet; `template_explanation()` gives deterministic plain English (the default output, no LLM); `OllamaExplainer` (default model `gemma4:e4b`, `--model` to change) writes prose from the fact sheet via the local Ollama API. Its answer goes through `verify_explanation()`: any plant from plants.csv that is not in the fact sheet, or any number (decimal or 2+ digits) that is not anywhere in the fact sheet, rejects it; one retry with the reason, then it falls back to the template. A blocked location (water/wet surface) never calls the LLM. Run: `python phase5_explainer.py --demo [--llm]` or `python phase5_explainer.py LAT LON [--llm] [--model NAME]`.
- `storage.py` — key-value cache with two interchangeable backends. SQLite (default, standard library, file `sylvan_cache.db`) or Postgres (optional: `pip install -r requirements-postgres.txt`, `SYLVAN_STORE=postgres`, `SYLVAN_DB_URL=postgresql://user:pass@host:5432/db`). Table `cache(key, value, created_at, expires_at)`; JSONB in Postgres. `make_key` rounds coordinates to 4 decimals (about 11 m) and includes a version and the radius. The version of each measurement comes from a `CACHE_VERSION` constant in the module that produces it (`phase2_terrain_extraction` = 3 since the multi-year swing, `phase1_data_pipeline` = 1, `phase4_inputs` = 1; the matcher uses 1 if a module has none), so cached data from older code is never reused. Bump the constant whenever a fetch function's output changes. `cached()` returns (value, hit/miss/refreshed/no-cache), normalises values through JSON so hits and misses look identical, and never lets a broken store stop the analysis.
- `test_storage.py` — plain-assert tests (`python test_storage.py`; add `SYLVAN_TEST_DB_URL` to include Postgres, it wipes the `cache` table). 31 checks per run, no Earth Engine needed (slow fetches are faked). Last run: SQLite and a real PostgreSQL 16, all passed.
- `requirements-postgres.txt` — `psycopg2-binary`, only needed for the Postgres backend.
- `requirements.txt` — `requests`, `earthengine-api`, `fastapi`, `uvicorn`, `httpx` (httpx only for `test_app.py`).
- `tiers.py` (Phase 6) — rule layer. `tier_for(entry)`, `group_by_tier(ranked)` (the page's tiers, no scores, alphabetical inside a tier), `order_by_tier(ranked)` (matcher entries in tier order, feeds the fact sheet), `TIER_ORDER`, `TIER_LABELS`, `TIER_DESCRIPTIONS` (the rule wording sent to the page). `python tiers.py --demo` prints the tiers offline. `test_tiers.py` tests it.
- `jobs.py` (Phase 6) — job layer, no web code. `start_job(params)` returns a job id and runs `run_live`, `match_plants`, `build_facts`, `group_by_tier`, `explain` (template only) in a background thread; `get_job(id)` returns state (queued, running, done, error), a plain-English stage, seconds, and the result. Stage comes from what `run_live` has already written to `CACHE_LOG`. One analysis at a time (`_RUN_LOCK`); keeps the newest 50 jobs in memory. When blocked, tiers are empty (enforced here). The score-ordered shortlist is not sent to the page. The full fact sheet is kept on the finished job (never sent out) so `start_explain_job(analysis_id, model)` can run `explain(facts, OllamaExplainer(model))` as a second job; one model call at a time (`_LLM_LOCK`); source is reported as llm, or template when the guard rejected the answer. `test_jobs.py` tests it with a faked `run_live`.
- `app.py` (Phase 6) — FastAPI routes: `GET /health`, `GET /`, `POST /analyze` (202 plus job id; input limits: lat -90 to 90, lon -180 to 180, radius above 0 and at most 5000 m, which is a sanity ceiling chosen by Claude), `GET /jobs/{id}`, `GET /llm/models`, `POST /jobs/{id}/explain` (202 plus a new job id; 404 unknown analysis, 409 unfinished or blocked, 422 unknown model; the model list is the `LLM_MODELS` constant in `app.py`). Refuses to start unless the working folder contains `plants.csv`. Run from the project folder: `python -m uvicorn app:app --reload`, then open http://127.0.0.1:8000 (FastAPI's test page is at /docs). `test_app.py` tests the routes.
- `static/index.html`, `static/app.js`, `static/style.css` (Phase 6) — the page: paste box, site dropdown (the `SITES` array at the top of `app.js`), polling with a stage line and a slow-run hint after 8 s. Results (step 5), in order: status banner (BLOCKED, demo, N warnings, or no warnings; the demo banner says the terrain checks were not run, because the gate does not run without terrain), eligibility warnings, conditions, plants grouped by tier (each plant a collapsed card with five check chips and weed flags; open it for the reason behind each check and its tier), data limits panel (limits, radius used, terrain summary line, cache line), ruled-out list collapsed with its count, plants with no data, the template plain-words text, a collapsed raw JSON block, and under the plain-words text the optional LLM controls (model menu, button, status line, a separate dashed panel for the model's text; shown only if the server lists models and the site is not blocked). When blocked, no plants are drawn. All server text goes in with `textContent`, never `innerHTML` (checked with hostile strings).
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

## 7b. Gate calibration data (live runs, 2026-10-06, imagery 2025)

| Site (radius) | Water/wet | Bare/built | Big swing | NDVI dry to peak | Known land type | Gate result |
|---|---|---|---|---|---|---|
| City centre, 22.0797 82.1409 (400 m) | 0% | 44% | 11% (2025); by year 32% (2023), 8% (2024), 11% (2025) | 0.196 to 0.349 | dense town | built-up warning (correct) |
| Fadhakhar Park, 22.042991 82.173492 (400 m) | 0% | 0% | 94% | 0.29 to 0.678 | park, trees and grass | no warning (correct) |
| Khapri, 22.033592 82.265111 (400 m) | 0% | 3% | 26% (2025), 100% (2023), 99% (2024) | 0.188 to 0.41 | farmland, fallow or harvested in the satellite view | single-year gate MISSED it; multi-year gate flags it (best year 100%) |
| Ash dyke, 22.079370 82.281826 (400 m) | 60% | 40% | 28% (2025); by year 94% (2023), 29% (2024), 28% (2025) | -0.09 to 0.115 | ash lagoon | blocked (correct); the old best-year rule would also have wrongly said cropland |
| Ash dyke (1000 m) | 17% | 42% | 29% | 0.081 to 0.287 | same, plus farmland and lake | not blocked (missed) |
| 22.002166 82.195423 (400 m) | 0% | 0% | 98% | 0.143 to 0.663 | green farmland (user checked the map) | cropland warning (correct) |

Observation: Khapri may look "not cropped" because 2025 imagery caught it fallow; a one-year seasonal rule only sees land that was cropped that year. FIX WRITTEN 2026-10-06; RUN LIVE ON KHAPRI 2026-10-07 (cache row `terrain:v3`): by year 2023 = 100%, 2024 = 99.2%, 2025 = 25.5%, best year 2023. The 2025 value matches the earlier single-year 26%, so the code is consistent with the old path. Hypothesis supported: Khapri was cropped in 2023 and 2024 and fallow in 2025. CONTROLS RUN 2026-10-07: city centre 32/8/11% and ash dyke 94/29/28% (2023/2024/2025). So the swing is not inflated everywhere (the city stays low), but a single year can spike (ash dyke 94% in 2023; 2023 is the highest year at both controls, cause unknown: possibly real lagoon changes or a 2023 imagery quirk). DECISION: the gate no longer uses the best year; the cropland warning needs a swing of 40% or more in at least 2 years (or the only year available) plus dry NDVI under 0.2. On the real values: Khapri flagged (2 of 3 years: 2023, 2024), city centre and ash dyke not flagged for cropland (the ash dyke is still blocked for water). Tuned on a handful of sites: unvalidated. A field cropped in only one of three years would be missed. Original note: `phase2_terrain_extraction.py` now computes the big-swing share separately for 2023, 2024 and 2025 (`big_swing_by_year`, `big_swing_fraction_best_year`, `best_swing_year`; years with under 10 low-cloud images are skipped), and the matcher gate uses the best year. This also tests the hypothesis: rerun Khapri at 400 m; if one year shows a high swing the hypothesis holds, if all three are low it is rejected. Fixture tests only; the Earth Engine code has not been run.
Observation: rainfall and temperature are identical (1487 mm, 26.5 C) at the park and the last site, so the Open-Meteo reanalysis grid is coarse; climate does not discriminate between nearby sites. Terrain, soil and elevation do.

## 7c. Phase 6 web UI tests (2026-10-09)

Verified by the user on their machine: `python tiers.py --demo` output and `test_tiers.py` (step 1, 3 tests at the time); the server runs and `test_app.py` passed (step 2 version); a demo job run from FastAPI's /docs returned state done (step 3).

Verified only in Claude's sandbox, NOT yet by the user: `test_jobs.py` (7 tests: demo job offline, unknown job, stage changes follow the log, blocked site gets no plants, error then next job still runs, queued job waits, old jobs pruned), the newer `test_app.py` (bad input gives 422, unknown job 404, demo end to end), `test_tiers.py` with `order_by_tier`, and the page logic of `static/app.js` (simulated browser against a real server with a fake `run_live` and a fake Ollama: 13 checks on the LLM controls (answer labelled with the model, template text unchanged, Ollama-down message, no controls when blocked, a late answer never lands in a newer result, hostile text stays text), 16 checks on the form and waiting (paste parsing, site menu, validation, 422 message, demo run, stage lines, slow hint) and 24 checks on the results page (demo, clean site, warning site, blocked site, section order, chips, ruled-out list, hostile text stays text). The look of the page has never been seen in a real browser by Claude; contrast ratios were calculated, not eyeballed.

`test_jobs.py` is now 11 tests (4 added for the LLM job: accepted answer, rejected answer falls back, Ollama down then next call works, refusals) and `test_app.py` 8 (LLM routes added).

Never run: the web path with real Earth Engine (a cached site should return in seconds, a new place in 1-2 minutes), and the LLM button with a real Ollama (all LLM tests use a fake explainer). The five sites for it are in `SITES` in `app.js`.

On the demo values (Bilaspur city centre) the tiers are: 1 Strong fit (Moringa), 12 Likely, 10 Caution, 3 ruled out, 6 with no data.

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

**Plant database**
- **Six species are blank** because the page could not be opened or found: banyan (*Ficus benghalensis*), bamboo (*Dendrocalamus strictus*), amla (*Phyllanthus emblica*), semal (*Bombax ceiba*), bijasal (*Pterocarpus marsupium*), chir pine (*Pinus roxburghii*). Do not fill from memory; get the datasheet text or leave blank.
- **pH is the weakest column.** World Agroforestry sheets usually describe pH in words, so many rows have no pH. The matcher must skip a missing factor and lower confidence, never count it as a pass.
- **Hill species need an elevation rule.** Deodar's sheet gives altitude 1200-3500 m; it should not be recommended on plains such as Bilaspur (~270 m). Elevation is already returned by Phase 2. Altitude limits are in the `notes` column, not yet in a numeric column; add `alt_min`/`alt_max` columns if the matcher needs them.
- **Sources disagree on what "range" means.** Khejri: ECOCROP optimal rain 400-800 mm vs World Agroforestry natural-range 120-250 mm. ECOCROP temperature definitions are not consistent across species (salai optimal 33-42 looks like a hot-season value). Decide what annual climate statistic to compare against (annual mean temperature and annual rainfall are the working choice).
- **Ecologically contested species.** ECOCROP flags babul (*Vachellia nilotica*) and jamun (*Syzygium cumini*) as able to become weeds. Eucalyptus, subabul and *Acacia auriculiformis* were deliberately left out of the list. App output should surface such flags.
- **Mahua row is weak**: only secondary sources, which disagree on rainfall (550-1500 vs 750-1875 mm). Verify before relying on it.
- **Interpretation choices Claude made**: Ziziphus temperature (sheet says '7-13 to 37-48'; inner 13/37 used as typical, outer 7/48 as extremes); bael temperature -6 to 48 is an extreme range, not a narrow optimum; texture words were derived from soil descriptions in the sheets (e.g. 'sandy loam' = medium,light). Gemini's 'heavy' for siris was changed to 'medium'.
- **Two rows were added that were not on the original list**: salai (*Boswellia serrata*) and khair (*Acacia catechu*), both Indian dry-forest natives found in ECOCROP.

**Matcher (Phase 4)**
- **It filters better than it ranks.** On Bilaspur's values 14 plants tie at 0.88 because the data is too coarse to separate them (a marginal fit and a missing value both score 0.5). A plant with full data and nothing wrong (moringa, 0.85) can rank below plants that simply have a missing factor, and very wide source ranges (bael temperature -6 to 48, rosewood 8 to 44) pass everything, so temperature does not discriminate. Consider presenting tiers (strong fit / possible / ruled out) instead of a numeric rank. Treat the ruled-out list and the warnings as the strongest output.
- **Only 13 of 32 plants have altitude limits.** A plant with no altitude data is not excluded at high elevation; on a 2000 m test site, mango, sissoo and salai still ranked. Add altitude for the rest.
- **Exclusions by pH rest on weak input.** pH comes from OpenLandMap (2018, 250 m, modelled). On Bilaspur it ruled out salai and khair (stated maximums 7.4 and 7). Confirm with a soil test.
- **Gate thresholds come from four sites** and are unvalidated. On those four it gave: city centre built-up warning; park none; Khapri farmland cropland warning; ash dyke blocked plus never-green warning.
- Both `phase4_matcher.py` and `phase5_explainer.py` accept `--radius METERS` (default 400) for the terrain circle. The ash-dyke test in Phase 2 used 400 m. At 1000 m the circle includes farmland and a lake outside the dyke: the live run at 1000 m was NOT blocked (42% bare/built warning only, 22-plant list). Default is now 400 m. Gate thresholds were calibrated on 1000 m circles for city/park/farmland and are unvalidated at 400 m; rerun all sites.
- Live run on Bilaspur city centre gave the same environment as the demo (1520 mm, 26.4 C, pH 7.58, medium, 269.4 m) plus the built-up warning (45% bare or built-up). Live runs on the other test sites are still to do: `python phase4_matcher.py LAT LON`.

**Explainer (Phase 5)**
- **Real models were run** on the demo values and on three live sites (`gemma4:e4b` on Khapri and the park, `qwen2.5:7b-instruct` on Khapri; the ash dyke correctly skipped the LLM). Findings:
  - `gemma4:e4b` was faithful on every plant check but wordy and clumsy ("weed source"). Once its Khapri answer was **cut off mid-sentence** (ended at "Moringa has a score", missing the ruled-out and no-data sections) and the first guard accepted it. Likely cause: Ollama's default context window is smaller than the prompt plus answer.
  - `qwen2.5:7b-instruct` read better but made real errors on Khapri: said Babul meets "most conditions" without mentioning its marginal rainfall; said Teak lacks altitude data (it has it) and Amaltas lacks pH data (it has pH, lacks texture); dropped Moringa; used bold markdown despite the prompt. Earlier on the demo it claimed Bael fits on texture (no data) and called the weed flag "invasive".
  - Gemma's park answer was accurate and complete. The template (no LLM) is correct in all cases.
- **Guard now checks:** plants not in the fact sheet; numbers (2+ digits or decimals) not anywhere in the fact sheet; unsourced words (`UNSOURCED_TERMS`); per plant: talking about a skipped factor without saying no data, saying no data for a factor that WAS checked, and dropping a marginal/poor check; completeness (every shortlisted, ruled-out and no-data plant must be named); and a cut-off flag from Ollama's `done_reason`. Replaying all real outputs: every good answer accepted, every bad one rejected for the specific errors above. A rejection triggers one retry, then the deterministic template.
- **Ollama call changes:** `num_ctx` 8192, `num_predict` 2048, compact JSON in the prompt, bold markers stripped. If answers still get cut off, raise `num_ctx` (8 GB VRAM should handle it for these models).
- **Limits that remain:** a real number can still sit on the wrong claim; the checks are keyword heuristics tied to sentence structure and will miss new kinds of drift or paraphrase; vague wording ("most factors") passes. The deterministic template is the trusted output; LLM text is labelled as LLM-written.
- Prompt gained two rules from these runs: a skipped check means no data, and use the flags' own wording.
- Not yet seen: the retry path against a real model. The new guard and prompt have only been tested by replaying saved outputs; rerun `--llm` on Khapri and the park with the updated file.

**Climate and air quality**
- Open-Meteo currently returns only current weather and a 7-day forecast. Plant matching needs long-term climate (annual rainfall, temperature range, dry-season length): switch to the historical archive endpoint before Phase 4.
- OpenAQ returns station metadata, not measurements. Air quality is the weakest input for plant suitability; treat as optional context, not a matching rule.

**Other**
- Earth Engine prints a feedback-survey line on init; harmless.

### Phase 6 caveats

- **LLM button:** one call can wait up to 300 s per attempt plus one retry (`MAX_RETRIES`), so up to about 10 minutes; the page gives up after 20. An answer that passes the guard can still put a real number on the wrong claim, so the page keeps the template text next to it.

- **One analysis at a time.** Concurrent requests queue behind a lock because `CACHE_LOG` is shared. Fine for one user. The stage line is read from that same shared list; a progress callback argument on `run_live` would be cleaner.
- **Jobs live in memory** (newest 50), lost on restart. No accounts, no auth, and raw error text is shown on the page: this is for local use only, do not put it on a public host as it is.
- **Start the server from the project folder.** `plants.csv` and `sylvan_cache.db` are found relative to the working folder; elsewhere a new empty cache would make every place look new (1-2 minutes). `app.py` now exits with a message instead.
- **Tiers measure completeness as well as fit.** On the demo values only Moringa is Strong, because many plants have no pH or texture data. Read Strong as "all four factors checked and none flagged", not "best plant". Filling the blank cells in `plants.csv` moves plants up.
- **The plain-words text covers the top 8 in tier order**, so Caution plants never appear in it; the page shows all of them.
- **No check for places outside India.** The plant list is an India-wide mix and the page accepts any coordinates; whether the soil and climate sources behave elsewhere has not been checked.
- **Radius changes the verdict** (ash dyke: blocked at 400 m, not at 1000 m). The page shows the radius used; the 5000 m input ceiling is arbitrary.

## 9. Security notes

- **Never commit `sylvan_cache.db` or any `*.db` file, or a database URL.** Add `*.db` to `.gitignore`. `SYLVAN_DB_URL` contains the Postgres password; set it as an environment variable only. Error messages from `storage.py` do not print the password.
- OpenAQ key lives only in the `OPENAQ_API_KEY` environment variable.
- Earth Engine credentials are cached locally by `earthengine authenticate`, outside the repo.
- Before every commit: run `git status` and confirm no keys, `.env`, or `venv/` are staged. If a key is ever committed, rotate it immediately.

## 10. Working preferences

- Direct, plain communication.
- Free-only tooling.
- Explain the *why* of each decision; user wants to build it hands-on rather than receive a finished black box.
- Confirm important decisions with the user before locking them in.
- Verify against reality (satellite view) rather than trusting a number; several of this phase's fixes came from the user's screenshots.
- Design decisions one at a time: Claude proposes options with reasons and marks its pick; the user chooses. For a decision the user hands over ("do what is good"), Claude decides, says what it chose and why, and records it here.
- When debugging, the user pastes only the output lines that are needed, not whole logs; ask for specific lines.

## 11. Next steps

000. **What happened 2026-10-07:** the user's earlier Khapri runs on Postgres used the OLD `phase2_terrain_extraction.py` (not yet copied over), so the multi-year code has still never run; the old-format terrain was cached under key `terrain:v2:...` (stale, now ignored since the new key is `v3`; optional cleanup: `DELETE FROM cache WHERE key LIKE 'terrain:v2:%';`). Verify the right file is in use: `Select-String -Path phase2_terrain_extraction.py -Pattern "CACHE_VERSION"` should show `CACHE_VERSION = 3`. Then run Khapri with `--brief`: expect `terrain miss, soil hit, climate hit`, a `best of N years` part in the terrain summary, the 2025 share near the earlier 26%, and the best year being the largest. Do NOT commit the multi-year change until this has been checked.
0000. **Multi-year swing: controls done, gate rule changed to 'recurs in at least 2 years'** (see section 7b). Still to do: find out why 2023 is high at both controls (compare image counts and cloud cover per year) and test on more cropland and barren sites. The terrain summary line lists every year.
00. **Cache:** run the same site twice with `--brief`; the second run should print `Cache (sqlite:sylvan_cache.db): terrain hit, soil hit, climate hit` and finish in seconds. Postgres has been tested only against a PostgreSQL 16 in Claude's sandbox, not on the user's Windows machine.
0. **Run the multi-year check live** on Khapri, the park, the city centre and the new farmland site (`python phase4_matcher.py LAT LON --brief`); the terrain summary line now shows the best of three years. Check the ash dyke at 400 m is still blocked.
0b. **Gate calibration.** The cropland rule (big-swing share 40% or more with dry NDVI under 0.2) fired on Khapri at 1000 m but not at 400 m, and the ash dyke slips through at 1000 m. Thresholds come from a handful of sites; do not retune on one site. Collect 3-4 more cropland sites and 2-3 degraded or barren natural sites (gullies, quarry, rocky scrub), run each at 400 m and 1000 m, then set thresholds. Consider evaluating the gate on both radii (small circle for the water block, larger circle for land-use context).

1. ~~Run the matcher live~~ done for Bilaspur city centre. Next: run it on the park, Khapri farmland and ash dyke coordinates (`python phase4_matcher.py LAT LON`) and check the gate and exclusions.
2. Compare matcher output against local knowledge (what actually grows well around Bilaspur) to see whether the exclusions and warnings make sense. Try the other test sites (park, Khapri, ash dyke) and one rural or degraded site.
3. Fill the 6 blank plant rows and add altitude limits for the remaining species; add pH where a source has numbers.
4. **Phase 5: rerun `--llm`** on Khapri and the park with the updated guard (check for cut-offs and rejections); decide whether to keep the LLM at all or use it only for a short overview paragraph with the per-plant lines left to the template.
4a. **Live results after the matcher fixes (2026-10-06, default 400 m radius):** city centre: built-up warning (44% bare/built); park: no warnings (0% bare/built, 94% big swing, NDVI dry 0.29); Khapri farmland: NO warning (swing only 26%, bare/built 3%, 97% sparse/crops, NDVI dry 0.188) although it is farmland, so the cropland rule missed it; ash dyke 400 m: blocked (60% water/wet); ash dyke 1000 m: not blocked (water/wet 17% is below the 20% warning level, peak NDVI 0.287 so no never-green warning; only a 42% built-up warning and a 23-plant list). LLM tails (gemma4:e4b) on Khapri and the park finished properly, were accepted first try and matched the plain report for the plants visible.
4b. **Matcher fixes made 2026-10-06** (see Decisions): pH margin, texture adjacency, milder poor, water warning, 400 m default radius, terrain summary line. Offline comparison on the four sites' saved environments: salai no longer excluded on pH 7.46-7.58 (now marginal), mango and sissoo no longer penalised for heavy soil (0.81 to 0.88), neem 0.69 to 0.71. Still to do: rerun the five live commands (the gate was not re-tested live at 400 m for city, park and Khapri).
5. **Phase 6: web UI, steps 1-5 of 7 written** (see 7c for what was checked where). To do next:
   - **Check on the user's machine:** `python test_tiers.py`, `python test_jobs.py`, `python test_app.py`; start the server from the project folder; demo run in the page; a cached site live (seconds); the ash dyke (should start with BLOCKED); one new place (stage lines, slow hint, 1-2 minutes); tell Claude if any colour is off.
   - **Step 5, results page: written** (see section 6, `static/app.js`). The user still has to look at it in a real browser; change the layout or wording after that.
   - **Step 6, LLM opt-in button: written** (see section 6). Needs a real test with Ollama running: pick a site, click the button, compare the panel with the template text; then stop Ollama and click again to see the error message.
   - **Step 7:** saved terrain, soil and climate fixtures for the five sites so the page can be built and tested without Earth Engine, tests for the new routes, update this file, commit after tests pass.
   - Later: map click for coordinates; progress callback in `run_live`; decide whether a weed flag (babul, jamun) should ever change a tier.
6. Later/optional: find a true degraded natural-land test site; monsoon cloud masking; WorldCover or JRC water cross-check; cross-check reanalysis rainfall against rain-gauge data.