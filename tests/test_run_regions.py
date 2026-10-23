"""
Tests for run_regions.py, with a fake run_live and temporary files:  python -m tests.test_run_regions
"""

import json
import tempfile
from pathlib import Path

from scripts import run_regions as rr
from phases.phase4_matcher import CACHE_LOG, DEMO_ENV

PLANTS = rr.plant_names()


def base(slug, **kw):
    s = {"slug": slug, "region": "Test", "name": slug, "lat": 20.0, "lon": 80.0, "radius_m": 400,
         "verified": True, "land_type": "open land", "expect_gate": "none"}
    s.update(kw)
    return s


def terrain(water=0.0):
    return {"land_cover_fractions": {"water_or_wet_surface": water, "bare_or_built": 0.0,
            "sparse_vegetation_or_crops": 0.3, "dense_vegetation": 0.6},
            "seasonality": {"ndvi_dry_p10_mean": 0.3, "ndvi_peak_p90_mean": 0.7, "big_swing_fraction": 0.1, "big_swing_by_year": {}},
            "vegetation": {}, "location": {"radius_m": 400}, "terrain": {"elevation_m": 269.4}}


def fake_run_live(lat, lon, radius_m, use_cache, refresh):
    CACHE_LOG.append(("store", "sqlite"))
    CACHE_LOG.append(("terrain", "miss"))
    if lat == 1.0:
        raise RuntimeError("earth engine says no")
    env = dict(DEMO_ENV)
    if lat == 3.0:
        env["ph"] = None
    t = terrain(water=0.6 if lat == 2.0 else 0.0)
    if lat == 20.0:
        t["footprints"] = {"share": 0.0564, "polygons": 264, "coverage": "ok"}
    if lat == 3.0:
        t["footprints"] = {"share": None, "coverage": "no_data"}
    return env, t


def run(sites, extra=()):
    tmp = Path(tempfile.mkdtemp())
    sites_path = tmp / "sites.json"
    sites_path.write_text(json.dumps({"sites": sites}), encoding="utf-8")
    code = rr.main(list(extra), sites_path=sites_path, report_path=tmp / "report.md",
                   fixtures_dir=tmp / "fx", run_live_fn=fake_run_live)
    report = (tmp / "report.md").read_text(encoding="utf-8") if (tmp / "report.md").exists() else None
    return code, report, tmp


def test_name_matching():
    assert rr.name_matches("Sal", "Sal")
    assert not rr.name_matches("Sal", "Salai / Indian frankincense")     # not a substring match
    assert rr.name_matches("Salai", "Salai / Indian frankincense")
    assert rr.name_matches("shisham", "Sissoo / Shisham")
    assert rr.name_matches("Bamboo", "Bamboo (male bamboo)")
    assert rr.name_matches("chir pine", "Chir pine")


def test_unready_sites_are_refused_with_reasons():
    ok = base("ok")
    assert rr.problems_with(ok, PLANTS) == []
    assert any("expect_gate" in p for p in rr.problems_with(base("a", expect_gate=""), PLANTS))
    assert any("land_type" in p for p in rr.problems_with(base("a", land_type=" "), PLANTS))
    assert any("verified" in p for p in rr.problems_with(base("a", verified=False), PLANTS))
    assert rr.problems_with(base("a", verified=False), PLANTS, include_unverified=True) == []
    assert any("Khejrii" in p for p in rr.problems_with(base("a", expect_plants=["Khejrii"]), PLANTS))
    assert any("missing 'lat'" in p for p in rr.problems_with({k: v for k, v in base("a").items() if k != "lat"}, PLANTS))


def test_nothing_runs_if_any_site_is_not_ready():
    code, report, tmp = run([base("good"), base("bad", expect_gate="")])
    assert code == 2 and report is None and not (tmp / "fx").exists()


