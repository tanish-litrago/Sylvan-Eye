"""
Sylvan Eye — Phase 6, step 7: saved measurements for the test sites.

Each fixture file holds exactly what run_live() returned for a site: the matcher's
environment and the terrain measurement. With them the web layer can be tested on real data
without Earth Engine, and the gate results written down in HANDOFF section 7b become tests.

    python -m scripts.export_fixtures     run once on a machine with the cache (seconds per cached
                                  site; 1-2 minutes per site that is not cached yet)

Files go in data/fixtures/<slug>.json. They are measurements, not verdicts: the rules are always
run again on them.
"""

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"

# slug, name, latitude, longitude, radius in metres. Same places as SITES in static/app.js,
# plus the ash dyke at 1000 m (the case the gate is known to miss).
SITES = [
    {"slug": "city-centre", "name": "Bilaspur city centre", "lat": 22.0797, "lon": 82.1409, "radius_m": 400},
    {"slug": "fadhakhar-park", "name": "Fadhakhar Park", "lat": 22.042991, "lon": 82.173492, "radius_m": 400},
    {"slug": "khapri", "name": "Khapri (farmland)", "lat": 22.033592, "lon": 82.265111, "radius_m": 400},
    {"slug": "ash-dyke-400", "name": "Ash dyke", "lat": 22.07937, "lon": 82.281826, "radius_m": 400},
    {"slug": "ash-dyke-1000", "name": "Ash dyke, wider radius", "lat": 22.07937, "lon": 82.281826, "radius_m": 1000},
    {"slug": "green-farmland", "name": "Green farmland (checked on map)", "lat": 22.002166, "lon": 82.195423, "radius_m": 400},
]


def fixture_path(slug, folder=None):
    return Path(folder or FIXTURE_DIR) / f"{slug}.json"


def save_fixture(site, env, terrain, exported_on, folder=None):
    """Write one site's measurements. Returns the path."""
    path = fixture_path(site["slug"], folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"site": site, "exported_on": exported_on, "env": env, "terrain": terrain}
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_fixture(slug, folder=None):
    """Returns (site, env, terrain), or None when that fixture has not been exported."""
    path = fixture_path(slug, folder)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["site"], data["env"], data["terrain"]
