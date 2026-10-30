"""Test models (PLA): head-fit gauges, fixture coupons, rail parts.

Builds one FreeCAD model per group (parts laid out in print orientation) and
writes stl/test_*.stl. Re-run after changing Params or rail.py.

TopHatFitTests.FCStd: try-on gauges for the wearer
  fit_ring_<circ>  hat opening at HeadCirc and one hat size (10 mm) either
                   side; circumference engraved at the front
  head_gauge       arch that clips onto a fit ring; its ruler measures how
                   high the top of the head sits (sets HeadClear)
  gauge_pointer    sleeve that slides up the ruler when the gauge is put on
FixtureTests.FCStd: joints between hat parts
  collar_ring      brim collar band (snap ridge, ribs, 12 mm of flat brim)
  crown_ring       crown bottom (snap groove, rib slots, hatband zone),
                   printed upside down like the full crown
                   (stl/tophat_hatband.stl is the hatband test on crown_ring)
  dovetail_flat_*  brim seam on the front/back axis (flat brim)
  dovetail_curl_*  brim seam on the side axis (curled brim)
  lip_ring         crown top band with the cage lip, top down
  finger_tip       CageFingers front finger tip; wedges behind lip_ring
RailTests.FCStd: cage mounting system, two sets to print and compare
  rail             50 mm T-rail on a test foot (same profile as the cage)
  slider_N         T sliders with 1.0 / 1.2 / 1.4 mm detent tongues
                   (1, 2, 3 side notches), printed front-down
  rail_dovetail    50 mm 45 deg dovetail rail on a test foot
  dovetail_slider_N  dovetail sliders, same tongues, with elephant-foot
                   chamfers and channel lead-ins
"""
import os
import sys
import importlib
import FreeCAD as App
import Part
import MeshPart
from FreeCAD import Vector as V

DIR = os.path.expanduser("~/src/github.com/mkoelle/printables/tophat")
sys.path.insert(0, DIR)
import rail
importlib.reload(rail)

if "TopHat" not in App.listDocuments():
    App.openDocument(os.path.join(DIR, "TopHat.FCStd"))
hat = App.getDocument("TopHat")
hat.recompute()
sh = hat.Params
val = lambda n: getattr(getattr(sh, n), "Value", getattr(sh, n))
BED = val("Bed")
SEGS = int(val("BrimSegs"))  # a multiple of 4: seams on both axes
A0, B0, CA, CB = val("A0"), val("B0"), val("CA"), val("CB")
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
BrimW, BrimT, CollarH, BandH = val("BrimW"), val("BrimT"), val("CollarH"), val("BandH")
CrownH, Wall, LipH, CageT = val("CrownH"), val("Wall"), val("LipH"), val("CageT")


def oval(a, b, za, zb):
    e = Part.Ellipse(V(0, 0, za), a, b).toShape()
    return Part.Face(Part.Wire([e])).extrude(V(0, 0, zb - za))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def band(a_in, b_in, a_out, b_out, za, zb):
    return oval(a_out, b_out, za, zb).cut(oval(a_in, b_in, za - 1, zb + 1))


def text(label, size, depth):
    """Solid text in the XY plane, centred on the origin, z from 0 to depth."""
    faces = [Part.makeFace(chars, "Part::FaceMakerBullseye")
             for chars in Part.makeWireString(label, FONT, size, 0)]
    t = Part.makeCompound(faces).extrude(V(0, 0, depth))
    c = t.BoundBox.Center
    t.translate(V(-c.x, -c.y, 0))
    return t


def orient(shape, flip=False, turn=0, back_down=False, front_down=False, x_up=False):
    s = shape.copy()
    if flip:
        s.rotate(V(), V(1, 0, 0), 180)
    if x_up:  # flat part built in the YZ plane: lay it on the bed
        s.rotate(V(), V(0, 1, 0), -90)
    if back_down:  # slider back face (min y) onto the bed
        s.rotate(V(), V(1, 0, 0), 90)
    if front_down:  # slider front face (max y) onto the bed
        s.rotate(V(), V(1, 0, 0), -90)
    if turn:
        s.rotate(V(), V(0, 0, 1), turn)
    bb = s.optimalBoundingBox()
    s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    return s


coupons = []  # (model, name, source shape, printable shape)
pairs = []    # (model, label, shape a, shape b) that must not overlap


def add(model, name, shape, **kw):
    coupons.append((model, name, shape, orient(shape, **kw)))
    return shape


