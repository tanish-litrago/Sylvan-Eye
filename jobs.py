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

The job RECORDS (state, result, error ...) live in a store: memory by default, Redis when
SYLVAN_JOBS=redis (see jobstore.py). The work always runs in threads in this process.
A record that says queued/running but is not backed by a live thread of this process (the
server was restarted, or the thread died) is reported as failed instead of hanging forever.

Two locks, two different jobs:
    _JOBS_LOCK  protects the in-process fact sheets and the set of live job ids
    _RUN_LOCK   lets ONE analysis run at a time. run_live records its progress in the
                module-level list CACHE_LOG, which it clears at the start of every run; two
                runs at once would overwrite each other's log. A queued job just waits here.
"""

import threading
import time
import traceback
import uuid

from jobstore import JobStoreError, make_store
from phase4_matcher import CACHE_LOG, DEMO_ENV, match_plants, run_live, terrain_summary_line
from phase5_explainer import OllamaExplainer, build_facts, explain, template_explanation
from tiers import TIER_DESCRIPTIONS, TIER_LABELS, TIER_ORDER, group_by_tier, order_by_tier

MAX_JOBS = 50          # keep only the newest jobs so memory does not grow forever

BOOT_ID = uuid.uuid4().hex     # new on every server start: tells a record made by THIS process apart
_STORE = None                  # job records: memory or Redis (jobstore.py), made on first use
_STORE_LOCK = threading.Lock()
_FACTS = {}                    # job id -> full fact sheet. In-process only, never stored or sent out.
_ACTIVE = set()                # ids of jobs whose thread is alive in THIS process
_JOBS_LOCK = threading.Lock()  # protects _FACTS and _ACTIVE
_RUN_LOCK = threading.Lock()
_LLM_LOCK = threading.Lock()   # one language-model call at a time (a local model is slow and heavy)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def start_job(params):
    """
    params: {"lat", "lon", "radius_m", "refresh", "demo"}. Starts the work in a background
    thread and returns the job id immediately. Raises JobStoreError if the record cannot be saved.
    """
    job_id = uuid.uuid4().hex
    _save_new(_new_record(job_id, "analysis", dict(params)))
    threading.Thread(target=_work, args=(job_id,), daemon=True).start()
    return job_id


def analyze(params):
    """
    Run one analysis in the calling thread (no background job) and return the same result the
    page gets. For scripts such as run_regions.py. params: lat, lon, radius_m, refresh, demo.
    """
    return _analyze(params)[0]


def get_job(job_id):
    """What the page needs for one job, or None if the id is unknown. May raise JobStoreError."""
    job = _load(job_id)
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
def _store():
    """The job store, made on first use (so a Redis that is not up yet does not stop the import)."""
    global _STORE
    with _STORE_LOCK:
        if _STORE is None:
            _STORE = make_store()
        return _STORE


def _new_record(job_id, kind, params):
    return {"id": job_id, "kind": kind, "params": params, "state": "queued",
            "created": time.time(), "started": None, "finished": None,
            "result": None, "error": None, "owner": BOOT_ID}


def _save_new(record, facts=None):
    """Save a new record and mark its job as alive in this process (before the thread starts)."""
    job_id = record["id"]
    with _JOBS_LOCK:
        _ACTIVE.add(job_id)
        if facts is not None:
            _remember_facts(job_id, facts)
    try:
        _store().put(record)
    except Exception:
        with _JOBS_LOCK:
            _ACTIVE.discard(job_id)
            _FACTS.pop(job_id, None)
        raise


def _remember_facts(job_id, facts):
    """Called with _JOBS_LOCK held. Keeps the newest MAX_JOBS fact sheets (oldest first out)."""
    _FACTS[job_id] = facts
    while len(_FACTS) > MAX_JOBS:
        del _FACTS[next(iter(_FACTS))]


def _finish(job_id):
    with _JOBS_LOCK:
        _ACTIVE.discard(job_id)


def _save_update(job_id, **fields):
    """Write from a worker thread. A store failure is logged, not raised: the thread must end."""
    try:
        _store().update(job_id, **fields)
    except Exception:
        traceback.print_exc()


def _load(job_id):
    """
    The record, with one rule added: a job that says queued/running but has no live thread in this
    process (the server was restarted, or the thread died before it could save its result) is
    turned into a failed job, so the page stops waiting.
    """
    store = _store()
    job = store.get(job_id)
    if job is None or job["state"] not in ("queued", "running"):
        return job
    with _JOBS_LOCK:
        alive = job["owner"] == BOOT_ID and job_id in _ACTIVE
    if alive:
        return job
    # Look again: the thread may have saved "done" and ended between our read and our check.
    job = store.get(job_id)
    if job is None or job["state"] not in ("queued", "running"):
        return job
    if job["owner"] != BOOT_ID:
        why = "The server was restarted while this job was running. Run it again."
    else:
        why = "The job stopped before it could save its result. Run it again."
    job.update(state="error", error=why, finished=time.time())
    store.update(job_id, state="error", error=why, finished=job["finished"])
    return job


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
    try:
        job = _store().get(job_id)
        if job is None:          # expired or pruned before it got to run
            return
        with _RUN_LOCK:          # queued jobs wait here
            _save_update(job_id, started=time.time(), state="running")
            try:
                result, facts = _analyze(job["params"])
                with _JOBS_LOCK:                          # facts first, then "done", so a job that
                    _remember_facts(job_id, facts)        # is done always has its facts ready
                _save_update(job_id, result=result, state="done", finished=time.time())
            except Exception as e:
                traceback.print_exc()                     # full detail stays in the server console
                _save_update(job_id, error=f"{type(e).__name__}: {e}", state="error",
                             finished=time.time())
    except Exception:
        traceback.print_exc()
    finally:
        _finish(job_id)


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
    is unknown (or expired, or the server restarted since) and ValueError if it cannot be explained
    yet or ever (unfinished, or blocked: the model is never used for a blocked location).
    """
    parent = _load(parent_id)
    if parent is None or parent["kind"] != "analysis":
        raise LookupError("unknown analysis (it may have expired)")
    if parent["state"] != "done":
        raise ValueError("the analysis is not finished yet")
    with _JOBS_LOCK:
        facts = _FACTS.get(parent_id)
    if facts is None:     # the fact sheet is kept in this process only
        raise LookupError("unknown analysis (it may have expired or the server restarted: "
                          "run the place again)")
    if facts["blocked"]:
        raise ValueError("the language model is never used for a blocked location")

    job_id = uuid.uuid4().hex
    _save_new(_new_record(job_id, "explain", {"parent": parent_id, "model": model}), facts=facts)
    threading.Thread(target=_work_explain, args=(job_id,), daemon=True).start()
    return job_id


