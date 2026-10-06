"""
Sylvan Eye — Phase 4: rule-based matcher.

Takes a location's environment and plants.csv and returns a ranked shortlist
with a reason for EVERY plant, including the ones ruled out. No LLM is involved:
every verdict comes from a number in plants.csv compared to a number we measured.

How a factor is judged (rainfall, temperature, pH):
    good           inside the source's typical range
    within_limits  the source gives only limits (e.g. "at least 500 mm") and we are inside
    marginal       outside the typical range but inside the stated extremes; for pH also within
                   PH_MARGIN of a stated extreme; for texture, one class away from the listed ones
    poor           outside the typical range and the source states no extreme on that side;
                   for texture, two classes away
    excluded       outside the stated extremes  -> plant is ruled out
    (blank cell)   no data -> factor is SKIPPED and confidence goes down. A missing
                   value is never counted as a pass.
Soil texture: in the plant's list = good, one class away (light/medium/heavy) = marginal,
    two away = poor (lists come from prose, so never excluded).
Elevation: outside the plant's altitude limits = excluded, inside = no score change.

Score = average over the 4 scored factors (rainfall, temperature, pH, texture), 0 to 1.
A factor with no data counts as a neutral 0.5 in the score, so a plant with little data
cannot outrank one with solid data just because nothing was checked.
Confidence = how many of the 5 factors (those 4 plus elevation) had data.

Run:
    python phase4_matcher.py --demo        offline, uses the measured Bilaspur values
    python phase4_matcher.py               live, default location (Bilaspur city centre)
    python phase4_matcher.py LAT LON       live, any location, e.g. python phase4_matcher.py 22.0336 82.2651
    add  --radius 1000  to size the terrain circle in metres (default 400)
    add  --brief        for a short report (10 plants, only the non-good checks)
"""

import csv
import sys

PLANTS_CSV = "plants.csv"

SCORES = {"good": 1.0, "within_limits": 0.7, "marginal": 0.5, "poor": 0.35}
NEUTRAL = 0.5  # value used for a scored factor that has no data
PH_MARGIN = 0.3        # pH this close beyond a stated limit counts as marginal, not excluded
                       # (pH is modelled at 250 m and is only good to a few tenths)
TEXTURE_ORDER = ["light", "medium", "heavy"]
DEFAULT_RADIUS = 400   # metres of terrain circle around the pin

# ---------------------------------------------------------------------------
# Eligibility gate thresholds. Starting guesses from only four test sites.
# ---------------------------------------------------------------------------
GATE_WATER_BLOCK = 0.5      # share water/wet surface at or above this -> do not recommend
GATE_WATER_WARN = 0.2       # share at or above this (but below the block level) -> warn
GATE_BUILT_WARN = 0.4       # share bare-or-built at or above this -> warn
GATE_SWING_WARN = 0.4       # big seasonal NDVI swing share ...
GATE_DRY_FLOOR_MAX = 0.2    # ... with a dry-season NDVI floor below this -> looks like cropland
GATE_NEVER_GREEN_PEAK = 0.15  # peak NDVI below this -> never greens up


def num(text):
    text = (text or "").strip()
    return float(text) if text else None


# ---------------------------------------------------------------------------
# Eligibility gate (uses the Phase 2 terrain result)
# ---------------------------------------------------------------------------
def check_eligibility(terrain: dict):
    """Returns (blocked, messages). Messages explain every block or warning."""
    cover = terrain["land_cover_fractions"]
    season = terrain["seasonality"]
    veg = terrain["vegetation"]
    blocked, messages = False, []

    if cover["water_or_wet_surface"] >= GATE_WATER_BLOCK:
        blocked = True
        messages.append(
            f"BLOCKED: {cover['water_or_wet_surface']:.0%} of the area reads as water or "
            f"wet surface, so plants cannot be recommended here."
        )
    elif cover["water_or_wet_surface"] >= GATE_WATER_WARN:
        messages.append(
            f"WARNING: {cover['water_or_wet_surface']:.0%} of the area reads as water or wet surface, "
            f"so part of it may be unplantable."
        )
    if cover["bare_or_built"] >= GATE_BUILT_WARN:
        messages.append(
            f"WARNING: {cover['bare_or_built']:.0%} is bare or built-up and the satellite "
            f"signal cannot tell these apart. If it is built-up, nothing can be planted."
        )
    if season["big_swing_fraction"] >= GATE_SWING_WARN and season["ndvi_dry_p10_mean"] < GATE_DRY_FLOOR_MAX:
        messages.append(
            "WARNING: vegetation swings between bare and green through the year, which "
            "looks like active cropland (unvalidated rule). Check whether the land is in use."
        )
    if season["ndvi_peak_p90_mean"] < GATE_NEVER_GREEN_PEAK:
        messages.append(
            "WARNING: the land never greens up. It could be barren, built-up, or "
            "non-natural ground (ash, mined or filled land), where soil data does not apply."
        )
    return blocked, messages


