"""
Sylvan Eye — Phase 3: plant database validator.

Checks plants.csv for mistakes while you fill it in from ECOCROP datasheets.
It never edits the file and never guesses values.

Run:  python validate_plants.py            (checks plants.csv)
      python validate_plants.py my.csv     (checks another file)

Rules checked for each of pH, rainfall and temperature:
    abs_min <= opt_min <= opt_max <= abs_max
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
        parts = [values[f"{prefix}_{k}"] for k in ("abs_min", "opt_min", "opt_max", "abs_max")]
        present = [p for p in parts if p is not None]
        if not present:
            continue
        if len(present) < 4:
            problems.append(f"{name}: {label} is only partly filled ({len(present)}/4 values)")
            continue
        if not (parts[0] <= parts[1] <= parts[2] <= parts[3]):
            problems.append(
                f"{name}: {label} must satisfy abs_min <= opt_min <= opt_max <= abs_max, "
                f"got {parts}"
            )
        if parts[0] < low or parts[3] > high:
            problems.append(f"{name}: {label} has a value outside {low} to {high}: {parts}")

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

        if filled == 0:
            empty.append(name)
        elif filled == len(NUMERIC_COLUMNS):
            complete.append(name)
        else:
            partial.append(name)

    print()
    print(f"{len(rows)} species in {path}")
    print(f"  complete (all 12 numbers): {len(complete)}")
    print(f"  partly filled:             {len(partial)}  {partial}")
    print(f"  not started:               {len(empty)}")
    print(f"  problems found:            {total_problems}")


if __name__ == "__main__":
    main()
