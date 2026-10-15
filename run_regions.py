"""
Sylvan Eye, Phase 7: run the matcher on sites in several regions and compare the result with
what YOU expected, written down BEFORE the run.

    python run_regions.py                     all sites in phase7_sites.json
    python run_regions.py jaisalmer shimla    only the named sites (slugs)
    python run_regions.py --refresh           ignore the cache and measure again
    python run_regions.py --include-unverified   run sites whose coordinates you have not
                                                 checked (for a first look only)

The rules of the protocol (the script enforces them):
  * every site needs land_type (what you SEE there) and expect_gate (none, warning or blocked)
    filled in before it will run, so the expectation cannot be copied from the result;
  * coordinates must be marked "verified": true (checked on the satellite view);
  * plant names must be spelled as in plants.csv (a typo would silently never match).
Tip: commit phase7_sites.json before running. The commit time proves the order.

Output: phase7_report.md (expected against actual, per site) and fixtures/<slug>.json (the
measurements, so the site can become a regression test without Earth Engine).
A first run of a new site takes 1-2 minutes (Earth Engine); cached sites take seconds.
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import jobs
from fixtures import save_fixture
from phase4_matcher import CACHE_LOG
from phase4_matcher import run_live as REAL_RUN_LIVE

ROOT = Path(__file__).resolve().parent
SITES_FILE = ROOT / "phase7_sites.json"
REPORT_FILE = ROOT / "phase7_report.md"
GATES = ("none", "warning", "blocked")
REQUIRED = ("slug", "region", "name", "lat", "lon", "radius_m")
ENV_COLUMNS = [("annual_rainfall_mm", "Rain mm"), ("annual_mean_temp_c", "Temp C"), ("ph", "pH"),
               ("soil_texture", "Texture"), ("elevation_m", "Elev m")]


# ---------------------------------------------------------------- reading and checking the sites
def load_sites(path=SITES_FILE):
    return json.loads(Path(path).read_text(encoding="utf-8"))["sites"]


def plant_names():
    with open(ROOT / "plants.csv", newline="", encoding="utf-8") as f:
        return [row["common_name"] for row in csv.DictReader(f)]


def name_parts(full_name):
    """'Sissoo / Shisham' -> ['sissoo', 'shisham']; 'Bamboo (male bamboo)' -> ['bamboo']."""
    return [re.sub(r"\(.*?\)", "", p).strip().lower() for p in full_name.split("/")]


def name_matches(expected, full_name):
    e = expected.strip().lower()
    return e == full_name.strip().lower() or e in name_parts(full_name)


def problems_with(site, known_plants, include_unverified=False):
    """Everything that stops this site from being run. Empty list = ready."""
    out = []
    for key in REQUIRED:
        if key not in site:
            out.append(f"missing '{key}'")
    if site.get("expect_gate") not in GATES:
        out.append("expect_gate must be none, warning or blocked (write it BEFORE the run)")
    if not str(site.get("land_type", "")).strip():
        out.append("land_type is empty (what do you see at this point?)")
    if not site.get("verified") and not include_unverified:
        out.append("coordinates not verified on the satellite view (set verified to true)")
    for field in ("expect_plants", "expect_ruled_out", "expect_not_strong"):
        for name in site.get(field, []):
            if not any(name_matches(name, k) for k in known_plants):
                out.append(f"{field}: '{name}' is not a plant in plants.csv")
    return out


# ---------------------------------------------------------------- running and comparing
def run_site(site, refresh=False, fixtures_dir=None, run_live_fn=None):
    """Measure (or read from the cache), save the fixture, run the page's pipeline."""
    fn = run_live_fn or REAL_RUN_LIVE
    started = time.time()
    CACHE_LOG.clear()
    env, terrain = fn(site["lat"], site["lon"], site["radius_m"], True, refresh)
    cache = [list(e) for e in CACHE_LOG]
    save_fixture({k: site[k] for k in ("slug", "region", "name", "lat", "lon", "radius_m")},
                 env, terrain, date.today().isoformat(), folder=fixtures_dir)

    real = jobs.run_live
    jobs.run_live = lambda *a, **k: (dict(env), terrain)       # the page's code, on these measurements
    try:
        result = jobs.analyze({"lat": site["lat"], "lon": site["lon"], "radius_m": site["radius_m"],
                               "refresh": False, "demo": False})
    finally:
        jobs.run_live = real
    result["cache"] = cache
    return result, round(time.time() - started, 1)


