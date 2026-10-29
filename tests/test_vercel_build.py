"""
Tests for scripts/vercel_build.sh (the Vercel build for the page): python -m tests.test_vercel_build
Skipped where there is no `sh` (plain Windows); it always runs on GitHub Actions and on Vercel.
"""

import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = shutil.which("sh")


def build(env_value):
    work = tempfile.mkdtemp()
    try:
        shutil.copytree(os.path.join(ROOT, "static"), os.path.join(work, "static"))
        env = {k: v for k, v in os.environ.items() if k != "SYLVAN_API_BASE"}
        if env_value is not None:
            env["SYLVAN_API_BASE"] = env_value
        out = subprocess.run([SH, os.path.join(ROOT, "scripts", "vercel_build.sh")], cwd=work, env=env,
                             capture_output=True, text=True)
        files = {}
        for name in ("public/index.html", "public/static/app.js", "public/static/config.js",
                     "public/static/vendor/leaflet/leaflet.js"):
            path = os.path.join(work, *name.split("/"))
            files[name] = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        return out, files
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_build_copies_the_page_and_writes_the_backend_address():
    out, files = build("https://sylvan-eye-api.onrender.com/")
    assert out.returncode == 0, out.stderr
    assert files["public/index.html"] and files["public/static/app.js"] and files["public/static/vendor/leaflet/leaflet.js"]
    assert 'window.SYLVAN_API_BASE = "https://sylvan-eye-api.onrender.com";' in files["public/static/config.js"]   # no trailing slash


def test_build_refuses_a_missing_or_unsafe_address():
    for value in (None, "", 'https://x.example"; alert(1); "', "https://x.example/ a"):
        out, files = build(value)
        assert out.returncode != 0 and files["public/static/config.js"] is None, repr(value)


if __name__ == "__main__":
    if SH is None:
        print("SKIPPED  no `sh` on this machine (the build runs on Vercel and on GitHub Actions)")
    else:
        test_build_copies_the_page_and_writes_the_backend_address()
        test_build_refuses_a_missing_or_unsafe_address()
    print("all vercel build tests passed")
