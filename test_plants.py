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


def test_semal_and_amla_are_assessed_from_their_ecocrop_sheets():
    # Filled 2026-10-14 (they were the first two of six empty rows). Both have a sheet at ecocrop.apps.fao.org.
    import csv
    rows = {r["common_name"]: r for r in csv.DictReader(open("plants.csv", encoding="utf-8"))}
    for name in ("Semal", "Amla"):
        assert rows[name]["source"].startswith("https://ecocrop.apps.fao.org/"), name
        assert rows[name]["rain_opt_min"] and rows[name]["temp_opt_min"] and rows[name]["ph_opt_min"], name
    ranked, excluded, blank = match_plants(dict(DEMO_ENV))
    assert "Semal" not in blank and "Amla" not in blank
    assert blank == []                       # all 32 species now have data (the last four filled 2026-10-14)


def test_banyan_has_no_altitude_minimum_but_a_1200_m_maximum():
    # Banyan (ECOCROP sheet id 6123): the sheet's 500-1200 m altitude is a record of where it is found, so only
    # the maximum is used; the plains must not rule it out. Confirmed by the user 2026-10-14 (see the row's notes).
    def at(elevation):
        ranked, excluded, blank = match_plants(dict(DEMO_ENV, annual_rainfall_mm=1500, annual_mean_temp_c=27.0,
                                                    ph=6.5, elevation_m=elevation))
        return ("offered" if any(e["name"] == "Banyan" for e in ranked) else
                "ruled out" if any(e["name"] == "Banyan" for e in excluded) else "no data")
    assert at(270) == "offered"                 # Bilaspur-like plains
    assert at(1100) == "offered"
    assert at(2000) == "ruled out"


def test_the_last_three_species_come_from_their_ecocrop_sheets():
    import csv
    rows = {r["common_name"]: r for r in csv.DictReader(open("plants.csv", encoding="utf-8"))}
    for name, sheet in (("Bamboo (male bamboo)", "5238"), ("Bijasal", "9046"), ("Chir pine", "8653")):
        assert rows[name]["source"].endswith("id=" + sheet), name
        assert rows[name]["rain_abs_min"] and rows[name]["temp_abs_max"] and rows[name]["ph_abs_max"], name
    # Bamboo's narrow acidic pH (absolute 4 to 6.5) rules out neutral soil; Chir pine has no altitude limit.
    ranked, excluded, blank = match_plants(dict(DEMO_ENV))                  # demo pH is 7.58
    assert any(e["name"] == "Bamboo (male bamboo)" for e in excluded)
    ranked, excluded, blank = match_plants(dict(DEMO_ENV, ph=5.0, annual_rainfall_mm=2000, annual_mean_temp_c=24.0, elevation_m=300))
    assert any(e["name"] == "Bamboo (male bamboo)" for e in ranked)
    assert rows["Chir pine"]["alt_min_m"] == "" and rows["Chir pine"]["alt_max_m"] == ""


def test_amla_rainfall_conflict_is_visible():
    # CONFLICT (see the row's notes): the ECOCROP sheet's absolute minimum is 700 mm, while Indian sources call
    # 630-800 mm ideal. The sheet is used until the user decides, so Amla is ruled out at 650 mm. If the
    # limit is changed on purpose, update this test and HANDOFF.
    status, reason = verdict("Amla", 650)
    assert status == "ruled out" and "700" in reason, (status, reason)


if __name__ == "__main__":
    test_sal_has_a_hard_rainfall_floor_of_1000_mm()
    test_semal_and_amla_are_assessed_from_their_ecocrop_sheets()
    test_banyan_has_no_altitude_minimum_but_a_1200_m_maximum()
    test_amla_rainfall_conflict_is_visible()
    test_mango_is_offered_in_the_konkan_but_not_beyond_3500_mm()
    print("all plant data tests passed")