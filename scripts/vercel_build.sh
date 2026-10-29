#!/bin/sh
# Vercel build for the page only (the backend runs elsewhere, for example on Render).
# Copies static/ into public/ and writes public/static/config.js from the SYLVAN_API_BASE setting,
# for example https://sylvan-eye-api.onrender.com . Run from the project folder.
set -eu

base="${SYLVAN_API_BASE:-}"
base="${base%/}"
case "$base" in
  *[!A-Za-z0-9:/._-]*) echo "SYLVAN_API_BASE may only hold letters, digits and : / . _ -" >&2; exit 1 ;;
esac
if [ -z "$base" ]; then
  echo "SYLVAN_API_BASE is not set: the page would look for the backend on Vercel itself." >&2
  exit 1
fi

rm -rf public
mkdir -p public/static
cp -r static/. public/static/
cp static/index.html public/index.html
printf '// Written by scripts/vercel_build.sh.\nwindow.SYLVAN_API_BASE = "%s";\n' "$base" > public/static/config.js
echo "public/ ready, backend at $base"
