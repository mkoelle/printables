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
  -> `cage.py` -> `test_kit.py`. `build_all.py` does all of it in about
  10 minutes (model 3.5, export 2, cage 2, tests 2). That can outlast one
  MCP call, so run the steps as separate calls.
- Rebuild only what a change touches. `cage.py`: only when the crown, lip,
  head or `rail.py` changes. `test_kit.py`: set `TEST_GROUPS` (any of
  "fit", "fixtures", "rail") in the same `execute_code` call before the
  `exec`; fixtures alone take about 1 minute. `build_all.py` takes
  `BUILD_STEPS` the same way.
- The `.FCStd` models are generated and not in git (`.gitignore`). After a
  fresh clone, run `build_all.py` before `cage.py` or `test_kit.py`.
- `tophat_param.py` is the single source of truth: it recreates `TopHat`
  from its parameter lists and builds every part as a plain `Part::Feature`
  shape, so spreadsheet edits do nothing. The documents keep only the
  finished parts (`Crown`, `CrownCut`, `CageLip`, `BrimRing`,
  `BrimQ<n>`), which the other scripts read.
- Shared code: `common.py` (shapes, `reader`, `place` / `write_stl` for
  print orientation and export, `grams`, checks), `seam.py` (brim seam
  key), `rail.py` (rails and sliders). Each script puts the folder on
  `sys.path` and reloads them.

## Verifying a change

Each script ends with `<script>: ALL CHECKS PASS`, or lists each failed
check (validity, single solid, printer fit against `Bed` and `BedH`,
overlaps, wedge-lip press, rail head clearance). Record new pass/fail conditions with `common.check`. Also:

- for hat-wide changes, rerun at `SIZE` "S" and "XL", then reset to "M";
- compare part weights with the README status when a change should not
  alter them.

## FreeCAD gotchas found in this project

- Fuse many shapes in one call (`a.fuse([b, c])`, as `common.fuse` does).
  Chained pairwise fuses produced invalid solids.
- `removeSplitter()` can break a valid solid; check `isValid()` after it
  (`common.refined` does). A boolean result shares geometry with its
  inputs, and `removeSplitter()` on it left the input `CrownCut` invalid,
  so `common.refined` and `common.fuse` work on a `copy()`. Refining the
  brim fuse left `BrimRing` invalid, so it stays unrefined.
- `Shape.BoundBox` is loose on refined or fused shapes; use
  `optimalBoundingBox()` for sizes and bed placement.
- `TopoShape.rotate/translate` change the shape's Placement. When putting
  such a shape in a `Part::Feature`, multiply placements instead of setting
  `Placement.Base`.
- FreeCAD expression trig (in the Params formulas) uses degrees.
- Engraved text uses `/System/Library/Fonts/Supplemental/Arial Bold.ttf`
  (macOS only).

## Conventions

- Units mm. X = front/back (long head axis), Y = sides, Z up from the brim
  underside. Ellipse parameter `t` (degrees) places features round the oval.
- New dimensions go in the parameter lists in `tophat_param.py` as Main,
  Advanced (formula) or Derived, with a note.
- Print orientation is set at export with `common.place`: crown flipped,
  wide oval parts turned 45 deg, brim pieces stood on their socket seam
  face, sliders front-down (tongue on the bed).
- `.FCBak` files are FreeCAD's automatic backups.
