"""
Tests for storage.py and the cache wiring in phase4_matcher.run_live.
No Earth Engine or network is needed: the slow fetch functions are replaced by fakes.

Run:
    python test_storage.py                     SQLite only (temporary file)
Postgres too (use a throwaway database, the tests wipe the 'cache' table):
    $env:SYLVAN_TEST_DB_URL = "postgresql://user:pass@localhost:5432/sylvan_test"
    python test_storage.py
"""

import os
import sys
import tempfile
import time
import types

import storage
from storage import PostgresStore, SqliteStore, cached, make_key

FAILS = []


def check(label, condition):
    print(("  ok   " if condition else "  FAIL ") + label)
    if not condition:
        FAILS.append(label)


def test_backend(store):
    print(f"\n== {store.name} ==")
    store.clear()
    check("starts empty", store.count() == 0)
    check("missing key returns None", store.get("nope") is None)

    value = {"a": 1, "b": [1.5, "x"], "c": {"d": None}}
    store.set("k1", value)
    check("round trip keeps the value", store.get("k1") == value)

    store.set("k1", {"a": 2})
    check("set overwrites (upsert)", store.get("k1") == {"a": 2} and store.count() == 1)

    store.set("short", {"v": 1}, ttl_seconds=0.2)
    check("value readable before expiry", store.get("short") == {"v": 1})
    time.sleep(0.4)
    check("value gone after expiry", store.get("short") is None)

    store.set("terrain:a", 1)
    store.set("terrain:b", 2)
    store.set("soil:a", 3)
    check("clear(prefix) removes only that prefix", store.clear("terrain:") == 2 and store.get("soil:a") == 3)
    store.set("we%ird_key", 9)
    store.set("weXird_key", 9)
    check("clear treats % and _ literally", store.clear("we%ird_") == 1 and store.get("weXird_key") == 9)
    store.delete("soil:a")
    check("delete removes a key", store.get("soil:a") is None)

    # cached() helper
    calls = []

    def compute():
        calls.append(1)
        return {"years": {2023: 0.1, 2024: 0.5}, "n": 3}

    v1, s1 = cached(store, "t:x", None, compute)
    v2, s2 = cached(store, "t:x", None, compute)
    check("cached: miss then hit, compute ran once", (s1, s2) == ("miss", "hit") and len(calls) == 1)
    check("cached: hit and miss have identical shape (int keys become strings)", v1 == v2 and "2023" in v1["years"])
    v3, s3 = cached(store, "t:x", None, compute, refresh=True)
    check("cached: refresh recomputes", s3 == "refreshed" and len(calls) == 2)
    _, s4 = cached(None, "t:x", None, compute)
    check("cached: no store means no-cache and still computes", s4 == "no-cache" and len(calls) == 3)
    store.clear()


class BrokenStore:
    name = "broken"

    def get(self, key):
        raise OSError("disk gone")

    def set(self, key, value, ttl_seconds=None):
        raise OSError("disk gone")


def test_keys_and_failures():
    print("\n== keys and failure handling ==")
    a = make_key("terrain", 22.07970, 82.14090, 400, 2)
    b = make_key("terrain", 22.079704, 82.140903, 400, 2)
    c = make_key("terrain", 22.0802, 82.1409, 400, 2)
    check("pins about 0.5 m apart share a key", a == b)
    check("pins about 50 m apart do not", a != c)
    check("radius and version change the key",
          a != make_key("terrain", 22.0797, 82.1409, 1000, 2) and a != make_key("terrain", 22.0797, 82.1409, 400, 3))
    value, status = cached(BrokenStore(), "k", None, lambda: {"ok": True})
    check("a broken store never stops the analysis", value == {"ok": True} and status == "miss")

    os.environ["SYLVAN_STORE"] = "mongo"
    try:
        storage.get_store()
        check("unknown backend is rejected", False)
    except storage.StoreError:
        check("unknown backend is rejected", True)
    os.environ["SYLVAN_STORE"] = "postgres"
    os.environ.pop("SYLVAN_DB_URL", None)
    try:
        storage.get_store()
        check("postgres without a URL is rejected", False)
    except storage.StoreError as e:
        check("postgres without a URL is rejected", "SYLVAN_DB_URL" in str(e))
    os.environ.pop("SYLVAN_STORE", None)


