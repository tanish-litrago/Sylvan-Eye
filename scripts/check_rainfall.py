"""
Sylvan Eye - v1.2.0: compares the rainfall the pipeline saved for each test site with published
station or district normals (rainfall_reference.csv, every value with its source URL).

    python -m scripts.check_rainfall

Offline: it reads data/fixtures/*.json and data/rainfall_reference.csv. It changes nothing.
This is a check of the climate source, not a rule: nothing here feeds the matcher.

How to read it: the pipeline value is a 2015-2024 average from a coarse grid; the references are
long-term averages (district or station), so differences of 30-50% are normal. Bands (pipeline
divided by reference):
    0.67x to 1.5x    ok
    1.5x to 2x       high    (or "low" below 0.67x)
    above 2x         FAR OFF (or "FAR LOW" below 0.5x)
These bands are a first guess for reading the table, not a rule used anywhere else.
"""

import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))


def load_reference(path=None):
    """Return {fixture_stem: row_dict}. A fixture listed twice is an error."""
    path = path or os.path.join(DATA, "rainfall_reference.csv")
    by_fixture = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for stem in [s.strip() for s in row["fixtures"].split(";") if s.strip()]:
                if stem in by_fixture:
                    raise ValueError(f"fixture '{stem}' is listed in two reference rows")
                by_fixture[stem] = row
    return by_fixture


def load_pipeline(fixture_dir=None):
    """Return {fixture_stem: (site name, annual rainfall mm)}."""
    fixture_dir = fixture_dir or os.path.join(DATA, "fixtures")
    out = {}
    for path in sorted(glob.glob(os.path.join(fixture_dir, "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        stem = os.path.splitext(os.path.basename(path))[0]
        out[stem] = (d["site"]["name"], d["env"].get("annual_rainfall_mm"))
    return out


def band(ratio):
    if ratio is None:
        return "no reference"
    if ratio > 2:
        return "FAR OFF"
    if ratio < 0.5:
        return "FAR LOW"
    if ratio > 1.5:
        return "high"
    if ratio < 2 / 3:
        return "low"
    return "ok"


def compare(pipeline, reference):
    """List of dicts, one per fixture, in fixture order."""
    rows = []
    for stem, (name, mm) in pipeline.items():
        ref = reference.get(stem)
        ref_mm = float(ref["reference_mm"]) if ref and ref["reference_mm"] else None
        alt_mm = float(ref["alt_mm"]) if ref and ref["alt_mm"] else None
        ratio = (mm / ref_mm) if (ref_mm and mm is not None) else None
        alt_ratio = (mm / alt_mm) if (alt_mm and mm is not None) else None
        rows.append({"fixture": stem, "name": name, "pipeline_mm": mm, "reference_mm": ref_mm,
                     "ratio": ratio, "band": band(ratio), "alt_mm": alt_mm, "alt_ratio": alt_ratio,
                     "place": ref["place"] if ref else ""})
    return rows


def main():
    rows = compare(load_pipeline(), load_reference())
    print(f"{'site':32s} {'pipeline':>8s} {'reference':>9s} {'ratio':>6s}  {'verdict':8s} second source")
    for r in rows:
        ref = f"{r['reference_mm']:.0f}" if r["reference_mm"] else "-"
        ratio = f"{r['ratio']:.2f}" if r["ratio"] else "-"
        alt = f"{r['alt_mm']:.0f} mm ({r['alt_ratio']:.2f}x)" if r["alt_mm"] else ""
        print(f"{r['name'][:32]:32s} {r['pipeline_mm']!s:>8s} {ref:>9s} {ratio:>6s}  {r['band']:8s} {alt}")
    print()
    print("Pipeline = Open-Meteo archive 2015-2024 (saved in fixtures/). Reference = published normals;")
    print("sources and notes per place are in rainfall_reference.csv.")


if __name__ == "__main__":
    main()
