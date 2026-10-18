# Changelog

## v1.1.0 - 2026-10-18

Docker, built in three layers: the app, Postgres as the cache, and Redis for job records. **Rules decide; the language model only explains, and it is off by default** (unchanged; the claim guard was not touched). Without Docker everything works as in v1.0.0.

### What is new

- **App container** (`Dockerfile`, `docker-compose.yml`): runs as a non-root user. Your existing Earth Engine login folder is mounted **read-only** (path in a git-ignored `.env`, see `.env.example`); credentials never go into the image or the repo. Ollama stays on your computer and the container reaches it at `host.docker.internal` (`SYLVAN_OLLAMA_URL`).
- **Postgres as the cache:** a `db` service with a healthcheck; the app waits for it. The password is set once in `.env` (`POSTGRES_PASSWORD`, letters and digits only) and is never written in the compose file. A new volume starts with an empty cache, so each place takes 1-2 minutes the first time.
- **Redis for job records only:** `jobstore.py` keeps the job records (state, result, error) in memory (default) or in Redis (`SYLVAN_JOBS=redis`, `SYLVAN_REDIS_URL`); records expire after one hour. The work still runs in threads inside the app; no worker process.
- **A job cut off by a server restart is reported as failed** ("The server was restarted while this job was running. Run it again.") instead of hanging. A job whose thread died without saving its result is reported failed too.
- **Job store down:** the server answers 503 and the page says "The job store (Redis) is not available. Try again in a moment." (it retries a few polls first, so a short blip recovers); a job the server no longer knows says so at once. A real network failure still says "Lost contact with the server".
- **Safety rules, checked by `test_docker_files.py`:** page published on `127.0.0.1` only; Postgres and Redis publish no port; non-root user; `.dockerignore` excludes `.env`, `*.db`, `venv/` and `.git`; no password or key in `docker-compose.yml`.

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