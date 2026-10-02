"""
Sylvan Eye — Phase 2: Terrain / Vegetation Extraction
Goal: satellite image -> structured terrain data (numbers, not just a picture).

What this script produces for one location:
  - NDVI  (vegetation greenness, from red + near-infrared bands)
  - NDWI  (water signal, from green + near-infrared bands)
  - a coarse land-cover split: water-or-wet-surface / bare-or-built / sparse vegetation / dense vegetation
  - elevation and slope (from SRTM, 30 m)

Run:  python phase2_terrain_extraction.py
Needs the same venv and Earth Engine login as Phase 1.
"""

import ee

EE_PROJECT = "sylvan-eye"

TEST_LAT = 22.0797
TEST_LON = 82.1409
LOCATION_NAME = "Bilaspur, Chhattisgarh"

# ---------------------------------------------------------------------------
# Tunable thresholds. These are coarse STARTING POINTS, not truth. Check them
# against a real satellite view of your location and adjust.
# ---------------------------------------------------------------------------
NDWI_WATER = 0.0      # 90th-percentile NDWI above this -> water_or_wet_surface
                      # (cannot tell small ponds from seasonally damp bare ground)
NDVI_SPARSE = 0.2     # NDVI below this -> bare soil / built-up
NDVI_DENSE = 0.5      # NDVI at or above this -> dense vegetation
SEASONAL_SWING = 0.25  # (p90 - p10) NDVI above this -> pixel changes a lot through the
                       # year, which suggests cropland or deciduous cover. A starting
                       # guess: validate it on known farmland vs known scrub.

CLASS_LABELS = {
    0: "water_or_wet_surface",
    1: "bare_or_built",
    2: "sparse_vegetation_or_crops",
    3: "dense_vegetation",
}