def test_match_mismatch_error_and_report():
    sites = [
        base("clean", lat=20.0, expect_gate="none", expect_plants=["Moringa"], expect_ruled_out=["Khejri"],
             expect_not_strong=["Amaltas"]),
        base("lake", lat=2.0, expect_gate="blocked"),
        base("wrong-guess", lat=2.5, expect_gate="none"),                # the system will say none: matches
        base("wrong-guess-2", lat=2.0, expect_gate="none"),              # same lake, wrong expectation
        base("boom", lat=1.0, expect_gate="none"),
        base("no-ph", lat=3.0, expect_gate="none"),
    ]
    code, report, tmp = run(sites)
    assert code == 1                                                    # one site failed to run
    assert "5 site(s)" not in report and "6 site(s)" in report
    assert "| clean |" in report and "MATCH" in report
    assert "### wrong-guess-2" in report and "you expected **none**, the system gave **blocked**" in report
    assert "### boom: ERROR" in report and "earth engine says no" in report
    assert "no-ph: no value for pH" in report                           # data coverage section
    assert "Outlines (share, count)" in report                          # v2.0.0: the extra number is in the table
    clean_row = next(l for l in report.splitlines() if l.startswith("| clean |"))
    assert "5.6% (264)" in clean_row
    assert "no data" in next(l for l in report.splitlines() if l.startswith("| no-ph |"))
    assert "| - |" in next(l for l in report.splitlines() if l.startswith("| lake |"))   # not measured
    assert "Building outlines (extra, not used for matching): 5.6% (264)" in report
    assert "Warnings: " in report and "BLOCKED" in report              # details of the lake
    # fixtures saved for the sites that ran, not for the one that failed
    assert (tmp / "fx" / "clean.json").exists() and (tmp / "fx" / "lake.json").exists()
    assert not (tmp / "fx" / "boom.json").exists()
    saved = json.loads((tmp / "fx" / "lake.json").read_text(encoding="utf-8"))
    assert saved["terrain"]["land_cover_fractions"]["water_or_wet_surface"] == 0.6


def test_blocked_site_expectations_about_plants_fail_honestly():
    code, report, _ = run([base("lake", lat=2.0, expect_gate="blocked", expect_plants=["Neem"])])
    assert code == 0 and "MISMATCH" in report and "Neem is an option" in report


def test_only_named_sites_and_unknown_names():
    code, report, _ = run([base("a"), base("b", expect_gate="")], extra=["a"])
    assert code == 0 and "| a |" in report and "| b |" not in report
    code, report, _ = run([base("a")], extra=["nope"])
    assert code == 2 and report is None


def test_report_option_writes_to_another_file():
    tmp = Path(tempfile.mkdtemp())
    sites_path = tmp / "sites.json"
    sites_path.write_text(json.dumps({"sites": [base("a")]}), encoding="utf-8")
    code = rr.main(["--report", str(tmp / "other.md")], sites_path=sites_path, report_path=tmp / "main.md",
                   fixtures_dir=tmp / "fx", run_live_fn=fake_run_live)
    assert code == 0 and (tmp / "other.md").exists() and not (tmp / "main.md").exists()


def test_regression_harness_statuses():
    from tests import test_regions as tr
    from scripts import fixtures
    tmp = Path(tempfile.mkdtemp())
    for slug, water in (("good", 0.0), ("lake", 0.6), ("lake2", 0.6), ("good2", 0.0), ("pend", 0.0)):
        fixtures.save_fixture({"slug": slug}, dict(DEMO_ENV), terrain(water), "2026-10-14", folder=tmp)
    sites = [base("good", status="accepted"), base("lake", status="accepted"),
             base("lake2", status="known_issue"), base("good2", status="known_issue"),
             base("nofixture", status="accepted"), base("pend", status="pending")]
    res = {r["slug"]: r["outcome"] for r in tr.evaluate(sites, tmp)}
    assert res["good"] == "ok" and res["lake"] == "FAIL"                  # accepted: must match
    assert res["lake2"] == "known issue still present"                    # known issue: miss persists
    assert res["good2"].startswith("FAIL")                                # known issue no longer reproduces
    assert res["nofixture"] == "SKIPPED" and res["pend"].startswith("pending")


if __name__ == "__main__":
    test_name_matching()
    test_unready_sites_are_refused_with_reasons()
    test_nothing_runs_if_any_site_is_not_ready()
    test_match_mismatch_error_and_report()
    test_blocked_site_expectations_about_plants_fail_honestly()
    test_only_named_sites_and_unknown_names()
    test_report_option_writes_to_another_file()
    test_regression_harness_statuses()
    print("all run_regions tests passed")