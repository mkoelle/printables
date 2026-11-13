"""Helpers shared by the top hat scripts: project paths, models, shapes,
Params access, print placement, STL export and checks.

Import from the scripts in models/, which put this folder on sys.path and
reload it (see CLAUDE.md).
"""
from pathlib import Path

import FreeCAD as App
import MeshPart
import Part
from FreeCAD import Vector as V

PROJECT = Path(__file__).resolve().parents[1]
BUILD = PROJECT / "build"               # generated .FCStd models, not in git
STL_PARTS = PROJECT / "stl" / "parts"   # the hat itself
STL_TESTS = PROJECT / "stl" / "tests"   # test coupons
STL_MOUNTS = PROJECT / "stl" / "mounts" # components for the rail sliders (mounts/)

PLA = 1.24e-3  # g per mm3
FLIP = (V(1, 0, 0), 180)  # turn for place(): upside down


# --- Models -----------------------------------------------------------------
def model_path(name):
    return BUILD / f"{name}.FCStd"


def open_model(name, optional=False):
    """The open document `name`, opened from build/ if needed. When it has
    not been built: None if optional, else FileNotFoundError."""
    if name not in App.listDocuments():
        if not model_path(name).exists():
            if optional:
                return None
            raise FileNotFoundError(f"{model_path(name)} not built yet: run models/hat.py first")
        App.openDocument(str(model_path(name)))
    return App.getDocument(name)


def new_model(name):
    """A fresh, empty document `name` (an open one is closed first)."""
    if name in App.listDocuments():
        App.closeDocument(name)
    return App.newDocument(name)


def save_model(doc):
    """Recompute, fit the view and save doc to build/<name>.FCStd."""
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    BUILD.mkdir(exist_ok=True)
    doc.saveAs(str(model_path(doc.Name)))


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


def turn(deg):
    """Turn for place(): deg about the vertical axis."""
    return V(0, 0, 1), deg


def place(shape, *turns):
    """Copy of shape rotated by each (axis, deg) in turn about the origin,
    then centred on the origin with its lowest point at z=0."""
    s = shape.copy()
    for axis, deg in turns:
        s.rotate(V(), axis, deg)
    bb = s.optimalBoundingBox()
    s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    return s


def write_stl(shape, path, what, bed, bed_h, deflection=0.05):
    """Mesh a placed shape to path and check it fits the bed (bed x bed,
    bed_h tall). Returns its bounding box."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=deflection,
                           AngularDeflection=0.1, Relative=False).write(str(path))
    bb = shape.optimalBoundingBox()
    check(bb.XLength <= bed and bb.YLength <= bed and bb.ZLength <= bed_h, f"{what} fits the printer")
    return bb


def size(bb):
    return f"{bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm"


def grams(shape):
    return shape.Volume * PLA


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
