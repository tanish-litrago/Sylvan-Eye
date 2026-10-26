"""
Tests for the eligibility gate's cropland rule on the REAL numbers measured so far
(HANDOFF 7b and the Phase 7 report):  python -m tests.test_gate

Each row: dry-season NDVI, big-swing share by year, and whether the land really is cropland
(the user's own check on the satellite view). If the cut-off moves, this table shows what changes.
"""

import glob
import json

from phases.phase4_matcher import GATE_DRY_FLOOR_MAX, GATE_OUTLINE_WARN, GATE_SWING_WARN, check_eligibility

# name, dry NDVI, swing by year, is it cropland?   (True / False / None = unclear; none left)
SITES = [
    ("green farmland",   0.143, {},                                         True),    # single-year data only
    ("Khapri",           0.188, {2023: 1.00, 2024: 0.992, 2025: 0.255},     True),
    ("Varanasi",         0.193, {2023: 0.91, 2024: 0.83, 2025: 0.87},       True),
    ("Solapur",          0.204, {2023: 0.92, 2024: 0.89, 2025: 0.73},       True),    # missed at a 0.2 cut-off
    ("Morena ravines",   0.275, {2023: 0.89, 2024: 0.90, 2025: 0.91},       False),   # ravines and scrub, user saw no farmland (P7-3)
    ("Fadhakhar Park",   0.290, {},                                         False),
    ("Shimla slope",     0.321, {2023: 0.52, 2024: 0.53, 2025: 0.76},       False),
    ("Puri",             0.388, {2023: 0.73, 2024: 0.69, 2025: 0.64},       False),
    ("Ratnagiri",        0.445, {2023: 0.35, 2024: 0.37, 2025: 0.23},       False),
    ("Jagdalpur forest", 0.595, {2023: 0.82, 2024: 0.85, 2025: 0.13},       False),   # deciduous forest swings too
    ("city centre",      0.196, {2023: 0.32, 2024: 0.08, 2025: 0.11},       False),   # no recurring swing
    ("ash dyke 400 m",   0.081, {2023: 0.94, 2024: 0.29, 2025: 0.28},       False),   # one year only
]
SINGLE_YEAR_SWING = {"green farmland": 0.98, "Fadhakhar Park": 0.94}


def terrain(dry, by_year, single_swing=0.0):
    return {"land_cover_fractions": {"water_or_wet_surface": 0.0, "bare_or_built": 0.0,
            "sparse_vegetation_or_crops": 0.3, "dense_vegetation": 0.6},
            "seasonality": {"ndvi_dry_p10_mean": dry, "ndvi_peak_p90_mean": 0.65,
                            "big_swing_fraction": single_swing, "big_swing_by_year": by_year},
            "vegetation": {}, "location": {"radius_m": 400}, "terrain": {"elevation_m": 100.0}}


def flagged(name, dry, by_year):
    _, messages = check_eligibility(terrain(dry, by_year, SINGLE_YEAR_SWING.get(name, 0.0)))
    return any("active cropland" in m for m in messages)


def test_known_sites_get_the_right_cropland_answer():
    for name, dry, by_year, is_crop in SITES:
        if is_crop is None:
            continue
        assert flagged(name, dry, by_year) == is_crop, f"{name}: cropland={is_crop}, dry NDVI {dry}"


def recurring_swing(name, by_year):
    """Same idea as the gate: a big swing in at least two years (or the single year we have)."""
    if not by_year:
        return SINGLE_YEAR_SWING.get(name, 0.0) >= GATE_SWING_WARN
    return sum(1 for f in by_year.values() if f >= GATE_SWING_WARN) >= min(2, len(by_year))


def test_the_cut_off_sits_in_the_gap_between_cropland_and_the_next_site():
    # Only sites with a recurring swing matter for this cut-off: without one the rule cannot fire.
    crop = max(d for _, d, _, c in SITES if c is True)
    other = min(d for n, d, y, c in SITES if c is not True and recurring_swing(n, y))
    assert crop < GATE_DRY_FLOOR_MAX < other, (crop, GATE_DRY_FLOOR_MAX, other)


def test_ravine_scrub_that_swings_like_crops_is_not_flagged():
    # Morena (P7-3): 59% crop-like cover and a 90% swing in every year, but ravines and scrub with
    # no farmland (the user's check). Only the dry-season floor, 0.275, keeps it apart from cropland.
    assert flagged("Morena ravines", 0.275, {2023: 0.89, 2024: 0.90, 2025: 0.91}) is False


