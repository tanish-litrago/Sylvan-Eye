"""
Tests for decisions written into plants.csv:  python -m tests.test_plants
"""

from phases.phase4_matcher import DEMO_ENV, PLANTS_CSV, match_plants


def verdict(name, rainfall, elevation=200):
    """('offered', rainfall verdict) or ('ruled out', reason) for one plant at a given rainfall and elevation."""
    ranked, excluded, blank = match_plants(dict(DEMO_ENV, annual_rainfall_mm=rainfall,
                                                annual_mean_temp_c=26.0, elevation_m=elevation))
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
    rows = {r["common_name"]: r for r in csv.DictReader(open(PLANTS_CSV, encoding="utf-8"))}
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
    rows = {r["common_name"]: r for r in csv.DictReader(open(PLANTS_CSV, encoding="utf-8"))}
    for name, sheet in (("Bamboo (male bamboo)", "5238"), ("Bijasal", "9046"), ("Chir pine", "8653")):
        assert rows[name]["source"].endswith("id=" + sheet), name
        assert rows[name]["rain_abs_min"] and rows[name]["temp_abs_max"] and rows[name]["ph_abs_max"], name
    # Bamboo's narrow acidic pH (absolute 4 to 6.5) rules out neutral soil. (Chir pine's altitude limits were added on 2026-10-19, see the test below.)
    ranked, excluded, blank = match_plants(dict(DEMO_ENV))                  # demo pH is 7.58
    assert any(e["name"] == "Bamboo (male bamboo)" for e in excluded)
    ranked, excluded, blank = match_plants(dict(DEMO_ENV, ph=5.0, annual_rainfall_mm=2000, annual_mean_temp_c=24.0, elevation_m=300))
    assert any(e["name"] == "Bamboo (male bamboo)" for e in ranked)
    assert rows["Chir pine"]["alt_min_m"] == "400" and rows["Chir pine"]["alt_max_m"] == "2300"


def test_amla_rainfall_floor_is_630_mm_and_dry_zone_orchards_are_offered():
    # 2026-10-19, user decision (option A): the ECOCROP sheet's 700 mm floor and 1500-2500 mm optimum are
    # replaced at the dry end by the Indian sources (630-800 mm ideal; zero-irrigation orchards at about
    # 750-830 mm). The maxima (2500 optimal, 4200 absolute) stay from the sheet. Before this Amla was ruled
    # out at 650 mm and only "poor" below 1500 mm.
    for mm in (600, 629):
        status, reason = verdict("Amla", mm)
        assert status == "ruled out" and "630" in reason, (mm, status, reason)
    for mm in (630, 650, 750, 831, 1200, 2500):
        assert verdict("Amla", mm) == ("offered", "good"), (mm, verdict("Amla", mm))
    status, rain = verdict("Amla", 3000)             # above the optimal maximum, below the absolute one
    assert status == "offered" and rain != "good", (status, rain)
    assert verdict("Amla", 4300)[0] == "ruled out"


def test_chir_pine_is_limited_to_400_2300_m():
    # 2026-10-19, user decision (option A): the ECOCROP sheet has no altitude values, so the limits come from the
    # Botanical Survey of India datasheet (400 to 2,300 m a.s.l.), used as hard limits. Before this chir pine was
    # offered in the plains. Rain 1200 mm and 26 C are inside its ranges, so only altitude decides here.
    for m in (100, 270, 399):                                 # plains, Bilaspur is about 270-300 m
        status, reason = verdict("Chir pine", 1200, elevation=m)
        assert status == "ruled out" and "400" in reason, (m, status, reason)
    for m in (400, 1000, 2262, 2300):                         # 2262 m is Shimla
        assert verdict("Chir pine", 1200, elevation=m)[0] == "offered", m
    for m in (2301, 3304):                                    # 3304 m is Leh
        status, reason = verdict("Chir pine", 1200, elevation=m)
        assert status == "ruled out" and "2300" in reason, (m, status, reason)


FLOORS = {"Arjun": 750, "Mahua": 550, "Peepal": 500, "Tamarind": 350, "Gamhar": 750, "Bael": 570, "Palash": 450,
          "Casuarina": 200, "Ber": 120, "Siris": 500, "Amaltas": 480, "Baheda": 900, "Deodar": 200,
          "Indian rosewood": 750}


