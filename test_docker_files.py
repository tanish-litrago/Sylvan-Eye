"""
Checks the safety rules of the Docker files by reading them as text (no Docker, no YAML library).

    python test_docker_files.py

Rules checked (layers 1-3):
  - the page is published on 127.0.0.1 only
  - the container does not run as root
  - the Earth Engine login is mounted read-only and never copied into the image
  - .dockerignore excludes .env, *.db, venv/ and .git
  - .gitignore excludes .env, *.db and venv/; .env.example exists and holds no real secret
  - no password, key or token written in docker-compose.yml or the Dockerfile
"""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
failures = 0


def check(name, ok, detail=""):
    global failures
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  -> {detail}"))
    if not ok:
        failures += 1


def read(name):
    p = HERE / name
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else None


def code_lines(lines):
    """Lines without comments and blank lines."""
    return [l for l in lines if l.strip() and not l.strip().startswith("#")]


def list_items(lines, key):
    """The '- item' lines under every 'key:' (simple indentation reader for our compose file)."""
    items = []
    for i, line in enumerate(lines):
        if line.strip() == f"{key}:":
            indent = len(line) - len(line.lstrip())
            for nxt in lines[i + 1:]:
                if not nxt.strip() or nxt.strip().startswith("#"):
                    continue
                if len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                if nxt.strip().startswith("- "):
                    items.append(nxt.strip()[2:].strip().strip('"').strip("'"))
    return items


SECRET_WORDS = re.compile(r"PASS|SECRET|TOKEN|KEY|CREDENTIAL|DB_URL|REDIS_URL", re.I)


def literal_secrets(lines):
    """KEY: value / KEY=value lines whose name looks secret and whose value is a literal, not ${...}."""
    bad = []
    for l in code_lines(lines):
        m = re.match(r"\s*(?:-\s*)?(?:ENV\s+|ARG\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*)$", l)
        if not m:
            continue
        name, value = m.group(1), m.group(2).strip().strip('"').strip("'")
        if "://" in value:
            continue  # a URL: judged by the password check below
        if SECRET_WORDS.search(name) and value and not value.startswith("${"):
            bad.append(f"{name}={value}")
    # a connection string with a literal password: scheme://user:password@host
    for l in code_lines(lines):
        for m in re.finditer(r"://[^/\s:@]+:([^@\s]+)@", l):
            if not m.group(1).startswith("${"):
                bad.append(l.strip())
    return bad


def main():
    dockerfile, compose = read("Dockerfile"), read("docker-compose.yml")
    dignore, gignore, example = read(".dockerignore"), read(".gitignore"), read(".env.example")

    print("== files exist ==")
    for name, content in [("Dockerfile", dockerfile), ("docker-compose.yml", compose),
                          (".dockerignore", dignore), (".gitignore", gignore),
                          (".env.example", example)]:
        check(f"{name} exists", content is not None)
    if None in (dockerfile, compose, dignore, gignore, example):
        return

    print("\n== the page is published on 127.0.0.1 only ==")
    ports = list_items(compose, "ports")
    check("compose publishes at least one port", len(ports) > 0)
    check("every published port starts with 127.0.0.1:",
          all(p.startswith("127.0.0.1:") for p in ports), str(ports))
    check("only the app publishes a port (the database has none)", len(ports) == 1, str(ports))
    check("no 0.0.0.0 mapping and no host networking",
          not any("0.0.0.0" in p for p in ports)
          and not any(re.match(r"\s*network_mode:\s*[\"']?host", l) for l in compose))

    print("\n== not root ==")
    users = [l.split(None, 1)[1].strip() for l in dockerfile if re.match(r"\s*USER\s+\S+", l)]
    check("Dockerfile sets a USER", len(users) > 0)
    check("the last USER is not root or 0",
          bool(users) and users[-1].split(":")[0].lower() not in ("root", "0"), str(users))
    check("compose does not force root or privileged mode",
          not any(re.match(r"\s*user:\s*[\"']?(root|0)\b", l) for l in compose)
          and not any(re.match(r"\s*privileged:\s*true", l) for l in compose))

    print("\n== Earth Engine login ==")
    ee = [v for v in list_items(compose, "volumes") if "earthengine" in v]
    check("compose mounts an earthengine folder", len(ee) == 1, str(ee))
    check("that mount is read-only (:ro)", all(v.endswith(":ro") for v in ee), str(ee))
    copies = [l for l in code_lines(dockerfile) if re.match(r"\s*(COPY|ADD)\b", l)]
    check("Dockerfile never copies a credentials file, .env or .config",
          not any(re.search(r"credential|\.env\b|\.config", l, re.I) for l in copies), str(copies))

    print("\n== .dockerignore ==")
    entries = [l.strip().rstrip("/") for l in code_lines(dignore)]
    for want, fits in [(".env", {".env", "**/.env"}), ("*.db", {"*.db", "**/*.db"}),
                       ("venv/", {"venv", "**/venv"}), (".git", {".git", "**/.git"})]:
        check(f".dockerignore excludes {want}", any(e in fits for e in entries), str(entries))

    print("\n== git and secrets ==")
    g = [l.strip().rstrip("/") for l in code_lines(gignore)]
    for want in [".env", "*.db", "venv"]:
        check(f".gitignore excludes {want}", want in g, str(g))
    check("no literal password, key or token in docker-compose.yml",
          not literal_secrets(compose), str(literal_secrets(compose)))
    check("no literal password, key or token in the Dockerfile",
          not literal_secrets(dockerfile), str(literal_secrets(dockerfile)))
    check(".env.example holds no real secret (secret names must be empty or a placeholder)",
          not [s for s in literal_secrets(example)
               if not re.search(r"change-?me|your|xxx|\.\.\.", s, re.I)],
          str(literal_secrets(example)))

    print("\n== Postgres (layer 2) ==")
    text = "\n".join(compose)
    check("app gets its database URL with the password as a ${POSTGRES_PASSWORD} reference",
          re.search(r"SYLVAN_DB_URL:.*:\$\{POSTGRES_PASSWORD[^}]*\}@", text) is not None)
    check("the db service sets its password from ${POSTGRES_PASSWORD}",
          re.search(r"POSTGRES_PASSWORD:\s*[\"']?\$\{POSTGRES_PASSWORD", text) is not None)
    check("the app waits for a healthy database",
          "service_healthy" in text and "pg_isready" in text)
    check(".env.example leaves POSTGRES_PASSWORD empty",
          any(re.fullmatch(r"POSTGRES_PASSWORD=\s*", l.strip()) for l in example))

    print("\n== Redis (layer 3) ==")
    check("the app is told to use Redis for job records",
          re.search(r"SYLVAN_JOBS:\s*redis\b", text) is not None
          and re.search(r"SYLVAN_REDIS_URL:\s*redis://redis:6379", text) is not None)
    check("the redis service has a healthcheck and the app waits for it",
          "redis-cli" in text and text.count("service_healthy") >= 2)
    check("the Dockerfile installs the Redis driver",
          any(l.strip().startswith("RUN") and "requirements-redis.txt" in l for l in code_lines(dockerfile)))
    check("Redis is not given a literal password in a URL",
          not re.search(r"redis://[^/\s:@]*:[^@\s$]+@", text))

    print()
    print("All Docker file checks passed." if failures == 0 else f"{failures} CHECK(S) FAILED.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()