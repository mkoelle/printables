# printables

Personal 3D-printable models. One folder per project; each is self-contained
with its own scripts, FreeCAD models, STLs and docs.

| Project | Description | Status |
|---------|-------------|--------|
| [tophat](tophat/) | Parametric top hat with a hidden cage for storage and IoT devices | Test prints (round 3 done; brim seam and crown joint next) |
| [plaguemask](plaguemask/) | Wearable full-face plague doctor mask with swappable beaks, eye inserts and trims | First model on default face values; needs measurements |

## Getting started

### Just printing

Every project's print-ready, bed-oriented STLs are committed in `<project>/stl/`.
Slice them in PLA; you don't need FreeCAD. Each project's `README.md` lists
the parts, and `TESTING.md` lists the test prints to make first.

### Changing a model

You need:

- **macOS** (scripts use macOS paths and a macOS system font for engraved
  text).
- **FreeCAD 1.1** from [freecad.org](https://www.freecad.org/downloads.php).
- **git**, and **[uv](https://docs.astral.sh/uv/)**: it provides `uvx`, which
  runs the FreeCAD MCP server for Claude Code.
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**, if you
  want Claude to edit and rebuild models.

Setup, once:

1. Clone to the path the scripts expect. Every script uses absolute paths
   under it:
   ```sh
   mkdir -p ~/src/github.com/mkoelle
   git clone https://github.com/mkoelle/printables ~/src/github.com/mkoelle/printables
   ```
2. Install the FreeCAD MCP addon
   ([neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp)) by
   copying its `addon/FreeCADMCP` folder into FreeCAD's addon directory, then
   restart FreeCAD:
   ```sh
   git clone https://github.com/neka-nat/freecad-mcp.git /tmp/freecad-mcp
   cp -R /tmp/freecad-mcp/addon/FreeCADMCP "$HOME/Library/Application Support/FreeCAD/v1-1/Mod/"
   ```
3. In FreeCAD, switch to the **MCP Addon** workbench and turn on
   **FreeCAD MCP > Auto-Start Server**. From then on, the RPC server, which
   listens on `localhost:9875`, starts with FreeCAD.
4. Register the MCP server with Claude Code:
   ```sh
   claude mcp add --scope user freecad -- uvx freecad-mcp
   ```

To rebuild a project by hand, open FreeCAD's Python console
(**View > Panels > Python console**) and run the project's build script, for
example:

```python
exec(open("/Users/<you>/src/github.com/mkoelle/printables/tophat/build_all.py").read())
```

Each project's `CLAUDE.md` gives the build order and the checks to read in the
output.

### Before working with Claude

1. **Open FreeCAD first** and check that the RPC server is running. With
   auto-start on, the Report view shows `[MCP] Auto-start: ...`. If not, click
   **Start RPC Server** in the MCP Addon workbench. Claude cannot build or
   check anything without it.
2. **Start Claude Code at the repo root**, so it reads the root `CLAUDE.md`:
   ```sh
   cd ~/src/github.com/mkoelle/printables && claude
   ```
3. **Check the connection.** Run `/mcp` in Claude Code; `freecad` should show
   as connected. If FreeCAD was started after Claude Code, reconnect it from
   `/mcp`.
4. **Watching changes.** The scripts open their models in FreeCAD as they
   build, so you see each result in the 3D view. Models saved by a script
   replace the file on disk. If you had that file open, close and reopen it
   (or **File > Revert**).
5. **Long builds.** A full rebuild can take longer than one MCP call allows.
   FreeCAD keeps working when the call times out; let it finish before asking
   Claude to check the results.

## Conventions

- **CAD:** FreeCAD 1.1, driven by Python scripts (parametric where possible).
  Scripts are the source of truth; `.FCStd` models and STLs are generated from
  them.
- **Printer:** 220 x 220 mm bed, PLA unless a project says otherwise.
- **Project layout:**
  - `README.md`: what it is, files, decisions, status
  - `CLAUDE.md`: how to build and check it (for coding agents)
  - `TESTING.md`: test prints and how to tune from them (if any)
  - `stl/`: print-ready STLs, already oriented for the bed
- STLs are committed so prints don't need FreeCAD. G-code and slicer output
  are not committed.
