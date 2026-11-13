# printables: agent notes

Monorepo of 3D-printable projects, one folder each. Before working on a
project, read its `CLAUDE.md` and `README.md`.

- FreeCAD 1.1 on macOS, driven through the MCP addon's RPC server
  (`127.0.0.1:9875`).
- Build with each project's mise tasks (`mise run build` in the project
  folder). They run scripts through `tools/fc.py`, which locks so builds
  never overlap and exits non-zero on errors or failed checks. Run long
  builds in the background.
- Use the `freecad` MCP server (`execute_code`) to inspect models, not to
  build: it skips the lock. If a call times out, FreeCAD keeps running:
  check `get_rpc_status`, then verify the saved results instead of
  rerunning.
- Setup for people (FreeCAD, the MCP addon, Claude Code) is in the root
  `README.md`. Keep it current when the toolchain changes.
- Scripts find their files from their own `__file__`; never hard-code repo
  paths. Run a script with `__file__` set (`fc.py` does).
- Keep projects independent: no imports across project folders.
- New project: create `<name>/` with `README.md`, `CLAUDE.md`, `mise.toml`,
  `models/`, `lib/` and `stl/` (layout in the root `README.md`), add a row
  to the table there, and make the root `build` task run its build.
- Print limits: 220 x 220 mm bed, PLA. Check that every exported part fits.
