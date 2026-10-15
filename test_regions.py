"""
Regression test on the Phase 7 sites:  python test_regions.py

Uses the saved measurements in fixtures/ (no Earth Engine). For every site in phase7_sites.json:
  status accepted     the system must match the (reviewed) expectations           -> else FAIL
  status known_issue  the documented miss must still be there                      -> else FAIL
                      (if it no longer reproduces, the system improved: update the status)
  status pending      no verdict yet, reported only
A site without a fixture is SKIPPED; run  python run_regions.py <slug>  to create it.
"""

import sys
import tempfile

import run_regions as rr
from fixtures import load_fixture


def evaluate(sites, fixtures_folder=None):
    """One result per site: slug, status, outcome, and the failed checks."""
    out = []
    for s in sites:
        status = s.get("status", "pending")
        loaded = load_fixture(s["slug"], fixtures_folder)
        if loaded is None:
            out.append({"slug": s["slug"], "status": status, "outcome": "SKIPPED", "failed": []})
            continue
        _, env, terrain = loaded
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = rr.run_site(s, fixtures_dir=tmp, run_live_fn=lambda *a, **k: (dict(env), terrain))
        failed = [c for c in rr.compare(s, result) if not c["ok"]]
        if status == "accepted":
            outcome = "ok" if not failed else "FAIL"
        elif status == "known_issue":
            outcome = "known issue still present" if failed else "FAIL (the known issue no longer reproduces: update status)"
        else:
            outcome = "pending" + (" (would match)" if not failed else " (would not match)")
        out.append({"slug": s["slug"], "status": status, "outcome": outcome, "failed": failed})
    return out


def main():
    results = evaluate(rr.load_sites())
    bad = 0
    for r in results:
        print(f"{r['slug']:<16} {r['status']:<12} {r['outcome']}")
        for c in r["failed"]:
            print(f"    - {c['what']}: expected {c['expected']}, got {c['actual']}")
        bad += r["outcome"].startswith("FAIL")
    ran = sum(r["outcome"] != "SKIPPED" for r in results)
    print(f"\n{ran} site(s) checked, {len(results) - ran} skipped, {bad} failed")
    if ran == 0:
        print("Nothing was tested: create the fixtures first (python run_regions.py).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
