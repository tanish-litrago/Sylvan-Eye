"""
Tests for jobstore.py and the job-record rules in jobs.py.  Plain asserts:  python -m tests.test_jobstore

The memory store is always tested. The Redis store is tested only when a Redis is available:
    $env:SYLVAN_TEST_REDIS_URL = "redis://localhost:6379/15"      (use a database you do not need)
Without it the Redis part is skipped and says so.
"""

import os
import time

import jobs
import jobstore
from jobstore import JobStoreError, MemoryJobStore, RedisJobStore, make_store

REDIS_URL = os.environ.get("SYLVAN_TEST_REDIS_URL", "").strip()
failures = 0


def check(name, ok, detail=""):
    global failures
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  -> {detail}"))
    if not ok:
        failures += 1


def record(job_id, **kw):
    r = {"id": job_id, "kind": "analysis", "params": {"demo": True}, "state": "queued",
         "created": time.time(), "started": None, "finished": None,
         "result": None, "error": None, "owner": "some-owner"}
    r.update(kw)
    return r


def test_store(store, label):
    print(f"\n== {label}: put / get / update ==")
    check("unknown id gives None", store.get("nope") is None)
    store.put(record("a"))
    got = store.get("a")
    check("put then get returns the same record", got is not None and got["state"] == "queued")
    check("update changes only the named fields",
          store.update("a", state="done", result={"x": [1, 2]}) is True
          and store.get("a")["state"] == "done" and store.get("a")["result"] == {"x": [1, 2]}
          and store.get("a")["owner"] == "some-owner")
    check("update of an unknown id returns False", store.update("nope", state="done") is False)
    copy = store.get("a")
    copy["state"] = "tampered"
    check("a returned record is a copy", store.get("a")["state"] == "done")


def test_memory_prunes():
    print("\n== memory: only the newest records are kept ==")
    s = MemoryJobStore(max_jobs=3)
    for i in range(5):
        s.put(record(f"j{i}"))
    check("old records dropped", s.count() == 3 and s.get("j0") is None and s.get("j4") is not None)


def test_make_store_errors():
    print("\n== choosing a store ==")
    saved = {k: os.environ.pop(k, None) for k in ("SYLVAN_JOBS", "SYLVAN_REDIS_URL")}
    try:
        check("default is memory", make_store().name == "memory")
        os.environ["SYLVAN_JOBS"] = "kafka"
        try:
            make_store()
            check("unknown kind rejected", False)
        except JobStoreError as e:
            check("unknown kind rejected", "kafka" in str(e))
        os.environ["SYLVAN_JOBS"] = "redis"
        try:
            make_store()
            check("redis without a URL rejected", False)
        except JobStoreError as e:
            check("redis without a URL rejected", "SYLVAN_REDIS_URL" in str(e))
        try:
            import redis  # noqa: F401
            have_driver = True
        except ImportError:
            have_driver = False
            print("SKIPPED  unreachable-Redis check (the redis driver is not installed: "
                  "pip install -r requirements-redis.txt)")
        if have_driver:
            try:
                RedisJobStore("redis://nobody:secretpw@localhost:1/0")
                check("unreachable Redis raises JobStoreError", False, "no error was raised")
            except JobStoreError as e:
                msg = str(e)
                check("unreachable Redis raises JobStoreError", "could not reach Redis" in msg, msg)
                check("the error never shows the URL or password",
                      "secretpw" not in msg and "localhost" not in msg, msg)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_restart_reported_as_failed(label):
    print(f"\n== {label}: a job left running by a stopped server is reported as failed ==")
    store = jobs._store()
    # What an earlier server process left behind: it owned this record and never finished it.
    store.put(record("old-running", state="running", started=time.time() - 30, owner="old-boot-id"))
    store.put(record("old-queued", state="queued", owner="old-boot-id"))
    store.put(record("old-done", state="done", result={"ok": 1}, finished=time.time(),
                     owner="old-boot-id"))
    v = jobs.get_job("old-running")
    check("running record of an old server -> error", v["state"] == "error" and v["stage"] == "Failed", v)
    check("the reason says the server restarted", "restarted" in (v["error"] or ""), v["error"])
    check("the page gets no result for it", v["result"] is None)
    check("the failure is saved (a second look gives the same answer)",
          store.get("old-running")["state"] == "error" and jobs.get_job("old-running")["state"] == "error")
    check("queued record of an old server -> error", jobs.get_job("old-queued")["state"] == "error")
    check("a finished record of an old server stays done",
          jobs.get_job("old-done")["state"] == "done" and jobs.get_job("old-done")["result"] == {"ok": 1})
    # Same process, but no live thread behind it (e.g. the final write failed): also not left hanging.
    store.put(record("orphan", state="running", owner=jobs.BOOT_ID))
    v = jobs.get_job("orphan")
    check("running record with no live thread -> error", v["state"] == "error"
          and "stopped before" in (v["error"] or ""), v)
    # A live job is NOT touched.
    with jobs._JOBS_LOCK:
        jobs._ACTIVE.add("alive")
    store.put(record("alive", state="running", owner=jobs.BOOT_ID))
    check("a job with a live thread stays running", jobs.get_job("alive")["state"] == "running")
    with jobs._JOBS_LOCK:
        jobs._ACTIVE.discard("alive")


