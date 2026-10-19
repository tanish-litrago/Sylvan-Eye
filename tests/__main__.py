"""
Run the tests from the project folder:

    python -m tests                 every test file, one line each
    python -m tests jobs storage    only test_jobs.py and test_storage.py
    python -m tests.test_jobs       one file, with its full output

Each file runs in its own process, so one cannot leak into another. A part that was skipped
(for example the Redis checks without SYLVAN_TEST_REDIS_URL) is shown under its file.
"""

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main(argv):
    names = sorted(os.path.splitext(os.path.basename(p))[0]
                   for p in glob.glob(os.path.join(HERE, "test_*.py")))
    if argv:
        wanted = [a if a.startswith("test_") else f"test_{a}" for a in argv]
        unknown = [w for w in wanted if w not in names]
        if unknown:
            print("No such test file:", ", ".join(unknown))
            return 2
        names = [n for n in names if n in wanted]
    failed = []
    for name in names:
        r = subprocess.run([sys.executable, "-m", f"tests.{name}"], cwd=ROOT,
                           capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        print(("ok    " if r.returncode == 0 else "FAIL  ") + name)
        for line in out.splitlines():
            if line.startswith("SKIPPED"):
                print("        " + line)
        if r.returncode != 0:
            failed.append(name)
            for line in out.strip().splitlines()[-8:]:
                print("        " + line)
    print()
    print(f"{len(names) - len(failed)} of {len(names)} test files passed" +
          (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
