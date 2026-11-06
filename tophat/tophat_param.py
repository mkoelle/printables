"""Parametric top hat, split into printable parts.

Parts: Crown, Hatband, BrimQ1..BrimQ<BrimSegs> (brim segments). The
interior cage (CageFingers) is built by cage.py from these Params.
- Head size comes from SIZE below (a preset or a measured circumference).
- Wall thicknesses are whole nozzle perimeters (Nozzle, WallPerims).
- Crown wall is JointT at the brim, over the snap groove and rib slots up
  to JointZ, then steps in 45 deg to Wall. The step sits under the hatband,
  whose cone the joint zone follows.
- Brim is flat beside the crown and curls up at the sides (Curl, FlatW).
  A binding band (RimW, RimT) stands proud round its outer edge, ending
  square to the sheet (also on the curls) with a rounded top (RimR) and a
  printable bottom chamfer (RimChamfer). The band is swept in Python when
  this script runs, like the segment count.
- Brim is cut into the fewest segments (a multiple of 4) that fit Bed;
  segments join with dovetail keys at each seam; keys follow the curl.
  Key corners are rounded and seam bed edges chamfered so printed corner
  bulges cannot hold the seams open (KeyRootR, KeyHeadR, KeyClr, SeamEF). Key and seam geometry is in seam.py.
- Brim carries an inner collar; the crown slides over it and seats on the brim.
This script is the single source of truth: change the main / advanced lists
below and rerun it. The Params spreadsheet shows the values used (its
formulas compute the derived ones); every part is a plain shape built from
those values, so editing the spreadsheet and recomputing changes nothing.
"""
import importlib
import math
import os
import sys
import FreeCAD as App
import Part

DIR = os.path.expanduser("~/src/github.com/mkoelle/printables/tophat")
sys.path.insert(0, DIR)
import common
import seam
importlib.reload(common)
importlib.reload(seam)
from common import box, check, ellipse, loft, oval, refined
from FreeCAD import Vector as V

# Head circumference presets, mm round the forehead. SIZE is a preset name or
# a measured circumference in mm. XXL's crown needs a bed over 220 mm.
SIZES = {"XS": 530, "S": 550, "M": 570, "L": 590, "XL": 610, "XXL": 630}
SIZE = "M"
HEAD_CIRC = float(SIZES.get(SIZE, SIZE))

if "TopHat" in App.listDocuments():
    App.closeDocument("TopHat")
doc = App.newDocument("TopHat")

