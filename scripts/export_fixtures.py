"""
Save the measurements for the test sites as data/fixtures/<slug>.json (see scripts/fixtures.py).

    python -m scripts.export_fixtures             all sites
    python -m scripts.export_fixtures khapri      only the named site(s) (the slugs are in fixtures.py)

Uses the cache, so a site you have already analysed takes seconds. A site that is not in the
cache needs Earth Engine and takes 1-2 minutes. One failing site does not stop the others.
"""

import sys
from datetime import date

from scripts.fixtures import SITES, save_fixture
from phases.phase4_matcher import CACHE_LOG, run_live


def main(wanted):
    sites = [s for s in SITES if not wanted or s["slug"] in wanted]
    unknown = set(wanted) - {s["slug"] for s in SITES}
    if unknown:
        print("Unknown site name(s):", ", ".join(sorted(unknown)))
        print("Known:", ", ".join(s["slug"] for s in SITES))
        return 1

    ok, failed = 0, []
    for s in sites:
        print(f"{s['slug']:<15} {s['name']} ({s['radius_m']} m) ... ", end="", flush=True)
        try:
            env, terrain = run_live(s["lat"], s["lon"], s["radius_m"], True, False)
            path = save_fixture(s, env, terrain, date.today().isoformat())
            status = ", ".join(f"{name} {st}" for name, st in CACHE_LOG if name != "store")
            print(f"saved ({status})")
            ok += 1
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            failed.append(s["slug"])
    print(f"\n{ok} saved, {len(failed)} failed" + (": " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