# --- Head fit gauges --------------------------------------------------------
FIT = "TopHatFitTests"
RING_T, RING_H = 2.4, 15.0       # fit ring band thickness and height
FLANGE_W, FLANGE_T = 6.0, 1.6    # stiffening flange at the bottom
Ka, Ease, circ = val("Ka"), val("Ease"), val("HeadCirc")


def fit_ring(c):
    a = (c + Ease) / Ka
    b = a * val("Oval")
    ring = band(a, b, a + RING_T, b + RING_T, 0, RING_H).fuse(
        band(a, b, a + RING_T + FLANGE_W, b + RING_T + FLANGE_W, 0, FLANGE_T))
    label = text(f"{c:.0f}", 4.0, 0.6)
    label.rotate(V(), V(0, 0, 1), 90)  # reads along the flange at the front
    label.translate(V(a + RING_T + FLANGE_W / 2, 0, FLANGE_T - 0.6))
    return ring.cut(label).removeSplitter()


rings = {c: add(FIT, f"fit_ring_{c:.0f}", fit_ring(c), turn=45)
         for c in (circ - 10, circ, circ + 10)}

# Head gauge: flat arch in the YZ plane (thickness along X) that clips onto
# the sides of the HeadCirc fit ring. Ruler ticks every 5 mm (long every 10)
# are heights above the ring bottom (= brim underside), labelled every 20.
G_T, LEG_W, BAR_H, RULER_W, FIT_CLR = 4.0, 10.0, 8.0, 6.0, 0.15
head = val("HeadClear")
z_lo, z_bar = 10 * round((head - 40) / 10), 10 * round((head + 30) / 10)
leg_y = B0 + RING_T / 2
gauge = [box(-G_T / 2, G_T / 2, -(leg_y + LEG_W / 2), leg_y + LEG_W / 2, z_bar, z_bar + BAR_H),
         box(-G_T / 2, G_T / 2, -RULER_W / 2, RULER_W / 2, z_lo, z_bar + 0.01)]
for sy in (-1, 1):
    leg = box(-G_T / 2, G_T / 2, sy * leg_y - LEG_W / 2, sy * leg_y + LEG_W / 2,
              RING_H - 10, z_bar + 0.01)
    y0, y1 = sorted((sy * (B0 - FIT_CLR), sy * (B0 + RING_T + FIT_CLR)))
    gauge.append(leg.cut(box(-G_T, G_T, y0, y1, RING_H - 11, RING_H)))  # fork
gauge = rail.fuse(gauge)
for z in range(int(z_lo) + 5, int(z_bar), 5):
    deep = 2.0 if z % 10 == 0 else 1.0
    gauge = gauge.cut(box(-G_T, G_T, RULER_W / 2 - deep, RULER_W, z - 0.4, z + 0.4))
    if z % 20 == 0:
        label = text(str(z), 3.0, 0.5)
        label.rotate(V(), V(0, 1, 0), 90)   # onto the +X face (top when printed)
        label.rotate(V(), V(1, 0, 0), 90)   # read along the ruler
        label.translate(V(G_T / 2 - 0.5, -0.8, z + 3))
        gauge = gauge.cut(label)
add(FIT, "head_gauge", gauge, x_up=True)

sleeve_in = (RULER_W + 2 * FIT_CLR, G_T + 2 * FIT_CLR)
pointer = box(-sleeve_in[1] / 2 - 1.6, sleeve_in[1] / 2 + 1.6,
              -sleeve_in[0] / 2 - 1.6, sleeve_in[0] / 2 + 1.6, 0, 10).cut(
          box(-sleeve_in[1] / 2, sleeve_in[1] / 2, -sleeve_in[0] / 2, sleeve_in[0] / 2, -1, 11))
add(FIT, "gauge_pointer", pointer)
pairs.append((FIT, f"fit_ring_{circ:.0f}/head_gauge", rings[circ], gauge))
on_ruler = pointer.copy()
on_ruler.translate(V(0, 0, z_lo + 20))
pairs.append((FIT, "head_gauge/gauge_pointer", gauge, on_ruler))

# --- Fixture coupons: joints between hat parts ------------------------------
FIX = "FixtureTests"
collar = add(FIX, "collar_ring", hat.BrimRing.Shape.common(
    oval(A0 + 12, B0 + 12, -1, BrimT + CollarH + 2)), turn=45)
crown_ring = add(FIX, "crown_ring", hat.Crown.Shape.common(
    box(-300, 300, -300, 300, -1, BrimT + BandH + 6)), flip=True, turn=45)
