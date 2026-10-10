"""
Tests for jobs.py. Plain asserts, no network, no Earth Engine:  python test_jobs.py
run_live is replaced by a fake that we control step by step with threading Events.
"""

import json
import threading
import time

import jobs
from phase4_matcher import CACHE_LOG, DEMO_ENV, match_plants
from phase5_explainer import template_explanation

REAL_RUN_LIVE = jobs.run_live


def params(**kw):
    p = {"lat": 22.0797, "lon": 82.1409, "radius_m": 400, "refresh": False, "demo": False}
    p.update(kw)
    return p


def fake_terrain(water=0.05):
    return {
        "land_cover_fractions": {"water_or_wet_surface": water, "bare_or_built": 0.05,
                                 "sparse_vegetation_or_crops": 0.3, "dense_vegetation": 0.6},
        "seasonality": {"ndvi_dry_p10_mean": 0.3, "ndvi_peak_p90_mean": 0.7,
                        "big_swing_fraction": 0.1, "big_swing_by_year": {}},
        "vegetation": {}, "location": {"radius_m": 400}, "terrain": {"elevation_m": 269.4},
    }


def wait_for(job_id, states, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = jobs.get_job(job_id)
        if v["state"] in states:
            return v
        time.sleep(0.01)
    raise AssertionError(f"job never reached {states}; last view: {jobs.get_job(job_id)}")


def wait_stage(job_id, stage_part, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = jobs.get_job(job_id)
        if stage_part in v["stage"]:
            return v
        time.sleep(0.01)
    raise AssertionError(f"stage never contained {stage_part!r}; last: {jobs.get_job(job_id)}")


def test_demo_job_runs_offline():
    v = wait_for(jobs.start_job(params(demo=True)), {"done", "error"})
    assert v["state"] == "done", v
    r = v["result"]
    ranked, _, _ = match_plants(dict(DEMO_ENV))
    assert sum(len(r["tiers"][t]) for t in r["tier_order"]) == len(ranked)
    assert r["facts"]["blocked"] is False
    assert "shortlist" not in r["facts"]            # the page shows tiers, not the score order
    assert r["facts"]["limits"] and r["facts"]["ruled_out"] is not None
    assert r["explanation"]["source"] == "template"
    assert set(r["tier_descriptions"]) == set(r["tier_order"])
    assert r["location"]["demo"] is True and r["terrain_summary"] is None
    # the plain-words text names the strong plant before any "caution" plant
    text = r["explanation"]["text"]
    strong = [p["name"] for p in r["tiers"]["strong"]]
    caution = [p["name"] for p in r["tiers"]["caution"]]
    assert strong and text.index(strong[0]) < min((text.index(c) for c in caution if c in text), default=10**9)


def test_unknown_job_is_none():
    assert jobs.get_job("nope") is None


def test_stages_follow_the_log_and_result_carries_cache():
    gate_terrain, gate_soil = threading.Event(), threading.Event()

    def fake(lat, lon, radius_m, use_cache, refresh):
        CACHE_LOG.append(("store", "sqlite"))
        gate_terrain.wait(5)
        CACHE_LOG.append(("terrain", "miss"))
        gate_soil.wait(5)
        CACHE_LOG.append(("soil", "hit"))
        CACHE_LOG.append(("climate", "hit"))
        return dict(DEMO_ENV), fake_terrain()

    jobs.run_live = fake
    try:
        jid = jobs.start_job(params())
        wait_stage(jid, "Fetching terrain")
        gate_terrain.set()
        wait_stage(jid, "Fetching soil")
        gate_soil.set()
        v = wait_for(jid, {"done", "error"})
        assert v["state"] == "done", v
        assert v["result"]["cache"] == [["store", "sqlite"], ["terrain", "miss"],
                                        ["soil", "hit"], ["climate", "hit"]]
        assert v["result"]["terrain_summary"].startswith("Terrain summary")
    finally:
        jobs.run_live = REAL_RUN_LIVE


def test_blocked_location_gets_no_plants():
    def fake(lat, lon, radius_m, use_cache, refresh):
        CACHE_LOG.append(("store", "off"))
        return dict(DEMO_ENV), fake_terrain(water=0.6)

    jobs.run_live = fake
    try:
        v = wait_for(jobs.start_job(params()), {"done", "error"})
        assert v["state"] == "done", v
        r = v["result"]
        assert r["facts"]["blocked"] is True
        assert any("BLOCKED" in w for w in r["facts"]["warnings"])
        assert all(r["tiers"][t] == [] for t in r["tier_order"])
        assert len(r["facts"]["ruled_out"]) > 0     # the reasons are still shown
    finally:
        jobs.run_live = REAL_RUN_LIVE


def test_error_is_reported_and_the_next_job_still_runs():
    def boom(*a, **k):
        raise RuntimeError("earth engine says no")

    jobs.run_live = boom
    try:
        v = wait_for(jobs.start_job(params()), {"done", "error"})
        assert v["state"] == "error" and "earth engine says no" in v["error"]
        assert v["result"] is None
    finally:
        jobs.run_live = REAL_RUN_LIVE
    v2 = wait_for(jobs.start_job(params(demo=True)), {"done", "error"})
    assert v2["state"] == "done"            # the lock was released after the failure


def test_second_job_waits_for_the_first():
    gate = threading.Event()

    def slow(lat, lon, radius_m, use_cache, refresh):
        CACHE_LOG.append(("store", "off"))
        gate.wait(5)
        return dict(DEMO_ENV), fake_terrain()

    jobs.run_live = slow
    try:
        first = jobs.start_job(params())
        wait_stage(first, "Fetching terrain")
        second = jobs.start_job(params(demo=True))
        time.sleep(0.1)
        assert jobs.get_job(second)["state"] == "queued"
        assert "Waiting" in jobs.get_job(second)["stage"]
        gate.set()
        assert wait_for(first, {"done", "error"})["state"] == "done"
        assert wait_for(second, {"done", "error"})["state"] == "done"
    finally:
        jobs.run_live = REAL_RUN_LIVE


def test_old_jobs_are_pruned():
    ids = [jobs.start_job(params(demo=True)) for _ in range(jobs.MAX_JOBS + 5)]
    wait_for(ids[-1], {"done", "error"})
    with jobs._JOBS_LOCK:
        assert len(jobs._JOBS) <= jobs.MAX_JOBS
    assert jobs.get_job(ids[0]) is None and jobs.get_job(ids[-1]) is not None


REAL_OLLAMA = jobs.OllamaExplainer


class FakeExplainer:
    """Stands in for Ollama. mode: ok (text that passes the checks), bad (rejected), down."""
    mode = "ok"

    def __init__(self, model="x"):
        self.model, self.name, self.truncated = model, f"ollama:{model}", False

    def explain(self, system, user):
        if FakeExplainer.mode == "down":
            raise RuntimeError("Could not reach Ollama. Start it (ollama serve).")
        if FakeExplainer.mode == "bad":
            return "Nothing useful."
        facts = json.loads(user.split("Fact sheet:\n", 1)[1].split("\n\nYour previous", 1)[0])
        return "Overview of this site. " + template_explanation(facts)


def with_fake_llm(mode):
    FakeExplainer.mode = mode
    jobs.OllamaExplainer = FakeExplainer


def demo_analysis():
    jid = jobs.start_job(params(demo=True))
    assert wait_for(jid, {"done", "error"})["state"] == "done"
    return jid


def test_llm_job_accepted_answer():
    with_fake_llm("ok")
    try:
        v = wait_for(jobs.start_explain_job(demo_analysis(), "gemma4:e4b"), {"done", "error"})
        assert v["state"] == "done" and v["kind"] == "explain", v
        r = v["result"]
        assert r["source"] == "llm" and r["model"] == "gemma4:e4b"
        assert r["text"].startswith("Overview of this site.")
        assert any("LLM-written text" in n for n in r["notes"])
        assert "facts" not in v                    # the fact sheet is never sent out
    finally:
        jobs.OllamaExplainer = REAL_OLLAMA


def test_llm_job_rejected_answer_falls_back_to_template():
    with_fake_llm("bad")
    try:
        v = wait_for(jobs.start_explain_job(demo_analysis(), "gemma4:e4b"), {"done", "error"})
        assert v["state"] == "done", v
        r = v["result"]
        assert r["source"] == "template" and any("rejected" in n for n in r["notes"])
    finally:
        jobs.OllamaExplainer = REAL_OLLAMA


def test_llm_job_ollama_down_is_an_error_message():
    with_fake_llm("down")
    try:
        v = wait_for(jobs.start_explain_job(demo_analysis(), "gemma4:e4b"), {"done", "error"})
        assert v["state"] == "error" and "Could not reach Ollama" in v["error"] and v["result"] is None
    finally:
        jobs.OllamaExplainer = REAL_OLLAMA
    with_fake_llm("ok")                           # the lock was released: the next call works
    try:
        v = wait_for(jobs.start_explain_job(demo_analysis(), "gemma4:e4b"), {"done", "error"})
        assert v["state"] == "done"
    finally:
        jobs.OllamaExplainer = REAL_OLLAMA


def test_llm_job_refusals():
    # unknown analysis
    try:
        jobs.start_explain_job("nope", "gemma4:e4b")
        assert False, "should have raised"
    except LookupError:
        pass
    # an explain job is not an analysis
    with_fake_llm("ok")
    try:
        ex = jobs.start_explain_job(demo_analysis(), "gemma4:e4b")
        wait_for(ex, {"done", "error"})
        try:
            jobs.start_explain_job(ex, "gemma4:e4b")
            assert False, "should have raised"
        except LookupError:
            pass
    finally:
        jobs.OllamaExplainer = REAL_OLLAMA
    # blocked location: never
    def blocked(lat, lon, radius_m, use_cache, refresh):
        CACHE_LOG.append(("store", "off"))
        return dict(DEMO_ENV), fake_terrain(water=0.6)
    jobs.run_live = blocked
    try:
        jid = jobs.start_job(params())
        assert wait_for(jid, {"done", "error"})["state"] == "done"
        try:
            jobs.start_explain_job(jid, "gemma4:e4b")
            assert False, "should have raised"
        except ValueError as e:
            assert "blocked" in str(e)
    finally:
        jobs.run_live = REAL_RUN_LIVE
    # unfinished analysis
    gate = threading.Event()
    def slow(lat, lon, radius_m, use_cache, refresh):
        CACHE_LOG.append(("store", "off"))
        gate.wait(5)
        return dict(DEMO_ENV), fake_terrain()
    jobs.run_live = slow
    try:
        jid = jobs.start_job(params())
        wait_stage(jid, "Fetching terrain")
        try:
            jobs.start_explain_job(jid, "gemma4:e4b")
            assert False, "should have raised"
        except ValueError as e:
            assert "not finished" in str(e)
        gate.set()
        wait_for(jid, {"done", "error"})
    finally:
        jobs.run_live = REAL_RUN_LIVE


if __name__ == "__main__":
    test_demo_job_runs_offline()
    test_unknown_job_is_none()
    test_stages_follow_the_log_and_result_carries_cache()
    test_blocked_location_gets_no_plants()
    test_error_is_reported_and_the_next_job_still_runs()
    test_second_job_waits_for_the_first()
    test_old_jobs_are_pruned()
    test_llm_job_accepted_answer()
    test_llm_job_rejected_answer_falls_back_to_template()
    test_llm_job_ollama_down_is_an_error_message()
    test_llm_job_refusals()
    print("all job tests passed")