def actual_gate(result):
    f = result["facts"]
    return "blocked" if f["blocked"] else ("warning" if f["warnings"] else "none")


def compare(site, result):
    """List of {what, expected, actual, ok}: your blind expectations against the result."""
    f = result["facts"]
    tiered = {t: [p["name"] for p in result["tiers"][t]] for t in result["tier_order"]}
    available = [n for names in tiered.values() for n in names]
    ruled_out = [o["name"] for o in f["ruled_out"]]
    checks = []

    got = actual_gate(result)
    checks.append({"what": "gate", "expected": site["expect_gate"], "actual": got, "ok": got == site["expect_gate"]})

    kw = str(site.get("expect_warning_contains", "")).strip()
    if kw:
        hit = any(kw.lower() in w.lower() for w in f["warnings"])
        checks.append({"what": f"a warning mentions '{kw}'", "expected": "yes", "actual": "yes" if hit else "no", "ok": hit})

    for name in site.get("expect_plants", []):
        hit = any(name_matches(name, n) for n in available)
        checks.append({"what": f"{name} is an option", "expected": "yes", "actual": "yes" if hit else "no", "ok": hit})
    for name in site.get("expect_ruled_out", []):
        hit = any(name_matches(name, n) for n in ruled_out)
        checks.append({"what": f"{name} is ruled out", "expected": "yes", "actual": "yes" if hit else "no", "ok": hit})
    for name in site.get("expect_not_strong", []):
        in_strong = any(name_matches(name, n) for n in tiered.get("strong", []))
        checks.append({"what": f"{name} is not Strong fit", "expected": "not strong",
                       "actual": "strong" if in_strong else "not strong", "ok": not in_strong})
    return checks