pairs.append((FIX, "collar_ring/crown_ring", collar, crown_ring))

tiles = {
    "dovetail_flat": (box(A0 + 8, A0 + BrimW + 1, -25, 25, -5, 60), f"BrimQ{SEGS}", "BrimQ1"),
    "dovetail_curl": (box(-25, 25, B0 + 8, B0 + BrimW + 1, -5, 60), f"BrimQ{SEGS // 4}", f"BrimQ{SEGS // 4 + 1}"),
}
for name, (clip, tongue_part, socket_part) in tiles.items():
    t = add(FIX, f"{name}_tongue", hat.getObject(tongue_part).Shape.common(clip))
    s = add(FIX, f"{name}_socket", hat.getObject(socket_part).Shape.common(clip))
    pairs.append((FIX, name, t, s))

def cage_part(model, obj):
    if model not in App.listDocuments():
        path = os.path.join(DIR, f"{model}.FCStd")
        if not os.path.exists(path):
            return None
        App.openDocument(path)
    o = App.getDocument(model).getObject(obj)
    return o.Shape if o else None


z_top = CrownH - Wall
lip_ring = add(FIX, "lip_ring", hat.Crown.Shape.common(
    band(val("LipBotA") - CageT - 6, val("LipBotB") - CageT - 6, CA * val("Flare") + Wall + 2,
         CB * val("Flare") + Wall + 2, z_top - LipH - 1, CrownH + 1)),
    flip=True, turn=45)
fingers = cage_part("CageFingers", "CageFingers")
if fingers:
    # front finger tip: must tuck behind the lip
    tip = add(FIX, "finger_tip", fingers.common(
        box(0, 300, -15, 15, val("CageZ1") - 25, CrownH)))
    pairs.append((FIX, "lip_ring/finger_tip (wedge press, >0 intended)", lip_ring, tip))

# --- Rail and sliders -----------------------------------------------------
RAIL_L = 50.0
for dt, prefix in ((False, ""), (True, "dovetail_")):
    foot = box(-15, 15, -12, 12 - rail.BASE_T, 0, rail.BASE_T)
    r = rail.rail(RAIL_L, dovetail=dt)
    r.translate(V(0, 0, rail.BASE_T))
    rail_name = "rail_dovetail" if dt else "rail"
    rail_coupon = add("RailTests", rail_name, rail.fuse([foot, r]))
    for i, t in enumerate(rail.TONGUES, start=1):
        s = rail.slider(t, i, dovetail=dt, chamfer=dt)
        add("RailTests", f"{prefix}slider{i}_tongue{t}mm", s, front_down=True)
        if i == 1:
            seated = s.copy()
            seated.translate(V(0, 0, rail.BASE_T + rail.seat_offset()))
            pairs.append(("RailTests", f"{rail_name}/{prefix}slider1 seated", rail_coupon, seated))

# --- Models + export ------------------------------------------------------
out = os.path.join(DIR, "stl")
os.makedirs(out, exist_ok=True)
total = 0.0
for model in dict.fromkeys(c[0] for c in coupons):
    if model in App.listDocuments():
        App.closeDocument(model)
    doc = App.newDocument(model)
    print(f"{model}.FCStd")
    x = 0.0
    for _, name, src, s in (c for c in coupons if c[0] == model):
        bb = s.optimalBoundingBox()
        o = doc.addObject("Part::Feature", name)
        o.Shape = s
        # lay out in a row, keeping the print orientation baked into s
        o.Placement = App.Placement(V(x + bb.XLength / 2, 0, 0), App.Rotation()).multiply(o.Placement)
        x += bb.XLength + 15
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02,
                                   AngularDeflection=0.1, Relative=False)
        m.write(os.path.join(out, f"test_{name}.stl"))
        grams = src.Volume / 1000 * 1.24
        total += grams
        fits = bb.XLength <= BED and bb.YLength <= BED
        print(f"  {name}: valid {src.isValid()} solids {len(src.Solids)} "
              f"{bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm fits={fits} {grams:.0f} g")
    for m_, label, a, b in pairs:
        if m_ == model:
            v = a.common(b).Volume
            print(f"  overlap {label}: {v:.3f} mm3" + ("" if "intended" in label else " (must be 0)"))
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    doc.saveAs(os.path.join(DIR, f"{model}.FCStd"))

print(f"total {total:.0f} g PLA | Clr {val('Clr'):.2f} Snap {val('Snap'):.2f} "
      f"head opening {2 * A0:.1f} x {2 * B0:.1f} mm")
