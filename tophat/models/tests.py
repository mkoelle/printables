"""Test models (PLA): head-fit gauges, fixture coupons, rail parts.

Builds one FreeCAD model per group in build/ (parts laid out in print orientation) and
writes stl/tests/test_*.stl. Re-run after changing Params or rail.py.

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
  joint_poc_brim   small proof of concept: a 30 deg arc of the brim joint
  joint_poc_crown  (collar, snap ridge, one rib) and the matching crown base
                   (snap groove, rib slot, joint zone and step). Checks fit,
                   rib engagement and snap feel before the full rings; an
                   arc is stiffer than a ring, so the click is firmer
  dovetail_flat_*  brim seam on the front/back axis (flat brim)
  lip_ring         crown top band with the cage lip, top down
  finger_tip       CageFingers front finger tip; wedges behind lip_ring
RailTests.FCStd: cage mounting system
  rail             50 mm dovetail cage rail on a test foot
  slider           12 mm slider with the 1.4 mm detent tongue, front-down
"""
import importlib
import math
import sys
from pathlib import Path
import FreeCAD as App
import Part
from FreeCAD import Vector as V

LIB = str(Path(__file__).resolve().parents[1] / "lib")
if LIB in sys.path:
    sys.path.remove(LIB)
sys.path.insert(0, LIB)  # first, so these modules win over other projects'
import common
import rail
importlib.reload(common)
importlib.reload(rail)
from common import FLIP, STL_TESTS, box, check, fuse, oval, place, size, turn, write_stl

# Groups to build: set TEST_GROUPS (e.g. {"fixtures"}) before exec to rebuild
# only those models; the rest keep their saved files. Consumed on each run.
GROUPS = set(globals().pop("TEST_GROUPS", None) or ("fit", "fixtures", "rail"))

hat = common.open_model("TopHat")
val = common.reader(hat.Params)
BED, BED_H = val("Bed"), val("BedH")
SEGS = int(val("BrimSegs"))  # a multiple of 4: seams on both axes
A0, B0, CA, CB = val("A0"), val("B0"), val("CA"), val("CB")
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
BrimW, BrimT, CollarH, BandH = val("BrimW"), val("BrimT"), val("CollarH"), val("BandH")
CrownH, Wall, LipH, CageT = val("CrownH"), val("Wall"), val("LipH"), val("CageT")
CapT = val("CapT")


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


coupons = []  # (model, name, source shape, printable shape)
pairs = []    # (model, label, shape a, shape b) that must not overlap


def add(model, name, shape, *turns):
    """Coupon `shape`, printed after place(shape, *turns)."""
    coupons.append((model, name, shape, place(shape, *turns)))
    return shape


