# Plague mask: agent notes

Read `README.md` for the agreed requirements, planned parts, measurements and
test plan. `mask.py` builds the model; its parameters are the dicts at the top.

- Follow the build approach proven in `../tophat`: FreeCAD 1.1 scripts run
  through the `freecad` MCP `execute_code` tool; a `Params` spreadsheet with
  Main / Advanced / Derived sections; scripts as the source of truth; STLs
  exported pre-oriented for the 220 x 220 mm bed; test coupons cut from the
  real model. Read `../tophat/CLAUDE.md` for the FreeCAD gotchas found there
  (single-call multi-fuse, `optimalBoundingBox`, `removeSplitter` validity,
  Placement handling).
- Keep this project independent: copy code from `../tophat` if useful, do not
  import across folders.
- Every style part (beak, eye bezel, trim) must fit the shared sockets on the
  base shell; check fits with overlap tests like `tophat/test_kit.py`.
- Nothing may block the wearer's breathing: keep the vent area a parameter
  and report it on every build.

## Running mask.py

- Run stages one MCP call at a time while developing:
  `MASK_STAGES = ["shell"]` then exec the file, then `["eyes"]`, and so on.
  Results stay in the FreeCAD session's globals between calls. Each stage
  prints its time; a full build takes about 40 s.
- Never run the whole build in one call while debugging: a hang blocks the
  FreeCAD GUI, and stopping the MCP task does not interrupt it (only
  force-quitting FreeCAD does).
- Booleans against the finished `shell` near the eye sockets return empty
  shapes (valid shell, `fix()` does not help). Build coupons and the fit frame
  from `outer.cut(inner).common(keep)` plus the socket parts instead.
- Cross-sections are 24-point B-spline superellipses (`SEC_PTS`); 64 points
  made booleans far slower.
