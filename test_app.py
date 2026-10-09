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


if __name__ == "__main__":
    test_health()
    test_page_is_served()
    test_static_files_are_served()
    test_unknown_route_is_404()
    test_analyze_rejects_bad_input()
    test_unknown_job_is_404()
    test_demo_analysis_end_to_end()
    print("all app tests passed")