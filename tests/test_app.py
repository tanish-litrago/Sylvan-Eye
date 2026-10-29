"""
Tests for app.py (step 2). Plain asserts:  python -m tests.test_app
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
    assert r.status_code == 200 and "--surface" in r.text
    r = client.get("/static/app.js")
    assert r.status_code == 200 and "parsePasted" in r.text
    assert "MSG_STORE_DOWN" in r.text and "MSG_JOB_GONE" in r.text   # the job-store wording (v1.1.0)


def test_fonts_and_their_licence_are_served_from_static():
    """v2.0.0: Atkinson Hyperlegible is bundled (no outside font host); the OFL needs its licence shipped."""
    css = client.get("/static/style.css").text
    for name in ("400-normal", "700-normal", "400-italic"):
        path = f"/static/fonts/atkinson-hyperlegible-latin-{name}.woff2"
        assert path in css, path                                  # the stylesheet points at it
        r = client.get(path)
        assert r.status_code == 200 and r.content[:4] == b"wOF2", path
    r = client.get("/static/fonts/LICENSE-atkinson-hyperlegible.txt")
    assert r.status_code == 200 and "SIL Open Font License" in r.text
    assert "fonts.googleapis.com" not in css and "https://" not in css   # nothing loads from outside


def test_map_files_are_served_and_loaded_in_order():
    """v2.0.0: Leaflet 1.9.4 is copied into static/vendor/leaflet (no CDN); BSD-2-Clause needs its licence shipped."""
    html = client.get("/").text
    assert 'id="map"' in html
    assert html.index("vendor/leaflet/leaflet.css") < html.index("/static/style.css")     # our CSS can override Leaflet's
    assert html.index("vendor/leaflet/leaflet.js") < html.index("/static/app.js")         # L exists when app.js runs
    assert "https://" not in html and "http://" not in html                                # nothing loads from outside
    js = client.get("/static/vendor/leaflet/leaflet.js")
    assert js.status_code == 200 and "Leaflet 1.9.4" in js.text[:200]
    assert client.get("/static/vendor/leaflet/leaflet.css").status_code == 200
    lic = client.get("/static/vendor/leaflet/LICENSE")
    assert lic.status_code == 200 and "BSD 2-Clause" in lic.text
    for name in ("layers.png", "layers-2x.png", "marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"):
        assert client.get("/static/vendor/leaflet/images/" + name).status_code == 200, name


def test_osm_tile_rules_are_kept():
    """OSM's tile usage policy: the browser must send a Referer (so no Referrer-Policy header or meta tag),
    the credit stays visible, the tile address is https and is one constant that can be switched."""
    for path in ("/", "/static/app.js", "/static/style.css"):
        names = {k.lower() for k in client.get(path).headers}
        assert "referrer-policy" not in names, path
    assert 'name="referrer"' not in client.get("/").text.lower()
    js = client.get("/static/app.js").text
    assert 'var TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";' in js
    assert 'OpenStreetMap</a> contributors' in js and "var TILE_CREDIT" in js


def test_page_code_never_puts_server_text_in_with_innerhtml():
    """HANDOFF rule: everything the server sends goes in with textContent. (Leaflet's own file is not ours.)"""
    js = client.get("/static/app.js").text
    code = "\n".join(line for line in js.splitlines() if not line.strip().startswith("//"))
    assert "innerHTML" not in code and "insertAdjacentHTML" not in code


def test_job_store_down_gives_503_with_a_message():
    import jobs
    from jobstore import JobStoreError

    real = jobs._store

    def broken():
        raise JobStoreError("the Redis job store failed: ConnectionError")

    jobs._store = broken
    try:
        r = client.post("/analyze", json={"lat": 22.0797, "lon": 82.1409, "demo": True})
        assert r.status_code == 503 and "job store" in r.json()["detail"], r.text
        r = client.get("/jobs/anything")
        assert r.status_code == 503 and "job store" in r.json()["detail"], r.text
    finally:
        jobs._store = real
    assert client.get("/jobs/anything").status_code == 404      # back to normal: unknown id


def test_unknown_route_is_404():
    assert client.get("/nope").status_code == 404


def test_analyze_rejects_bad_input():
    assert client.post("/analyze", json={"lat": 91, "lon": 82}).status_code == 422
    assert client.post("/analyze", json={"lat": 22, "lon": 181}).status_code == 422
    assert client.post("/analyze", json={"lat": 22, "lon": 82, "radius_m": 0}).status_code == 422
    assert client.post("/analyze", json={"lat": 22, "lon": 82, "radius_m": 99999}).status_code == 422
    assert client.post("/analyze", json={"lat": "abc", "lon": 82}).status_code == 422
    assert client.post("/analyze", json={"lon": 82}).status_code == 422


def test_points_outside_india_are_refused_with_a_message():
    for lat, lon in [(52.52, 13.405), (0.0, -160.0), (-33.9, 151.2), (60.0, 82.0)]:   # Berlin, Pacific, Sydney, Siberia
        r = client.post("/analyze", json={"lat": lat, "lon": lon})
        assert r.status_code == 422 and "outside India" in r.json()["detail"], (lat, lon)


def test_offline_demo_ignores_the_coordinates_so_they_are_not_refused():
    # The page sends 0, 0 when the demo box is ticked and the fields are empty (v2.1.1 refused that: fixed in v2.2.0).
    for lat, lon in [(0, 0), (52.52, 13.405)]:
        r = client.post("/analyze", json={"lat": lat, "lon": lon, "radius_m": 400, "refresh": False, "demo": True})
        assert r.status_code == 202, (lat, lon)


def test_the_india_box_keeps_the_far_corners_and_islands():
    from app import inside_india
    for name, lat, lon in [("Leh", 34.15, 77.58), ("Kanyakumari", 8.09, 77.54), ("Port Blair", 11.62, 92.73),
                           ("Kavaratti", 10.57, 72.64), ("Tawang", 27.59, 91.86), ("Dhordo, Kutch", 23.85, 69.7),
                           ("Bilaspur", 22.08, 82.14)]:
        assert inside_india(lat, lon), name


def test_known_limit_the_box_is_coarse_and_lets_some_neighbours_through():
    from app import inside_india
    assert inside_india(27.7, 85.3)      # Kathmandu is inside the rectangle; a country border check is not built


def test_llm_switched_off_lists_no_models_and_refuses_explain():
    import app as app_module
    assert app_module.llm_models_for("off") == [] and app_module.llm_models_for(" OFF ") == []
    assert app_module.llm_models_for(None) == app_module.llm_models_for("on") == [app_module.OLLAMA_MODEL]
    old = app_module.LLM_MODELS
    app_module.LLM_MODELS = []
    try:
        assert client.get("/llm/models").json()["models"] == []
        r = client.post("/jobs/anything/explain", json={})
        assert r.status_code == 409 and "switched off" in r.json()["detail"]
    finally:
        app_module.LLM_MODELS = old


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
    from phases.phase5_explainer import template_explanation

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
    test_fonts_and_their_licence_are_served_from_static()
    test_map_files_are_served_and_loaded_in_order()
    test_osm_tile_rules_are_kept()
    test_page_code_never_puts_server_text_in_with_innerhtml()
    test_job_store_down_gives_503_with_a_message()
    test_unknown_route_is_404()
    test_analyze_rejects_bad_input()
    test_unknown_job_is_404()
    test_points_outside_india_are_refused_with_a_message()
    test_offline_demo_ignores_the_coordinates_so_they_are_not_refused()
    test_the_india_box_keeps_the_far_corners_and_islands()
    test_known_limit_the_box_is_coarse_and_lets_some_neighbours_through()
    test_llm_switched_off_lists_no_models_and_refuses_explain()
    test_demo_analysis_end_to_end()
    test_llm_models_and_explain_routes()
    print("all app tests passed")