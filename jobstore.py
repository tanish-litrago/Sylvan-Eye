"""
Sylvan Eye - v1.1.0 layer 3: where job records are kept.

A job record is a small dict: id, kind, params, state, created, started, finished, result, error,
owner. Two interchangeable stores, chosen by environment (like storage.py):

    SYLVAN_JOBS=memory   (default)   a dict inside the server process
    SYLVAN_JOBS=redis                records in Redis; SYLVAN_REDIS_URL=redis://host:6379/0

Only the RECORD lives here. The work still runs in threads inside the app, and the full fact
sheet (used by the optional LLM job) stays in the app's memory, never in the store.
Redis records expire after JOB_TTL_SECONDS (renewed on every write).

No rules and no web code here.
"""

import json
import os
import threading

JOB_TTL_SECONDS = 3600     # a Redis record disappears an hour after its last write
MAX_MEMORY_JOBS = 50       # the memory store keeps only the newest jobs
KEY_PREFIX = "sylvan:job:"


class JobStoreError(Exception):
    """The job store cannot be used. The message never contains the Redis URL."""


# ---------------------------------------------------------------------------
# Memory (default)
# ---------------------------------------------------------------------------
class MemoryJobStore:
    name = "memory"

    def __init__(self, max_jobs=MAX_MEMORY_JOBS):
        self._max = max_jobs
        self._jobs = {}                    # dicts keep insertion order: the first keys are oldest
        self._lock = threading.Lock()

    def put(self, record):
        with self._lock:
            self._jobs[record["id"]] = dict(record)
            while len(self._jobs) > self._max:
                del self._jobs[next(iter(self._jobs))]

    def get(self, job_id):
        with self._lock:
            rec = self._jobs.get(job_id)
            return dict(rec) if rec is not None else None

    def update(self, job_id, **fields):
        """Change fields of an existing record in one step. False if the record is gone."""
        with self._lock:
            rec = self._jobs.get(job_id)
            if rec is None:
                return False
            rec.update(fields)
            return True

    def count(self):
        with self._lock:
            return len(self._jobs)


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------
class RedisJobStore:
    name = "redis"

    def __init__(self, url=None, ttl=JOB_TTL_SECONDS, client=None):
        try:
            import redis
        except ImportError:
            raise JobStoreError("Redis needs the driver: pip install -r requirements-redis.txt") from None
        self._redis = redis
        self._ttl = ttl
        self._lock = threading.Lock()      # one read-modify-write at a time inside this process
        try:
            self._client = client or redis.Redis.from_url(
                url, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
            self._client.ping()
        except ValueError:
            raise JobStoreError("SYLVAN_REDIS_URL is not a valid Redis URL "
                                "(for example redis://redis:6379/0)") from None
        except redis.RedisError as e:
            raise JobStoreError(f"could not reach Redis: {type(e).__name__}") from None

    def _fail(self, e):
        raise JobStoreError(f"the Redis job store failed: {type(e).__name__}") from None

    def _write(self, record):
        try:
            payload = json.dumps(record)
        except (TypeError, ValueError) as e:
            raise JobStoreError(f"a job record could not be saved as JSON: {e}") from None
        try:
            self._client.set(KEY_PREFIX + record["id"], payload, ex=self._ttl)
        except self._redis.RedisError as e:
            self._fail(e)

    def put(self, record):
        self._write(record)

    def get(self, job_id):
        try:
            raw = self._client.get(KEY_PREFIX + job_id)
        except self._redis.RedisError as e:
            self._fail(e)
        return json.loads(raw) if raw is not None else None

    def update(self, job_id, **fields):
        with self._lock:
            rec = self.get(job_id)
            if rec is None:
                return False
            rec.update(fields)
            self._write(rec)
            return True

    def count(self):
        try:
            return sum(1 for _ in self._client.scan_iter(match=KEY_PREFIX + "*"))
        except self._redis.RedisError as e:
            self._fail(e)


# ---------------------------------------------------------------------------
# Choosing a store
# ---------------------------------------------------------------------------
def make_store():
    kind = os.environ.get("SYLVAN_JOBS", "memory").strip().lower()
    if kind == "memory":
        return MemoryJobStore()
    if kind == "redis":
        url = os.environ.get("SYLVAN_REDIS_URL", "").strip()
        if not url:
            raise JobStoreError("SYLVAN_JOBS=redis needs SYLVAN_REDIS_URL, "
                                "e.g. redis://localhost:6379/0")
        return RedisJobStore(url)
    raise JobStoreError(f"unknown SYLVAN_JOBS '{kind}' (use memory or redis)")
