"""Rebuild everything in order, inside FreeCAD (Python console or MCP execute_code).

  exec(open(os.path.expanduser("~/src/github.com/mkoelle/printables/tophat/build_all.py")).read())

1. tophat_param.py  rebuild TopHat from the parameter defaults in that script
2. save TopHat.FCStd
3. export_stl.py    hat part STLs
4. cage.py          CageFingers model + STL (reads TopHat)
5. test_kit.py      TopHatFitTests / FixtureTests / RailTests models + STLs

Step 1 discards any Params edits made only in the spreadsheet; put lasting
changes in the main / advanced lists in tophat_param.py.
"""
import os
import FreeCAD as App

DIR = os.path.expanduser("~/src/github.com/mkoelle/printables/tophat")
for name in ("CageFingers", "TopHatFitTests", "FixtureTests", "RailTests"):
    if name in App.listDocuments():
        App.closeDocument(name)

for step in ("tophat_param.py", "SAVE", "export_stl.py", "cage.py", "test_kit.py"):
    print(f"=== {step}")
    if step == "SAVE":
        App.getDocument("TopHat").saveAs(os.path.join(DIR, "TopHat.FCStd"))
        continue
    exec(open(os.path.join(DIR, step)).read())