class _Recording:
    """Wraps the explainer and keeps what the model actually wrote, so a rejection can show it."""

    def __init__(self, inner):
        self.inner, self.name, self.last_text = inner, inner.name, ""

    @property
    def truncated(self):
        return getattr(self.inner, "truncated", False)

    def explain(self, system, user):
        self.last_text = self.inner.explain(system, user)
        return self.last_text


def _work_explain(job_id):
    try:
        job = _store().get(job_id)
        with _JOBS_LOCK:
            facts = _FACTS.get(job_id)
        if job is None:
            return
        if facts is None:
            _save_update(job_id, error="the fact sheet is no longer available: run the place again",
                         state="error", finished=time.time())
            return
        with _LLM_LOCK:
            _save_update(job_id, started=time.time(), state="running")
            try:
                model = job["params"]["model"]
                recorder = _Recording(OllamaExplainer(model=model))
                text, notes = explain(facts, recorder)
                # explain() falls back to the template when the checks reject the model's answer.
                source = "template" if text == template_explanation(facts) else "llm"
                if source == "template":
                    # Show what the model really wrote, so the cause (empty, cut off, wrong plant
                    # names, ...) can be read instead of guessed.
                    notes = notes + [f"What the model wrote last ({len(recorder.last_text)} characters, "
                                     f"first 400): {recorder.last_text[:400]!r}"]
                _save_update(job_id, result={"source": source, "text": text, "notes": notes,
                                             "model": model},
                             state="done", finished=time.time())
            except Exception as e:      # e.g. Ollama is not running: the message says what to do
                traceback.print_exc()
                _save_update(job_id, error=f"{type(e).__name__}: {e}", state="error",
                             finished=time.time())
    except Exception:
        traceback.print_exc()
    finally:
        _finish(job_id)