def test_known_limit_built_up_hill_town_is_not_flagged():
    # KNOWN LIMIT (HANDOFF P7-4): at the Shimla point the user saw over 40% town, but the land
    # cover read only 7% bare or built-up, below the 40% warning level. If this starts failing
    # the gate has improved (for example a building-footprint signal): update the test and HANDOFF.
    terrain_ = terrain(0.321, {2023: 0.52, 2024: 0.53, 2025: 0.76})
    terrain_["land_cover_fractions"]["bare_or_built"] = 0.07
    _, messages = check_eligibility(terrain_)
    assert not any("built-up" in m for m in messages)


# ---- building-outline warning (v2.1.0) ----------------------------------------------------------
# name, outline share, bare/built, water, what the gate should add
OUTLINES = [
    ("Kochi",      0.438, 0.37, 0.01, "warning"),   # land cover read 37% (line 40%); the outlines say town
    ("Kolkata",    0.466, 0.82, 0.01, "nothing"),   # the land-cover warning already says it: no second one
    ("Darjeeling", 0.418, 0.13, 0.61, "note"),      # BLOCKED as water; the note explains, the block stays
    ("Kalimpong",  0.296, 0.34, 0.00, "warning"),
    ("Pirangut",   0.205, 0.10, 0.00, "warning"),   # lowest edge, user expected a warning
    ("Kakdwip",    0.165, 0.05, 0.01, "nothing"),   # highest large village, user expected none
    ("Shimla",     0.056, 0.07, 0.00, "nothing"),   # known limit: houses under trees stay under the line
]


def with_outline(share, built, water, coverage="ok"):
    t = terrain(0.5, {})
    t["land_cover_fractions"].update(bare_or_built=built, water_or_wet_surface=water)
    t["footprints"] = {"share": share, "coverage": coverage}
    return t


def outline_messages(t):
    blocked, messages = check_eligibility(t)
    return blocked, [m for m in messages if "building outlines" in m]


def test_outline_line_on_real_numbers():
    for name, share, built, water, want in OUTLINES:
        blocked, got = outline_messages(with_outline(share, built, water))
        kind = "nothing" if not got else ("note" if got[0].startswith("NOTE") else "warning")
        assert kind == want, (name, got)
        assert blocked == (water >= 0.5), name        # the rule never changes the block


def test_line_sits_between_the_largest_village_and_the_lowest_edge():
    assert 0.165 < GATE_OUTLINE_WARN <= 0.205
    assert outline_messages(with_outline(GATE_OUTLINE_WARN, 0.0, 0.0))[1]
    assert not outline_messages(with_outline(GATE_OUTLINE_WARN - 0.001, 0.0, 0.0))[1]


def test_no_outline_data_adds_nothing():
    for cov in ("no_data", "error"):
        assert not outline_messages(with_outline(None, 0.0, 0.0, cov))[1]
    assert not outline_messages(terrain(0.5, {}))[1]  # no footprints key at all (older data, demo)


def test_saved_fixtures_only_gain_a_message_and_never_change_the_block():
    changed = []
    for path in sorted(glob.glob("data/fixtures/*.json")):
        t = json.load(open(path, encoding="utf-8"))["terrain"]
        if "footprints" not in t:
            continue
        before = check_eligibility({k: v for k, v in t.items() if k != "footprints"})
        after = check_eligibility(t)
        assert before[0] == after[0], path
        extra = [m for m in after[1] if m not in before[1]]
        assert all(m in after[1] for m in before[1]), path       # old messages untouched
        assert all("building outlines" in m for m in extra), path
        if extra:
            changed.append(path.split("/")[-1].split("\\")[-1])
    assert "kochi.json" in changed and "darjeeling.json" in changed, changed


if __name__ == "__main__":
    test_known_sites_get_the_right_cropland_answer()
    test_the_cut_off_sits_in_the_gap_between_cropland_and_the_next_site()
    test_ravine_scrub_that_swings_like_crops_is_not_flagged()
    test_known_limit_built_up_hill_town_is_not_flagged()
    test_outline_line_on_real_numbers()
    test_line_sits_between_the_largest_village_and_the_lowest_edge()
    test_no_outline_data_adds_nothing()
    test_saved_fixtures_only_gain_a_message_and_never_change_the_block()
    print("all gate tests passed")