# --- Parameters -----------------------------------------------------------
# Main: the knobs you normally change. Advanced: formulas from Main (override
# with a plain value if needed). Derived: computed geometry. Edit these lists,
# not the spreadsheet: it is rebuilt from them on every run.
sh = doc.addObject("Spreadsheet::Sheet", "Params")
main = [
    ("HeadCirc", f"{HEAD_CIRC:g} mm", f"Head circumference (size {SIZE}; set SIZE in tophat_param.py)"),
    ("Oval",     "0.8",    "Head width/length ratio (0.75 long oval .. 0.85 round)"),
    ("CrownH",   "177.8 mm", "Total hat height (brim bottom to crown top), 7 in"),
    ("Flare",    "1.06",   "Crown top scale vs base"),
    ("BrimW",    "65 mm",  "Brim width beyond head opening"),
    ("Curl",     "25 mm",  "Brim side curl height at outer edge (> 0)"),
    ("Nozzle",   "0.4 mm", "Nozzle diameter; vertical walls are whole perimeters of it"),
    ("WallPerims", "4",    "Crown wall perimeters above the hatband (Wall = Nozzle * WallPerims)"),
    ("Clr",      "0.2 mm", "Print clearance for all fits (tune per printer)"),
    ("Bed",      "220 mm", "Square print bed size; sets the brim segment count"),
]
advanced = [
    ("JointPerims", "7",               "Crown wall perimeters at the brim joint (JointT), under the hatband"),
    ("CapT",      "1.2 mm",            "Crown top cap thickness (6 layers, printed on the bed)"),
    ("BrimT",     "1.6 mm",            "Brim thickness (8 layers at 0.2 mm, as cad_tophat)"),
    ("RimW",      "6 mm",              "Edge binding band width (like a grosgrain-bound brim)"),
    ("RimT",      "1.2 mm",            "Edge binding height above the brim top face"),
    ("RimR",      "1.6 mm",            "Edge binding: outer top rounding radius"),
    ("RimChamfer", "0.6 mm",           "Edge binding: outer bottom 45 deg chamfer (prints on the bed)"),
    ("CollarT",   "Nozzle * round(JointPerims * 2 / 3)", "Brim collar wall thickness (inside crown), whole perimeters"),
    ("CollarH",   "12 mm",             "Brim collar height above brim"),
    ("BandH",     "CrownH / 5",        "Hatband height"),
    ("BandT",     "Nozzle * 3",        "Hatband thickness, 3 perimeters"),
    ("Ease",      "5 mm",              "Fit allowance added to circumference"),
    ("FlatW",     "6 mm",              "Flat brim margin beside crown before curl"),
    ("KeyNeck",   "BrimW * 0.15",      "Dovetail neck width (at seam)"),
    ("KeyHead",   "KeyNeck * 1.6",     "Dovetail head width"),
    ("KeyDepth",  "KeyNeck * 0.8",     "Dovetail depth past seam"),
    ("KeyRootR",  "2 mm",              "Dovetail root rounding radius (with KeyHeadR, nearly fills the flank: S-curve flanks)"),
    ("KeyHeadR",  "3.4 mm",            "Dovetail head rounding radius (root + head must stay under about 5.7 mm)"),
    ("KeyClr",    "0.1 mm",            "Dovetail tongue-to-socket clearance (tighter than Clr; chosen from test prints)"),
    ("SeamEF",    "0.4 mm",            "45 deg chamfer on seam and key bed edges (elephant foot)"),
    ("SeamGap",   "0.3 mm",            "Test coupons: set-back per side at the cut edge, a square corner the brim lacks"),
    ("SeamTaper", "4 mm",              "Test coupons: length over which the cut-edge set-back tapers to contact"),
    ("RibR",      "0.8 mm",            "Alignment rib height (into crown wall slot)"),
    ("RibW",      "6 mm",              "Alignment rib width"),
    ("RibWFront", "RibW + 4 mm",       "Wide front-right rib (sets crown orientation)"),
    ("Snap",      "JointT * 0.2",      "Snap ridge height on collar"),
    ("SnapH",     "Snap * 5",          "Snap ridge height along Z"),
    ("SupAngle",  "40",                "Curl underside flatter than this (deg from horizontal) gets breakaway fins"),
    ("SupGap",    "0.2 mm",            "Breakaway fins: gap to the curl underside (one layer)"),
    ("SupFin",    "0.8 mm",            "Breakaway fin thickness (two perimeters)"),
    ("SupPitch",  "3 mm",              "Breakaway fin spacing"),
    ("SupMinH",   "0.4 mm",            "Lowest fin worth printing; under a lower ceiling the brim gets a foot to the bed"),
    ("HeadClear", "90 mm",             "Top of head above brim underside (from the head gauge)"),
    ("HeadGap",   "10 mm",             "Space kept between the head and cage rails/sliders"),
    ("CageT",     "CollarT",           "Cage shell thickness (cage inner = head opening)"),
    ("CageRingH", "6 mm",              "Cage top/bottom ring height"),
    ("LipH",      "6 mm",              "Wedge lip height: lower 40% lead-in taper, upper 60% press band"),
    ("LipPress",  "0.2 mm",            "Finger squeeze: lip-to-wall gap at the top is CageT minus this"),
    ("LipLead",   "1 mm",              "Lip lead-in: clearance to the finger tips at the lip bottom"),
]
derived = [
    ("Wall", "Nozzle * WallPerims", "Crown wall thickness above the hatband"),
    ("JointT", "Nozzle * JointPerims", "Crown wall thickness at the brim; joint parts scale from it"),
    ("Ka", "pi * (3 * (1 + Oval) - sqrt((3 + Oval) * (1 + 3 * Oval)))",
           "Ellipse perimeter factor: P = a * Ka (Ramanujan)"),
    ("A0", "(HeadCirc + Ease) / Ka", "Head opening half-length (front/back)"),
    ("B0", "A0 * Oval",              "Head opening half-width (side)"),
    ("CA", "A0 + CollarT + Clr",     "Crown inner half-length at base"),
    ("CB", "B0 + CollarT + Clr",     "Crown inner half-width at base"),
    ("HatSizeUS", "(HeadCirc / 25.4 mm) / pi", "US hat size (inches / pi)"),
    ("BandS", "1 + (Flare - 1) * (BandH - CollarH - 1 mm) / (CrownH - CapT - BrimT - CollarH - 1 mm)",
              "Crown inner scale at the hatband top (wall reaches Wall there)"),
    ("JointZ", "BrimT + CollarH + Clr + 1 mm", "Top of the thick joint zone: 1 mm above the rib slots"),
    ("JointA", "CA + JointT + (CA * BandS + Wall - CA - JointT) * (JointZ - BrimT) / BandH",
               "Crown outer half-length at JointZ (on the hatband cone)"),
    ("JointB", "CB + JointT + (CB * BandS + Wall - CB - JointT) * (JointZ - BrimT) / BandH",
               "Crown outer half-width at JointZ (on the hatband cone)"),
    ("JointS2", "1 + (Flare - 1) * (JointZ + JointT - Wall - BrimT - CollarH - 1 mm) / (CrownH - CapT - BrimT - CollarH - 1 mm)",
                "Crown inner scale where the 45 deg step reaches Wall"),
    ("CrownTopA", "CA * Flare + Wall", "Crown top outer half-length"),
    ("CrownTopB", "CB * Flare + Wall", "Crown top outer half-width"),
    ("CrownFit45", "2 * sqrt((CrownTopA ^ 2 + CrownTopB ^ 2) / 2)",
                   "Crown footprint turned 45 deg on bed"),
    ("CurlY0", "CB + JointT + Clr + BandT + FlatW", "Curl starts at |y| beyond this"),
    ("CurlD",  "B0 + BrimW - CurlY0",       "Curl run from start to side edge"),
    ("CurlR",  "(CurlD ^ 2 + Curl ^ 2) / (2 * Curl)", "Curl arc radius"),
    ("BrimSegs", "4", "Brim segments: fewest multiple of 4 that fit Bed (set by tophat_param.py)"),
    ("CageZ0", "BrimT + CollarH",           "Cage bottom (rests on collar top)"),
    ("CageZ1", "CrownH - CapT - Clr",       "Cage top (just under crown top)"),
    ("LipS0",  "1 + (Flare - 1) * (CrownH - CapT - LipH - BrimT - CollarH - 1 mm) / (CrownH - CapT - BrimT - CollarH - 1 mm)",
               "Crown inner scale at the lip bottom"),
    ("LipS1",  "1 + (Flare - 1) * (CrownH - CapT - 0.6 * LipH - BrimT - CollarH - 1 mm) / (CrownH - CapT - BrimT - CollarH - 1 mm)",
               "Crown inner scale where the press band starts"),
    ("LipMidA", "CA * LipS1 - CageT + LipPress", "Wedge lip outer half-length where the press band starts"),
    ("LipMidB", "CB * LipS1 - CageT + LipPress", "Wedge lip outer half-width where the press band starts"),
    ("LipBotA", "CA * LipS0 - Clr - CageT - LipLead", "Wedge lip outer half-length at its bottom"),
    ("LipBotB", "CB * LipS0 - Clr - CageT - LipLead", "Wedge lip outer half-width at its bottom"),
    ("LipTopA", "CA * Flare - CageT + LipPress", "Wedge lip outer half-length at the crown top"),
    ("LipTopB", "CB * Flare - CageT + LipPress", "Wedge lip outer half-width at the crown top"),
]
sh.set("A1", "Generated by tophat_param.py: edit the lists there and rerun; edits here are lost")
row = 3
for title, items in (("Main", main), ("Advanced", advanced), ("Derived", derived)):
    sh.set(f"A{row}", title); sh.set(f"B{row}", "Value"); sh.set(f"C{row}", "Note")
    sh.setStyle(f"A{row}:C{row}", "bold")
    for alias, val, note in items:
        row += 1
        sh.set(f"A{row}", alias); sh.set(f"B{row}", f"={val}"); sh.set(f"C{row}", note)
        sh.setAlias(f"B{row}", alias)
    row += 2
