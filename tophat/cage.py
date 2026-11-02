"""Interior mounting cage for the top hat (PLA, prints upright, no supports).

CageFingers.FCStd: one piece, a bottom ring plus one spring finger per rail.
The fingers hug the flared crown wall (Clr gap). Squeeze the finger tips in,
push the cage up through the crown's bottom opening; the fingers spring out
flush and tuck behind the crown's wedge lip, which presses them to the wall
when the crown snaps onto the brim; the tips' inner edges are bevelled to
slide onto it. The ring sits on the brim collar and its inner size equals
the head opening.

RAIL_COUNT dovetail rails (see rail.py), one per finger, run from just above the
head to just under the lip, following the wall's flare. The head is modelled
as a dome: full opening size up to the collar top, rising to HeadClear at the
centre. Rails stop HeadGap above that dome, measured at a seated slider's
inner face, so they reach lower than HeadClear at the sides. The model
includes the head dome (transparent) for reference.

Re-run after changing Params. Writes stl/tophat_cage_fingers.stl.
"""
import math
import os
import sys
import importlib
import FreeCAD as App
import Part
import MeshPart
from FreeCAD import Vector as V

DIR = os.path.expanduser("~/src/github.com/mkoelle/printables/tophat")
sys.path.insert(0, DIR)
import common
import rail
importlib.reload(common)
importlib.reload(rail)
from common import box, check, ellipse, loft, oval

RAIL_COUNT = 6                     # 6: front, back + 4 at 60 deg steps
RAIL_T = [k * 360 / RAIL_COUNT for k in range(RAIL_COUNT)]  # ellipse parameters
FINGER_W = rail.BASE_W + 8         # finger width
BEVEL_D, BEVEL_H = 0.5, 1.0        # finger tip inner bevel: depth, height

if "TopHat" not in App.listDocuments():
    App.openDocument(os.path.join(DIR, "TopHat.FCStd"))
hat = App.getDocument("TopHat")
hat.recompute()
sh = hat.Params
val = common.reader(sh)
BED = val("Bed")
CA, CB, Clr, T = val("CA"), val("CB"), val("Clr"), val("CageT")
F, ring_h, head = val("Flare"), val("CageRingH"), val("HeadClear")
z0, z1 = val("CageZ0"), val("CageZ1")
zm = val("BrimT") + val("CollarH") + 1          # crown inner starts flaring
zt = val("CrownH") - val("CapT")                # crown inner top
lip_bot = zt - val("LipH")
A0, B0, gap = val("A0"), val("B0"), val("HeadGap")
zb = z0                                         # head is full width up to here
# a seated slider's inner face, measured inward from the cage inner face
SLIDER_DEPTH = rail.BASE_T / 2 + rail.Y_FACE + rail.DEPTH + rail.CLR + rail.FRONT


def scale(z):
    """Crown inner scale at height z (straight up to zm, then linear)."""
    return 1.0 if z <= zm else 1 + (F - 1) * (z - zm) / (zt - zm)


def axes(z, inset):
    """Half-axes of the cage surface `inset` inside the crown wall at z."""
    return CA * scale(z) - Clr - inset, CB * scale(z) - Clr - inset


def wall_solid(inset, za=None, zb=None):
    """Solid bounded by the surface `inset` inside the crown wall."""
    za, zb = (z0 if za is None else za), (z1 if zb is None else zb)
    zs = sorted({za, max(za, min(zm, zb)), zb})
    return loft([ellipse(*axes(z, inset), z) for z in zs])


def inner_point(t, z):
    a, b = axes(z, T)
    return V(a * math.cos(t), b * math.sin(t), z)


def dome(x, y):
    """Head surface height at (x, y): ellipsoid cap on the opening."""
    rho2 = (x / A0) ** 2 + (y / B0) ** 2
    return zb + (head - zb) * math.sqrt(max(0.0, 1 - rho2))


def rail_bottom(t):
    """Lowest rail start keeping a seated slider HeadGap above the head."""
    z = head
    for _ in range(30):
        p = inner_point(t, z)
        a, b = axes(z, T)
        n = V(-b * math.cos(t), -a * math.sin(t), 0)  # inward normal
        n.normalize()
        q = p + n * SLIDER_DEPTH
        z = max(z0 + ring_h + 2, dome(q.x, q.y) + gap)
    return z


def head_solid(offset=0.0):
    """Head dome (raised by offset) plus the straight part below zb."""
    cap = Part.makeSphere(1.0)
    cap = cap.transformGeometry(App.Matrix(A0, 0, 0, 0, 0, B0, 0, 0, 0, 0, head - zb, 0, 0, 0, 0, 1))
    cap.translate(V(0, 0, zb + offset))
    cap = cap.common(box(-300, 300, -300, 300, zb + offset, 400))
    base = oval(A0, B0, 0, zb + offset)
    return cap.fuse(base).removeSplitter()


