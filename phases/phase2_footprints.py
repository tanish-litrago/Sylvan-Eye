"""
Sylvan Eye - v2.0.0: building footprints around a point.

What share of the circle do building outlines cover? Sentinel-2 cannot tell barren land from
roofs; building outlines can (Jaisalmer and Leh read 100% bare-or-built from imagery but have
almost no buildings). It is an EXTRA number: the gate, the matcher and the fact sheet do not
use it.

Source: Google Open Buildings V3 polygons in Earth Engine, inferred from imagery in May 2023
(a snapshot, so newer buildings are missing). Licence CC-BY-4.0: credit it where it is shown.

Run:  python -m phases.phase2_footprints LAT LON [RADIUS_M]
"""

import sys

import ee

from phases.phase2_terrain_extraction import EE_PROJECT

# Cache version of get_footprints()'s output. Bump it whenever the returned data changes.
CACHE_VERSION = 1

BUILDINGS = "GOOGLE/Research/open-buildings/v3/polygons"
SOURCE = "Google Open Buildings V3 polygons (Earth Engine), inferred May 2023"
LICENSE = "CC-BY-4.0"

MIN_CONFIDENCE = 0.65       # the dataset's own floor, so every polygon counts (v2.0.0 decision 3;
                            # revisit if a footprint number ever feeds a gate rule)
COVERAGE_RADIUS_M = 5000    # no polygon within this distance = no data here, not "no buildings"
                            # (v2.0.0 decision 6; the 5 km is a judgement, not a sourced figure)


def summarize(raw):
    """Turn the four raw numbers from Earth Engine into the result dict. No Earth Engine here."""
    covered = raw["nearby"] > 0
    share = raw["footprint_m2"] / raw["circle_m2"] if covered else None
    return {
        "share": None if share is None else round(share, 4),
        "polygons": raw["polygons"],
        "coverage": "ok" if covered else "no_data",
        "min_confidence": MIN_CONFIDENCE,
        "coverage_check_m": COVERAGE_RADIUS_M,
        "source": SOURCE,
        "license": LICENSE,
    }


def get_footprints(lat: float, lon: float, radius_m: int = 400):
    """Share of the circle (radius_m metres) covered by building footprints. Polygons are cut at
    the circle edge. Overlapping polygons are not merged, so the share can be slightly high."""
    ee.Initialize(project=EE_PROJECT)
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(radius_m)
    buildings = ee.FeatureCollection(BUILDINGS)
    inside = buildings.filterBounds(region).filter(ee.Filter.gte("confidence", MIN_CONFIDENCE))
    cut = inside.map(lambda f: f.set("m2", f.geometry().intersection(region, 1).area(1)))
    raw = ee.Dictionary({
        "circle_m2": region.area(1),
        "footprint_m2": cut.aggregate_sum("m2"),
        "polygons": inside.size(),
        "nearby": buildings.filterBounds(point.buffer(COVERAGE_RADIUS_M)).limit(1).size(),
    }).getInfo()
    return summarize(raw)


if __name__ == "__main__":
    lat, lon = float(sys.argv[1]), float(sys.argv[2])
    print(get_footprints(lat, lon, float(sys.argv[3]) if len(sys.argv) > 3 else 400))
