# Sylvan Eye

Give it a location, and it tells you which trees could be planted there, why, and what the data cannot tell you.

**Rules decide; the language model only explains, and it is off by default.** Every verdict comes from fixed rules over measured data and a sourced plant table. An optional local language model can rewrite the explanation in prose, but its text is checked claim by claim against the facts and discarded if it fails.

> **Status:** v1.0.0 is a working, documented prototype. It is **not** validated for real planting decisions. Always confirm with a local soil test and local forestry advice. See [Known limits](#known-limits).

## What it does

1. **Measures the place** (latitude, longitude and a radius, default 400 m): terrain and vegetation from Sentinel-2 imagery over three years (Google Earth Engine), elevation from SRTM, soil from SoilGrids 2.0 / OpenLandMap, and climate from the Open-Meteo historical archive. Measurements are cached.
2. **Checks eligibility:** blocks open water; warns about built-up or bare ground, active cropland, and land that never greens up.
3. **Matches 32 plant species** (limits from FAO ECOCROP and World Agroforestry sheets) on rainfall, temperature, pH, soil texture and altitude. A plant outside a stated absolute limit is ruled out with the reason. The rest are grouped as **Strong fit**, **Likely, not fully verified** or **Caution**. They are grouped, not ranked, because the data cannot put them in order.
4. **Shows everything that matters,** not just a list: warnings first, the conditions, per-check chips for every plant, the ruled-out list with reasons, and the limits of the data.

## Requirements

- Python 3.11 or newer
- A Google account with [Earth Engine](https://earthengine.google.com/) access and a Google Cloud project
- Optional: [Ollama](https://ollama.com/) for the language-model rewrite

## Setup

```powershell
git clone https://github.com/tanish-litrago/Sylvan-Eye.git
cd Sylvan-Eye
python -m venv venv
venv\Scripts\Activate.ps1          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
earthengine authenticate
```

The Earth Engine project name `sylvan-eye` is set as `EE_PROJECT` in `phase1_data_pipeline.py` and `phase2_terrain_extraction.py`. Change both to your own Google Cloud project that has Earth Engine enabled.

## Run the web page

From the project folder (the app refuses to start anywhere else, because it finds `plants.csv` and the cache by relative path):

```powershell
python -m uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. Paste "lat, lon" copied from Google Maps, or pick a test site, then click **Analyse**. A place measured for the first time takes 1-2 minutes; a cached place takes seconds. Ticking **Offline demo values** under Advanced needs no Earth Engine.

The app has no login and shows raw error text. Run it on your own computer only.

## Command line

```powershell
python phase4_matcher.py --demo                    # offline, measured Bilaspur values
python phase4_matcher.py 22.0336 82.2651           # live, any location
python phase5_explainer.py --demo                  # with the explanation text
python phase5_explainer.py LAT LON --llm           # explanation rewritten by the local model
```

## Optional: the local language model

Install Ollama, run `ollama pull gemma4:e4b`, and keep it running. The page then shows a **Rewrite with local LLM** button. Only `gemma4:e4b` is supported: `qwen2.5:7b-instruct` was rejected by the claim guard. If the model's answer fails the checks you get the fixed-rules text again, with the reasons. A blocked location never uses the model.

## Settings (environment variables)

| Variable | Meaning | Default |
|---|---|---|
| `SYLVAN_STORE` | `sqlite` or `postgres` (cache backend) | `sqlite` |
| `SYLVAN_SQLITE_PATH` | SQLite cache file | `sylvan_cache.db` |
| `SYLVAN_DB_URL` | Postgres connection string (needs `pip install -r requirements-postgres.txt`) | none |
| `SYLVAN_OLLAMA_URL` | Ollama chat endpoint | `http://localhost:11434/api/chat` |

## Plant data

`plants.csv` holds 32 species. **A blank cell means "not found", never a guess,** and every row carries the URL of the sheet its numbers came from. After editing, run:

```powershell
python validate_plants.py
```

## Tests

Plain scripts, no framework. Each prints a closing line when it passes.

```powershell
python test_tiers.py       python test_jobs.py        python test_app.py
python test_gate.py        python test_plants.py      python test_run_live.py
python test_run_regions.py python test_storage.py
python test_fixtures.py    python test_regions.py     # need fixtures/ (see below)
```

`test_app.py` needs `httpx`, and `fixtures/` is created by `python export_fixtures.py` (the six original test sites) and `python run_regions.py` (the Phase 7 sites). `run_regions.py` runs sites listed in `phase7_sites.json` and compares the result with expectations written *before* the run; it refuses a site until those are filled in.

## Project layout

| Path | Role |
|---|---|
| `phase1_data_pipeline.py`, `phase2_terrain_extraction.py`, `phase4_inputs.py` | Data: soil, terrain, climate |
| `phase4_matcher.py` | Eligibility gate and plant matcher |
| `tiers.py` | Strong / Likely / Caution grouping |
| `phase5_explainer.py` | Fact sheet, fixed-rules text, optional model rewrite, claim guard |
| `storage.py` | Measurement cache (SQLite or Postgres) |
| `jobs.py`, `app.py`, `static/` | Background jobs, web routes, the page |
| `plants.csv`, `validate_plants.py` | Plant requirements and their checker |
| `fixtures.py`, `export_fixtures.py`, `run_regions.py`, `phase7_sites.json` | Saved measurements and regional testing |
| `HANDOFF.md` | Full state, decisions, findings and next steps |
| `CHANGELOG.md` | Release notes |

## Known limits

- The built-up warning can miss houses on wooded hill slopes; barren natural land also gets the bare-or-built-up warning.
- Gate thresholds rest on few sites. Rainfall readings at Leh and Solapur look high and are unverified.
- 14 of 32 plants have no stated absolute rainfall minimum, and only 18 have any altitude limit.
- One analysis runs at a time and jobs live in memory.

The complete list, with the reasons behind each decision, is in [`HANDOFF.md`](HANDOFF.md).

## Data sources

[FAO ECOCROP](https://ecocrop.apps.fao.org/) and the [World Agroforestry Agroforestree Database](https://apps.worldagroforestry.org/treedb2/) (plant requirements); [SoilGrids 2.0](https://soilgrids.org/) and [OpenLandMap](https://openlandmap.org/) (soil); Copernicus Sentinel-2 and USGS SRTM through [Google Earth Engine](https://earthengine.google.com/); [Open-Meteo](https://open-meteo.com/) (climate).

## License

Apache 2.0, see [`LICENSE`](LICENSE).
