"""
Tests for run_live with the three data sources replaced by fakes:  python -m tests.test_run_live
Covers the Phase 7 lake finding: open water has no soil, so a blocked site must give the
blocked answer instead of crashing.
"""

from phases import phase1_data_pipeline
from phases import phase2_terrain_extraction
from phases import phase4_inputs
import jobs
from phases.phase4_matcher import run_live

SOIL = {"surface_soil": {"ph": {"value": 6.5}, "clay": {"value": 20}, "sand": {"value": 40}}}
CLIMATE = {"annual_rainfall_mm": 1200, "annual_mean_temp_c": 25.0}


def terrain(water):
    return {"land_cover_fractions": {"water_or_wet_surface": water, "bare_or_built": 0.0,
            "sparse_vegetation_or_crops": 0.3, "dense_vegetation": 0.6},
            "seasonality": {"ndvi_dry_p10_mean": 0.3, "ndvi_peak_p90_mean": 0.7, "big_swing_fraction": 0.1, "big_swing_by_year": {}},
            "vegetation": {}, "location": {"radius_m": 400}, "terrain": {"elevation_m": 500.0}}


def with_sources(water, soil_works):
    def get_soil(lat, lon):
        if not soil_works:
            raise RuntimeError("No soil source returned values. SoilGrids: all values empty")
        return SOIL
    phase2_terrain_extraction.get_terrain_data = lambda lat, lon, radius_m=400: terrain(water)
    phase1_data_pipeline.get_soil_data = get_soil
    phase4_inputs.get_climate_normals = lambda lat, lon: CLIMATE


def test_blocked_water_site_without_soil_returns_the_environment_instead_of_crashing():
    with_sources(water=0.6, soil_works=False)
    env, ter = run_live(23.2, 77.3, 400, use_cache=False)
    assert env["ph"] is None and env["soil_texture"] is None
    assert env["annual_rainfall_mm"] == 1200 and env["elevation_m"] == 500.0
    assert ter["land_cover_fractions"]["water_or_wet_surface"] == 0.6


def test_land_that_is_not_blocked_still_fails_loudly_without_soil():
    with_sources(water=0.0, soil_works=False)
    try:
        run_live(23.2, 77.3, 400, use_cache=False)
        assert False, "should have raised"
    except RuntimeError as e:
        assert "No soil source" in str(e)


def test_normal_site_is_unchanged():
    with_sources(water=0.0, soil_works=True)
    env, _ = run_live(23.2, 77.3, 400, use_cache=False)
    assert env["ph"] == 6.5 and env["soil_texture"] is not None


def test_the_page_pipeline_shows_blocked_for_a_lake_without_soil():
    with_sources(water=0.6, soil_works=False)
    result = jobs.analyze({"lat": 23.2, "lon": 77.3, "radius_m": 400, "refresh": False, "demo": False})
    assert result["facts"]["blocked"] is True
    assert any("BLOCKED" in w for w in result["facts"]["warnings"])
    assert all(result["tiers"][t] == [] for t in result["tier_order"])
    assert result["facts"]["environment"]["ph"] is None
    assert result["explanation"]["text"]                      # the plain-words text still builds


if __name__ == "__main__":
    test_blocked_water_site_without_soil_returns_the_environment_instead_of_crashing()
    test_land_that_is_not_blocked_still_fails_loudly_without_soil()
    test_normal_site_is_unchanged()
    test_the_page_pipeline_shows_blocked_for_a_lake_without_soil()
    print("all run_live tests passed")
