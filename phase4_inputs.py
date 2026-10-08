"""
Sylvan Eye — Phase 4 inputs: long-term climate and soil texture class.

The plant table (plants.csv) uses MEAN ANNUAL temperature and ANNUAL rainfall,
and light/medium/heavy soil texture. Phase 1 gave us a weather forecast and
clay/sand percentages, which can't be compared to those ranges directly.
This file turns them into comparable numbers:

  get_climate_normals(lat, lon)  -> annual mean temp, annual rainfall, dry months...
  classify_soil_texture(clay, sand) -> "light" / "medium" / "heavy"

Data source: Open-Meteo Historical Weather API (free, no key).
Run:  python phase4_inputs.py
"""

import requests

TEST_LAT = 22.0797
TEST_LON = 82.1409
LOCATION_NAME = "Bilaspur, Chhattisgarh"

# ---------------------------------------------------------------------------
# Tunable settings. Starting points, not truth: change them and rerun.
# ---------------------------------------------------------------------------
START_YEAR = 2015
END_YEAR = 2024            # full calendar years only, so every year is complete
DRY_MONTH_MM = 30          # a calendar month with less average rain than this is "dry"
MIN_DAYS_PER_YEAR = 350    # skip a year if too many days are missing

# Soil texture cutoffs (percent of clay / sand in the surface layer)
HEAVY_CLAY_MIN = 35        # clay at or above this -> heavy
LIGHT_SAND_MIN = 50        # sand at or above this ...
LIGHT_CLAY_MAX = 20        # ... and clay below this -> light; everything else -> medium

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Cache version of get_climate_normals()'s output. Bump it whenever the returned data changes.
CACHE_VERSION = 1


# ---------------------------------------------------------------------------
# Climate
# ---------------------------------------------------------------------------
def fetch_daily(lat: float, lon: float, start_year: int, end_year: int):
    """Daily mean temperature (C) and rainfall (mm) from Open-Meteo's archive."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{start_year}-01-01",
        "end_date": f"{end_year}-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "auto",
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=60)
    resp.raise_for_status()
    daily = resp.json().get("daily", {})
    return (
        daily.get("time", []),
        daily.get("temperature_2m_mean", []),
        daily.get("precipitation_sum", []),
    )


def summarize_daily(dates, temps, rains):
    """
    Turn daily numbers into the long-term statistics the plant table needs.
    Pure function (no network), so it can be tested with made-up data.
    """
    by_year = {}   # year -> {"t": [...], "r": [...], "days": n}
    by_month = {}  # month (1-12) -> {year -> rain total}
    month_temps = {m: [] for m in range(1, 13)}

    for date, t, r in zip(dates, temps, rains):
        year, month = int(date[:4]), int(date[5:7])
        y = by_year.setdefault(year, {"t": [], "r": [], "days": 0})
        y["days"] += 1
        if t is not None:
            y["t"].append(t)
            month_temps[month].append(t)
        if r is not None:
            y["r"].append(r)
            by_month.setdefault(month, {}).setdefault(year, 0.0)
            by_month[month][year] += r

    good_years = sorted(
        yr for yr, y in by_year.items()
        if y["days"] >= MIN_DAYS_PER_YEAR and len(y["t"]) >= MIN_DAYS_PER_YEAR
        and len(y["r"]) >= MIN_DAYS_PER_YEAR
    )
    if not good_years:
        raise RuntimeError("No complete years of data returned")

    annual_temp = [sum(by_year[y]["t"]) / len(by_year[y]["t"]) for y in good_years]
    annual_rain = [sum(by_year[y]["r"]) for y in good_years]

    # Average rainfall for each calendar month across the good years
    month_rain = {}
    for m in range(1, 13):
        totals = [by_month.get(m, {}).get(y, 0.0) for y in good_years]
        month_rain[m] = sum(totals) / len(totals)

    month_mean_temp = {
        m: (sum(v) / len(v) if v else None) for m, v in month_temps.items()
    }
    valid_month_temps = [v for v in month_mean_temp.values() if v is not None]
    dry_months = [m for m, mm in month_rain.items() if mm < DRY_MONTH_MM]

    return {
        "years_used": good_years,
        "annual_mean_temp_c": round(sum(annual_temp) / len(annual_temp), 1),
        "annual_rainfall_mm": round(sum(annual_rain) / len(annual_rain)),
        "annual_rainfall_driest_year_mm": round(min(annual_rain)),
        "annual_rainfall_wettest_year_mm": round(max(annual_rain)),
        "coldest_month_mean_c": round(min(valid_month_temps), 1),
        "hottest_month_mean_c": round(max(valid_month_temps), 1),
        "dry_months": dry_months,
        "dry_month_count": len(dry_months),
        "monthly_rainfall_mm": {m: round(v) for m, v in month_rain.items()},
    }


def get_climate_normals(lat: float, lon: float,
                        start_year: int = START_YEAR, end_year: int = END_YEAR):
    dates, temps, rains = fetch_daily(lat, lon, start_year, end_year)
    result = summarize_daily(dates, temps, rains)
    result["source"] = f"Open-Meteo historical archive, {start_year}-{end_year}"
    return result


# ---------------------------------------------------------------------------
# Soil texture
# ---------------------------------------------------------------------------
def classify_soil_texture(clay_pct: float, sand_pct: float) -> str:
    """
    Crude three-way class to match plants.csv (light / medium / heavy).
      heavy  : clay-rich (clay >= HEAVY_CLAY_MIN)
      light  : sandy, little clay (sand >= LIGHT_SAND_MIN and clay < LIGHT_CLAY_MAX)
      medium : everything else (loams)
    This is a simplification of the full soil texture triangle.
    """
    if clay_pct >= HEAVY_CLAY_MIN:
        return "heavy"
    if sand_pct >= LIGHT_SAND_MIN and clay_pct < LIGHT_CLAY_MAX:
        return "light"
    return "medium"


# ---------------------------------------------------------------------------
def main():
    print(f"Climate normals for: {LOCATION_NAME} ({TEST_LAT}, {TEST_LON})\n")
    c = get_climate_normals(TEST_LAT, TEST_LON)

    print(f"Source:               {c['source']}")
    print(f"Years used:           {c['years_used'][0]}-{c['years_used'][-1]} ({len(c['years_used'])} years)")
    print(f"Annual mean temp:     {c['annual_mean_temp_c']} C")
    print(f"Annual rainfall:      {c['annual_rainfall_mm']} mm "
          f"(driest year {c['annual_rainfall_driest_year_mm']}, "
          f"wettest {c['annual_rainfall_wettest_year_mm']})")
    print(f"Coldest / hottest month mean: {c['coldest_month_mean_c']} / {c['hottest_month_mean_c']} C")
    print(f"Dry months (<{DRY_MONTH_MM} mm): {c['dry_month_count']}  {c['dry_months']}")
    print("Monthly rainfall (mm):")
    for m in range(1, 13):
        print(f"  {m:>2}: {c['monthly_rainfall_mm'][m]}")

    print("\nSoil texture class from Phase 1 soil data:")
    try:
        from phase1_data_pipeline import get_soil_data
        soil = get_soil_data(TEST_LAT, TEST_LON)["surface_soil"]
        clay, sand = soil["clay"]["value"], soil["sand"]["value"]
        print(f"  clay {clay}%, sand {sand}%  ->  {classify_soil_texture(clay, sand)}")
    except Exception as e:
        print(f"  skipped ({e})")


if __name__ == "__main__":
    main()