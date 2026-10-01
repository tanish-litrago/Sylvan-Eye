"""
Sylvan Eye — Phase 1: Data Pipeline
Goal: for ONE hardcoded location, confirm you can fetch all four data types
successfully. No imagery analysis, no matching logic yet — just prove the
data flows in.

Install dependencies:
    pip install requests earthengine-api

Before running:
    1. Sign up for Earth Engine access: https://signup.earthengine.google.com/
    2. Authenticate once from your terminal:  earthengine authenticate
       (this opens a browser, logs you in, and caches credentials locally)
"""

import requests

# ---------------------------------------------------------------------------
# Hardcoded test location — change this to whatever region you want to test
# ---------------------------------------------------------------------------
TEST_LAT = 22.0797
TEST_LON = 82.1409
LOCATION_NAME = "Bilaspur, Chhattisgarh"

# Your Google Cloud project registered for Earth Engine
EE_PROJECT = "sylvan-eye"


# ---------------------------------------------------------------------------
# 1. Satellite Image Layer — Google Earth Engine (Sentinel-2)
# ---------------------------------------------------------------------------
def get_sentinel2_data(lat: float, lon: float):
    """
    Pulls a recent, cloud-filtered Sentinel-2 image for a point and returns
    basic band statistics (proof that imagery access works). Real terrain
    extraction happens in Phase 2 — this just confirms the connection.
    """
    import ee

    ee.Initialize(project=EE_PROJECT)  # credentials cached by `earthengine authenticate`

    point = ee.Geometry.Point([lon, lat])

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(point)
        .filterDate("2025-01-01", "2026-01-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )

    image = collection.first()
    if image is None:
        raise RuntimeError("No Sentinel-2 image found for this location/date range")

    # Sample a small region around the point for a few key bands
    bands = image.select(["B4", "B3", "B2", "B8"])  # Red, Green, Blue, NIR
    sample = bands.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point.buffer(100),  # 100m buffer
        scale=10,
    ).getInfo()

    return {
        "source": "Sentinel-2 (Earth Engine)",
        "image_id": image.get("system:index").getInfo(),
        "band_means": sample,
    }


# ---------------------------------------------------------------------------
# 2a. Environmental Data Layer — Soil (via Earth Engine)
# ---------------------------------------------------------------------------
# The SoilGrids REST API is paused by ISRIC. We read soil data through Earth
# Engine instead, trying two sources in order:
#   1. SoilGrids 2.0 community assets (projects/soilgrids-isric/...)
#   2. OpenLandMap (official Earth Engine catalog) as a fallback
# Each entry: property -> (asset id, band, multiplier to real units, unit)
SOIL_SOURCES = [
    (
        "SoilGrids 2.0 (Earth Engine)",
        {
            "ph": ("projects/soilgrids-isric/phh2o_mean", 0, 0.1, "pH"),
            "organic_carbon": ("projects/soilgrids-isric/soc_mean", 0, 0.1, "g/kg"),
            "clay": ("projects/soilgrids-isric/clay_mean", 0, 0.1, "%"),
            "sand": ("projects/soilgrids-isric/sand_mean", 0, 0.1, "%"),
        },
    ),
    (
        "OpenLandMap (Earth Engine)",
        {
            "ph": ("OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02", "b0", 0.1, "pH"),
            "organic_carbon": (
                "OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02", "b0", 5, "g/kg",
            ),
            "clay": ("OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02", "b0", 1, "%"),
            "sand": ("OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02", "b0", 1, "%"),
        },
    ),
]


def _sample_soil_source(properties: dict, point):
    import ee

    parsed = {}
    for name, (asset, band, multiplier, unit) in properties.items():
        image = ee.Image(asset).select(band)
        raw = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point.buffer(500),
            scale=250,
            maxPixels=1e6,
        ).getInfo()
        value = next(iter(raw.values()), None)
        parsed[name] = {
            "value": round(value * multiplier, 2) if value is not None else None,
            "unit": unit,
        }
    return parsed


def get_soil_data(lat: float, lon: float):
    """Surface-layer (0 cm) soil properties: pH, organic carbon, clay, sand."""
    import ee

    ee.Initialize(project=EE_PROJECT)
    point = ee.Geometry.Point([lon, lat])

    tried = []
    for source_name, properties in SOIL_SOURCES:
        try:
            parsed = _sample_soil_source(properties, point)
        except Exception as e:
            tried.append(f"{source_name}: error {e}")
            continue
        if any(v["value"] is not None for v in parsed.values()):
            return {"source": source_name, "surface_soil": parsed}
        tried.append(f"{source_name}: all values empty")

    # Fail loudly instead of reporting success on empty data
    raise RuntimeError("No soil source returned values. " + " | ".join(tried))


# ---------------------------------------------------------------------------
# 2b. Environmental Data Layer — Climate (Open-Meteo)
# ---------------------------------------------------------------------------
def get_openmeteo_data(lat: float, lon: float):
    """
    Open-Meteo — completely free, no API key required.
    Docs: https://open-meteo.com/en/docs
    Pulling current conditions here; historical/forecast endpoints exist too.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation",
        "daily": "precipitation_sum",
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {
        "source": "Open-Meteo",
        "current": data.get("current"),
        "daily_precipitation_sum": data.get("daily", {}).get("precipitation_sum"),
    }


# ---------------------------------------------------------------------------
# 2c. Environmental Data Layer — Air Quality (OpenAQ)
# ---------------------------------------------------------------------------
def get_openaq_data(lat: float, lon: float, radius_m: int = 25000):
    """
    OpenAQ v3 — free, but requires a (free) API key from openaq.org.
    Sign up: https://explore.openaq.org/register
    Set your key as an environment variable: OPENAQ_API_KEY
    """
    import os

    api_key = os.environ.get("OPENAQ_API_KEY", "")
    url = "https://api.openaq.org/v3/locations"
    params = {"coordinates": f"{lat},{lon}", "radius": radius_m, "limit": 5}
    headers = {"X-API-Key": api_key} if api_key else {}

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {"source": "OpenAQ", "nearby_stations": data.get("results", [])}


# ---------------------------------------------------------------------------
# Run all four and report what worked
# ---------------------------------------------------------------------------
def main():
    print(f"Testing data pipeline for: {LOCATION_NAME} ({TEST_LAT}, {TEST_LON})\n")

    fetchers = [
        ("Sentinel-2 (Earth Engine)", lambda: get_sentinel2_data(TEST_LAT, TEST_LON)),
        ("Soil (Earth Engine)", lambda: get_soil_data(TEST_LAT, TEST_LON)),
        ("Open-Meteo", lambda: get_openmeteo_data(TEST_LAT, TEST_LON)),
        ("OpenAQ", lambda: get_openaq_data(TEST_LAT, TEST_LON)),
    ]

    results = {}
    for name, fetch in fetchers:
        print(f"--- {name} ---")
        try:
            result = fetch()
            results[name] = result
            print("OK")
            print(result)
        except Exception as e:
            print(f"FAILED: {e}")
        print()

    ok_count = len(results)
    print(f"Summary: {ok_count}/4 sources returned data successfully.")


if __name__ == "__main__":
    main()