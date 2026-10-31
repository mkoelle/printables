# Top hat project: agent notes

Read `README.md` first (parts, files, decisions, status) and `TESTING.md`
(test prints). This file covers how to work on the code.

## Running the scripts

- All scripts run inside the FreeCAD GUI (FreeCAD 1.1, macOS), not plain Python.
- Use the `freecad` MCP server's `execute_code` tool:
  `exec(open("/Users/mkoelle/src/github.com/mkoelle/printables/tophat/<script>.py").read())`.
  Pass `timeout` 600-1800 for cage and test builds; pass
  `include_screenshot: false` unless you need to see the model.
- If MCP tools are not loaded, the addon's XML-RPC server on `localhost:9875`
  takes the same call:
  `xmlrpc.client.ServerProxy("http://localhost:9875").execute_code(src)`.
  FreeCAD must be running with the MCP addon's RPC server started.
- Rebuild order: `tophat_param.py` -> save `TopHat.FCStd` -> `export_stl.py`
  -> `cage.py` -> `test_kit.py`. `build_all.py` does all of it, but takes
  longer than one MCP call allows (over 30 min); run the steps as separate
  calls. `cage.py` only needs rerunning when the crown, lip or `rail.py`
  changes.
- `tophat_param.py` recreates `TopHat` from its parameter defaults, which
  discards spreadsheet-only edits.
- Some geometry is built in Python when `tophat_param.py` runs, not driven
  by spreadsheet expressions: `BrimSegs`, the edge binding (`Rim`) and the
  dovetail keys and seam reliefs (`KeyPrism<q>`, `SeamCut<q>`). Rerun the
  script after changing the parameters they read.

## Verifying a change

Every script prints validity, solid count, overlaps and bed fit. After a
change, confirm:

- all parts `valid True solids 1`;
- overlaps 0, except the wedge lip / finger press, which is intended;
- `fits=True` (`Bed`, 220 mm by default);
- rails show no head-dome overlap;
- for hat-wide changes, rerun at `SIZE` "S" and "XL", then reset to "M";
- `tophat_param.py` prints the brim segment count and crown fit; it must not
  say `DOES NOT FIT` for the size you print.

## FreeCAD gotchas found in this project

- Fuse many shapes in one call (`a.fuse([b, c])`, as `rail.fuse` does).
  Chained pairwise fuses produced invalid solids.
- `removeSplitter()` can break a valid solid; check `isValid()` after it.
  The same goes for `Refine` on Part boolean features, whose default comes
  from the user's preferences: it left `BrimRing` invalid, so `BrimSolid`
  and `BrimRing` set `Refine = False`.
- `Shape.BoundBox` is loose on refined or fused shapes; use
  `optimalBoundingBox()` for sizes and bed placement.
- `TopoShape.rotate/translate` change the shape's Placement. When putting
  such a shape in a `Part::Feature`, multiply placements instead of setting
  `Placement.Base`.
- FreeCAD expression trig uses degrees.
- Engraved text uses `/System/Library/Fonts/Supplemental/Arial Bold.ttf`
  (macOS only).

## Conventions

- Units mm. X = front/back (long head axis), Y = sides, Z up from the brim
  underside. Ellipse parameter `t` (degrees) places features round the oval.
- New dimensions go in the `Params` spreadsheet (`tophat_param.py`) as Main,
  Advanced (formula) or Derived, with a note.
- Print orientation is set at export: crown flipped, wide oval parts turned
  45 deg, sliders front-down (tongue on the bed).
- `.FCBak` files are FreeCAD's automatic backups.
