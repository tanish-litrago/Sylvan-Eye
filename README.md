# Sylvan Eye

Give it a location, and it tells you which trees could be planted there, why, and what the data cannot tell you.

**Rules decide; the language model only explains, and it is off by default.** Every verdict comes from fixed rules over measured data and a sourced plant table. An optional local language model can rewrite the explanation in prose, but its text is checked claim by claim against the facts and discarded if it fails.

> **Status:** v2.1.0 is a working, documented prototype. It is **not** validated for real planting decisions. Always confirm with a local soil test and local forestry advice. See [Known limits](#known-limits).

## What it does

1. Measures the place (latitude, longitude and a radius, default 400 m): terrain and vegetation from Sentinel-2 imagery over three years (Google Earth Engine), elevation from SRTM, soil from SoilGrids 2.0 / OpenLandMap, and climate from the Open-Meteo historical archive. Measurements are cached. It also measures how much of the circle building outlines cover; at 18.5% or more the gate adds a warning (see Known limits).
2. Checks eligibility: blocks open water; warns about built-up or bare ground (from land cover, or from building outlines at 18.5% or more), active cropland, and land that never greens up.
3. Matches 32 plant species (limits from FAO ECOCROP and World Agroforestry sheets, plus a few Indian government and flora sources, each cited in the plant's row) on rainfall, temperature, pH, soil texture and altitude. A plant outside a stated absolute limit is ruled out with the reason. The rest are grouped as **Strong fit**, **Likely, not fully verified** or **Caution**. They are grouped, not ranked, because the data cannot put them in order.
4. Shows the whole picture: warnings first, the conditions, per-check chips for every plant, the ruled-out list with reasons, and the limits of the data.

## Requirements

- Python 3.11 or newer
- A Google account with [Earth Engine](https://earthengine.google.com/) access and a Google Cloud project
- Optional: [Ollama](https://ollama.com/) for the language-model rewrite
- Optional: [Docker Desktop](https://www.docker.com/products/docker-desktop/) to run the whole stack (app, Postgres, Redis)

## Setup

```powershell
git clone https://github.com/tanish-litrago/Sylvan-Eye.git
cd Sylvan-Eye
python -m venv venv
venv\Scripts\Activate.ps1          # macOS/Linux: source venv/bin/activate
pip install -r requirements/requirements.txt
earthengine authenticate
```

The Earth Engine project name `sylvan-eye` is set as `EE_PROJECT` in `phases/phase1_data_pipeline.py` and `phases/phase2_terrain_extraction.py`. Change both to your own Google Cloud project that has Earth Engine enabled.

## Run the web page

From the project folder (the imports need it as the working folder; the plant table `data/plants.csv` and the cache file `sylvan_cache.db` are found from the project's own folders):

```powershell
python -m uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. Click the map, paste "lat, lon" copied from Google Maps, type the coordinates or pick a test site, then click **Analyse**. A place measured for the first time takes 1-2 minutes; a cached place takes seconds. Ticking **Offline demo values** under Advanced needs no Earth Engine.

A click on the map only places the point, and a marker can be dragged; nothing runs until you press Analyse. The circle on the map has the radius from Advanced. Your browser loads the map tiles from OpenStreetMap's server, so they need internet; the form works without them.

The app has no login and shows raw error text. Run it on your own computer only.

## Run with Docker

One command starts the app, Postgres (the cache) and Redis (job records). You still need `earthengine authenticate` once on your own computer: the container uses that login, mounted read-only, and never copies it.

The Docker files live in `docker/`. Run every `docker compose` command from that folder:

```powershell
cd docker
copy .env.example .env
notepad .env                                  # set SYLVAN_EE_DIR and POSTGRES_PASSWORD (see below)
docker compose up -d --build
docker compose ps                             # app, db and redis should say (healthy)
```

Then open <http://127.0.0.1:8000>. In `docker/.env`:

- `SYLVAN_EE_DIR`: your Earth Engine login folder, with forward slashes, e.g. `C:/Users/YOURNAME/.config/earthengine`.
- `POSTGRES_PASSWORD`: choose one, letters and digits only. It is applied when the database is first created.

A new Docker volume starts with an empty cache, so each place takes 1-2 minutes the first time; later runs take seconds. The cache survives `docker compose down`; `docker compose down -v` deletes it.

Ollama stays on your computer (for the GPU). The container reaches it at `host.docker.internal`. If the rewrite button cannot connect, set the Windows variable `OLLAMA_HOST=0.0.0.0` and restart Ollama. That opens Ollama to your local network, so only do it on a network you trust.

If Redis stops, the page says "The job store (Redis) is not available. Try again in a moment." Start it again with `docker compose start redis` and run the place again; the app needs no restart. Redis keeps nothing on disk, so a job that was running when Redis restarted is gone and the page says "The server no longer knows this job ... Run it again." If the app itself restarts during a job, the job is reported as failed.

Safety: the page is published on `127.0.0.1` only (the app has no login and shows raw error text), Postgres and Redis publish no port, the app runs as a non-root user, and `.env` is excluded from git and from the image. `python -m tests.test_docker_files` checks this from the files. The compose project name is fixed (`sylvaneye`), so the volumes keep their names wherever the folder is.

## Command line

```powershell
python -m phases.phase4_matcher --demo             # offline, measured Bilaspur values
python -m phases.phase4_matcher 22.0336 82.2651    # live, any location
python -m phases.phase5_explainer --demo           # with the explanation text
python -m phases.phase5_explainer LAT LON --llm    # explanation rewritten by the local model
```

## Optional: the local language model

Install Ollama, run `ollama pull gemma4:e4b`, and keep it running. The page then shows a **Rewrite with local LLM** button. Only `gemma4:e4b` is supported: `qwen2.5:7b-instruct` was rejected by the claim guard. If the model's answer fails the checks you get the fixed-rules text again, with the reasons. A blocked location never uses the model. On the 32 saved places that reach the model, one run of `python -m scripts.guard_stats` showed the guard accepting 29 answers on the first try and 1 after the retry; 2 fell back to the fixed text.

## Settings (environment variables)

| Variable | Meaning | Default |
|---|---|---|
| `SYLVAN_STORE` | `sqlite` or `postgres` (cache backend) | `sqlite` |
| `SYLVAN_SQLITE_PATH` | SQLite cache file | `sylvan_cache.db` in the project folder |
| `SYLVAN_DB_URL` | Postgres connection string (needs `pip install -r requirements/requirements-postgres.txt`) | none |
| `SYLVAN_JOBS` | `memory` or `redis` (where job records are kept) | `memory` |
| `SYLVAN_REDIS_URL` | Redis address, e.g. `redis://localhost:6379/0` (needs `pip install -r requirements/requirements-redis.txt`) | none |
| `SYLVAN_OLLAMA_URL` | Ollama chat endpoint | `http://localhost:11434/api/chat` (in Docker: `http://host.docker.internal:11434/api/chat`) |

Docker also reads `SYLVAN_EE_DIR` and `POSTGRES_PASSWORD` from `docker/.env` (see [Run with Docker](#run-with-docker)); compose sets the store and Redis variables itself.

## Plant data

`data/plants.csv` holds 32 species. A blank cell means "not found", never a guess. Every row carries the URL of the sheet its numbers came from. After editing, run:

```powershell
python -m scripts.validate_plants
```

## Tests

Plain scripts, no framework. From the project folder:

```powershell
python -m tests                  # every test file, one line each; skipped parts are shown
python -m tests jobs storage     # only some files
python -m tests.test_jobs        # one file, with its full output
```

`test_fixtures` and `test_regions` need `data/fixtures/` (created by `python -m scripts.export_fixtures` for the six original test sites and `python -m scripts.run_regions` for the Phase 7 sites). `run_regions` runs the sites listed in `data/phase7_sites.json` and compares the result with expectations written *before* the run; it refuses a site until those are filled in. Open-Meteo's free service limits how many ten-year requests it answers: when many new places are measured in one go, add `--pause 120` to wait between them (a 429 answer stops the run and names the limit that was hit; places already measured are cached). `test_app` needs `httpx`.

`test_jobstore` always tests the memory store; set `SYLVAN_TEST_REDIS_URL` (a Redis database you do not need: it deletes `sylvan:job:*` keys there) to include Redis, or run it inside Docker, from the `docker/` folder: `docker compose run --rm -e SYLVAN_TEST_REDIS_URL=redis://redis:6379/15 app python -m tests.test_jobstore`.

The rainfall check against published normals (offline) is `python -m scripts.check_rainfall`.

## Project layout

| Path | Role |
|---|---|
| `app.py`, `jobs.py`, `jobstore.py`, `storage.py`, `tiers.py`, `static/` | The web app: routes, background jobs, where their records are kept (memory or Redis), the measurement cache (SQLite or Postgres), Strong / Likely / Caution grouping, the page |
| `phases/` | `phase1_data_pipeline`, `phase2_terrain_extraction`, `phase2_footprints` (building outlines), `phase4_inputs` (soil, terrain, climate), `phase4_matcher` (eligibility gate and plant matcher), `phase5_explainer` (fact sheet, fixed-rules text, optional model rewrite, claim guard) |
| `data/` | `plants.csv`, `rainfall_reference.csv`, `phase7_sites.json`, `phase7_report.md`, `fixtures/` (saved measurements of the test sites) |
| `scripts/` | `validate_plants`, `export_fixtures`, `run_regions`, `check_rainfall`, `guard_stats`, and `fixtures` (the loader for `data/fixtures`); run as `python -m scripts.<name>` |
| `tests/` | all tests; `python -m tests` runs them |
| `requirements/` | `requirements.txt`, `requirements-postgres.txt`, `requirements-redis.txt` |
| `docker/` | `Dockerfile`, `docker-compose.yml`, `.env.example` (copy to `docker/.env`) |
| `.dockerignore` | stays in the project folder: it applies to the Docker build context |
| `HANDOFF.md` | Full state, decisions, findings and next steps |
| `CHANGELOG.md` | Release notes |

## Known limits

- The built-up warning relies on satellite land cover. At Kochi it read 37% as built, just under the 40% line, and at Darjeeling it read the town as 61% water and blocked the place for that reason. Barren natural land also gets the bare-or-built-up warning. Since v2.1.0 the outline warning covers Kochi (43.8% outlines); Darjeeling is still blocked, now with a note that the water reading may be shade or roofs.
- The building-outline share feeds one thing: a warning at 18.5% or more (it never blocks, and it is skipped when the land-cover warning already fired). Plant matching does not use it. The line sits between the largest village (16.5%, Kakdwip) and the lowest peri-urban edge (20.5%, Pirangut) on 35 saved places, so it rests on few places. Houses under trees stay below it (Shimla, 5.6%). The outlines are a May 2023 snapshot, so newer buildings are missing, and some small crowded roofs have no outline, so the share is a floor. If no outline exists within 5 km of the point, the result says there is no footprint data instead of 0%.
- Gate thresholds rest on few sites. The cropland rule warned on natural grassland and scrub at Cherrapunji and Dive Ghat, and missed farmland at Anantapur by 0.004 of dry-season greenness. It does not see orchards or tea (Malihabad, Dibrugarh), and tidal mangrove forest (Sundarbans) gets no warning. The rainfall reading at Leh was checked against published normals and is far too high; the page says so at 2,000 m and above. Solapur is inconclusive. Cherrapunji (0.44 of the published figure) and Pampore (2.1 times) are far off too, because a weather grid cannot hold a one-valley rainfall peak. Dive Ghat and five places added in v2.1.0 have no rainfall reference yet.
- Every plant has a rainfall minimum and an altitude limit. Each is the end of a published range for where the tree grows, not a tested limit, so an irrigated planting outside the range may still work. Babul's altitude comes from a sheet for a different subspecies. Chir pine is a Himalayan species and the matcher does not check its range. 16 plants have no absolute rainfall maximum, 14 no absolute temperature limits and 17 no absolute pH limits.
- One analysis runs at a time. Job records live in memory, or in Redis with `SYLVAN_JOBS=redis` (Docker); either way the work runs in threads inside the app, so a restart cuts off a running job and it is reported as failed. Redis holds job records only (one hour, nothing on disk, no password, not reachable from outside Docker); the optional model's fact sheet stays in the app's memory, so after a restart the rewrite button on an old analysis asks you to run the place again.

The complete list, with the reasons behind each decision, is in [`HANDOFF.md`](HANDOFF.md).

## Data sources

[FAO ECOCROP](https://ecocrop.apps.fao.org/) and the [World Agroforestry Agroforestree Database](https://apps.worldagroforestry.org/treedb2/) (plant requirements, with single values from the Botanical Survey of India, ICAR journals, Useful Tropical Plants and the Flora of Pakistan, each cited in the plant's row); [SoilGrids 2.0](https://soilgrids.org/) and [OpenLandMap](https://openlandmap.org/) (soil); Copernicus Sentinel-2 and USGS SRTM through [Google Earth Engine](https://earthengine.google.com/); [Open-Meteo](https://open-meteo.com/) (climate); [Google Open Buildings V3](https://sites.research.google/open-buildings/) building outlines (inferred from imagery in May 2023, licence CC-BY-4.0); [Leaflet](https://leafletjs.com/) 1.9.4 (BSD 2-Clause, copied into `static/vendor/leaflet/` with its licence); map tiles from [OpenStreetMap](https://www.openstreetmap.org/copyright) (© OpenStreetMap contributors, shown on the map); the Atkinson Hyperlegible typeface (SIL Open Font License 1.1, copied into `static/fonts/` with its licence).

## License

Apache 2.0, see [`LICENSE`](LICENSE).