"""
Sylvan Eye — storage layer: a small key-value cache with two interchangeable backends.

Why: the slow, repeated work (Earth Engine terrain calls, a 10-year climate download, soil
lookups) never changes for the same place, so it is fetched once and stored. Only RAW
MEASUREMENTS are cached, never the matcher's verdicts (so changing a threshold applies at
once) and never the LLM's text.

Backends (same interface, pick with environment variables):
    SQLite   (default)  no server, one file.        SYLVAN_SQLITE_PATH=sylvan_cache.db
    Postgres (optional) needs a server + psycopg2.  SYLVAN_STORE=postgres
                                                    SYLVAN_DB_URL=postgresql://user:pass@host:5432/dbname

Caching is best-effort: if the store is broken or missing, analysis still runs and just
recomputes. Never commit the .db file or a database URL (it contains a password).
"""

import json
import os
import sqlite3
import time
from contextlib import closing


class StoreError(RuntimeError):
    """The store could not be created or used (message never contains a password)."""


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
class Store:
    name = "store"

    def get(self, key):
        """Return the stored JSON value, or None if missing or expired."""
        raise NotImplementedError

    def set(self, key, value, ttl_seconds=None):
        """Store a JSON-serialisable value; ttl_seconds=None means it never expires."""
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def clear(self, prefix=""):
        """Delete every key starting with prefix (all keys if empty). Returns how many."""
        raise NotImplementedError

    def count(self):
        raise NotImplementedError


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ---------------------------------------------------------------------------
# SQLite backend (standard library only)
# ---------------------------------------------------------------------------
class SqliteStore(Store):
    def __init__(self, path="sylvan_cache.db"):
        self.path = path
        self.name = f"sqlite:{os.path.basename(path)}"
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS cache ("
                    "key TEXT PRIMARY KEY, value TEXT NOT NULL, "
                    "created_at REAL NOT NULL, expires_at REAL)"
                )
        except sqlite3.Error as e:
            raise StoreError(f"could not open SQLite file {path}: {e}") from None

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def get(self, key):
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,)).fetchone()
            if row is None:
                return None
            value, expires_at = row
            if expires_at is not None and expires_at <= time.time():
                with conn:
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                return None
            return json.loads(value)

    def set(self, key, value, ttl_seconds=None):
        now = time.time()
        expires = None if ttl_seconds is None else now + ttl_seconds
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO cache (key, value, created_at, expires_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (key) DO UPDATE SET value = excluded.value, "
                "created_at = excluded.created_at, expires_at = excluded.expires_at",
                (key, json.dumps(value), now, expires),
            )

    def delete(self, key):
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))

    def clear(self, prefix=""):
        with closing(self._connect()) as conn, conn:
            cur = conn.execute("DELETE FROM cache WHERE key LIKE ? ESCAPE '\\'", (_escape_like(prefix) + "%",))
            return cur.rowcount

    def count(self):
        with closing(self._connect()) as conn:
            return conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]