doc.recompute()
val = common.reader(sh)


# --- Brim segment count ---------------------------------------------------
def ray(a, b, phi):
    """Distance from the centre to ellipse (a, b) along polar angle phi (deg)."""
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    return a * b / math.hypot(b * c, a * s)


def segment_side(n, k):
    """Smallest square (any turn on the bed) holding brim segment k of n."""
    a0, b0, w = val("A0"), val("B0"), val("BrimW")
    p0, p1 = 360 * k / n, 360 * (k + 1) / n
    pts = []
    for i in range(41):
        phi = p0 + (p1 - p0) * i / 40
        for r in (ray(a0, b0, phi), ray(a0 + w, b0 + w, phi)):
            pts.append((r * math.cos(math.radians(phi)), r * math.sin(math.radians(phi))))
    # dovetail tongue reaching KeyDepth past the end seam
    c, s = math.cos(math.radians(p1)), math.sin(math.radians(p1))
    mid = (ray(a0, b0, p1) + val("CollarT") + ray(a0 + w, b0 + w, p1)) / 2
    for r in (mid - val("KeyHead") / 2, mid + val("KeyHead") / 2):
        pts.append((r * c - val("KeyDepth") * s, r * s + val("KeyDepth") * c))
    best = math.inf
    for turn in range(0, 180, 2):
        tc, ts = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        xs = [x * tc - y * ts for x, y in pts]
        ys = [x * ts + y * tc for x, y in pts]
        best = min(best, max(max(xs) - min(xs), max(ys) - min(ys)))
    return best


