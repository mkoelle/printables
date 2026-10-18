# printables

Personal 3D-printable models. One folder per project; each is self-contained
with its own scripts, FreeCAD models, STLs and docs.

| Project | Description | Status |
|---------|-------------|--------|
| [tophat](tophat/) | Parametric top hat with a hidden cage for storage and IoT devices | Test prints (round 1) |
| [plaguemask](plaguemask/) | Wearable full-face plague doctor mask with swappable beaks, eye inserts and trims | Pre-design (needs face measurements) |

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
