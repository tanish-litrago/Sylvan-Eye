# Sylvan Eye - the app container (layer 1; layer 2 adds the Postgres driver).
# Credentials are NOT built in: the Earth Engine login is mounted at run time (docker-compose.yml).

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
COPY requirements.txt requirements-postgres.txt ./
RUN pip install -r requirements.txt -r requirements-postgres.txt

COPY --chown=app:app . .

USER app

# Without compose (plain `docker run`) the cache is SQLite, kept in /data (mount a volume there).
# With docker-compose.yml the cache is Postgres instead.
ENV SYLVAN_SQLITE_PATH=/data/sylvan_cache.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

# 0.0.0.0 is the address INSIDE the container (needed so Docker can reach it).
# Who can reach the page from outside is decided by the 127.0.0.1 port mapping in docker-compose.yml.
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]