bed = val("Bed")
for N in (4, 8, 12, 16):
    side = max(segment_side(N, k) for k in range(N))
    if side <= bed:
        break
else:
    raise ValueError(f"brim needs more than 16 segments for a {bed:.0f} mm bed")
sh.set(sh.getCellFromAlias("BrimSegs"), f"={N}")
doc.recompute()
crown_fit = val("CrownFit45")
print(f"size {SIZE} ({val('HeadCirc'):.0f} mm), Wall {val('Wall'):.2f} / joint {val('JointT'):.2f} mm, "
      f"brim {N} segments ({side:.1f} mm each on a {bed:.0f} mm bed), crown at 45 deg "
      f"{crown_fit:.1f} mm" + ("" if crown_fit <= bed else " DOES NOT FIT the bed"))

# --- Geometry -------------------------------------------------------------
# Every part is built here as a plain shape from the Params values; only the
# finished parts go into the document (Crown, CrownCut, CageLip, Hatband,
# BrimRing, BrimQ1..N), so cage.py, test_kit.py and export_stl.py read them.
def rot_z(deg):
    return App.Placement(V(), App.Rotation(V(0, 0, 1), deg))


def feature(name, shape, color=None):
    f = doc.addObject("Part::Feature", name)
    f.Shape = shape
    if color and App.GuiUp:
        f.ViewObject.ShapeColor = color
    return f


CA, CB, BrimT, CollarH = val("CA"), val("CB"), val("BrimT"), val("CollarH")
JointT, Wall, Clr, CrownH, CapT = val("JointT"), val("Wall"), val("Clr"), val("CrownH"), val("CapT")
BandS, Flare = val("BandS"), val("Flare")
z_band = BrimT + val("BandH")

# --- Crown: open bottom, seats on brim top, slides over collar ------------
# Outer wall: JointT thick at the brim on the hatband cone up to JointZ,
# a 45 deg step in to Wall, then Wall thick up to the cap. Under the band
# the step leaves a hidden gap between crown and band.
JointZ, JointS2 = val("JointZ"), val("JointS2")
outer = loft([
    ellipse(CA + JointT, CB + JointT, BrimT),
    ellipse(val("JointA"), val("JointB"), JointZ),
    ellipse(CA * JointS2 + Wall, CB * JointS2 + Wall, JointZ + JointT - Wall),
    ellipse(CA * BandS + Wall, CB * BandS + Wall, z_band),
    ellipse(val("CrownTopA"), val("CrownTopB"), CrownH),
])
# Inner wall stays straight over the collar so the snap fit keeps its grip
inner = loft([
    ellipse(CA, CB, BrimT - 1),
    ellipse(CA, CB, BrimT + CollarH + 1),
    ellipse(CA * Flare, CB * Flare, CrownH - CapT),
])
crown_body = outer.cut(inner)

# --- Hatband: cone over the joint zone, Clr gap inside, BandT thick -------
# Visual reference for a fabric band (38-50 mm grosgrain); optional print.
# Slides on from the crown's narrow bottom end before the crown meets the
# brim; gravity seats it on the brim top.
def band_loft(offset):
    return loft([ellipse(CA + JointT + offset, CB + JointT + offset, BrimT),
                 ellipse(CA * BandS + Wall + offset, CB * BandS + Wall + offset, z_band)])


