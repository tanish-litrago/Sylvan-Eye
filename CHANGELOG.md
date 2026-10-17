# Changelog

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