def get_terrain_data(
    lat: float,
    lon: float,
    radius_m: int = 1000,
    start: str = "2025-01-01",
    end: str = "2026-01-01",
):
    """
    Summarize the land around a point (a circle of radius_m metres).

    Uses a MEDIAN composite of all low-cloud Sentinel-2 images in the date range
    instead of one image, so a single hazy or odd-season scene doesn't skew results.
    """
    ee.Initialize(project=EE_PROJECT)

    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(radius_m)

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )
    image_count = collection.size().getInfo()
    if image_count == 0:
        raise RuntimeError("No low-cloud Sentinel-2 images for this place/date range")

    composite = collection.median()

    # Normalized difference = (a - b) / (a + b). It's a ratio, so the 10000x
    # reflectance scaling of Sentinel-2 cancels out.
    ndvi = composite.normalizedDifference(["B8", "B4"]).rename("ndvi")  # NIR, Red
    # Water is seasonal (ponds shrink, get algae, dry out), so a year-long MEDIAN
    # hides it. Instead compute NDWI per image, then take the 90th percentile per
    # pixel: "does this pixel look like water in at least some images?"
    # (a plain max is too noisy: cloud shadows and wet soil spike it.)
    ndwi = (
        collection.map(
            lambda img: img.normalizedDifference(["B3", "B8"]).rename("ndwi")  # Green, NIR
        )
        .reduce(ee.Reducer.percentile([90]))
        .select(0)
        .rename("ndwi")
    )

    # Seasonal NDVI behaviour. Cropland swings between bare and green through the
    # year; degraded scrub or bare ground stays low and flat. So compute NDVI per
    # image, then per pixel take the 10th percentile (driest-looking) and 90th
    # percentile (greenest-looking) and look at the gap between them.
    ndvi_pct = (
        collection.map(
            lambda img: img.normalizedDifference(["B8", "B4"]).rename("ndvi")
        )
        .reduce(ee.Reducer.percentile([10, 90]))  # bands: ndvi_p10, ndvi_p90
    )
    ndvi_low = ndvi_pct.select("ndvi_p10")
    ndvi_high = ndvi_pct.select("ndvi_p90")
    ndvi_range = ndvi_high.subtract(ndvi_low).rename("ndvi_range")
    swing = ndvi_range.gt(SEASONAL_SWING).rename("swing")  # 1 where big seasonal swing

    # Coarse classification, later rules override earlier ones:
    # start as bare (1) -> sparse (2) -> dense (3) -> water_or_wet_surface (0) wins last.
    land_class = (
        ee.Image(1)
        .where(ndvi.gte(NDVI_SPARSE), 2)
        .where(ndvi.gte(NDVI_DENSE), 3)
        .where(ndwi.gt(NDWI_WATER), 0)
        .rename("land_class")
    )

    # --- Sentinel-2 statistics at its native 10 m resolution ---
    s2_stats = (
        ndvi.addBands(ndwi)
        .addBands(ndvi_low.rename("ndvi_p10"))
        .addBands(ndvi_high.rename("ndvi_p90"))
        .addBands(ndvi_range)
        .addBands(swing)
        .reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=10, maxPixels=1e7)
        .getInfo()
    )

    histogram = (
        land_class.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=region,
            scale=10,
            maxPixels=1e7,
        )
        .getInfo()
        .get("land_class", {})
    )
    total = sum(histogram.values()) or 1
    land_cover_fractions = {
        label: round(histogram.get(str(code), 0) / total, 3)
        for code, label in CLASS_LABELS.items()
    }

    # --- Elevation and slope from SRTM (30 m) ---
    srtm = ee.Image("USGS/SRTMGL1_003")
    terrain = srtm.rename("elevation").addBands(ee.Terrain.slope(srtm).rename("slope"))
    terrain_stats = terrain.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=30, maxPixels=1e7
    ).getInfo()

    return {
        "location": {"lat": lat, "lon": lon, "radius_m": radius_m},
        "imagery": {
            "source": "Sentinel-2 SR median composite (Earth Engine)",
            "date_range": [start, end],
            "images_used": image_count,
        },
        "vegetation": {
            "ndvi_mean": round(s2_stats["ndvi"], 3),
            "ndwi_p90_mean": round(s2_stats["ndwi"], 3),
        },
        "seasonality": {
            "ndvi_dry_p10_mean": round(s2_stats["ndvi_p10"], 3),
            "ndvi_peak_p90_mean": round(s2_stats["ndvi_p90"], 3),
            "ndvi_range_mean": round(s2_stats["ndvi_range"], 3),
            "big_swing_fraction": round(s2_stats["swing"], 3),
        },
        "land_cover_fractions": land_cover_fractions,
        "terrain": {
            "elevation_m": round(terrain_stats["elevation"], 1),
            "slope_deg": round(terrain_stats["slope"], 2),
        },
    }


def main():
    print(f"Terrain extraction for: {LOCATION_NAME} ({TEST_LAT}, {TEST_LON})\n")
    result = get_terrain_data(TEST_LAT, TEST_LON)

    print(f"Images used: {result['imagery']['images_used']}")
    print(f"NDVI mean:   {result['vegetation']['ndvi_mean']}")
    print(f"NDWI (p90):  {result['vegetation']['ndwi_p90_mean']}")
    seasonal = result["seasonality"]
    print(f"NDVI dry (p10):   {seasonal['ndvi_dry_p10_mean']}")
    print(f"NDVI peak (p90):  {seasonal['ndvi_peak_p90_mean']}")
    print(f"NDVI range:       {seasonal['ndvi_range_mean']}")
    print(f"Big-swing area:   {seasonal['big_swing_fraction'] * 100:.1f}%")
    print(f"Elevation:   {result['terrain']['elevation_m']} m")
    print(f"Slope:       {result['terrain']['slope_deg']} degrees")
    print("Land cover:")
    for label, fraction in result["land_cover_fractions"].items():
        print(f"  {label:<28} {fraction * 100:5.1f}%")


if __name__ == "__main__":
    main()