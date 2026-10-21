"""
Tests for the building-footprint signal (v2.0.0):  python -m tests.test_footprints

The Earth Engine call itself cannot run here, so the maths and the rules are tested on its raw
numbers, run_live is tested with a faked fetch, and the real shares are checked against the saved
fixtures (SKIPPED for a fixture that has no footprints yet: re-run the exporters).
"""

import json
import os
import tempfile

# Never touch the real cache file: this process uses its own.
os.environ["SYLVAN_STORE"] = "sqlite"
os.environ["SYLVAN_SQLITE_PATH"] = os.path.join(tempfile.mkdtemp(), "test_footprints.db")

import jobs
from phases import phase2_footprints
from phases.phase4_matcher import CACHE_LOG, run_live
from scripts.fixtures import FIXTURE_DIR, load_fixture
from tests.test_run_live import with_sources

SAMPLE = {"share": 0.2, "polygons": 120, "coverage": "ok"}


def raw(footprint_m2=100000.0, polygons=120, nearby=120):
    return {"circle_m2": 500000.0, "footprint_m2": footprint_m2, "polygons": polygons, "nearby": nearby}


def test_share_is_footprint_area_over_circle_area():
    r = phase2_footprints.summarize(raw())
    assert r["share"] == 0.2 and r["polygons"] == 120 and r["coverage"] == "ok"
    assert r["min_confidence"] == 0.65 and r["license"] == "CC-BY-4.0" and "May 2023" in r["source"]


def test_covered_place_with_no_buildings_is_zero_not_missing():
    r = phase2_footprints.summarize(raw(footprint_m2=0.0, polygons=0, nearby=40))
    assert r["share"] == 0.0 and r["coverage"] == "ok"


def test_no_polygon_within_5_km_means_no_data_not_zero():
    r = phase2_footprints.summarize(raw(footprint_m2=0.0, polygons=0, nearby=0))
    assert r["share"] is None and r["coverage"] == "no_data"
    assert r["coverage_check_m"] == 5000


def test_run_live_adds_footprints_to_terrain_and_keeps_the_return_shape():
    with_sources(water=0.0, soil_works=True)
    phase2_footprints.get_footprints = lambda lat, lon, radius_m=400: SAMPLE
    out = run_live(23.2, 77.3, 400, use_cache=False)
    assert len(out) == 2
    env, terrain = out
    assert terrain["footprints"] == SAMPLE
    assert env["ph"] == 6.5 and terrain["terrain"]["elevation_m"] == 500.0
    assert dict(CACHE_LOG)["footprints"] == "no-cache"


def test_a_failing_fetch_does_not_stop_the_analysis_and_is_not_cached():
    with_sources(water=0.0, soil_works=True)
    calls = []

    def flaky(lat, lon, radius_m=400):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("earth engine says no")
        return SAMPLE

    phase2_footprints.get_footprints = flaky
    env, terrain = run_live(11.1111, 77.7777, 400)                  # uses the temp cache
    fp = terrain["footprints"]
    assert fp["share"] is None and fp["coverage"] == "error" and "earth engine says no" in fp["error"]
    assert env["ph"] == 6.5                                           # the rest still ran
    assert dict(CACHE_LOG)["footprints"] == "error"
    _, terrain = run_live(11.1111, 77.7777, 400)                    # the error was not stored
    assert dict(CACHE_LOG)["footprints"] == "miss" and terrain["footprints"] == SAMPLE
    run_live(11.1111, 77.7777, 400)
    assert dict(CACHE_LOG)["footprints"] == "hit" and len(calls) == 2


def test_page_result_carries_footprints_but_the_fact_sheet_and_text_do_not():
    with_sources(water=0.0, soil_works=True)
    phase2_footprints.get_footprints = lambda lat, lon, radius_m=400: SAMPLE
    r = jobs.analyze({"lat": 12.3456, "lon": 78.9012, "radius_m": 400, "refresh": True, "demo": False})
    assert r["footprints"] == SAMPLE
    assert "footprint" not in json.dumps(r["facts"]).lower()          # claim guard input is unchanged
    assert "footprint" not in r["explanation"]["text"].lower()


def test_real_saved_shares():
    """Real numbers from the v2.0.0 probe, checked on the fixtures that already have footprints."""
    expected = {"city-centre": (0.33, 0.38), "shimla": (0.045, 0.065)}
    slugs = sorted(p.stem for p in FIXTURE_DIR.glob("*.json"))
    assert slugs, "no fixtures found: this test would check nothing"
    for slug in slugs:
        fp = load_fixture(slug)[2].get("footprints")
        if fp is None:
            print(f"SKIPPED {slug}: fixture has no footprints (re-run the exporters)")
            continue
        assert (fp["share"] is None) == (fp["coverage"] != "ok"), slug
        assert fp["share"] is None or 0.0 <= fp["share"] <= 1.0, slug
        if slug in expected and fp["share"] is not None:
            lo, hi = expected[slug]
            assert lo <= fp["share"] <= hi, (slug, fp["share"])
        print(f"ok      {slug}: share {fp['share']}, coverage {fp['coverage']}")


if __name__ == "__main__":
    test_share_is_footprint_area_over_circle_area()
    test_covered_place_with_no_buildings_is_zero_not_missing()
    test_no_polygon_within_5_km_means_no_data_not_zero()
    test_run_live_adds_footprints_to_terrain_and_keeps_the_return_shape()
    test_a_failing_fetch_does_not_stop_the_analysis_and_is_not_cached()
    test_page_result_carries_footprints_but_the_fact_sheet_and_text_do_not()
    test_real_saved_shares()
    print("all footprint tests passed")
