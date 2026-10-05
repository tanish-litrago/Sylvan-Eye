"""
Sylvan Eye — Phase 3: plant database validator.

Checks plants.csv for mistakes while you fill it in from ECOCROP datasheets.
It never edits the file and never guesses values.

Run:  python validate_plants.py            (checks plants.csv)
      python validate_plants.py my.csv     (checks another file)

Column meaning:
    *_opt_min / *_opt_max : the typical or "grows best" range stated by the source
    *_abs_min / *_abs_max : the bracketed extremes the source gives (optional)
Rules checked for each of pH, rainfall and temperature:
    - the typical (opt) pair is filled as a pair (min and max together)
    - if an extreme (abs) is given it must contain the typical range:
      abs_min <= opt_min and opt_max <= abs_max
    - a single-sided limit is allowed ("up to 40" -> only opt_max or abs_max)
Plus: pH between 0 and 14, rainfall not negative, plausible temperatures,
a source for any row that has numbers, soil_texture in an allowed set.
"""

import csv
import sys

# (label, prefix, lowest allowed value, highest allowed value)
RANGES = [
    ("pH", "ph", 0, 14),
    ("rainfall (mm/year)", "rain", 0, 12000),
    ("temperature (C)", "temp", -50, 60),
]
ALLOWED_TEXTURE = {"light", "medium", "heavy", "organic"}
NUMERIC_COLUMNS = [
    f"{prefix}_{kind}_{bound}"
    for _, prefix, _, _ in RANGES
    for kind in ("opt", "abs")
    for bound in ("min", "max")
]


def to_float(text):
    text = (text or "").strip()
    if text == "":
        return None
    return float(text)  # raises ValueError on bad input


def check_row(row):
    """Return (problems, filled_count) for one plant row."""
    problems = []
    name = row.get("common_name") or row.get("scientific_name") or "?"

    values = {}
    for col in NUMERIC_COLUMNS:
        try:
            values[col] = to_float(row.get(col))
        except ValueError:
            problems.append(f"{name}: '{row.get(col)}' in {col} is not a number")
            values[col] = None

    filled = sum(v is not None for v in values.values())

    for label, prefix, low, high in RANGES:
        amin = values[f"{prefix}_abs_min"]
        omin = values[f"{prefix}_opt_min"]
        omax = values[f"{prefix}_opt_max"]
        amax = values[f"{prefix}_abs_max"]
        present = [v for v in (amin, omin, omax, amax) if v is not None]
        if not present:
            continue
        if (omin is None) != (omax is None):
            problems.append(f"{name}: {label} typical range has only one end; "
                            f"fill both opt_min and opt_max (or leave both blank)")
        if omin is not None and omax is not None and omin > omax:
            problems.append(f"{name}: {label} opt_min {omin} is above opt_max {omax}")
        if amin is not None and omin is not None and amin > omin:
            problems.append(f"{name}: {label} abs_min {amin} is above opt_min {omin}")
        if amax is not None and omax is not None and amax < omax:
            problems.append(f"{name}: {label} abs_max {amax} is below opt_max {omax}")
        if min(present) < low or max(present) > high:
            problems.append(f"{name}: {label} has a value outside {low} to {high}: {present}")

    try:
        alt_lo, alt_hi = to_float(row.get("alt_min_m")), to_float(row.get("alt_max_m"))
        if alt_lo is not None and alt_hi is not None and alt_lo > alt_hi:
            problems.append(f"{name}: alt_min_m {alt_lo} is above alt_max_m {alt_hi}")
        if (alt_lo is not None and alt_lo < -500) or (alt_hi is not None and alt_hi > 9000):
            problems.append(f"{name}: altitude outside a plausible range")
    except ValueError:
        problems.append(f"{name}: altitude columns must be numbers")

    texture = (row.get("soil_texture") or "").strip().lower()
    if texture:
        for item in [t.strip() for t in texture.replace("/", ",").split(",") if t.strip()]:
            if item not in ALLOWED_TEXTURE:
                problems.append(f"{name}: soil_texture '{item}' not in {sorted(ALLOWED_TEXTURE)}")

    if filled > 0 and not (row.get("source") or "").strip():
        problems.append(f"{name}: has values but no source")

    return problems, filled


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "plants.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total_problems = 0
    complete, partial, empty = [], [], []
    seen = set()

    for row in rows:
        name = row.get("common_name") or row.get("scientific_name") or "?"
        sci = (row.get("scientific_name") or "").strip().lower()
        if sci in seen:
            print(f"PROBLEM  {name}: duplicate scientific name")
            total_problems += 1
        seen.add(sci)

        problems, filled = check_row(row)
        for p in problems:
            print(f"PROBLEM  {p}")
        total_problems += len(problems)

        typical_pairs = sum(
            1 for _, prefix, _, _ in RANGES
            if (row.get(f"{prefix}_opt_min") or "").strip()
            and (row.get(f"{prefix}_opt_max") or "").strip()
        )
        if filled == 0:
            empty.append(name)
        elif typical_pairs == len(RANGES):
            complete.append(name)
        else:
            partial.append(name)

    print()
    print(f"{len(rows)} species in {path}")
    print(f"  complete (pH, rain and temp typical ranges): {len(complete)}")
    print(f"  partly filled:             {len(partial)}  {partial}")
    print(f"  not started:               {len(empty)}")
    print(f"  problems found:            {total_problems}")


if __name__ == "__main__":
    main()