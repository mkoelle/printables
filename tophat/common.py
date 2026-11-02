"""Helpers shared by the top hat scripts: shapes, Params access and checks.

Import from scripts run inside FreeCAD (see CLAUDE.md), after putting this
folder on sys.path and reloading, as the scripts do for rail.py and seam.py.
"""
import Part
from FreeCAD import Vector as V


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box between the given coordinates."""
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def ellipse(a, b, z=0.0):
    """Closed ellipse wire in the plane z, half-axes a along X and b along Y."""
    return Part.Wire([Part.Ellipse(V(0, 0, z), a, b).toShape()])


def oval(a, b, z0, z1):
    """Elliptic prism from z0 to z1."""
    return Part.Face(ellipse(a, b, z0)).extrude(V(0, 0, z1 - z0))


def loft(wires, ruled=True):
    """Solid loft through the wires."""
    return Part.makeLoft(wires, True, ruled)


def fuse(shapes):
    """Fuse in one boolean (chained pairwise fuses can yield invalid solids)."""
    s = shapes[0].fuse(shapes[1:]) if len(shapes) > 1 else shapes[0]
    return s.copy().removeSplitter()


def refined(shape):
    """removeSplitter() when the result stays valid, else the shape as is.
    Works on a copy: a boolean result shares geometry with its inputs, and
    removeSplitter() on it can leave those inputs invalid."""
    r = shape.copy().removeSplitter()
    return r if r.isValid() else shape


def reader(sheet):
    """val(name): a Params cell as a plain number (mm for lengths)."""
    return lambda n: getattr(getattr(sheet, n), "Value", getattr(sheet, n))


# --- Checks -----------------------------------------------------------------
# Scripts call check() for each pass/fail condition they print, then
# summary() once at the end, which prints ALL CHECKS PASS or the failures.
FAILURES = []


def check(ok, what):
    """Record a failed check; returns ok so it can sit inside a print."""
    if not ok:
        FAILURES.append(what)
    return ok


def summary(script):
    if FAILURES:
        print(f"{script}: {len(FAILURES)} CHECK(S) FAILED")
        for f in FAILURES:
            print(f"  FAIL {f}")
    else:
        print(f"{script}: ALL CHECKS PASS")
    failed = list(FAILURES)
    FAILURES.clear()
    return failed
