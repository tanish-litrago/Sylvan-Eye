"""
Sylvan Eye - v2.1.0: how often does the claim guard accept or reject the local LLM on the saved places?

    python -m scripts.guard_stats                  # every saved fixture, model gemma4:e4b
    python -m scripts.guard_stats khapri hisar     # only these
    python -m scripts.guard_stats --model NAME

Needs Ollama running with the model pulled. It reads data/fixtures/*.json, asks the model for each
place that is not blocked (a blocked place never uses the LLM), and counts what explain() did with the
answer: accepted on the first try, accepted after the one retry, or fell back to the template text.
It changes nothing and writes nothing. One call can take minutes on a laptop.
"""

import glob
import os
import sys
import time

from phases.phase4_matcher import match_plants
from phases.phase5_explainer import OLLAMA_MODEL, OllamaExplainer, build_facts, explain
from scripts.fixtures import load_fixture
from tiers import order_by_tier

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.normpath(os.path.join(HERE, "..", "data", "fixtures"))


def classify(notes):
    """What explain() did, read from its notes."""
    rejected = [n for n in notes if "rejected:" in n]
    if notes and notes[-1].startswith("LLM answer rejected"):
        return "template (guard rejected both tries)"
    return "accepted after retry" if rejected else "accepted first try"


def measure_site(slug, explainer, folder=None):
    """(outcome, rejection reasons) for one saved place."""
    loaded = load_fixture(slug, folder)
    if loaded is None:
        return "no fixture", []
    _, env, terrain = loaded
    ranked, excluded, blank = match_plants(env)
    facts = build_facts(env, terrain, order_by_tier(ranked), excluded, blank)
    if facts["blocked"]:
        return "blocked (LLM not used)", []
    _, notes = explain(facts, explainer)
    return classify(notes), [n.split("rejected: ", 1)[1] for n in notes if "rejected: " in n]


def summarize(results):
    counts = {}
    for _, outcome, _ in results:
        counts[outcome] = counts.get(outcome, 0) + 1
    asked = sum(v for k, v in counts.items() if k.startswith(("accepted", "template")))
    return counts, asked


def main():
    argv, model, slugs = sys.argv[1:], OLLAMA_MODEL, []
    while argv:
        a = argv.pop(0)
        if a == "--model":
            model = argv.pop(0)
        else:
            slugs.append(a)
    slugs = slugs or [os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(os.path.join(FIXTURES, "*.json")))]
    explainer, results = OllamaExplainer(model=model), []
    for slug in slugs:
        started = time.time()
        outcome, reasons = measure_site(slug, explainer)
        results.append((slug, outcome, reasons))
        print(f"{slug:<18} {outcome:<38} {time.time() - started:5.0f} s")
        for r in reasons:
            print(f"    rejected: {r[:150]}")
    counts, asked = summarize(results)
    print(f"\nmodel {model}: asked for {asked} place(s)")
    for k, v in sorted(counts.items()):
        print(f"  {v:3d}  {k}")


if __name__ == "__main__":
    main()