# ---------------------------------------------------------------- the report
def build_report(rows, run_date):
    ran = [r for r in rows if r["error"] is None]
    errors = [r for r in rows if r["error"] is not None]
    mism = [r for r in ran if not all(c["ok"] for c in r["checks"])]
    L = ["# Phase 7: regional test report", "",
         f"Run on {run_date}. {len(rows)} site(s): {len(ran) - len(mism)} matched your expectations, "
         f"{len(mism)} did not, {len(errors)} failed to run.", "",
         "Your expectations were written before the run (see the commit history of phase7_sites.json). "
         "A mismatch is a finding to review: either the system or the expectation is wrong.", "",
         "## Summary", "",
         "| Site | Region | Gate: you / system | " + " | ".join(h for _, h in ENV_COLUMNS) +
         " | Strong / Likely / Caution | Ruled out | Seconds | Result |",
         "|" + "---|" * (8 + len(ENV_COLUMNS))]
    for r in rows:
        s = r["site"]
        if r["error"] is not None:
            L.append(f"| {s['slug']} | {s['region']} | {s['expect_gate']} / - | " + " | ".join("-" for _ in ENV_COLUMNS) + " | - | - | - | ERROR |")
            continue
        res = r["result"]
        env = res["facts"]["environment"]
        vals = " | ".join("missing" if env.get(k) is None else str(env[k]) for k, _ in ENV_COLUMNS)
        t = res["tiers"]
        counts = " / ".join(str(len(t[x])) for x in res["tier_order"])
        ok = all(c["ok"] for c in r["checks"])
        L.append(f"| {s['slug']} | {s['region']} | {s['expect_gate']} / {actual_gate(res)} | {vals} | {counts} | "
                 f"{len(res['facts']['ruled_out'])} | {r['seconds']} | {'MATCH' if ok else 'MISMATCH'} |")

    L += ["", "## Mismatches to review", ""]
    if not mism and not errors:
        L.append("None. Every expectation matched.")
    for r in mism:
        L.append(f"### {r['site']['slug']} ({r['site']['name']})")
        for c in r["checks"]:
            if not c["ok"]:
                L.append(f"- {c['what']}: you expected **{c['expected']}**, the system gave **{c['actual']}**")
        L.append("")
    for r in errors:
        L += [f"### {r['site']['slug']}: ERROR", f"- {r['error']}", ""]

    missing = [(r["site"]["slug"], [h for k, h in ENV_COLUMNS if r["result"]["facts"]["environment"].get(k) is None])
               for r in ran]
    missing = [(s, m) for s, m in missing if m]
    L += ["## Data coverage", ""]
    L += [f"- {s}: no value for {', '.join(m)}" for s, m in missing] or ["Every measured value was present at every site."]

    L += ["", "## Site details", ""]
    for r in ran:
        s, res = r["site"], r["result"]
        f, t = res["facts"], res["tiers"]
        L += [f"### {s['slug']}: {s['name']} ({s['region']})",
              f"- Point {s['lat']}, {s['lon']}, radius {s['radius_m']} m. You saw: {s['land_type']}.",
              f"- {res['terrain_summary']}" if res.get("terrain_summary") else "- Terrain: not measured",
              f"- Cache: " + (", ".join(f"{a} {b}" for a, b in res["cache"]) or "none"),
              f"- Warnings: " + (" ".join(f["warnings"]) or "none")]
        for x in res["tier_order"]:
            L.append(f"- {res['tier_labels'][x]} ({len(t[x])}): " + (", ".join(p["name"] for p in t[x]) or "none"))
        L.append(f"- Ruled out ({len(f['ruled_out'])}): " + ("; ".join(f"{o['name']}: {o['reason']}" for o in f["ruled_out"]) or "none"))
        if f["not_assessed_no_data"]:
            L.append(f"- No data to assess: {', '.join(f['not_assessed_no_data'])}")
        L.append("- Your checks:")
        L += [f"  - [{'x' if c['ok'] else ' '}] {c['what']} (expected {c['expected']}, got {c['actual']})" for c in r["checks"]]
        L.append("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- command line
def main(argv=None, sites_path=SITES_FILE, report_path=REPORT_FILE, fixtures_dir=None, run_live_fn=None):
    ap = argparse.ArgumentParser(description="Phase 7 regional test runner")
    ap.add_argument("slugs", nargs="*", help="only these sites")
    ap.add_argument("--refresh", action="store_true", help="measure again, ignore the cache")
    ap.add_argument("--include-unverified", action="store_true", help="also run sites not marked verified")
    ap.add_argument("--report", help="write the report here instead of phase7_report.md (use it when re-running a few sites)")
    args = ap.parse_args(argv)

    sites = load_sites(sites_path)
    known = {s["slug"] for s in sites}
    unknown = set(args.slugs) - known
    if unknown:
        print("Unknown site(s):", ", ".join(sorted(unknown)), "| known:", ", ".join(sorted(known)))
        return 2
    wanted = [s for s in sites if not args.slugs or s["slug"] in args.slugs]

    plants = plant_names()
    bad = {s.get("slug", "?"): problems_with(s, plants, args.include_unverified) for s in wanted}
    bad = {k: v for k, v in bad.items() if v}
    if bad:
        print("Nothing was run. Fix these first (or run only the ready sites by naming them):\n")
        for slug, issues in bad.items():
            print(f"  {slug}")
            for i in issues:
                print(f"    - {i}")
        return 2

    rows = []
    for s in wanted:
        print(f"{s['slug']:<22} {s['name']} ... ", end="", flush=True)
        try:
            result, seconds = run_site(s, args.refresh, fixtures_dir, run_live_fn)
            row = {"site": s, "result": result, "error": None, "seconds": seconds, "checks": compare(s, result)}
            print("MATCH" if all(c["ok"] for c in row["checks"]) else "MISMATCH", f"({seconds} s)")
        except Exception as e:
            row = {"site": s, "result": None, "error": f"{type(e).__name__}: {e}", "seconds": 0, "checks": []}
            print("ERROR:", row["error"])
        rows.append(row)

    report_path = args.report or report_path
    Path(report_path).write_text(build_report(rows, date.today().isoformat()), encoding="utf-8")
    print(f"\nReport written to {report_path}")
    return 1 if any(r["error"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())