"""
Sylvan Eye — Phase 6, step 2: web app skeleton.

Routes:
    GET  /health        is the server alive
    GET  /              the page
    POST /analyze       start an analysis; answers at once with a job id (HTTP 202)
    GET  /jobs/{id}     status of that job; carries the result when it is done

The work itself lives in jobs.py; this file only maps URLs to it and validates input.

Run (from the project folder, venv active):
    python -m uvicorn app:app --reload
then open http://127.0.0.1:8000
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import jobs
from phase4_matcher import DEFAULT_RADIUS

# Paths are built from this file's location, not from the folder you launch the server in,
# so the app finds its page no matter where you start it from.
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

MAX_RADIUS_M = 5000   # a sanity ceiling I chose, not a rule from the data: change it if you need to

# plants.csv and the cache file (sylvan_cache.db) are found relative to the folder the server
# is started from. Started anywhere else, every run would fail (no plants.csv) or quietly start
# a new empty cache, so every place would look new and take 1-2 minutes. Fail loudly instead.
if not (Path.cwd() / "plants.csv").exists():
    raise SystemExit("Start the server from the project folder (the one that contains "
                     "plants.csv), e.g.  cd \"C:\\Projects\\Sylvan Eye\"  then  "
                     "python -m uvicorn app:app --reload")

app = FastAPI(title="Sylvan Eye")


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
    return {"job_id": jobs.start_job(req.model_dump())}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    """The page calls this every couple of seconds until state is 'done' or 'error'."""
    view = jobs.get_job(job_id)
    if view is None:
        raise HTTPException(status_code=404, detail="unknown job")
    return view


@app.get("/")
def index():
    """Serve the single page."""
    return FileResponse(STATIC_DIR / "index.html")


# Anything under /static/... is served straight from the static folder (css, js, images).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")