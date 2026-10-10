"""
Sylvan Eye — Phase 6, step 1: tiers.

The matcher gives every plant that is not ruled out a verdict on four scored factors
(rainfall, temperature, pH, texture). Many plants tie on the numeric score because a
missing value and a marginal fit both count as 0.5, so a ranked list shows an order the
data cannot support. This module groups plants into three tiers instead. It is part of
the RULE layer: the web page only displays what this module decides.

    strong   all four factors have data, and every one is good or within_limits
    likely   nothing is marginal or poor, but at least one of the four has no data
             (nothing wrong was found, but it is not fully verified)
    caution  at least one factor is marginal or poor (something was flagged)

Elevation is not part of the tier: it only rules plants out (that already happened in
match_plants), exactly as it is outside the numeric score.

A verdict this module does not know is treated as a flag, never as a pass, so a new
verdict added to the matcher later cannot silently put a plant in "strong".

Run:
    python tiers.py --demo     offline, uses the measured Bilaspur values
"""

import sys

SCORED = ("rainfall", "temperature", "pH", "texture")
CLEAN = {"good", "within_limits"}

TIER_ORDER = ("strong", "likely", "caution")
TIER_LABELS = {
    "strong": "Strong fit",
    "likely": "Likely, not fully verified",
    "caution": "Caution",
}

TIER_DESCRIPTIONS = {
    "strong": "All four checks (rainfall, temperature, pH, texture) have data and none is marginal or poor.",
    "likely": "Nothing is marginal or poor, but at least one check has no data, so it is not fully verified.",
    "caution": "At least one check is marginal or poor.",
}


def tier_for(entry):
    """Return (tier, reason) for one matcher entry (one item of match_plants()'s 'ranked')."""
    verdicts = {f: entry["factors"][f][0] for f in SCORED}
    flagged = [f"{v} {f}" for f, v in verdicts.items() if v is not None and v not in CLEAN]
    missing = [f for f, v in verdicts.items() if v is None]

    if flagged:
        reason = "flagged: " + ", ".join(flagged)
        if missing:
            reason += "; no data: " + ", ".join(missing)
        return "caution", reason
    if missing:
        return "likely", "no data: " + ", ".join(missing)
    return "strong", "all four checks have data and none is flagged"


def group_by_tier(ranked):
    """
    Group the matcher's 'ranked' list into tiers. Returns
    {"strong": [...], "likely": [...], "caution": [...]}, each plant as a dict with its
    per-factor checks. Inside a tier the order is alphabetical on purpose: there is no rank
    to show, because the data cannot separate these plants. The input is not modified.
    """
    groups = {t: [] for t in TIER_ORDER}
    for e in ranked:
        tier, reason = tier_for(e)
        groups[tier].append({
            "name": e["name"],
            "scientific_name": e["scientific_name"],
            "tier_reason": reason,
            "factors_with_data": f"{e['confidence_n']} of 5",
            "checks": {k: {"result": v or "skipped", "detail": why}
                       for k, (v, why) in e["factors"].items()},
            "flags": e["flags"],
        })
    for plants in groups.values():
        plants.sort(key=lambda p: p["name"])
    return groups


def order_by_tier(ranked):
    """
    The matcher's own entries (not copies), in tier order: strong, then likely, then caution,
    alphabetical inside a tier. Used to build the fact sheet that feeds the plain-words text,
    so the text names the best-supported plants first instead of an arbitrary order among ties.
    """
    rank = {t: i for i, t in enumerate(TIER_ORDER)}
    return sorted(ranked, key=lambda e: (rank[tier_for(e)[0]], e["name"]))


def main():
    from phase4_matcher import DEMO_ENV, match_plants
    ranked, excluded, blank = match_plants(dict(DEMO_ENV))
    groups = group_by_tier(ranked)
    for t in TIER_ORDER:
        print(f"\n{TIER_LABELS[t]} ({len(groups[t])})")
        for p in groups[t]:
            print(f"  {p['name']:<22} {p['tier_reason']}")
    print(f"\nRuled out: {len(excluded)}   No data at all: {len(blank)}")


if __name__ == "__main__":
    if "--demo" not in sys.argv:
        print("Only the offline demo is available here: python tiers.py --demo")
        sys.exit(1)
    main()