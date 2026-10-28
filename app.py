"""
Sylvan Eye — Phase 6, step 2: web app skeleton.

Routes:
    GET  /health        is the server alive
    GET  /              the page
    POST /analyze       start an analysis; answers at once with a job id (HTTP 202)
    GET  /jobs/{id}     status of that job; carries the result when it is done
    GET  /llm/models    the local models the page may offer
    POST /jobs/{id}/explain   optional: rewrite a finished analysis with a local language model

The work itself lives in jobs.py; this file only maps URLs to it and validates input.

Run (from the project folder, venv active):
    python -m uvicorn app:app --reload
then open http://127.0.0.1:8000
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import jobs
from jobstore import JobStoreError
from phases.phase4_matcher import DEFAULT_RADIUS, PLANTS_CSV
from phases.phase5_explainer import OLLAMA_MODEL

# Paths are built from this file's location, not from the folder you launch the server in,
# so the app finds its page no matter where you start it from.
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

def llm_models_for(setting):
    """SYLVAN_LLM=off lists no models, so the page hides the language-model control (for a host without Ollama)."""
    return [] if str(setting or "").strip().lower() == "off" else [OLLAMA_MODEL]


LLM_MODELS = llm_models_for(os.environ.get("SYLVAN_LLM"))   # qwen2.5:7b-instruct was dropped (user decision, 2026-10-10): see HANDOFF section 8
MAX_RADIUS_M = 5000   # a sanity ceiling I chose, not a rule from the data: change it if you need to

# The plant table (data/plants.csv) and the SQLite cache file (sylvan_cache.db, next to this file)
# are found from the project's own folders, not from where the server is started. Imports
# (phases, jobs, ...) do need the project folder as the working folder: start with
#   cd "C:\\Projects\\Sylvan Eye"  then  python -m uvicorn app:app --reload
if not Path(PLANTS_CSV).exists():
    raise SystemExit(f"Plant table not found at {PLANTS_CSV}: check the folder layout (data/plants.csv).")

app = FastAPI(title="Sylvan Eye")


@app.exception_handler(JobStoreError)
def job_store_unavailable(request, exc):
    """The job store (Redis) cannot be used: say so plainly instead of a bare server error."""
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# A coarse box around India (Andaman, Nicobar and Lakshadweep included). It refuses Berlin or the
# Pacific; parts of neighbouring countries inside the box still pass. Sylvan Eye's plant table,
# soil and rainfall checks were built and tested on Indian places only.
INDIA_LAT = (6.0, 37.5)
INDIA_LON = (68.0, 98.0)


def inside_india(lat, lon):
    return INDIA_LAT[0] <= lat <= INDIA_LAT[1] and INDIA_LON[0] <= lon <= INDIA_LON[1]


class AnalyzeRequest(BaseModel):
    """What the page sends. FastAPI rejects anything outside these limits with HTTP 422."""
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    radius_m: float = Field(default=DEFAULT_RADIUS, gt=0, le=MAX_RADIUS_M)
    refresh: bool = False   # recompute the measurements instead of using the cache
    demo: bool = False      # skip the satellite step and use the offline Bilaspur values


@app.get("/health")
def health():
    """Tiny route the page calls on load to prove the browser can reach the server."""
    return {"status": "ok"}


@app.post("/analyze", status_code=202)
def analyze(req: AnalyzeRequest):
    """Start a job and return its id. 202 means: accepted, not finished."""
    if not inside_india(req.lat, req.lon):
        raise HTTPException(status_code=422, detail=(
            "This point is outside India. Sylvan Eye works for India only: its plant table, "
            "soil and rainfall checks were built and tested on Indian places."))
    return {"job_id": jobs.start_job(req.model_dump())}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    """The page calls this every couple of seconds until state is 'done' or 'error'."""
    view = jobs.get_job(job_id)
    if view is None:
        raise HTTPException(status_code=404, detail="unknown job")
    return view


class ExplainRequest(BaseModel):
    model: str = OLLAMA_MODEL


@app.get("/llm/models")
def llm_models():
    return {"models": LLM_MODELS, "default": OLLAMA_MODEL}


@app.post("/jobs/{job_id}/explain", status_code=202)
def explain_job(job_id: str, req: ExplainRequest):
    """Start the optional language-model rewrite. Poll the returned id with GET /jobs/{id}."""
    if not LLM_MODELS:
        raise HTTPException(status_code=409, detail="The language model is switched off on this server.")
    if req.model not in LLM_MODELS:
        raise HTTPException(status_code=422, detail="unknown model")
    try:
        return {"job_id": jobs.start_explain_job(job_id, req.model)}
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/")
def index():
    """Serve the single page."""
    return FileResponse(STATIC_DIR / "index.html")


# Anything under /static/... is served straight from the static folder (css, js, images).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")