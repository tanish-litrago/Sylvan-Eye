"""
Tests for tiers.py. Plain asserts, no test framework:  python test_tiers.py
"""

from phase4_matcher import DEMO_ENV, match_plants
from tiers import SCORED, TIER_ORDER, group_by_tier, order_by_tier, tier_for


def entry(**verdicts):
    """A minimal matcher entry. Unnamed factors default to 'good'."""
    factors = {f: (verdicts.get(f, "good"), "reason") for f in SCORED}
    factors["elevation"] = ("ok", "reason")
    return {"name": "X", "scientific_name": "x x", "factors": factors,
            "confidence_n": 5, "flags": []}


def test_rules():
    assert tier_for(entry())[0] == "strong"
    assert tier_for(entry(rainfall="within_limits"))[0] == "strong"
    assert tier_for(entry(pH=None))[0] == "likely"
    assert tier_for(entry(pH=None, texture=None))[0] == "likely"
    assert tier_for(entry(rainfall="marginal"))[0] == "caution"
    assert tier_for(entry(texture="poor"))[0] == "caution"
    # flagged wins over missing, and the reason still mentions both
    tier, reason = tier_for(entry(rainfall="marginal", pH=None))
    assert tier == "caution" and "marginal rainfall" in reason and "pH" in reason
    # an unknown verdict is a flag, never a pass
    assert tier_for(entry(rainfall="something_new"))[0] == "caution"


def test_elevation_does_not_change_tier():
    e = entry()
    e["factors"]["elevation"] = (None, "no altitude data for this plant")
    assert tier_for(e)[0] == "strong"


def test_grouping_on_demo_data():
    ranked, excluded, blank = match_plants(dict(DEMO_ENV))
    before = [dict(e) for e in ranked]
    groups = group_by_tier(ranked)

    assert list(groups) == list(TIER_ORDER)
    # every ranked plant lands in exactly one tier
    names = [p["name"] for t in TIER_ORDER for p in groups[t]]
    assert sorted(names) == sorted(e["name"] for e in ranked)
    assert len(names) == len(set(names))
    # no flagged plant is ever in strong or likely
    for t in ("strong", "likely"):
        for p in groups[t]:
            for k in SCORED:
                assert p["checks"][k]["result"] in ("good", "within_limits", "skipped")
    # strong plants have no skipped check
    for p in groups["strong"]:
        assert all(p["checks"][k]["result"] != "skipped" for k in SCORED)
    # alphabetical inside a tier, and the input list is untouched
    for t in TIER_ORDER:
        assert [p["name"] for p in groups[t]] == sorted(p["name"] for p in groups[t])
    assert ranked == before


def test_order_by_tier():
    ranked, _, _ = match_plants(dict(DEMO_ENV))
    ordered = order_by_tier(ranked)
    assert sorted(e["name"] for e in ordered) == sorted(e["name"] for e in ranked)
    tiers_in_order = [tier_for(e)[0] for e in ordered]
    assert tiers_in_order == sorted(tiers_in_order, key=TIER_ORDER.index)   # never goes backwards
    for t in TIER_ORDER:
        names = [e["name"] for e in ordered if tier_for(e)[0] == t]
        assert names == sorted(names)


if __name__ == "__main__":
    test_rules()
    test_elevation_does_not_change_tier()
    test_grouping_on_demo_data()
    test_order_by_tier()
    print("all tier tests passed")