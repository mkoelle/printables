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
  -> `cage.py` -> `test_kit.py`. `build_all.py` does all of it.
- `tophat_param.py` recreates `TopHat` from its parameter defaults, which
  discards spreadsheet-only edits.

## Verifying a change

Every script prints validity, solid count, overlaps and bed fit. After a
change, confirm:

- all parts `valid True solids 1`;
- overlaps 0, except the wedge lip / finger press, which is intended;
- `fits=True` (220 mm bed);
- rails show no head-dome overlap;
- for hat-wide changes, rerun at `HeadCirc` 550 and 610 mm, then reset to 570.

## FreeCAD gotchas found in this project

- Fuse many shapes in one call (`a.fuse([b, c])`, as `rail.fuse` does).
  Chained pairwise fuses produced invalid solids.
- `removeSplitter()` can break a valid solid; check `isValid()` after it.
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
  45 deg, sliders on their back.
- `.FCBak` files are FreeCAD's automatic backups.
