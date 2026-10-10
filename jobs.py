"""
Sylvan Eye — Phase 6, step 3: the job layer.

A first-time analysis takes 1-2 minutes (Earth Engine), too long to hold a web request
open. So the web layer works in two steps:

    start_job(params)  -> job_id      returns at once; the work runs in a background thread
    get_job(job_id)    -> status      the page asks this every couple of seconds

This module has NO web code (no FastAPI) so it can be tested on its own. It also contains no
rules: it only calls the existing entry points in order
    run_live -> match_plants -> build_facts / group_by_tier -> explain (template, no LLM)
and packs what they return.

Two locks, two different jobs:
    _JOBS_LOCK  protects the dict of jobs while threads add and remove entries
    _RUN_LOCK   lets ONE analysis run at a time. run_live records its progress in the
                module-level list CACHE_LOG, which it clears at the start of every run; two
                runs at once would overwrite each other's log. A queued job just waits here.
"""

import threading
import time
import traceback
import uuid

from phase4_matcher import CACHE_LOG, DEMO_ENV, match_plants, run_live, terrain_summary_line
from phase5_explainer import OllamaExplainer, build_facts, explain, template_explanation
from tiers import TIER_DESCRIPTIONS, TIER_LABELS, TIER_ORDER, group_by_tier, order_by_tier

MAX_JOBS = 50          # keep only the newest jobs so memory does not grow forever

_JOBS = {}
_JOBS_LOCK = threading.Lock()
_RUN_LOCK = threading.Lock()
_LLM_LOCK = threading.Lock()   # one language-model call at a time (a local model is slow and heavy)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def start_job(params):
    """
    params: {"lat", "lon", "radius_m", "refresh", "demo"}. Starts the work in a background
    thread and returns the job id immediately.
    """
    job_id = uuid.uuid4().hex
    job = {"id": job_id, "kind": "analysis", "params": dict(params), "state": "queued",
           "created": time.time(), "started": None, "finished": None,
           "result": None, "error": None, "facts": None}
    with _JOBS_LOCK:
        _JOBS[job_id] = job
        _prune()
    threading.Thread(target=_work, args=(job_id,), daemon=True).start()
    return job_id


def get_job(job_id):
    """What the page needs for one job, or None if the id is unknown."""
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        return None
    state = job["state"]
    return {
        "job_id": job_id,
        "kind": job["kind"],            # analysis | explain
        "state": state,                 # queued | running | done | error
        "stage": _stage(job),           # a plain-English line for the page to show
        "seconds": _seconds(job),
        "result": job["result"] if state == "done" else None,
        "error": job["error"] if state == "error" else None,
    }


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
def _prune():
    """Called with _JOBS_LOCK held. Dicts keep insertion order, so the first keys are oldest."""
    while len(_JOBS) > MAX_JOBS:
        del _JOBS[next(iter(_JOBS))]


def _seconds(job):
    if job["started"] is None:
        return 0.0
    return round((job["finished"] or time.time()) - job["started"], 1)


def _stage(job):
    state = job["state"]
    explain_job = job["kind"] == "explain"
    if state == "queued":
        return ("Waiting for the local model to be free" if explain_job
                else "Waiting for another analysis to finish")
    if state == "done":
        return "Done"
    if state == "error":
        return "Failed"
    if explain_job:
        return "Waiting for the local model (this can take a minute or more)"
    if job["params"]["demo"]:
        return "Matching plants"
    # Running a live analysis. run_live adds one entry to CACHE_LOG after each measurement
    # finishes, so what is missing from the log is what it is working on right now.
    done = {name for name, _ in list(CACHE_LOG)}
    if "climate" in done:
        return "Matching plants"
    if "soil" in done:
        return "Fetching climate"
    if "terrain" in done:
        return "Fetching soil"
    if "store" in done:
        return "Fetching terrain (satellite imagery: the slow step on a first run)"
    return "Starting"


def _work(job_id):
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:          # pruned before it got to run
        return
    with _RUN_LOCK:          # queued jobs wait here
        job["started"] = time.time()
        job["state"] = "running"
        try:
            job["result"], job["facts"] = _analyze(job["params"])   # result first ...
            job["state"] = "done"                         # ... then state, so a poll never sees
        except Exception as e:                            # "done" without a result
            traceback.print_exc()                         # full detail stays in the server console
            job["error"] = f"{type(e).__name__}: {e}"
            job["state"] = "error"
        finally:
            job["finished"] = time.time()


