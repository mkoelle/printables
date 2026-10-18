# Plague mask: agent notes

Read `README.md` for the agreed requirements, planned parts, measurements and
test plan. The project is in pre-design: nothing is modelled yet.

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
