# Sylvan Eye - the app container (layer 1; layer 2 adds the Postgres driver, layer 3 the Redis driver).
# The build context is the PROJECT folder (docker-compose.yml sets it with context: ..), so COPY
# paths below start from the project root. Credentials are NOT built in: the Earth Engine login
# is mounted at run time (docker-compose.yml).

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# A normal user instead of root. /data holds the cache (a Docker volume is mounted there);
# /home/app/.config/earthengine is where the Earth Engine login folder gets mounted.
# earthengine-api looks for its login at ~/.config/earthengine/credentials, so HOME must be /home/app.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app \
 && mkdir -p /app /data /home/app/.config/earthengine \
 && chown -R app:app /app /data /home/app

WORKDIR /app

# Dependencies first, so editing app code does not reinstall them (Docker reuses this layer).
COPY requirements/requirements.txt requirements/requirements-postgres.txt requirements/requirements-redis.txt ./requirements/
RUN pip install -r requirements/requirements.txt -r requirements/requirements-postgres.txt -r requirements/requirements-redis.txt

COPY --chown=app:app . .

USER app

# Without compose (plain `docker run`) the cache is SQLite, kept in /data (mount a volume there).
# With docker-compose.yml the cache is Postgres instead.
ENV SYLVAN_SQLITE_PATH=/data/sylvan_cache.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=3)"

# 0.0.0.0 is the address INSIDE the container (needed so Docker can reach it).
# Who can reach the page from outside is decided by the 127.0.0.1 port mapping in docker-compose.yml.
# A host such as Render sets PORT; locally and in compose it stays 8000.
CMD ["sh", "-c", "python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]