def test_fourteen_species_get_a_rainfall_floor_from_their_stated_minimum():
    # 2026-10-19, user decision (option A): the sources give only a range and no lower limit, so the lower end of the
    # range is a hard floor, the same rule as Sal's (2026-10-14). Before this these plants were never ruled out for dryness.
    import csv
    rows = {r["common_name"]: r for r in csv.DictReader(open(PLANTS_CSV, encoding="utf-8"))}
    for name, floor in FLOORS.items():
        r = rows[name]
        assert r["rain_abs_min"] == str(floor) == r["rain_opt_min"], (name, r["rain_abs_min"], r["rain_opt_min"])
        assert "RAINFALL FLOOR" in r["notes"], name
    # every other plant keeps what it had: no plant is left without a rainfall minimum
    assert [n for n, r in rows.items() if not r["rain_abs_min"].strip()] == []


def test_the_new_floors_rule_plants_out_in_dry_places_but_not_wet_ones():
    for name, floor in (("Peepal", 500), ("Tamarind", 350), ("Baheda", 900), ("Ber", 120)):
        status, reason = verdict(name, floor - 1)
        assert status == "ruled out" and str(floor) in reason, (name, status, reason)
        assert verdict(name, floor)[0] == "offered", name                     # exactly on the floor is allowed
    assert verdict("Peepal", 224)[0] == "ruled out"                           # Jaisalmer
    assert verdict("Ber", 224)[0] == "offered"                                # Ber's floor is only 120 mm


ALTITUDE = {"Tamarind": ("", 1500), "Arjun": ("", 1200), "Sal": (100, 1500), "Mango": ("", 1200),
            "Sissoo / Shisham": ("", 1500), "Jamun": ("", 1800), "Karanj / Pongamia": ("", 1200),
            "Salai / Indian frankincense": ("", 1150), "Khair / Catechu": ("", 1500), "Mahua": ("", 1200),
            "Amaltas": ("", 1220), "Khejri": ("", 600), "Babul": ("", 1340)}


def test_thirteen_species_get_altitude_limits_from_checked_sources():
    # 2026-10-20: the user found the values (with an AI tool), Claude opened the pages and checked each quoted line
    # (CABI could not be opened and is not used). Sal's minimum of 100 m is the user's decision B; Babul's 1340 m is
    # the user's decision B too (a sheet for another subspecies, the caveat is in its notes). Now every plant has an altitude limit.
    import csv
    rows = {r["common_name"]: r for r in csv.DictReader(open(PLANTS_CSV, encoding="utf-8"))}
    for name, (mn, mx) in ALTITUDE.items():
        r = rows[name]
        assert r["alt_min_m"] == str(mn) and r["alt_max_m"] == str(mx), (name, r["alt_min_m"], r["alt_max_m"])
        assert "ALTITUDE LIMIT" in r["notes"] and "http" in r["notes"], name
    assert "subspecies" in rows["Babul"]["notes"]                                # the caveat travels with the number
    assert [n for n, r in rows.items() if not r["alt_min_m"].strip() and not r["alt_max_m"].strip()] == []


def test_altitude_limits_stop_lowland_trees_in_the_mountains():
    # Before this Tamarind, Arjun, Mahua and Amaltas were offered at Leh (3,304 m) and ten of these plants at Shimla.
    for name, rain, hi in (("Tamarind", 1000, 1500), ("Arjun", 1000, 1200), ("Mango", 1000, 1200)):
        assert verdict(name, rain, elevation=hi)[0] == "offered", name
        status, reason = verdict(name, rain, elevation=hi + 1)
        assert status == "ruled out" and str(hi) in reason, (name, status, reason)
    for m in (99, 13, 56):                                       # Sal below 100 m (Puri, Ratnagiri)
        status, reason = verdict("Sal", 1500, elevation=m)
        assert status == "ruled out" and "100" in reason, (m, status, reason)
    assert verdict("Sal", 1500, elevation=100)[0] == "offered"
    assert verdict("Sal", 1500, elevation=1501)[0] == "ruled out"


if __name__ == "__main__":
    test_sal_has_a_hard_rainfall_floor_of_1000_mm()
    test_semal_and_amla_are_assessed_from_their_ecocrop_sheets()
    test_banyan_has_no_altitude_minimum_but_a_1200_m_maximum()
    test_amla_rainfall_floor_is_630_mm_and_dry_zone_orchards_are_offered()
    test_the_last_three_species_come_from_their_ecocrop_sheets()
    test_chir_pine_is_limited_to_400_2300_m()
    test_mango_is_offered_in_the_konkan_but_not_beyond_3500_mm()
    test_fourteen_species_get_a_rainfall_floor_from_their_stated_minimum()
    test_the_new_floors_rule_plants_out_in_dry_places_but_not_wet_ones()
    test_thirteen_species_get_altitude_limits_from_checked_sources()
    test_altitude_limits_stop_lowland_trees_in_the_mountains()
    print("all plant data tests passed")