# Top hat project: agent notes

Read `README.md` first (parts, files, decisions, status) and `TESTING.md`
(test prints). This file covers how to work on the code.

## Layout

- `models/`: the scripts you run, one per build step: `hat.py` (the
  `TopHat` model), `export.py` (hat STLs), `cage.py`, `tests.py`,
  `mounts.py` (components), `layout.py` (components placed in the hat), and
  `build_all.py` (hat to tests in order).
- `mounts/`: one module per rail component, loaded by `mount.load`; the
  contract is in `lib/mount.py` and `mounts/README.md`.
- `lib/`: imported only. `common.py` (project paths, `open_model` /
  `new_model` / `save_model`, shapes, `reader`, `place` / `write_stl` for
  print orientation and export, `grams`, checks), `seam.py` (brim seam
  key), `rail.py` (rails and sliders), `mount.py` (slider shoes, rail
  frames from the cage's `Rails` sheet, the component catalogue). Import
  `mount` after reloading `rail`: it reads `rail` when it loads. Each script in `models/` puts `lib/`
  first on `sys.path` and reloads these.
- `build/`: generated `.FCStd` models and FreeCAD's `.FCBak` backups, not in
  git. `stl/parts/`: the hat. `stl/tests/`: test coupons. `stl/mounts/`:
  components.
- Paths come from each script's own `__file__` (`common.PROJECT`), so the
  repo can live anywhere. A script must run with `__file__` set (see below).

## Running the scripts

- All scripts run inside the FreeCAD GUI (FreeCAD 1.1, macOS), not plain
  Python. FreeCAD must be open with the MCP addon's RPC server started.
- Build with mise from `tophat/`. Each task runs one script through
  `../tools/fc.py` and is skipped when its outputs are newer than its
  sources:
  - `mise run build`: everything that changed (all steps after a clone,
    about 10 minutes: hat 3.5, export 2, cage 2, tests 2)
  - `mise run hat`, `export`, `cage`, `tests`: one step, after any step it
    depends on that is out of date. `mise run -f --skip-deps <step>`
    reruns only that step (`-f` alone forces its dependencies too)
  - `mise run tests --groups fixtures`: only some test groups (`fit`,
    `fixtures`, `rail`); fixtures alone take about 1 minute
  - `mise run mounts`, `mise run layout`: components, and their fit in the
    hat (edit `LAYOUT` in `models/layout.py`)
- Run builds through mise (or `python3 ../tools/fc.py models/<script>.py`),
  not through MCP `execute_code`. `fc.py` takes a lock so two builds never
  run in FreeCAD at once, and exits non-zero on an error or failed check.
  A long build can outlast the Bash tool's timeout: run it in the
  background.
- Use MCP `execute_code` only to inspect models. To run a script there, set
  `__file__`: `p = ".../tophat/models/<script>.py"; exec(open(p).read(),
  {"__file__": p})`. Pass `include_screenshot: false` unless you need to see
  the model.
- `models/hat.py` is the single source of truth: it recreates `TopHat`
  from its parameter lists, builds every part as a plain `Part::Feature`
  shape and saves `build/TopHat.FCStd`, so spreadsheet edits do nothing.
  The documents keep only the finished parts (`Crown`, `CrownCut`,
  `CageLip`, `BrimRing`, `BrimQ<n>`), which the other scripts read.
- When you add an input to a script (a new `lib/` module, another model),
  add it to that task's `sources` in `mise.toml`, or edits to it will not
  trigger a rebuild.

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
- New dimensions go in the parameter lists in `models/hat.py` as Main,
  Advanced (formula) or Derived, with a note.
- Print orientation is set at export with `common.place`: crown flipped,
  wide oval parts turned 45 deg, brim pieces stood on their socket seam
  face, sliders front-down (tongue on the bed).
- `build/*.FCBak` files are FreeCAD's automatic backups.
