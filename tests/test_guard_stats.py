"""
Tests for the claim-guard measurement script, with a scripted explainer (no Ollama):
python -m tests.test_guard_stats
"""

from phases.phase5_explainer import build_facts, template_explanation
from phases.phase4_matcher import match_plants
from scripts import guard_stats as gs
from scripts.fixtures import load_fixture
from tiers import order_by_tier


class Scripted:
    """Gives the answers in order, then repeats the last one."""
    name = "scripted"
    truncated = False

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), 0

    def explain(self, system, user):
        i = min(self.calls, len(self.answers) - 1)
        self.calls += 1
        return self.answers[i]


def good_text(slug="khapri"):
    _, env, terrain = load_fixture(slug)
    ranked, excluded, blank = match_plants(env)
    return template_explanation(build_facts(env, terrain, order_by_tier(ranked), excluded, blank))


BAD = "Rubber tree 99999 is the best choice here."


def test_classify_reads_the_notes():
    assert gs.classify(["LLM-written text (x)."]) == "accepted first try"
    assert gs.classify(["attempt 1 rejected: a", "LLM-written text (x)."]) == "accepted after retry"
    assert gs.classify(["attempt 1 rejected: a", "attempt 2 rejected: b",
                        "LLM answer rejected, showing the deterministic text instead"]).startswith("template")


def test_measure_site_three_outcomes():
    ok = good_text()
    assert gs.measure_site("khapri", Scripted(ok))[0] == "accepted first try"
    outcome, reasons = gs.measure_site("khapri", Scripted(BAD, ok))
    assert outcome == "accepted after retry" and len(reasons) == 1
    outcome, reasons = gs.measure_site("khapri", Scripted(BAD))
    assert outcome.startswith("template") and len(reasons) == 2


def test_blocked_place_never_calls_the_model():
    fake = Scripted(BAD)
    assert gs.measure_site("bhopal-lake", fake)[0] == "blocked (LLM not used)" and fake.calls == 0
    assert gs.measure_site("no-such-place", fake)[0] == "no fixture"


def test_summarize_counts_only_places_that_asked_the_model():
    counts, asked = gs.summarize([("a", "accepted first try", []), ("b", "blocked (LLM not used)", []),
                                  ("c", "template (guard rejected both tries)", [])])
    assert asked == 2 and counts["blocked (LLM not used)"] == 1


if __name__ == "__main__":
    test_classify_reads_the_notes()
    test_measure_site_three_outcomes()
    test_blocked_place_never_calls_the_model()
    test_summarize_counts_only_places_that_asked_the_model()
    print("all guard_stats tests passed")
