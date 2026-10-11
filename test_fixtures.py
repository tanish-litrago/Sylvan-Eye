"""
Tests on REAL saved measurements:  python test_fixtures.py

Turns the gate results recorded in HANDOFF section 7b into tests, run through the same job
layer the web page uses. Needs fixtures/ from `python export_fixtures.py`; a site whose
fixture is missing is reported as SKIPPED, never silently passed.
"""

import time

import jobs
from fixtures import SITES, load_fixture

REAL_RUN_LIVE = jobs.run_live


def analyse(slug):
    """Run one fixture through the job layer. Returns the result, or None if no fixture."""
    loaded = load_fixture(slug)
    if loaded is None:
        return None
    site, env, terrain = loaded

    def from_fixture(lat, lon, radius_m, use_cache, refresh):
        return dict(env), terrain

    jobs.run_live = from_fixture
    try:
        jid = jobs.start_job({"lat": site["lat"], "lon": site["lon"], "radius_m": site["radius_m"],
                              "refresh": False, "demo": False})
        for _ in range(500):
            v = jobs.get_job(jid)
            if v["state"] in ("done", "error"):
                break
            time.sleep(0.01)
    finally:
        jobs.run_live = REAL_RUN_LIVE
    assert v["state"] == "done", v
    return v["result"]


def text(result):
    return " ".join(result["facts"]["warnings"])


# What HANDOFF 7b recorded for each site (live runs, imagery 2025).
def check_city_centre(r):
    assert not r["facts"]["blocked"] and "bare or built-up" in text(r)

def check_fadhakhar_park(r):
    assert not r["facts"]["blocked"] and r["facts"]["warnings"] == []

def check_khapri(r):
    assert not r["facts"]["blocked"] and "cropland" in text(r)      # the multi-year rule catches it

def check_ash_dyke_400(r):
    assert r["facts"]["blocked"] and "BLOCKED" in text(r)

def check_ash_dyke_1000(r):
    # KNOWN LIMIT (HANDOFF 7b): at 1000 m the water share drops to 17% and the gate misses it.
    # If this ever starts failing because the site IS blocked now, the gate improved: update it.
    assert not r["facts"]["blocked"]

def check_green_farmland(r):
    assert not r["facts"]["blocked"] and "cropland" in text(r)


EXPECTED = {
    "city-centre": check_city_centre, "fadhakhar-park": check_fadhakhar_park, "khapri": check_khapri,
    "ash-dyke-400": check_ash_dyke_400, "ash-dyke-1000": check_ash_dyke_1000,
    "green-farmland": check_green_farmland,
}


def check_invariants(r):
    """True for every site: the page contract the rules layer must keep."""
    tiered = [p["name"] for t in r["tier_order"] for p in r["tiers"][t]]
    ruled = [o["name"] for o in r["facts"]["ruled_out"]]
    blank = list(r["facts"]["not_assessed_no_data"])
    names = tiered + ruled + blank
    assert len(names) == len(set(names))                 # no plant appears in two places
    if r["facts"]["blocked"]:
        assert tiered == []                              # blocked: no plant is recommended
    assert r["facts"]["limits"] and r["terrain_summary"]


if __name__ == "__main__":
    checked, skipped = 0, []
    for s in SITES:
        r = analyse(s["slug"])
        if r is None:
            print(f"SKIPPED {s['slug']}: no fixture (run python export_fixtures.py)")
            skipped.append(s["slug"])
            continue
        EXPECTED[s["slug"]](r)
        check_invariants(r)
        print(f"ok      {s['slug']}")
        checked += 1
    print(f"\n{checked} site(s) checked, {len(skipped)} skipped")
    if checked == 0:
        print("Nothing was tested: export the fixtures first.")
