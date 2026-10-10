"""
Tests for app.py (step 2). Plain asserts:  python test_app.py
Needs httpx (only for these tests):  pip install httpx
"""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_page_is_served():
    r = client.get("/")
    assert r.status_code == 200 and "Sylvan Eye" in r.text


def test_static_files_are_served():
    r = client.get("/static/style.css")
    assert r.status_code == 200 and "--paper" in r.text
    r = client.get("/static/app.js")
    assert r.status_code == 200 and "parsePasted" in r.text


def test_unknown_route_is_404():
    assert client.get("/nope").status_code == 404


def test_analyze_rejects_bad_input():
    assert client.post("/analyze", json={"lat": 91, "lon": 82}).status_code == 422
    assert client.post("/analyze", json={"lat": 22, "lon": 181}).status_code == 422
    assert client.post("/analyze", json={"lat": 22, "lon": 82, "radius_m": 0}).status_code == 422
    assert client.post("/analyze", json={"lat": 22, "lon": 82, "radius_m": 99999}).status_code == 422
    assert client.post("/analyze", json={"lat": "abc", "lon": 82}).status_code == 422
    assert client.post("/analyze", json={"lon": 82}).status_code == 422


def test_unknown_job_is_404():
    assert client.get("/jobs/does-not-exist").status_code == 404


def test_demo_analysis_end_to_end():
    r = client.post("/analyze", json={"lat": 22.0797, "lon": 82.1409, "demo": True})
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    import time
    for _ in range(300):
        view = client.get(f"/jobs/{job_id}").json()
        if view["state"] in ("done", "error"):
            break
        time.sleep(0.02)
    assert view["state"] == "done", view
    assert view["result"]["location"]["radius_m"] == 400     # default radius is echoed back
    assert set(view["result"]["tiers"]) == {"strong", "likely", "caution"}


def test_llm_models_and_explain_routes():
    import json, time
    import jobs
    from phase5_explainer import template_explanation

    m = client.get("/llm/models").json()
    assert m["default"] in m["models"] and len(m["models"]) >= 1

    assert client.post("/jobs/nope/explain", json={"model": m["default"]}).status_code == 404

    r = client.post("/analyze", json={"lat": 22.0797, "lon": 82.1409, "demo": True})
    job_id = r.json()["job_id"]
    for _ in range(300):
        if client.get(f"/jobs/{job_id}").json()["state"] in ("done", "error"):
            break
        time.sleep(0.02)

    assert client.post(f"/jobs/{job_id}/explain", json={"model": "not-a-model"}).status_code == 422

    class Fake:
        def __init__(self, model="x"):
            self.model, self.name, self.truncated = model, f"ollama:{model}", False
        def explain(self, system, user):
            facts = json.loads(user.split("Fact sheet:\n", 1)[1].split("\n\nYour previous", 1)[0])
            return "Overview. " + template_explanation(facts)

    real = jobs.OllamaExplainer
    jobs.OllamaExplainer = Fake
    try:
        r = client.post(f"/jobs/{job_id}/explain", json={"model": m["default"]})
        assert r.status_code == 202
        ex_id = r.json()["job_id"]
        for _ in range(300):
            view = client.get(f"/jobs/{ex_id}").json()
            if view["state"] in ("done", "error"):
                break
            time.sleep(0.02)
        assert view["state"] == "done" and view["kind"] == "explain", view
        assert view["result"]["source"] == "llm"
    finally:
        jobs.OllamaExplainer = real
    # an explain job id is not an analysis
    assert client.post(f"/jobs/{ex_id}/explain", json={"model": m["default"]}).status_code == 404


if __name__ == "__main__":
    test_health()
    test_page_is_served()
    test_static_files_are_served()
    test_unknown_route_is_404()
    test_analyze_rejects_bad_input()
    test_unknown_job_is_404()
    test_demo_analysis_end_to_end()
    test_llm_models_and_explain_routes()
    print("all app tests passed")