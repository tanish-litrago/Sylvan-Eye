"""
Tests for the demo-only server (SYLVAN_MODE=demo) and for CORS, with no Earth Engine, weather or Ollama.
python -m tests.test_demo_mode
"""

import os
import subprocess
import sys
import time

from fastapi.testclient import TestClient

import app as app_module
import jobs
from scripts.fixtures import list_fixtures

client = TestClient(app_module.app)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class demo_server:
    """Switch the running app to demo-only mode for a block of code."""
    def __enter__(self):
        self.saved = (app_module.DEMO, app_module.LLM_MODELS, jobs.run_live)
        app_module.DEMO, app_module.LLM_MODELS = True, []

        def no_live(*a, **k):
            raise AssertionError("the demo-only server must never call run_live")
        jobs.run_live = no_live

    def __exit__(self, *exc):
        app_module.DEMO, app_module.LLM_MODELS, jobs.run_live = self.saved


def wait_done(job_id, seconds=60):
    end = time.time() + seconds
    while time.time() < end:
        job = client.get(f"/jobs/{job_id}").json()
        if job["state"] in ("done", "error"):
            return job
        time.sleep(0.2)
    raise AssertionError("job did not finish")


def test_config_in_live_mode_lists_no_places():
    body = client.get("/config").json()
    assert body == {"mode": "live", "places": []}


def test_list_fixtures_has_what_the_page_needs():
    places = list_fixtures()
    assert places and all(set(p) == {"slug", "name", "lat", "lon", "radius_m"} for p in places)
    assert [p["name"].lower() for p in places] == sorted(p["name"].lower() for p in places)


def test_config_in_demo_mode_lists_the_saved_places_and_no_models():
    with demo_server():
        body = client.get("/config").json()
        assert body["mode"] == "demo" and body["places"] == list_fixtures()
        assert client.get("/llm/models").json()["models"] == []


def test_demo_server_answers_a_saved_place_from_its_fixture():
    slug = next(p["slug"] for p in list_fixtures() if p["slug"] == "khapri")
    with demo_server():
        r = client.post("/analyze", json={"lat": 0, "lon": 0, "place": slug})
        assert r.status_code == 202
        job = wait_done(r.json()["job_id"])
    assert job["state"] == "done", job
    res = job["result"]
    saved = next(p for p in list_fixtures() if p["slug"] == slug)
    assert res["location"]["lat"] == saved["lat"] and res["location"]["lon"] == saved["lon"]
    assert res["location"]["demo"] is False and res["cache"] == []
    assert res["explanation"]["source"] == "template" and res["tiers"]


def test_demo_server_refuses_anything_that_is_not_a_saved_place():
    with demo_server():
        for body in ({"lat": 22.08, "lon": 82.14}, {"lat": 22.08, "lon": 82.14, "place": "no-such-place"},
                     {"lat": 52.5, "lon": 13.4, "place": "../etc/passwd"}):
            r = client.post("/analyze", json=body)
            assert r.status_code == 422 and "saved places" in r.json()["detail"], body


def test_demo_server_refuses_the_language_model():
    with demo_server():
        r = client.post("/jobs/anything/explain", json={})
        assert r.status_code == 409


def test_a_client_cannot_pick_the_fixture_itself():
    # `fixture` is not a request field: an extra key is ignored, so it cannot reach the job.
    r = client.post("/analyze", json={"lat": 22.08, "lon": 82.14, "demo": True, "fixture": "khapri"})
    assert r.status_code == 202
    assert "fixture" not in jobs._load(r.json()["job_id"])["params"]


def test_cors_origins_parsing():
    assert app_module.cors_origins(None) == [] and app_module.cors_origins("  ") == []
    assert app_module.cors_origins("https://a.vercel.app/, https://b.example") == ["https://a.vercel.app", "https://b.example"]


def run_with_cors(origin_header, setting):
    code = (
        "import warnings; warnings.simplefilter('ignore')\n"
        "from fastapi.testclient import TestClient\nimport app\n"
        f"r = TestClient(app.app).get('/health', headers={{'Origin': {origin_header!r}}})\n"
        "print(r.status_code, r.headers.get('access-control-allow-origin'))\n")
    env = dict(os.environ, SYLVAN_CORS_ORIGINS=setting)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, env=env)
    return out.stdout.strip().splitlines()[-1]


def test_cors_allows_only_the_listed_origin():
    assert run_with_cors("https://my-site.vercel.app", "https://my-site.vercel.app") == "200 https://my-site.vercel.app"
    assert run_with_cors("https://evil.example", "https://my-site.vercel.app") == "200 None"
    assert run_with_cors("https://my-site.vercel.app", "") == "200 None"      # no setting, no CORS


if __name__ == "__main__":
    test_config_in_live_mode_lists_no_places()
    test_list_fixtures_has_what_the_page_needs()
    test_config_in_demo_mode_lists_the_saved_places_and_no_models()
    test_demo_server_answers_a_saved_place_from_its_fixture()
    test_demo_server_refuses_anything_that_is_not_a_saved_place()
    test_demo_server_refuses_the_language_model()
    test_a_client_cannot_pick_the_fixture_itself()
    test_cors_origins_parsing()
    test_cors_allows_only_the_listed_origin()
    print("all demo mode tests passed")
