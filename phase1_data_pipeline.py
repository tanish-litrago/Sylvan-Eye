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

    ee.Initialize()  # uses credentials cached by `earthengine authenticate`

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
# 2a. Environmental Data Layer — Soil (SoilGrids)
# ---------------------------------------------------------------------------
def get_soilgrids_data(lat: float, lon: float):
    """
    SoilGrids REST API — no API key required.
    Docs: https://www.isric.org/explore/soilgrids/faq-soilgrids
    """
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["phh2o", "soc", "sand", "clay"],
        "depth": "0-5cm",
        "value": "mean",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    layers = data.get("properties", {}).get("layers", [])
    parsed = {}
    for layer in layers:
        name = layer["name"]
        depths = layer.get("depths", [])
        if depths:
            parsed[name] = depths[0]["values"].get("mean")

    return {"source": "SoilGrids", "properties_0_5cm": parsed}


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
        ("SoilGrids", lambda: get_soilgrids_data(TEST_LAT, TEST_LON)),
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