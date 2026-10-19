"""
Tests for the high-mountain rainfall note (v1.2.0).   python -m tests.test_altitude_note
Offline: uses the saved fixtures. The note is a limit line only; nothing else may change.
"""

import re

from phases import phase5_explainer as p5
from scripts.fixtures import load_fixture
from phases.phase4_matcher import match_plants

from tests import test_fixtures
def facts_for(slug):
    return test_fixtures.analyse(slug)["facts"]


def test_note_shows_at_leh_and_shimla_only():
    for slug in ("leh", "shimla"):
        f = facts_for(slug)
        assert f["limits"][0] == p5.HIGH_ALTITUDE_LIMIT, slug
        assert f["limits"][1:] == p5.LIMITS, slug
    for slug in ("bhopal-lake", "city-centre", "jagdalpur", "solapur", "puri"):
        assert facts_for(slug)["limits"] == p5.LIMITS, slug


def test_threshold_is_inclusive_and_missing_elevation_is_safe():
    assert p5.limits_for({"elevation_m": 1999.9}) == p5.LIMITS
    assert p5.limits_for({"elevation_m": 2000})[0] == p5.HIGH_ALTITUDE_LIMIT
    assert p5.limits_for({}) == p5.LIMITS and p5.limits_for(None) == p5.LIMITS
    assert p5.limits_for({"elevation_m": None}) == p5.LIMITS
    assert p5.LIMITS == p5.limits_for({"elevation_m": 100})      # the shared list is never modified


def test_note_is_safe_for_the_claim_guard():
    assert not re.search(r"\d", p5.HIGH_ALTITUDE_LIMIT), "the guard compares numbers: keep digits out"
    assert not re.search(r"altitude|elevation", p5.HIGH_ALTITUDE_LIMIT, re.I)


def full_facts(slug):
    """The complete fact sheet (the page only gets part of it), built the way jobs.py builds it."""
    site, env, terrain = load_fixture(slug)
    ranked, excluded, blank = match_plants(env)
    return p5.build_facts(env, terrain, ranked, excluded, blank)


def test_the_note_changes_nothing_but_the_limits():
    """Switch the note off (threshold far above any mountain) and compare the whole fact sheet."""
    with_note = full_facts("leh")
    saved = p5.HIGH_ALTITUDE_M
    p5.HIGH_ALTITUDE_M = 10 ** 9
    try:
        without = full_facts("leh")
    finally:
        p5.HIGH_ALTITUDE_M = saved
    assert with_note["limits"][0] == p5.HIGH_ALTITUDE_LIMIT and without["limits"] == p5.LIMITS
    a, b = dict(with_note), dict(without)
    a.pop("limits"); b.pop("limits")
    assert a == b, "the note must not change the shortlist, ruled-out list, warnings or gate"


def test_template_text_and_a_faithful_llm_answer_both_carry_the_note():
    f = full_facts("leh")
    text = p5.template_explanation(f)
    assert "Leh" in text and "rainfall records" in text

    class Faithful:
        name = "fake"
        def explain(self, system, user):
            return p5.template_explanation(f)

    out, notes = p5.explain(f, Faithful())
    assert notes and notes[0].startswith("LLM-written text"), notes     # the guard accepted it


if __name__ == "__main__":
    test_note_shows_at_leh_and_shimla_only()
    test_threshold_is_inclusive_and_missing_elevation_is_safe()
    test_note_is_safe_for_the_claim_guard()
    test_the_note_changes_nothing_but_the_limits()
    test_template_text_and_a_faithful_llm_answer_both_carry_the_note()
    print("all altitude note tests passed")
