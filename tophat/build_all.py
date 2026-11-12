"""Rebuild everything in order, inside FreeCAD (Python console or MCP execute_code).

  exec(open(os.path.expanduser("~/src/github.com/mkoelle/printables/tophat/build_all.py")).read())

1. tophat_param.py  rebuild TopHat from the parameter lists in that script
2. save TopHat.FCStd
3. export_stl.py    hat part STLs
4. cage.py          CageFingers model + STL (reads TopHat)
5. test_kit.py      TopHatFitTests / FixtureTests / RailTests models + STLs

Each script ends with "<script>: ALL CHECKS PASS" or a list of failures.

To rebuild only part of it, set these before exec (both are consumed):
  BUILD_STEPS = ("tophat_param.py", "SAVE", "export_stl.py")  # skip cage, tests
  TEST_GROUPS = {"fixtures"}                                  # fit, fixtures, rail
cage.py only needs rerunning when the crown, lip, head or rail.py changes;
the fit and rail tests only when head size or rail.py changes.

The .FCStd models are not in git: after a fresh clone, run this once before
cage.py or test_kit.py. A full run takes about 10 minutes, which can outlast
one MCP call; from Claude, run the steps as separate calls (FreeCAD
finishes a timed-out call).
"""
import os
import FreeCAD as App

DIR = os.path.expanduser("~/src/github.com/mkoelle/printables/tophat")
STEPS = globals().pop("BUILD_STEPS", None) or (
    "tophat_param.py", "SAVE", "export_stl.py", "cage.py", "test_kit.py")
for name in ("CageFingers", "TopHatFitTests", "FixtureTests", "RailTests"):
    if name in App.listDocuments():
        App.closeDocument(name)

for step in STEPS:
    print(f"=== {step}")
    if step == "SAVE":
        App.getDocument("TopHat").saveAs(os.path.join(DIR, "TopHat.FCStd"))
        continue
    exec(open(os.path.join(DIR, step)).read())
