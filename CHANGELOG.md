# Changelog

## v2.2.0 - 2026-10-28

A free, safe public demo: the server can show only the saved places, and the page can live on Vercel while the server lives on Render. Nothing changes for local runs and Docker unless you set the new settings.

### Added

- `SYLVAN_MODE=demo`: `POST /analyze` accepts a saved place by its `place` slug and answers it from `data/fixtures` (no Earth Engine, no weather calls, no language model); anything else gets 422 "This server only shows saved places". `GET /config` tells the page the mode and lists the places (`scripts/fixtures.py: list_fixtures`).
- `SYLVAN_CORS_ORIGINS`: lets a page hosted elsewhere call the server. Only the listed addresses get CORS headers; with nothing set there is no CORS at all.
- Page: `static/config.js` holds the backend address (empty means the same server); in demo mode the page shows a "Saved place" list and hides the coordinate boxes, paste box, advanced options and map clicks; if the server is asleep it says "Waking the server" and keeps trying for up to 3 minutes; it now shows the server's own sentence for a rejected request.
- `scripts/vercel_build.sh` and `vercel.json` (the page on Vercel, backend address from `SYLVAN_API_BASE`, refused if missing or unsafe) and `render.yaml` (the backend on Render's free plan in demo mode).
- Dockerfile: the app listens on `$PORT` when a host sets it, 8000 otherwise; the health check follows the same port.
- Tests: `tests/test_demo_mode.py` (demo server, the fixture path, CORS), `tests/test_vercel_build.py` (skipped where there is no `sh`), and one in `tests/test_app.py`.
- README: a "Deploy a free demo" section and two settings rows.

### Fixed

- v2.1.1 refused the offline demo ("Offline demo values" ticked with empty coordinates) as "outside India", because the page then sends 0, 0. The offline demo ignores coordinates, so they are no longer checked for it. The India refusal still applies to every real analysis.

### Findings

- In the sandbox, the demo server used about 54 MB of memory after three analyses, well under Render's 512 MB free limit. This is a measurement on Claude's Linux sandbox, not on Render.

### Not changed

- The gate, the plant matching, the claim guard and the live analysis path. `SYLVAN_LLM` still works; demo mode switches the language model off by itself.

### Tested

- `python -m tests`: unit tests, a real server run in demo mode with CORS headers checked by `curl`, and the page logic exercised in a simulated browser page (jsdom) against mocked server answers (live, demo, older server, sleeping server, address prefix, rejected request). Claude's sandbox only.
- Not tested by Claude: a real browser, the real Vercel build, the real Render deploy, and the free-plan wake-up time. Run `python -m tests` and the demo on your machine.

## v2.1.1 - 2026-10-27

Small hardening after an outside review of the project (a simulated screening panel). No change to the gate, the plant matching or the claim guard.

### Added

- `SYLVAN_EE_PROJECT`: the Earth Engine project is read from the environment (default `sylvan-eye`, the author's project) instead of being edited in two source files. It reaches the Docker container through `docker/docker-compose.yml` and `docker/.env.example`.
- One start-up helper, `init_earth_engine()` in `phases/phase1_data_pipeline.py`, used by all four Earth Engine calls. If Earth Engine cannot start it raises a message that names the project and says to set `SYLVAN_EE_PROJECT` and run `earthengine authenticate`.
- India refusal: `POST /analyze` answers 422 "This point is outside India" for points outside a coarse rectangle (latitude 6.0 to 37.5, longitude 68.0 to 98.0), demo mode included. The rectangle is not a border, so Kathmandu and similar places inside it still run; a test records this limit.
- GitHub Actions workflow `.github/workflows/tests.yml`: runs `python -m tests` on Linux with Python 3.12 on every push to `main` and on pull requests.
- `SYLVAN_LLM=off`: the server lists no language models, so the page hides the "Rewrite with local LLM" control, and `POST /jobs/{id}/explain` answers 409 "switched off". Meant for a host without Ollama; unset, nothing changes.
- Tests: `tests/test_ee_settings.py` (environment variable, start-up error message, with a fake `ee`), and three tests in `tests/test_app.py` for the India refusal.

### Changed

- README: setup uses the environment variable, a settings row, a CI note, an India limit, a short "what it honestly gets wrong" line and a section on what was built by me and what by AI.

### Not done

- Requirements are still lower-bounded, not pinned.
- No rainfall-confidence refusal, no held-out test set judged by someone else, no hosted or demo-only mode.
- The CI workflow has not been run yet; its first run may need a fix.

### Tested

- Claude's sandbox only: unit tests (Python 3.12.3, Linux). Run `python -m tests` on your machine for the real result.

## v2.1.0 - 2026-10-26

A building-outline warning for the gate, rainfall references for more places, a measurement of the claim guard, and seven more test places. The rules still decide and the language model only explains; the claim guard, the block rule and the plant matching are unchanged.

### Added

- Building-outline warning (`GATE_OUTLINE_WARN = 0.185` in `phases/phase4_matcher.py`). At 18.5% outline coverage or more the gate warns that the place may be built-up. It only warns. It is skipped when the land-cover built-up warning already fired, and on a place blocked as water it adds a note instead and the block stays.
- Third Phase 7 round: 7 places between dense towns and open land (3 large villages, 2 peri-urban edges, 2 small towns: Kuderu, Bellare, Kakdwip, Sohana in Mohali, Pirangut, Sandila, Kalimpong). The user checked each point on the satellite view; the expectations were written before the run.
- `scripts/guard_stats.py` and `tests/test_guard_stats.py`: run the local model on every saved place and count what the claim guard did (accepted first try, accepted after the retry, fell back to the fixed text). The test uses a scripted explainer, so it needs no Ollama.
- Rainfall references in `data/rainfall_reference.csv` for Cherrapunji, Ludhiana, Anantapur (also used for Kuderu), Hisar, Malihabad, Dibrugarh, Pampore, Kochi, Darjeeling, Kolkata and Sundarbans (also used for Kakdwip). Each value comes from a page that was opened.

### Changed

- `tests/test_rainfall_check.py`: Cherrapunji (0.44 of the reference, FAR LOW) and Pampore (2.11, FAR OFF) are named known cases next to Leh. `NOT_YET_REFERENCED` now holds Dive Ghat and five round-3 places.
- The outline warning text includes the share, so the fact sheet and the fixed-rules text now carry that number. v2.0.0 kept it out of both; the word "footprint" still does not appear in them.
- Kochi's documented miss is fixed. Kalimpong's mismatch on the old gate (it warned for the cropland rule only) is fixed the same way. Both are `accepted` in `data/phase7_sites.json`.

### Findings (details in HANDOFF section 13)

- Outline share: 6.8% to 16.5% at the three villages, 20.5% to 45.8% at the edges and towns. The gap holds on all 35 places.
- Cropland rule: of the signals in the saved data only slope separates cropland from the two wrongly warned places (cropland 2.0 to 3.2 degrees, Cherrapunji 5.8, Dive Ghat 17.9). The evidence is two places without cropland and no labelled cropland on a slope, so the rule is unchanged.
- Claim guard on `gemma4:e4b`, one run on 35 places: 3 blocked, 29 accepted first try, 1 after the retry, 2 fell back to the fixed text. The five rejected attempts were plants left out (3), cut-off answers (2) and a wrong "no data" claim (1). No change made.
- Cherrapunji and Pampore read far from published normals; Dive Ghat has no usable reference page.

### Tested

- `python -m tests`: 17 of 17 test files, run by the user on 2026-10-26.
- Run by the user: the 7 new places live with Earth Engine, the guard measurement with Ollama, and the Docker stack rebuilt with `--build` (app, db and redis healthy, the map working at `127.0.0.1:8000`).
- Claude's sandbox: unit tests only. It cannot run Docker, Earth Engine, Ollama or a browser.

### Upgrading

- `docker compose up -d --build` from `docker/`. Cached measurements stay valid; the warning is computed from the saved outline share, so nothing is measured again.

## v2.0.0 - 2026-10-24

Better signals, wider testing and a new page. The rules still decide and the language model only explains; the claim guard and the gate are unchanged.

### Added

- Building-outline share (`phases/phase2_footprints.py`): the share of the circle covered by Google Open Buildings V3 outlines (all outlines, confidence 0.65 and up; polygons cut at the circle edge). It is an extra number: the gate, the matching and the explanation do not use it. It has its own cache version and its own cache entry, so cached terrain, soil and climate stay valid. If no outline exists within 5 km of the point the result says "no data" instead of 0%, and a failed lookup is shown without stopping the analysis. The job result has a new `footprints` entry and the job's stage line has a new step, "Fetching building footprints".
- Map on the page (Leaflet 1.9.4, copied into `static/vendor/leaflet/`; OpenStreetMap tiles). A click places the point, the marker can be dragged, and the circle shows the radius. The paste box, the site menu and the typed fields move the marker too. Nothing runs until Analyse is pressed.
- Second Phase 7 round: 12 more places (farmland, an orchard, a tea estate, rain-shadow, very wet and cold-valley places, four dense towns, a mangrove forest), points checked on the satellite view by the user, expectations written before the run. 4 matched and 8 are documented known issues (see the findings below).
- Phase 7 report: a column "Outlines (share, count)" and a line per site. `python -m scripts.run_regions --pause SECONDS` waits after each place that was measured live.
- `RateLimited` (in `phases/phase4_inputs.py`): an Open-Meteo 429 answer is reported with the service's own reason (minute, hour or day limit), and `run_regions` stops instead of sending more requests.
- Tests: `test_footprints.py` and `test_climate_fetch.py` are new (16 test files); `test_app.py` checks the bundled fonts and map files, that no Referrer-Policy is set (OpenStreetMap's tile policy needs the Referer), and that page code never uses `innerHTML`.

### Changed: the page

- Two columns on wide screens (map and inputs stay in view on the left, results on the right), one column on narrow screens. Warnings stay first and always open.
- New look in the same frog colours: lime shrinks to one accent, surfaces are a pale tint of the belly colour, orange is used for warnings only and never for body text, and the "no warnings" banner is neutral. Contrast was checked for every text colour; the lime "Strong fit" bar is the one decoration under 3:1 and the tier name is written out next to it.
- One typeface, Atkinson Hyperlegible, copied into `static/fonts/` (SIL OFL 1.1, licence included), with tabular figures. Nothing loads from a CDN; only the map tiles come from outside.
- Empty tiers take one line each and keep their rule wording. A new block "Also measured, not used for matching" shows the building-outline share with its limit and credit. The "In plain words" text is unchanged and still always shown. Buttons, fields and map controls are at least 44 px high.
- `tests/test_rainfall_check.py` lists the 12 new places as having no rainfall reference yet; each one leaves the list when it gets a sourced row.

### Findings (second Phase 7 round, details in HANDOFF section 12)

- Cropland rule: it warned on natural grassland and scrub (Cherrapunji, Dive Ghat) and missed farmland at Anantapur by 0.004. The dry-season greenness of Cherrapunji's grassland (0.116) lies between two cropland sites (Hisar 0.115, Pampore 0.122), so no cut-off on that number separates them.
- Orchards and tea (Malihabad, Dibrugarh) and tidal mangrove forest (Sundarbans) get no warning; the gate has no rule for them.
- Building outlines: 35.6% to 46.6% at the four dense town cores, 5.6% or less at every other place. Land cover read Kochi's town as 37% built and Darjeeling's as 61% water.

### Tested

- `python -m tests`: 16 of 16 test files.
- Claude's sandbox: the real app in a headless browser at 1440 and 390 px with placeholder map tiles and a saved fixture standing in for Earth Engine (map clicks, marker drag, typing, pasting, site menu, radius, an Analyse run, keyboard order, tap sizes, no sideways scrolling).
- Run by the user: the page with real OpenStreetMap tiles, the footprint entry in Docker, and the 12 new places live with Earth Engine.
- Not seen: the map and the footprint block inside Docker, and the page on a real phone (the app listens on 127.0.0.1 only).

### Upgrading

- `docker compose up -d --build` from `docker/` (the image copies the whole project, so the fonts and Leaflet come with it).
- A place that was cached before gets one extra lookup (seconds) the first time; cached terrain, soil and climate stay valid.
- When measuring many new places, use `--pause 120` with `run_regions` (Open-Meteo's free service caps ten-year requests).

## v1.2.0 - 2026-10-20

Data you can trust. The rules still decide and the language model only explains; the claim guard is unchanged.

### Changed: folder layout

The flat project folder is now organised. Phases moved to `phases/`, tests to `tests/`, requirements to `requirements/`, Docker files to `docker/`, data files (`plants.csv`, `rainfall_reference.csv`, `phase7_sites.json`, `phase7_report.md`, `fixtures/`) to `data/`, helper programs (`validate_plants`, `export_fixtures`, `run_regions`, `check_rainfall`, `fixtures`) to `scripts/`. `app.py`, `jobs.py`, `jobstore.py`, `storage.py`, `tiers.py`, `static/` and `.dockerignore` stay in the project folder.

When upgrading:
- Commands changed, always run from the project folder: `python -m phases.phase4_matcher --demo`, `python -m scripts.validate_plants`, `python -m tests` (all tests) or `python -m tests.test_jobs` (one). `python -m uvicorn app:app --reload` is unchanged.
- `pip install -r requirements/requirements.txt`.
- Docker: run `docker compose` from the `docker/` folder, and move your `.env` to `docker/.env`. The compose project name is fixed to `sylvaneye`, so the volumes (your cache) keep their names.
- The SQLite cache default is now next to `storage.py`, which is the same place as before when started from the project folder, and the plant table is found from the code's location, so the app no longer refuses to start from another folder (imports still need the project folder).

### Added

- Rainfall check against published station or district normals (`data/rainfall_reference.csv`, `python -m scripts.check_rainfall`): Leh is far too high (836 mm against about 90 mm); the other test sites are within about 0.94x to 1.31x, mostly above; Solapur is inconclusive.
- A limit note on the page at 2,000 m and above: the rainfall figure is the least reliable input in high mountains. It is only a note: no rule, score or ranking changes.

### Changed: plant data (`data/plants.csv`, every value with its source in the row's notes)

- Amla: rainfall floor and optimum minimum 630 mm (were 700 and 1500), from Indian sources and zero-irrigation orchards.
- Chir pine: altitude limits 400-2300 m (Botanical Survey of India); it is no longer offered in the plains.
- 14 plants (Arjun, Mahua, Peepal, Tamarind, Gamhar, Bael, Palash, Casuarina, Ber, Siris, Amaltas, Baheda, Deodar, Indian rosewood) got a rainfall floor equal to the lower end of their stated range.
- 13 plants got altitude limits (maxima; Sal also a 100 m minimum): Tamarind, Arjun, Sal, Mango, Sissoo, Jamun, Karanj, Salai, Khair, Mahua, Amaltas, Khejri, Babul. Every plant now has a rainfall minimum and an altitude limit. On the saved sites: Leh no longer offers Amaltas, Arjun, Mahua or Tamarind; Shimla rules out 11 lowland plants; Chir pine is no longer offered at the nine plains sites, and Sal is no longer offered at Puri, Ratnagiri and Varanasi.

### Fixed

- `test_the_last_three_species_come_from_their_ecocrop_sheets` was missing from the run list of `test_plants.py` since v1.0.0, so it never ran. It runs now.

### Tested

- All 14 test files pass (`python -m tests`), and `validate_plants` finds no problems; each new data rule has a test that fails on the old data. The Redis checks of `test_jobstore` run only with `SYLVAN_TEST_REDIS_URL` (inside Docker they passed).
- On Windows with Docker Desktop, run from `docker/`: the three services come up healthy, the cache volume is kept, and the Redis tests pass inside the new image.
- The values for the altitude limits were found with an AI tool and then checked by opening each page. CABI Compendium pages block automated requests, so no CABI value was used.

### Known limits

- A stated range records where a tree grows. It was not tested as a limit, so an irrigated planting outside it may still work.
- Babul's 1340 m comes from a sheet for a different subspecies than the common Indian one; Chir pine is a Himalayan species and the matcher does not check geography, so it is still offered at some central and southern sites between 400 and 2300 m.
- Rainfall: only one high-mountain site (Leh) has a clear answer; Solapur is inconclusive; most references are district averages, not stations.
- 16 plants have no absolute rainfall maximum, 14 no absolute temperature limits, 17 no absolute pH limits.
- The v1.1.0 limits below still apply.

### Next

- v2.0.0: better signals and wider testing (building footprints, more regions, map input).

## v1.1.0 - 2026-10-18

Docker, built in three layers: the app, Postgres as the cache, and Redis for job records. The rules still decide and the language model only explains; it is off by default, and the claim guard is unchanged. Without Docker everything works as in v1.0.0.

### What is new

- App container (`Dockerfile`, `docker-compose.yml`): runs as a non-root user. Your existing Earth Engine login folder is mounted read-only (path in a git-ignored `.env`, see `.env.example`); credentials never go into the image or the repo. Ollama stays on your computer and the container reaches it at `host.docker.internal` (`SYLVAN_OLLAMA_URL`).
- Postgres as the cache: a `db` service with a healthcheck; the app waits for it. The password is set once in `.env` (`POSTGRES_PASSWORD`, letters and digits only) and is never written in the compose file. A new volume starts with an empty cache, so each place takes 1-2 minutes the first time.
- Redis for job records only: `jobstore.py` keeps the job records (state, result, error) in memory (default) or in Redis (`SYLVAN_JOBS=redis`, `SYLVAN_REDIS_URL`); records expire after one hour. The work still runs in threads inside the app; no worker process.
- A job cut off by a server restart is reported as failed ("The server was restarted while this job was running. Run it again.") instead of hanging. A job whose thread died without saving its result is reported failed too.
- Job store down: the server answers 503 and the page says "The job store (Redis) is not available. Try again in a moment." (it retries a few polls first, so a short blip recovers); a job the server no longer knows says so at once. A real network failure still says "Lost contact with the server".
- Safety rules, checked by `test_docker_files.py`: page published on `127.0.0.1` only; Postgres and Redis publish no port; non-root user; `.dockerignore` excludes `.env`, `*.db`, `venv/` and `.git`; no password or key in `docker-compose.yml`.

### Tested

- All test files pass, including the new `test_jobstore.py` (both stores, the failed-job rules, expiry) and `test_docker_files.py`. The job tests also pass against a real Redis.
- Run on Windows with Docker Desktop: the three services come up healthy, a new place runs with Earth Engine from inside the container, the cache survives `docker compose down` and `up`, the Redis tests pass inside the Docker network, and restarting the app during a running analysis made the page report the failed job; running it again worked.
- The language-model button works from inside the container (Ollama on the host).
- The page's job-store messages were checked with a stubbed server in Node and by `test_app.py` (503 routes, wording present); not yet seen in a browser.

### Known limits

- The fact sheet used by the optional model is kept in the app's memory only, so after a restart the button on an old analysis asks you to run the place again.
- Redis has no password and saves nothing to disk; it is reachable only inside the Docker network. If Redis restarts, the job records are lost.
- One app process is assumed.
- The Postgres password is applied only when the volume is first created; changing it later needs `docker compose down -v`, which deletes the cache.
- If Ollama cannot be reached from the container, the fix is `OLLAMA_HOST=0.0.0.0` on your computer, which opens Ollama to your local network.
- Not done: `cap_drop`, a read-only root filesystem, a Redis password.
- The v1.0.0 limits below still apply.

### Next

- v1.2.0: data you can trust (sources for the missing plant limits, rainfall check).
- v2.0.0: better signals and wider testing (building footprints, more regions, map input).

## v1.0.0 - 2026-10-17

First complete version of Sylvan Eye: give it a location and it tells you which trees could be planted there, why, and what the data cannot tell you. **Rules decide; the language model only explains, and it is off by default.**

This is a working, documented prototype. It is **not** validated for real planting decisions. Always confirm with a local soil test and local forestry advice.

### What it does

- **Measures a place** (coordinates and a radius, default 400 m): terrain and vegetation from satellite data (Google Earth Engine, three years of seasonal change), modelled soil (SoilGrids / OpenLandMap) and reanalysis climate. Measurements are cached (SQLite by default, Postgres optional).
- **Eligibility gate:** blocks open water; warns about built-up or bare ground, active cropland (strong seasonal swing in at least two years) and land that never greens up.
- **Plant matcher:** 32 species from FAO ECOCROP and World Agroforestry sheets, each checked on rainfall, temperature, pH, soil texture and altitude. Plants outside a stated absolute limit are ruled out with the reason; the rest are grouped as **Strong fit**, **Likely, not fully verified** or **Caution** (not ranked, because the data cannot separate them).
- **Explanation:** a fixed-rules text always; an optional rewrite by a local model (gemma4:e4b through Ollama) that passes a claim-level guard or falls back to the fixed text.
- **Web page** (FastAPI, plain HTML/JS): paste "lat, lon" from Google Maps or pick a test site; a background job with progress for the 1-2 minute first run; results show the status banner, eligibility warnings, conditions, tiers with per-check chips, the data limits, the ruled-out list with reasons, and the explanation.

### Tested

- Unit tests for the tiers, jobs, routes, gate rule, plant data, runner and storage; saved measurements for 16 sites (fixtures).
- **Phase 7:** ten sites across ten regions of India, with expectations written before the run. It found and fixed: a crash on open water (no soil), the cropland cut-off missing Solapur (0.2 to 0.24), Sal and Mango limits. Other findings are documented limits.

### Known limits

- The built-up warning can miss houses on wooded hill slopes (Shimla). Barren natural land also gets the bare-or-built-up warning.
- Gate thresholds rest on few sites (the cropland cut-off on four cropland sites).
- Rainfall readings at Leh (836 mm) and Solapur (928 mm) look high and were not checked against a station source.
- 14 of 32 plants have no stated absolute rainfall minimum, Amla's 700 mm minimum conflicts with Indian sources, Chir pine has no altitude limit, only 18 of 32 plants have any altitude limit.
- One analysis runs at a time; jobs live in memory; no login, so run it on your own computer only.
- Only gemma4:e4b is supported for the optional rewrite (qwen2.5:7b-instruct was rejected by the guard).

Details, decisions and the full findings list are in `HANDOFF.md`.

### Next

- v1.1.0: Docker (app, Postgres, Redis job store).
- v1.2.0: data you can trust (sources for the missing plant limits, rainfall check).
- v2.0.0: better signals and wider testing (building footprints, more regions, map input).