# ---------------------------------------------------------------------------
# Postgres backend (needs: pip install psycopg2-binary, and a running server)
# ---------------------------------------------------------------------------
class PostgresStore(Store):
    def __init__(self, dsn):
        try:
            import psycopg2
            from psycopg2.extensions import parse_dsn
        except ImportError:
            raise StoreError("Postgres needs the driver: pip install psycopg2-binary") from None
        self._psycopg2 = psycopg2
        self.dsn = dsn
        try:
            parts = parse_dsn(dsn)
            self.name = f"postgres:{parts.get('host', 'local')}/{parts.get('dbname', '?')}"
        except psycopg2.Error:
            raise StoreError("SYLVAN_DB_URL is not a valid Postgres connection string") from None
        try:
            with closing(self._connect()) as conn, conn, conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS cache ("
                    "key TEXT PRIMARY KEY, value JSONB NOT NULL, "
                    "created_at DOUBLE PRECISION NOT NULL, expires_at DOUBLE PRECISION)"
                )
        except psycopg2.Error as e:
            raise StoreError(f"could not use Postgres ({self.name}): {type(e).__name__}: "
                             f"{str(e).strip().splitlines()[0] if str(e).strip() else ''}") from None

    def _connect(self):
        return self._psycopg2.connect(self.dsn, connect_timeout=5)

    def get(self, key):
        with closing(self._connect()) as conn, conn, conn.cursor() as cur:
            cur.execute("SELECT value, expires_at FROM cache WHERE key = %s", (key,))
            row = cur.fetchone()
            if row is None:
                return None
            value, expires_at = row
            if expires_at is not None and expires_at <= time.time():
                cur.execute("DELETE FROM cache WHERE key = %s", (key,))
                return None
            return value  # psycopg2 already turns JSONB into Python objects

    def set(self, key, value, ttl_seconds=None):
        now = time.time()
        expires = None if ttl_seconds is None else now + ttl_seconds
        with closing(self._connect()) as conn, conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO cache (key, value, created_at, expires_at) VALUES (%s, %s::jsonb, %s, %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, "
                "created_at = EXCLUDED.created_at, expires_at = EXCLUDED.expires_at",
                (key, json.dumps(value), now, expires),
            )

    def delete(self, key):
        with closing(self._connect()) as conn, conn, conn.cursor() as cur:
            cur.execute("DELETE FROM cache WHERE key = %s", (key,))

    def clear(self, prefix=""):
        with closing(self._connect()) as conn, conn, conn.cursor() as cur:
            cur.execute("DELETE FROM cache WHERE key LIKE %s ESCAPE '\\'", (_escape_like(prefix) + "%",))
            return cur.rowcount

    def count(self):
        with closing(self._connect()) as conn, conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cache")
            return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Choosing a backend
# ---------------------------------------------------------------------------
def get_store():
    kind = os.environ.get("SYLVAN_STORE", "sqlite").strip().lower()
    if kind == "sqlite":
        return SqliteStore(os.environ.get("SYLVAN_SQLITE_PATH", "sylvan_cache.db"))
    if kind in ("postgres", "postgresql"):
        dsn = os.environ.get("SYLVAN_DB_URL", "").strip()
        if not dsn:
            raise StoreError("SYLVAN_STORE=postgres needs SYLVAN_DB_URL, e.g. "
                             "postgresql://user:password@localhost:5432/sylvan")
        return PostgresStore(dsn)
    raise StoreError(f"unknown SYLVAN_STORE '{kind}' (use sqlite or postgres)")


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------
def make_key(namespace, lat, lon, radius=None, version=1, extra=""):
    """
    Key = namespace, a version number, coordinates rounded to 4 decimals (about 11 m, so a
    tiny change in the pin still hits), and the terrain radius when it matters. Bump the
    version when the code that produces the value changes, so old values are not reused.
    """
    parts = [namespace, f"v{version}", f"{lat:.4f}", f"{lon:.4f}"]
    if radius is not None:
        parts.append(f"r{radius:g}")
    if extra:
        parts.append(str(extra))
    return ":".join(parts)


def cached(store, key, ttl_seconds, compute, refresh=False):
    """
    Returns (value, status). status: "hit", "miss", "refreshed" or "no-cache".
    Values go through JSON on every path, so a hit and a miss return identical shapes
    (for example dict keys are always strings). A failing store never stops the analysis.
    """
    if store is not None and not refresh:
        try:
            value = store.get(key)
            if value is not None:
                return value, "hit"
        except Exception as e:  # best-effort cache
            print(f"[cache read failed, recomputing: {type(e).__name__}]")

    value = json.loads(json.dumps(compute()))
    if store is None:
        return value, "no-cache"
    try:
        store.set(key, value, ttl_seconds)
    except Exception as e:
        print(f"[cache write failed: {type(e).__name__}]")
    return value, "refreshed" if refresh else "miss"