def test_explain_after_restart(label):
    print(f"\n== {label}: the fact sheet is not stored ==")
    jid = jobs.start_job({"lat": 22.0797, "lon": 82.1409, "radius_m": 400, "refresh": False, "demo": True})
    for _ in range(500):
        if jobs.get_job(jid)["state"] in ("done", "error"):
            break
        time.sleep(0.02)
    check("demo analysis finished", jobs.get_job(jid)["state"] == "done")
    raw = jobs._store().get(jid)
    check("the stored record has no fact sheet", "facts" not in raw and "shortlist" not in str(raw.keys()))
    with jobs._JOBS_LOCK:
        jobs._FACTS.pop(jid, None)             # what a restart does: the in-process facts are gone
    try:
        jobs.start_explain_job(jid, "gemma4:e4b")
        check("explain after a restart is refused", False)
    except LookupError as e:
        check("explain after a restart is refused", "run the place again" in str(e), str(e))


def test_redis_only():
    print("\n== redis: expiry and shape ==")
    import redis
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    store = RedisJobStore(REDIS_URL, ttl=600)
    store.put(record("ttl-job"))
    ttl = client.ttl(jobstore.KEY_PREFIX + "ttl-job")
    check("a record expires (TTL is set)", 0 < ttl <= 600, ttl)
    store.update("ttl-job", state="running")
    check("an update renews the expiry", client.ttl(jobstore.KEY_PREFIX + "ttl-job") > 590)
    short = RedisJobStore(REDIS_URL, ttl=1)
    short.put(record("short"))
    time.sleep(1.5)
    check("an expired record is gone", short.get("short") is None)
    try:
        store.put(record("bad", result={"x": {1, 2}}))      # a set is not JSON
        check("a record that is not JSON-safe raises JobStoreError", False)
    except JobStoreError:
        check("a record that is not JSON-safe raises JobStoreError", True)
    check("records are plain JSON text", isinstance(client.get(jobstore.KEY_PREFIX + "ttl-job"), str))
    for k in client.scan_iter(match=jobstore.KEY_PREFIX + "*"):
        client.delete(k)


def main():
    test_store(MemoryJobStore(), "memory store")
    test_memory_prunes()
    test_make_store_errors()

    jobs._STORE = MemoryJobStore()
    test_restart_reported_as_failed("memory")
    test_explain_after_restart("memory")

    if REDIS_URL:
        test_store(RedisJobStore(REDIS_URL), "redis store")
        jobs._STORE = RedisJobStore(REDIS_URL)
        test_restart_reported_as_failed("redis")
        test_explain_after_restart("redis")
        test_redis_only()
    else:
        print("\nSKIPPED  Redis tests (set SYLVAN_TEST_REDIS_URL to run them)")

    print()
    print("All job store checks passed." if failures == 0 else f"{failures} CHECK(S) FAILED.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