def place_rail(deg):
    """Rail on the cage inner face at ellipse parameter deg, along the flare."""
    t = math.radians(deg)
    z_start = rail_bottom(t)
    p0, p1 = inner_point(t, z_start), inner_point(t, lip_bot - 2)
    d = p1 - p0
    length = d.Length
    d.normalize()
    a, b = axes(z_start, T)
    tan = V(-a * math.sin(t), b * math.cos(t), 0)
    tan = tan - d * tan.dot(d)
    tan.normalize()
    inward = d.cross(tan)
    inward.normalize()
    x = inward.cross(d)
    r = rail.rail(length)
    r.translate(V(0, rail.BASE_T / 2, 0))  # backing straddles the inner face
    m = App.Matrix(x.x, inward.x, d.x, p0.x,
                   x.y, inward.y, d.y, p0.y,
                   x.z, inward.z, d.z, p0.z,
                   0, 0, 0, 1)
    return r.transformGeometry(m), length, z_start


def ray_box(deg, width):
    """Vertical slab from the axis out through the wall at ellipse parameter deg."""
    t = math.radians(deg)
    phi = math.degrees(math.atan2(CB * math.sin(t), CA * math.cos(t)))
    b = box(0, 300, -width / 2, width / 2, z0 - 1, z1 + 1)
    b.rotate(V(), V(0, 0, 1), phi)
    return b


outer, inner = wall_solid(0), wall_solid(T, z0 - 1, z1 + 1)
shell = outer.cut(inner)
rails = [place_rail(deg) for deg in RAIL_T]
rail_shapes = [r.common(outer) for r, _, _ in rails]

# --- Bottom ring + one finger per rail -------------------------------------
keep = [box(-300, 300, -300, 300, z0 - 1, z0 + ring_h)]
keep += [ray_box(d, FINGER_W) for d in RAIL_T]
fingers = rail.fuse([shell.common(rail.fuse(keep))] + rail_shapes)
zc = z1 - BEVEL_H
bevel = loft([ellipse(*axes(zc, T + 0.01), zc),
              ellipse(*axes(z1 + 1, T - BEVEL_D * (BEVEL_H + 1) / BEVEL_H), z1 + 1)])
fingers = fingers.cut(bevel)


# --- Checks ------------------------------------------------------------------
def finger_squeeze():
    """Inward flex at a finger tip to pass the crown's bottom opening."""
    a, b = axes(z1, 0)
    return max(a - (CA - Clr), b - (CB - Clr))


def finger_strain():
    length = z1 - (z0 + ring_h)
    return 3 * T * finger_squeeze() / (2 * length ** 2) * 100


crown = hat.CrownCut.Shape  # crown without the lip
lip = hat.CageLip.Shape
brims = [hat.getObject(f"BrimQ{i}").Shape for i in range(1, int(val("BrimSegs")) + 1)]
head_shape = head_solid()
for (r, length, z_start), t, rs in zip(rails, RAIL_T, rail_shapes):
    check(rs.common(head_solid(gap)).Volume < 0.001, f"rail t={t:.0f} clear of the head (HeadGap)")
    print(f"rail t={t:.0f}: {length:.0f} mm ({int(length // rail.PITCH)} steps, "
          f"{int(length // (rail.SLIDER_L + rail.TAB_EXT + 1))} sliders), "
          f"starts {z_start:.0f} mm, head overlap {rs.common(head_shape).Volume:.3f} / "
          f"with HeadGap {rs.common(head_solid(gap)).Volume:.3f} mm3")


def report(name, s):
    o = s.common(crown).Volume
    b = max(s.common(x).Volume for x in brims)
    check(s.isValid() and len(s.Solids) == 1, f"{name} valid single solid")
    check(o < 0.01 and b < 0.01, f"{name} clear of crown and brim")
    print(f"{name}: valid {s.isValid()} solids {len(s.Solids)} "
          f"{s.Volume / 1000 * 1.24:.0f} g, overlap crown {o:.3f} brim {b:.3f}")


report("CageFingers", fingers)
check(fingers.common(lip).Volume > 0.01, "finger tips pressed by the wedge lip")
print(f"  wedge lip press: {fingers.common(lip).Volume:.1f} mm3 overlap "
      f"(intended, LipPress {val('LipPress'):.2f} mm)")
print(f"  finger tip squeeze to insert {finger_squeeze():.1f} mm, "
      f"root strain {finger_strain():.2f}%")


# --- Models + export -------------------------------------------------------
def save_model(model, parts):
    if model in App.listDocuments():
        App.closeDocument(model)
    doc = App.newDocument(model)
    for name, s, color in parts + [("HeadDome", head_shape, (0.85, 0.7, 0.6))]:
        o = doc.addObject("Part::Feature", name)
        o.Shape = s
        if App.GuiUp:
            o.ViewObject.ShapeColor = color
            if name == "HeadDome":
                o.ViewObject.Transparency = 75
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    doc.saveAs(os.path.join(DIR, f"{model}.FCStd"))


def export(shape, name, turn=0):
    s = shape.copy()
    if turn:
        s.rotate(V(), V(0, 0, 1), turn)
    bb = s.optimalBoundingBox()
    s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.1, Relative=False)
    m.write(os.path.join(DIR, "stl", f"tophat_cage_{name}.stl"))
    bb = s.optimalBoundingBox()
    check(bb.XLength <= BED and bb.YLength <= BED, f"cage {name} fits the bed")
    print(f"  stl {name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm "
          f"fits={bb.XLength <= BED and bb.YLength <= BED}")


save_model("CageFingers", [("CageFingers", fingers, (0.2, 0.45, 0.75))])
export(fingers, "fingers", turn=45)
common.summary("cage")