# ---------------------------------------------------------------------------
# Factor judgments
# ---------------------------------------------------------------------------
def judge_range(value, row, prefix, unit, margin=0.0):
    """Judge one numeric factor. Returns (verdict, reason) or (None, reason) if no data."""
    omin, omax = num(row.get(f"{prefix}_opt_min")), num(row.get(f"{prefix}_opt_max"))
    amin, amax = num(row.get(f"{prefix}_abs_min")), num(row.get(f"{prefix}_abs_max"))
    if value is None:
        return None, "no measurement for this location"
    if all(b is None for b in (omin, omax, amin, amax)):
        return None, "no data for this plant"

    if omin is not None and omax is not None:
        if omin <= value <= omax:
            return "good", f"{value:g}{unit} is inside the typical range {omin:g} to {omax:g}"
        if value < omin:
            if amin is not None:
                if value >= amin:
                    return "marginal", f"{value:g}{unit} is below the typical range ({omin:g}) but above the stated minimum {amin:g}"
                if margin and value >= amin - margin:
                    return "marginal", (f"{value:g}{unit} is {amin - value:.2f} below the stated minimum {amin:g}, "
                                        f"within the {margin:g} margin allowed for modelled data")
                return "excluded", f"{value:g}{unit} is below the stated minimum {amin:g}"
            return "poor", f"{value:g}{unit} is below the typical range (starts at {omin:g}); no stated minimum"
        if amax is not None:
            if value <= amax:
                return "marginal", f"{value:g}{unit} is above the typical range ({omax:g}) but below the stated maximum {amax:g}"
            if margin and value <= amax + margin:
                return "marginal", (f"{value:g}{unit} is {value - amax:.2f} above the stated maximum {amax:g}, "
                                    f"within the {margin:g} margin allowed for modelled data")
            return "excluded", f"{value:g}{unit} is above the stated maximum {amax:g}"
        return "poor", f"{value:g}{unit} is above the typical range (ends at {omax:g}); no stated maximum"

    # Only limits are known (one-sided or extremes without a typical range)
    if amin is not None and value < amin:
        if margin and value >= amin - margin:
            return "marginal", (f"{value:g}{unit} is {amin - value:.2f} below the stated minimum {amin:g}, "
                                f"within the {margin:g} margin allowed for modelled data")
        return "excluded", f"{value:g}{unit} is below the stated minimum {amin:g}"
    if amax is not None and value > amax:
        if margin and value <= amax + margin:
            return "marginal", (f"{value:g}{unit} is {value - amax:.2f} above the stated maximum {amax:g}, "
                                f"within the {margin:g} margin allowed for modelled data")
        return "excluded", f"{value:g}{unit} is above the stated maximum {amax:g}"
    return "within_limits", f"{value:g}{unit} is within the stated limits (no typical range given)"


def judge_texture(env_texture, row):
    items = [t.strip().lower() for t in (row.get("soil_texture") or "").replace("/", ",").split(",") if t.strip()]
    if env_texture is None:
        return None, "no soil texture for this location"
    if not items:
        return None, "no texture data for this plant"
    if env_texture in items:
        return "good", f"{env_texture} soil is in its listed textures ({', '.join(items)})"
    ranks = [TEXTURE_ORDER.index(t) for t in items if t in TEXTURE_ORDER]
    if env_texture in TEXTURE_ORDER and ranks:
        gap = min(abs(TEXTURE_ORDER.index(env_texture) - r) for r in ranks)
        if gap == 1:
            return "marginal", f"{env_texture} soil is one class away from its listed textures ({', '.join(items)})"
    return "poor", f"{env_texture} soil is not in its listed textures ({', '.join(items)})"


