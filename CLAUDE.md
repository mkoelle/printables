# printables: agent notes

Monorepo of 3D-printable projects, one folder each. Before working on a
project, read its `CLAUDE.md` and `README.md`.

- FreeCAD 1.1 on macOS, reached through the `freecad` MCP server
  (`execute_code`). Fallback: the addon's XML-RPC server on `localhost:9875`.
- Scripts in each project use absolute paths under
  `~/src/github.com/mkoelle/printables/<project>`. Update them if a project
  moves.
- Keep projects independent: no imports across project folders.
- New project: create `<name>/` with `README.md`, `CLAUDE.md` and `stl/`, and
  add a row to the table in the root `README.md`.
- Print limits: 220 x 220 mm bed, PLA. Check that every exported part fits.
