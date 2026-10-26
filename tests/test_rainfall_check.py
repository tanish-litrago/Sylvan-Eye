"""
Tests for rainfall_reference.csv and check_rainfall.py.   python -m tests.test_rainfall_check
Offline: reads the saved fixtures and the CSV only.
"""

import csv
import glob
import os

from scripts import check_rainfall as cr

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))


# v2.0.0: the 12 places added in the second Phase 7 round have no reference page checked yet. The check
# script shows them as "no reference" (it never guesses). Each one leaves this set when it gets a row in
# rainfall_reference.csv with a source that was opened, and the test below insists on that.
# v2.1.0: Dive Ghat still has no page I could open. The 5 round-3 places below are new and not yet looked up;
# Kuderu and Kakdwip share the district rows of Anantapur and Sundarbans (same districts).
NOT_YET_REFERENCED = {"dive-ghat", "bellare", "mohali-sohana", "pirangut", "sandila", "kalimpong"}


def test_every_reference_row_has_a_source_and_a_number():
    with open(os.path.join(DATA, "rainfall_reference.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 10
    for r in rows:
        assert r["source_url"].startswith("https://"), r["place"]
        assert r["basis"].strip(), r["place"]
        assert float(r["reference_mm"]) > 0, r["place"]
        if r["alt_mm"].strip():                       # a second value needs its own source
            assert float(r["alt_mm"]) > 0 and r["alt_url"].startswith("https://"), r["place"]


def test_every_fixture_is_covered_once():
    ref = cr.load_reference()            # raises if a fixture is listed in two rows
    stems = {os.path.splitext(os.path.basename(p))[0]
             for p in glob.glob(os.path.join(DATA, "fixtures", "*.json"))}
    assert stems, "no fixtures found"
    assert (stems - set(ref)) - NOT_YET_REFERENCED == set(), f"fixtures without a reference: {(stems - set(ref)) - NOT_YET_REFERENCED}"
    assert NOT_YET_REFERENCED & set(ref) == set(), "has a reference now: remove it from NOT_YET_REFERENCED"
    assert set(ref) - stems == set(), f"reference rows naming a missing fixture: {set(ref) - stems}"


def test_bands():
    assert cr.band(None) == "no reference"
    assert cr.band(1.0) == "ok" and cr.band(1.5) == "ok" and cr.band(0.67) == "ok"
    assert cr.band(1.6) == "high" and cr.band(0.6) == "low"
    assert cr.band(2.1) == "FAR OFF" and cr.band(0.4) == "FAR LOW"


def test_leh_is_far_off_and_nothing_else_is():
    rows = {r["fixture"]: r for r in cr.compare(cr.load_pipeline(), cr.load_reference())}
    assert rows["leh"]["band"] == "FAR OFF" and rows["leh"]["ratio"] > 5
    # v2.1.0: a second known case. The weather grid smooths Cherrapunji's one-valley rainfall peak.
    assert rows["cherrapunji"]["band"] == "FAR LOW", rows["cherrapunji"]
    # v2.1.0: Pampore on the Kashmir valley floor; the grid reads about twice the district figure.
    assert rows["pampore"]["band"] == "FAR OFF", rows["pampore"]
    known = ("leh", "cherrapunji", "pampore")
    others = [r["fixture"] for r in rows.values()
              if r["fixture"] not in known and r["fixture"] not in NOT_YET_REFERENCED and r["band"] != "ok"]
    assert others == [], others          # if this changes, the saved data or the references changed


def test_missing_reference_is_reported_not_guessed():
    rows = cr.compare({"x": ("Somewhere", 500)}, {})
    assert rows[0]["band"] == "no reference" and rows[0]["ratio"] is None


def test_duplicate_fixture_is_an_error(tmp_path=None):
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "r.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["place", "fixtures", "reference_mm", "basis", "source_url", "alt_mm", "alt_basis",
                    "alt_url", "note"])
        w.writerow(["A", "leh", 100, "b", "https://x", "", "", "", ""])
        w.writerow(["B", "leh", 200, "b", "https://x", "", "", "", ""])
    try:
        cr.load_reference(p)
        assert False, "should have raised"
    except ValueError:
        pass


if __name__ == "__main__":
    test_every_reference_row_has_a_source_and_a_number()
    test_every_fixture_is_covered_once()
    test_bands()
    test_leh_is_far_off_and_nothing_else_is()
    test_missing_reference_is_reported_not_guessed()
    test_duplicate_fixture_is_an_error()
    print("all rainfall check tests passed")