def _analyze(p):
    lat, lon, radius = p["lat"], p["lon"], p["radius_m"]
    if p["demo"]:
        env, terrain, cache = dict(DEMO_ENV), None, []
    else:
        # Clear the shared log ourselves first: run_live imports heavy modules before it
        # clears the log, and until then a poll would read the PREVIOUS run's progress.
        CACHE_LOG.clear()
        env, terrain = run_live(lat, lon, radius, True, p["refresh"])
        cache = [list(entry) for entry in CACHE_LOG]

    ranked, excluded, blank = match_plants(env)
    # The fact sheet (and so the plain-words text) lists plants in tier order, strong first.
    # Among tied scores the matcher's own order is arbitrary and could put a "caution" plant
    # ahead of a "likely" one in the text while the page shows the opposite.
    facts = build_facts(env, terrain, order_by_tier(ranked), excluded, blank)

    # When blocked, no plant is recommended: the rule is enforced here, not left to the page.
    tiers = {t: [] for t in TIER_ORDER} if facts["blocked"] else group_by_tier(ranked)

    # The page shows tiers, not the score-ordered shortlist, so the shortlist is left out of
    # what is sent. (The explanation text below is still built from the full fact sheet.)
    page_facts = {k: v for k, v in facts.items() if k not in ("shortlist", "shortlist_note")}

    text, notes = explain(facts)    # template only: the LLM is a separate, opt-in step (later)

    result = {
        "location": {"lat": lat, "lon": lon, "radius_m": radius, "demo": p["demo"]},
        "facts": page_facts,
        "tiers": tiers,
        "tier_order": list(TIER_ORDER),
        "tier_labels": dict(TIER_LABELS),
        "tier_descriptions": dict(TIER_DESCRIPTIONS),
        "terrain_summary": terrain_summary_line(terrain) if terrain else None,
        "explanation": {"source": "template", "text": text, "notes": notes},
        "cache": cache,
    }
    # The full fact sheet stays on the server (never sent to the page) so an optional
    # language-model job can be run on exactly the facts the rules produced.
    return result, facts


# ---------------------------------------------------------------------------
# Optional language-model explanation (a second job, started by the user)
# ---------------------------------------------------------------------------
def start_explain_job(parent_id, model):
    """
    Start a language-model rewrite of a FINISHED analysis. Raises LookupError if the analysis
    is unknown (or was pruned) and ValueError if it cannot be explained yet or ever
    (unfinished, or blocked: the model is never used for a blocked location).
    """
    with _JOBS_LOCK:
        parent = _JOBS.get(parent_id)
    if parent is None or parent["kind"] != "analysis":
        raise LookupError("unknown analysis (it may have expired)")
    if parent["state"] != "done":
        raise ValueError("the analysis is not finished yet")
    if parent["facts"]["blocked"]:
        raise ValueError("the language model is never used for a blocked location")

    job_id = uuid.uuid4().hex
    job = {"id": job_id, "kind": "explain", "params": {"parent": parent_id, "model": model},
           "state": "queued", "created": time.time(), "started": None, "finished": None,
           "result": None, "error": None, "facts": parent["facts"]}
    with _JOBS_LOCK:
        _JOBS[job_id] = job
        _prune()
    threading.Thread(target=_work_explain, args=(job_id,), daemon=True).start()
    return job_id


def _work_explain(job_id):
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        return
    with _LLM_LOCK:
        job["started"] = time.time()
        job["state"] = "running"
        try:
            model, facts = job["params"]["model"], job["facts"]
            text, notes = explain(facts, OllamaExplainer(model=model))
            # explain() falls back to the template when the checks reject the model's answer.
            source = "template" if text == template_explanation(facts) else "llm"
            job["result"] = {"source": source, "text": text, "notes": notes, "model": model}
            job["state"] = "done"
        except Exception as e:      # e.g. Ollama is not running: the message says what to do
            traceback.print_exc()
            job["error"] = f"{type(e).__name__}: {e}"
            job["state"] = "error"
        finally:
            job["finished"] = time.time()