def judge_elevation(elev, row):
    lo, hi = num(row.get("alt_min_m")), num(row.get("alt_max_m"))
    if elev is None:
        return None, "no elevation for this location"
    if lo is None and hi is None:
        return None, "no altitude data for this plant"
    if lo is not None and elev < lo:
        return "excluded", f"{elev:g} m is below its altitude range ({lo:g} to {hi:g} m)"
    if hi is not None and elev > hi:
        return "excluded", f"{elev:g} m is above its altitude limit ({hi:g} m)"
    return "ok", f"{elev:g} m is within its altitude limits"


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def match_plants(env: dict, plants_csv: str = PLANTS_CSV):
    """
    env keys: annual_rainfall_mm, annual_mean_temp_c, ph, soil_texture, elevation_m
    (any may be None). Returns (ranked, excluded, skipped_blank).
    """
    ranked, excluded, blank = [], [], []
    with open(plants_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        name = row["common_name"] or row["scientific_name"]
        factors = {
            "rainfall": judge_range(env.get("annual_rainfall_mm"), row, "rain", " mm"),
            "temperature": judge_range(env.get("annual_mean_temp_c"), row, "temp", " C"),
            "pH": judge_range(env.get("ph"), row, "ph", "", margin=PH_MARGIN),
            "texture": judge_texture(env.get("soil_texture"), row),
            "elevation": judge_elevation(env.get("elevation_m"), row),
        }
        if all(v is None for v, _ in factors.values()):
            blank.append(name)
            continue

        known = {k: (v, why) for k, (v, why) in factors.items() if v is not None}
        confidence_n = len(known)
        hit = next(((k, why) for k, (v, why) in known.items() if v == "excluded"), None)
        flags = []
        if "weed" in (row.get("notes") or "").lower():
            flags.append("source flags it as able to become a weed")

        entry = {
            "name": name, "scientific_name": row["scientific_name"],
            "factors": factors, "confidence_n": confidence_n, "flags": flags,
        }
        if hit:
            entry["excluded_because"] = f"{hit[0]}: {hit[1]}"
            excluded.append(entry)
            continue
        scored = [SCORES[v] for k, (v, _) in known.items() if k != "elevation" and v in SCORES]
        missing = 4 - len(scored)
        entry["score"] = round((sum(scored) + NEUTRAL * missing) / 4, 2)
        ranked.append(entry)

    ranked.sort(key=lambda e: (-e["score"], -e["confidence_n"], e["name"]))
    return ranked, excluded, blank


def confidence_label(n):
    return "high" if n >= 4 else "medium" if n == 3 else "low"


def terrain_summary_line(terrain):
    cover, season = terrain["land_cover_fractions"], terrain["seasonality"]
    return (f"Terrain summary (radius {terrain['location']['radius_m']:g} m): "
            f"water/wet {cover['water_or_wet_surface']:.0%}, bare/built {cover['bare_or_built']:.0%}, "
            f"sparse vegetation or crops {cover['sparse_vegetation_or_crops']:.0%}, "
            f"dense vegetation {cover['dense_vegetation']:.0%}; "
            f"NDVI dry {season['ndvi_dry_p10_mean']} to peak {season['ndvi_peak_p90_mean']}, "
            f"big seasonal swing {season['big_swing_fraction']:.0%}")


def print_brief(env, terrain, ranked, excluded, blank, top=10):
    """Compact report: only what is needed to judge a run. Use --brief."""
    print(f"Env: rain {env['annual_rainfall_mm']} mm | temp {env['annual_mean_temp_c']} C | "
          f"pH {env['ph']} | {env['soil_texture']} soil | {env['elevation_m']} m")
    if terrain:
        blocked, messages = check_eligibility(terrain)
        print(terrain_summary_line(terrain))
        for m in messages:
            print(m)
        if blocked:
            print("No plant recommendations produced.")
            return
        if not messages:
            print("Eligibility check: no warnings.")
    print(f"Shortlist ({len(ranked)} not ruled out), top {min(top, len(ranked))}:")
    for i, e in enumerate(ranked[:top], 1):
        notes = [f"{k} {v}" for k, (v, _) in e["factors"].items() if v in ("within_limits", "marginal", "poor")]
        notes += [f"{k} skipped" for k, (v, _) in e["factors"].items() if v is None]
        weed = " [weed flag]" if e["flags"] else ""
        detail = f" ({'; '.join(notes)})" if notes else ""
        print(f"{i:>2}. {e['name']} {e['score']:.2f}{detail}{weed}")
    print("Ruled out: " + ("; ".join(f"{e['name']} ({e['excluded_because']})" for e in excluded) or "none"))
    print(f"Not assessed (no data): {len(blank)}")


def print_report(env, terrain, ranked, excluded, blank, top=15):
    print("Environment used:")
    for k, v in env.items():
        print(f"  {k}: {v}")

    if terrain:
        blocked, messages = check_eligibility(terrain)
        print("\n" + terrain_summary_line(terrain))
        print()
        for m in messages:
            print(m)
        if blocked:
            print("\nNo plant recommendations produced.")
            return
        if not messages:
            print("\nEligibility check: no warnings.")

    print(f"\nRanked shortlist ({len(ranked)} plants not ruled out), top {min(top, len(ranked))}:")
    for i, e in enumerate(ranked[:top], 1):
        score = f"{e['score']:.2f}"
        print(f"\n{i:>2}. {e['name']} ({e['scientific_name']})  score {score}, "
              f"confidence {confidence_label(e['confidence_n'])} ({e['confidence_n']}/5 factors)")
        for k, (v, why) in e["factors"].items():
            label = v if v else "skipped"
            print(f"      {k:<11} {label:<14} {why}")
        for flag in e["flags"]:
            print(f"      NOTE: {flag}")

    print(f"\nRuled out ({len(excluded)}):")
    for e in excluded:
        print(f"  - {e['name']}: {e['excluded_because']}")
    if blank:
        print(f"\nNo data in plants.csv, not assessed ({len(blank)}): {', '.join(blank)}")
    print("\nNote: soil pH and texture come from a modelled 250 m dataset and rainfall/temperature "
          "from reanalysis data. Confirm with a local soil test before planting.")


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
DEMO_ENV = {  # measured for Bilaspur in earlier phases
    "annual_rainfall_mm": 1520,
    "annual_mean_temp_c": 26.4,
    "ph": 7.58,
    "soil_texture": "medium",
    "elevation_m": 269.4,
}


def run_live(lat, lon, radius_m=DEFAULT_RADIUS):
    from phase2_terrain_extraction import get_terrain_data
    from phase1_data_pipeline import get_soil_data
    from phase4_inputs import get_climate_normals, classify_soil_texture

    terrain = get_terrain_data(lat, lon, radius_m=radius_m)
    soil = get_soil_data(lat, lon)["surface_soil"]
    climate = get_climate_normals(lat, lon)
    env = {
        "annual_rainfall_mm": climate["annual_rainfall_mm"],
        "annual_mean_temp_c": climate["annual_mean_temp_c"],
        "ph": soil["ph"]["value"],
        "soil_texture": classify_soil_texture(soil["clay"]["value"], soil["sand"]["value"]),
        "elevation_m": terrain["terrain"]["elevation_m"],
    }
    return env, terrain


def parse_radius(argv, default=DEFAULT_RADIUS):
    """Pull '--radius METERS' out of argv (in place) and return it."""
    if "--radius" in argv:
        i = argv.index("--radius")
        radius = float(argv[i + 1])
        del argv[i:i + 2]
        return radius
    return default


def main():
    argv = sys.argv[1:]
    radius = parse_radius(argv)
    args = [a for a in argv if not a.startswith("--")]
    if "--demo" in argv:
        print("Location: demo values measured for Bilaspur (offline)\n")
        env, terrain = dict(DEMO_ENV), None
    else:
        lat, lon = (float(args[0]), float(args[1])) if len(args) >= 2 else (22.0797, 82.1409)
        print(f"Location: {lat}, {lon} (terrain radius {radius:g} m)\n")
        env, terrain = run_live(lat, lon, radius)
    ranked, excluded, blank = match_plants(env)
    if "--brief" in argv:
        print_brief(env, terrain, ranked, excluded, blank)
    else:
        print_report(env, terrain, ranked, excluded, blank)


if __name__ == "__main__":
    main()