band = band_loft(Clr + val("BandT")).cut(band_loft(Clr))

# --- Brim sheet: flat centre band, sides curl up along a cylinder arc ----
# Curl arc is tangent to the flat band at |y| = CurlY0, axis parallel to X.
CurlY0, CurlR = val("CurlY0"), val("CurlR")


def brim_sheet(thick):
    """Flat centre band plus both curls, `thick` up from the brim underside."""
    flat = box(-300, 300, -CurlY0, CurlY0, 0, thick)
    axis = V(-300, CurlY0, CurlR)
    tube = Part.makeCylinder(CurlR, 600, axis, V(1, 0, 0)).cut(
        Part.makeCylinder(CurlR - thick, 600, axis, V(1, 0, 0)))
    pos = tube.common(box(-300, 300, CurlY0, CurlY0 + CurlR, -1, CurlR))
    neg = pos.mirror(V(), V(0, 1, 0))
    return refined(flat.fuse([pos, neg]))


# --- Brim ring with collar ------------------------------------------------
# the sheet stops inside the edge binding, which carries the true edge
A0, B0, BrimW = val("A0"), val("B0"), val("BrimW")
brim_disc = brim_sheet(BrimT).common(
    oval(A0 + BrimW - val("RimW") / 3, B0 + BrimW - val("RimW") / 3, -1, val("Curl") + BrimT + 9))


# --- Edge binding ---------------------------------------------------------
# Profile in (s, h): s along the sheet, outward (0 = brim edge), h along the
# sheet normal (0 = underside). Swept round the edge with the profile square
# to the sheet, so the curls end square instead of in a vertical knife cut.
def edge_frame(u_t):
    """Brim edge at ellipse parameter u_t: underside point, sheet normal, outward."""
    a, b = A0 + BrimW, B0 + BrimW
    x, y = a * math.cos(u_t), b * math.sin(u_t)
    dy = abs(y) - CurlY0
    if dy > 0:  # on a curl: underside height and sheet normal
        sphi = dy / CurlR
        z = CurlR - math.sqrt(CurlR * CurlR - dy * dy)
        n = V(0, -math.copysign(sphi, y), math.sqrt(1 - sphi * sphi))
    else:
        z, n = 0.0, V(0, 0, 1)
    nh = V(math.cos(u_t) / a, math.sin(u_t) / b, 0)
    nh.normalize()
    out = nh - n * nh.dot(n)
    out.normalize()
    return V(x, y, z), n, out