# --- Head fit gauges --------------------------------------------------------
if "fit" in GROUPS:
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


    rings = {c: add(FIT, f"fit_ring_{c:.0f}", fit_ring(c), turn(45))
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
    gauge = fuse(gauge)
    for z in range(int(z_lo) + 5, int(z_bar), 5):
        deep = 2.0 if z % 10 == 0 else 1.0
        gauge = gauge.cut(box(-G_T, G_T, RULER_W / 2 - deep, RULER_W, z - 0.4, z + 0.4))
        if z % 20 == 0:
            label = text(str(z), 3.0, 0.5)
            label.rotate(V(), V(0, 1, 0), 90)   # onto the +X face (top when printed)
            label.rotate(V(), V(1, 0, 0), 90)   # read along the ruler
            label.translate(V(G_T / 2 - 0.5, -0.8, z + 3))
            gauge = gauge.cut(label)
    add(FIT, "head_gauge", gauge, (V(0, 1, 0), -90))  # built in the YZ plane: lay it flat

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
if "fixtures" in GROUPS:
    FIX = "FixtureTests"
    collar = add(FIX, "collar_ring", hat.BrimRing.Shape.common(
        oval(A0 + 12, B0 + 12, -1, BrimT + CollarH + 2)), turn(45))
    crown_ring = add(FIX, "crown_ring", hat.Crown.Shape.common(
        box(-300, 300, -300, 300, -1, BrimT + BandH + 6)), FLIP, turn(45))
    pairs.append((FIX, "collar_ring/crown_ring", collar, crown_ring))

    # Joint proof of concept: 30 deg arc centred on the Q2 rib (ellipse t=135)
    POC_T, POC_ARC = 135, 30
    co_a, co_b = A0 + val("CollarT"), B0 + val("CollarT")
    phi = math.degrees(math.atan2(co_b * math.sin(math.radians(POC_T)),
                                  co_a * math.cos(math.radians(POC_T))))
    sector = Part.makeCylinder(300, 400, V(0, 0, -100), V(0, 0, 1), POC_ARC)
    sector.rotate(V(), V(0, 0, 1), phi - POC_ARC / 2)
    poc_brim = add(FIX, "joint_poc_brim", hat.BrimRing.Shape.common(
        oval(A0 + 12, B0 + 12, -1, BrimT + CollarH + 2)).common(sector))
    poc_crown = add(FIX, "joint_poc_crown", hat.Crown.Shape.common(
        box(-300, 300, -300, 300, -1, val("JointZ") + val("JointT") - Wall + 6)).common(sector), FLIP)
    pairs.append((FIX, "joint_poc", poc_brim, poc_crown))

    # the coupon's cut end is a square corner the real brim does not have, so it
    # gets a set-back of SEAM_GAP a side, tapering to contact over SEAM_TAPER
    SEAM_GAP, SEAM_TAPER = 0.3, 4.0

    def cut_end_relief(u0):
        g, L = SEAM_GAP, SEAM_TAPER
        uv = [(u0 - 1, -g), (u0, -g), (u0 + L, 0), (u0, g), (u0 - 1, g), (u0 - 1, -g)]
        pts = [V(u, v, -5) for u, v in uv]
        return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, 65))


    def play(a, b, step=2.0):
        """How far a can move in -y (pulling the seam open) before it hits b."""
        lo, hi = 0.0, step
        for _ in range(12):
            m = (lo + hi) / 2
            if a.translated(V(0, -m, 0)).common(b).Volume > 0.01:
                hi = m
            else:
                lo = m
        return lo


    # brim seam on the front axis, flat brim: last piece's tongue, BrimQ1's socket
    clip = box(A0 + 8, A0 + BrimW + 1, -25, 25, -5, 60)
    end = cut_end_relief(A0 + 8)
    t = add(FIX, "dovetail_flat_tongue", hat.getObject(f"BrimQ{SEGS}").Shape.common(clip).cut(end))
    s = add(FIX, "dovetail_flat_socket", hat.BrimQ1.Shape.common(clip).cut(end))
    pairs.append((FIX, "dovetail_flat", t, s))
    print(f"  dovetail_flat: pull-apart play {play(t, s):.2f} mm")

    def cage_part(model, obj):
        doc = common.open_model(model, optional=True)
        o = doc and doc.getObject(obj)
        return o.Shape if o else None


    z_top = CrownH - CapT
    lip_ring = add(FIX, "lip_ring", hat.Crown.Shape.common(
        band(val("LipBotA") - CageT - 6, val("LipBotB") - CageT - 6, CA * val("Flare") + Wall + 2,
             CB * val("Flare") + Wall + 2, z_top - LipH - 1, CrownH + 1)),
        FLIP, turn(45))
    fingers = cage_part("CageFingers", "CageFingers")
    if fingers:
        # front finger tip: must tuck behind the lip
        tip = add(FIX, "finger_tip", fingers.common(
            box(0, 300, -15, 15, val("CageZ1") - 25, CrownH)))
        pairs.append((FIX, "lip_ring/finger_tip (wedge press, >0 intended)", lip_ring, tip))

# --- Rail and sliders -----------------------------------------------------
if "rail" in GROUPS:
    RAIL_L = 50.0
    foot = box(-15, 15, -12, 12 - rail.BASE_T, 0, rail.BASE_T)
    r = rail.rail(RAIL_L)
    r.translate(V(0, 0, rail.BASE_T))
    rail_coupon = add("RailTests", "rail", fuse([foot, r]))
    s = rail.slider()
    add("RailTests", "slider", s, (V(1, 0, 0), -90))  # front face (max y) down
    seated = s.copy()
    seated.translate(V(0, 0, rail.BASE_T + rail.seat_offset()))
    pairs.append(("RailTests", "rail/slider seated", rail_coupon, seated))

# --- Models + export ------------------------------------------------------
total = 0.0
for model in dict.fromkeys(c[0] for c in coupons):
    doc = common.new_model(model)
    print(f"{model}.FCStd")
    x = 0.0
    for _, name, src, s in (c for c in coupons if c[0] == model):
        bb = s.optimalBoundingBox()
        o = doc.addObject("Part::Feature", name)
        o.Shape = s
        # lay out in a row, keeping the print orientation baked into s
        o.Placement = App.Placement(V(x + bb.XLength / 2, 0, 0), App.Rotation()).multiply(o.Placement)
        x += bb.XLength + 15
        write_stl(s, STL_TESTS / f"test_{name}.stl", name, BED, BED_H, deflection=0.02)
        total += common.grams(src)
        check(src.isValid() and len(src.Solids) == 1, f"{name} valid single solid")
        print(f"  {name}: valid {src.isValid()} solids {len(src.Solids)} {size(bb)} "
              f"{common.grams(src):.0f} g")
    for m_, label, a, b in pairs:
        if m_ == model:
            v = a.common(b).Volume
            check(v > 0.01 if "intended" in label else v < 0.01, f"overlap {label} {v:.3f} mm3")
            print(f"  overlap {label}: {v:.3f} mm3" + ("" if "intended" in label else " (must be 0)"))
    common.save_model(doc)

print(f"total {total:.0f} g PLA | Clr {val('Clr'):.2f} Snap {val('Snap'):.2f} "
      f"head opening {2 * A0:.1f} x {2 * B0:.1f} mm | built: {', '.join(sorted(GROUPS))}")
common.summary("tests")