def test_run_live(env_vars):
    """run_live with fake slow functions: the second call must come entirely from the cache."""
    print(f"\n== run_live caching ({env_vars.get('SYLVAN_STORE', 'sqlite')}) ==")
    for k, v in env_vars.items():
        os.environ[k] = v
    counts = {"terrain": 0, "soil": 0, "climate": 0}

    fake2 = types.ModuleType("phase2_terrain_extraction")
    def get_terrain_data(lat, lon, radius_m=400):
        counts["terrain"] += 1
        return {"terrain": {"elevation_m": 269.4}, "location": {"radius_m": radius_m},
                "seasonality": {"big_swing_by_year": {2024: 0.47}, "best_swing_year": 2024}}
    fake2.get_terrain_data = get_terrain_data
    fake1 = types.ModuleType("phase1_data_pipeline")
    def get_soil_data(lat, lon):
        counts["soil"] += 1
        return {"surface_soil": {"ph": {"value": 7.5}, "clay": {"value": 33.0}, "sand": {"value": 38.0}}}
    fake1.get_soil_data = get_soil_data
    sys.modules["phase2_terrain_extraction"], sys.modules["phase1_data_pipeline"] = fake2, fake1

    import phase4_inputs
    original = phase4_inputs.get_climate_normals
    def get_climate_normals(lat, lon, *a, **k):
        counts["climate"] += 1
        return {"annual_rainfall_mm": 1520, "annual_mean_temp_c": 26.4}
    phase4_inputs.get_climate_normals = get_climate_normals

    import phase4_matcher as m
    try:
        storage.get_store().clear()
        env1, terrain1 = m.run_live(22.0797, 82.1409)
        log1 = dict(m.CACHE_LOG)
        env2, terrain2 = m.run_live(22.0797, 82.1409)
        log2 = dict(m.CACHE_LOG)
        check("first call: all three miss", [log1[k] for k in ("terrain", "soil", "climate")] == ["miss"] * 3)
        check("second call: all three hit", [log2[k] for k in ("terrain", "soil", "climate")] == ["hit"] * 3)
        check("slow functions ran exactly once each", counts == {"terrain": 1, "soil": 1, "climate": 1})
        check("environment is identical on hit and miss", env1 == env2 and terrain1 == terrain2)
        check("environment values are right", env1["ph"] == 7.5 and env1["soil_texture"] == "medium"
              and env1["elevation_m"] == 269.4 and env1["annual_rainfall_mm"] == 1520)
        m.run_live(22.0797, 82.1409, refresh=True)
        check("--refresh recomputes everything", counts == {"terrain": 2, "soil": 2, "climate": 2})
        m.run_live(22.0797, 82.1409, use_cache=False)
        check("--no-cache recomputes and reports it", counts == {"terrain": 3, "soil": 3, "climate": 3}
              and dict(m.CACHE_LOG)["store"] == "off")
        fake2.CACHE_VERSION = 7
        m.run_live(22.0797, 82.1409)
        store = storage.get_store()
        check("terrain key takes its version from the producing module",
              store.get(make_key("terrain", 22.0797, 82.1409, 400, 7)) is not None
              and store.get(make_key("terrain", 22.0797, 82.1409, 400, 3)) is None)
        check("old-version entries are never reused (it recomputed terrain, not soil)",
              counts["terrain"] == 4 and counts["soil"] == 3)
        del fake2.CACHE_VERSION
        counts.update(terrain=3)  # reset for the next check
        m.run_live(22.0797, 82.1409, radius_m=1000)
        check("a different radius is a new terrain entry but reuses soil and climate",
              counts == {"terrain": 4, "soil": 3, "climate": 3})
        storage.get_store().clear()
    finally:
        phase4_inputs.get_climate_normals = original
        for k in env_vars:
            os.environ.pop(k, None)


if __name__ == "__main__":
    folder = tempfile.mkdtemp()
    sqlite_path = os.path.join(folder, "test_cache.db")
    test_backend(SqliteStore(sqlite_path))
    test_keys_and_failures()
    test_run_live({"SYLVAN_STORE": "sqlite", "SYLVAN_SQLITE_PATH": sqlite_path})

    dsn = os.environ.get("SYLVAN_TEST_DB_URL")
    if dsn:
        test_backend(PostgresStore(dsn))
        test_run_live({"SYLVAN_STORE": "postgres", "SYLVAN_DB_URL": dsn})
        try:
            PostgresStore("postgresql://nobody:wrong@localhost:1/nothing")
            check("unreachable Postgres is reported", False)
        except storage.StoreError as e:
            check("unreachable Postgres is reported without leaking the password", "wrong" not in str(e))
    else:
        print("\n(Postgres tests skipped: set SYLVAN_TEST_DB_URL to run them)")

    print(f"\n{'ALL PASSED' if not FAILS else 'FAILED: ' + str(FAILS)}")
    sys.exit(1 if FAILS else 0)