def binding():
    bt, rt, rw = BrimT, val("RimT"), val("RimW")
    r, c, t = val("RimR"), val("RimChamfer"), BrimT + val("RimT")

    def arc(cx, cy, rad, a0, a1, n):
        return [(cx + rad * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + rad * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    prof = ([(-rw, 0.0)] + arc(-rw + rt, bt, rt, 180, 90, 6)
            + arc(-r, t - r, r, 90, 0, 8) + [(0.0, c), (-c, 0.0)])

    def station(u_t):
        q, n, out = edge_frame(u_t)
        pts = [q + out * s_ + n * h for s_, h in prof]
        return Part.makePolygon(pts + [pts[0]])

    k = 160
    return Part.makeLoft([station(2 * math.pi * i / k) for i in range(k)], True, True, True)


CollarT = val("CollarT")
collar = oval(A0 + CollarT, B0 + CollarT, 0, BrimT + CollarH)
brim_hole = oval(A0, B0, -1, BrimT + CollarH + 1)

# --- Brim-to-crown joint --------------------------------------------------
# Ribs: one per brim segment on the collar, mid-arc (off the seams), engaging
# vertical slots in the crown wall. Q1 rib is wider so the crown fits one way.
# Snap: ramped ridge round the collar clicks into a groove in the crown wall.
CO_A, CO_B = A0 + CollarT, B0 + CollarT


def rib(t, width, grow, z_lo, height):
    """Box standing on the collar at ellipse parameter t (deg), square to it."""
    ang = math.degrees(math.atan2(CO_A * math.sin(math.radians(t)), CO_B * math.cos(math.radians(t))))
    w = width + 2 * grow
    a = math.radians(ang)
    b = Part.makeBox(1 + val("RibR") + grow, w, height)
    b.Placement = App.Placement(
        V(CO_A * math.cos(math.radians(t)) - math.cos(a) + w / 2 * math.sin(a),
          CO_B * math.sin(math.radians(t)) - math.sin(a) - w / 2 * math.cos(a), z_lo),
        App.Rotation(V(0, 0, 1), ang))
    return b


def snap_ring(grow):
    zm, half, bump = BrimT + CollarH / 2, val("SnapH") / 2 + grow, val("Snap") + grow
    return loft([ellipse(CO_A + grow, CO_B + grow, zm - half),
                 ellipse(CO_A + grow + bump, CO_B + grow + bump, zm),
                 ellipse(CO_A + grow, CO_B + grow, zm + half)])


rib_angles = [(k + 0.5) * 360 / N for k in range(N)]  # one per segment, mid-arc
ribs, slots = [], []
for q, t in enumerate(rib_angles, start=1):
    width = val("RibWFront") if q == 1 else val("RibW")
    ribs.append(rib(t, width, 0, BrimT, CollarH))
    slots.append(rib(t, width, Clr, BrimT - 1, CollarH + Clr + 1))
crown_cut = crown_body.cut(slots + [snap_ring(Clr)])  # one cut with all tools

# Wedge lip: hangs from the crown top just inside the cage finger tips. Its
# lower 40% is a lead-in taper (LipLead clearance at the bottom), its upper
# 60% a press band running parallel to the wall CageT - LipPress away. Seating
# the crown on the brim drives the lip down inside the tips and presses them
# flat to the wall. Prints on the inner face (crown prints top-down), so
# nothing shows outside.
lip_zb = CrownH - CapT - val("LipH")
lip_zm = lip_zb + 0.4 * val("LipH")


def lip_loft(inset, ext):
    """Lip surface `inset` inside the outer face, extended `ext` past its ends."""
    return loft([ellipse(val("LipBotA") - inset, val("LipBotB") - inset, lip_zb - ext),
                 ellipse(val("LipMidA") - inset, val("LipMidB") - inset, lip_zm),
                 ellipse(val("LipTopA") - inset, val("LipTopB") - inset, CrownH - CapT + ext + 0.5)])


lip = lip_loft(0, 0).cut(lip_loft(val("CageT"), 1))
crown = refined(crown_cut.fuse(lip))

# refining these left BrimRing invalid, so they stay unrefined
# --- Curl underside: foot and breakaway fins -----------------------------
# The curl leaves the flat brim almost horizontally, so its underside starts
# as a ceiling only fractions of a mm above the bed: unsupported it sags and
# strings, and slicer supports weld to it. Where that ceiling is lower than
# SupGap + SupMinH the brim is filled down to the bed (a foot at most 0.6 mm
# thick); beyond it, up to where the underside is steeper than SupAngle,
# free-standing fins stop SupGap short of the underside. The fins are
# separate bodies exported with each piece; the piece lifts off them.
SupGap, z_min = val("SupGap"), val("SupGap") + val("SupMinH")
dy_foot = math.sqrt(2 * CurlR * z_min - z_min ** 2)        # ceiling reaches z_min
dy_fin = CurlR * math.sin(math.radians(val("SupAngle")))   # underside reaches SupAngle
z_fin = CurlR - math.sqrt(CurlR ** 2 - dy_fin ** 2)
inside_edge = oval(A0 + BrimW - val("RimW") - 1, B0 + BrimW - val("RimW") - 1, -1, z_fin + 2)


def below_curls(y0, y1, z1, gap):
    """Space under both curls for CurlY0 + y0 < |y| < CurlY0 + y1, from the
    bed to z1 and at least gap below the underside, inside the binding."""
    axis = V(-300, CurlY0, CurlR)
    one = box(-300, 300, CurlY0 + y0, CurlY0 + y1, 0, z1).cut(
        Part.makeCylinder(CurlR + gap, 600, axis, V(1, 0, 0)))
    return one.fuse(one.mirror(V(), V(0, 1, 0))).common(inside_edge)


foot = below_curls(0, dy_foot, z_min, 0)
pitch, fin = val("SupPitch"), val("SupFin")
stripes = Part.makeCompound([box(x - fin / 2, x + fin / 2, -300, 300, -1, z_fin + 1)
                             for x in [pitch * i for i in range(-int(300 / pitch), int(300 / pitch) + 1)]])
fins = below_curls(dy_foot, dy_fin, z_fin, SupGap).common(stripes)
brim_ring = brim_disc.fuse([binding(), collar, snap_ring(0), foot] + ribs).cut(brim_hole)

# --- Dovetail keys --------------------------------------------------------
# Seam k lies on the ray at k*360/N deg; its tongue belongs to segment k and
# enters segment k+1. Key and seam reliefs come from seam.py.
P_SEAM = seam.params(val)


def seam_tools(k):
    """Tongue solid, socket tool and relief tool for seam k, placed globally."""
    phi = k * 360 / N
    shapes = seam.seam_tools(P_SEAM, ray(A0, B0, phi), ray(A0 + BrimW, B0 + BrimW, phi))
    for s_ in shapes:
        s_.Placement = rot_z(phi).multiply(s_.Placement)
    return shapes


tools = [seam_tools(k) for k in range(N)]
pieces, supports = [], []
for q in range(1, N + 1):
    sector = Part.makeCylinder(400, 300, V(0, 0, -100), V(0, 0, 1), 360 / N)
    sector.rotate(V(), V(0, 0, 1), (q - 1) * 360 / N)
    owned, incoming = q % N, q - 1  # seam indices
    # Keys are tall prisms clipped to the brim, so they follow the curl
    keyed = refined(brim_ring.common(sector).fuse(brim_ring.common(tools[owned][0])))
    cut = tools[incoming][1].fuse([tools[owned][2], tools[incoming][2]])
    pieces.append(refined(keyed.cut(cut)))
    # fins under this piece: its sector plus its tongue, less its socket
    region = sector.fuse(tools[owned][0]).cut(tools[incoming][1])
    supports.append(fins.common(region))

# --- Document -------------------------------------------------------------
feature("CrownCut", crown_cut)
feature("CageLip", lip)
feature("BrimRing", brim_ring)
crown_f = feature("Crown", crown, (0.05, 0.05, 0.05))
band_f = feature("Hatband", band, (0.45, 0.05, 0.08))
shades = [(0.12, 0.12, 0.12), (0.22, 0.22, 0.25)]
for q, piece in enumerate(pieces, start=1):
    feature(f"BrimQ{q}", piece, shades[(q - 1) % 2])
    feature(f"BrimQ{q}Support", supports[q - 1], (0.6, 0.6, 0.6))
doc.recompute()

for name in ["Crown", "CrownCut", "CageLip", "BrimRing", "Hatband"] + [f"BrimQ{q}" for q in range(1, N + 1)]:
    s_ = doc.getObject(name).Shape
    ok = s_.isValid() and len(s_.Solids) == 1
    print(f"{name}: valid {s_.isValid()} solids {len(s_.Solids)} {s_.Volume / 1000 * 1.24:.0f} g")
    check(ok, f"{name} valid single solid")
o = band.common(crown).Volume
print(f"overlap hatband/crown {o:.3f} mm3 (must be 0)")
check(o < 0.01, "hatband/crown overlap")
for i in range(N):
    for j in range(i + 1, N):
        o = pieces[i].common(pieces[j]).Volume
        check(o < 0.01, f"BrimQ{i + 1}/BrimQ{j + 1} overlap {o:.3f} mm3")
for q, sup in enumerate(supports, start=1):
    o = max(sup.common(p_).Volume for p_ in pieces)
    check(sup.isValid() and o < 0.001, f"BrimQ{q}Support valid and clear of the brim ({o:.3f} mm3)")
print(f"curl supports: foot to {dy_foot:.1f} mm into the curl (max {z_min:.1f} mm), fins to "
      f"{dy_fin:.1f} mm ({z_fin:.1f} mm high), {sum(len(s_.Solids) for s_ in supports)} fins, "
      f"{sum(s_.Volume for s_ in supports) / 1000 * 1.24:.0f} g")
check(crown_fit <= bed, "crown fits the bed at 45 deg")
check(side <= bed, "brim segments fit the bed")
common.summary("tophat_param")

if App.GuiUp:
    import FreeCADGui as Gui
    for name in ("CrownCut", "CageLip", "BrimRing"):
        doc.getObject(name).ViewObject.Visibility = False
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
