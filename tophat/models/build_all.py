"""Rebuild the whole top hat in order, inside FreeCAD.

From the repo, `mise run build` is usually better: it runs the same steps
but skips those whose inputs have not changed (see CLAUDE.md). This script
always runs every step. In FreeCAD's Python console:

  p = "<repo>/tophat/models/build_all.py"; exec(open(p).read(), {"__file__": p})

1. hat.py     TopHat model from the parameter lists in hat.py
2. export.py  hat part STLs (reads TopHat)
3. cage.py    CageFingers model + STL (reads TopHat)
4. tests.py   TopHatFitTests / FixtureTests / RailTests models + STLs

Models go to build/ (not in git), STLs to stl/. Each script ends with
"<script>: ALL CHECKS PASS" or a list of failures. A full run takes about
10 minutes.

To run only some steps, or some test groups, add them to the dict:
  {"__file__": p, "BUILD_STEPS": ("hat", "export"), "TEST_GROUPS": {"fixtures"}}
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = globals().get("BUILD_STEPS") or ("hat", "export", "cage", "tests")
OPTS = {k: globals()[k] for k in ("TEST_GROUPS",) if k in globals()}

for step in STEPS:
    print(f"=== {step}")
    path = str(HERE / f"{step}.py")
    exec(compile(open(path).read(), path, "exec"), {"__file__": path, "__name__": "__main__", **OPTS})
