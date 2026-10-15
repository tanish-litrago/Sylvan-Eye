"""
Tests for decisions written into plants.csv:  python test_plants.py
"""

from phase4_matcher import DEMO_ENV, match_plants


def verdict(name, rainfall):
    """('offered', rainfall verdict) or ('ruled out', reason) for one plant at a given rainfall."""
    ranked, excluded, blank = match_plants(dict(DEMO_ENV, annual_rainfall_mm=rainfall,
                                                annual_mean_temp_c=26.0, elevation_m=200))
    for e in ranked:
        if e["name"] == name:
            return "offered", e["factors"]["rainfall"][0]
    for e in excluded:
        if e["name"] == name:
            return "ruled out", e["excluded_because"]
    raise AssertionError(f"{name} is in neither list")


def test_sal_has_a_hard_rainfall_floor_of_1000_mm():
    # HANDOFF P7-6 (2026-10-14): the sources give only the required range (1000 mm and up), so the
    # lower end is the floor. Before this Sal was offered at 224 mm (Jaisalmer) as "poor".
    for rain in (224, 786, 928):                           # Jaisalmer, Morena, Solapur
        status, reason = verdict("Sal", rain)
        assert status == "ruled out" and "1000" in reason, (rain, status, reason)
    assert verdict("Sal", 1000)[0] == "offered"             # exactly on the floor is allowed
    assert verdict("Sal", 1700)[0] == "offered"            # Jagdalpur-like rainfall


def test_mango_is_offered_in_the_konkan_but_not_beyond_3500_mm():
    # HANDOFF P7-7 (2026-10-14): ECOCROP's absolute maximum was 2600 mm, but commercial Alphonso
    # orchards across the Konkan (Ratnagiri 3364 mm in the Phase 7 run) normally get about 3500 mm.
    status, rain_verdict = verdict("Mango", 3364)
    assert status == "offered" and rain_verdict == "marginal", (status, rain_verdict)   # offered, with a marginal check
    assert verdict("Mango", 3500)[0] == "offered"
    status, reason = verdict("Mango", 3600)
    assert status == "ruled out" and "3500" in reason, (status, reason)
    assert verdict("Mango", 1200)[1] == "good"


if __name__ == "__main__":
    test_sal_has_a_hard_rainfall_floor_of_1000_mm()
    test_mango_is_offered_in_the_konkan_but_not_beyond_3500_mm()
    print("all plant data tests passed")
