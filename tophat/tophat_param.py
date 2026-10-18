"""Parametric top hat, split into printable parts.

Parts: Crown, Hatband, BrimQ1..BrimQ4 (brim quadrants). The interior
cage (CageFingers) is built by cage.py from these Params.
- Brim is flat beside the crown and curls up at the sides (Curl, FlatW).
- Brim quadrants join with dovetail keys at each seam; keys follow the curl.
- Brim carries an inner collar; the crown slides over it and seats on the brim.
Edit the Main section of the Params spreadsheet and recompute.
"""
import FreeCAD as App

if "TopHat" in App.listDocuments():
    App.closeDocument("TopHat")
doc = App.newDocument("TopHat")

# --- Parameters -----------------------------------------------------------
# Main: the knobs you normally change. Advanced: formulas from Main (override
# with a plain value if needed). Derived: computed geometry, do not edit.
sh = doc.addObject("Spreadsheet::Sheet", "Params")
main = [
    ("HeadCirc", "570 mm", "Head circumference (S 550, M 570, L 590, XL 610)"),
    ("Oval",     "0.8",    "Head width/length ratio (0.75 long oval .. 0.85 round)"),
    ("CrownH",   "150 mm", "Total hat height (brim bottom to crown top)"),
    ("Flare",    "1.06",   "Crown top scale vs base"),
    ("BrimW",    "65 mm",  "Brim width beyond head opening"),
    ("Curl",     "25 mm",  "Brim side curl height at outer edge (> 0)"),
    ("Wall",     "3 mm",   "Crown wall thickness; other thicknesses scale from it"),
    ("Clr",      "0.2 mm", "Print clearance for all fits (tune per printer)"),
]
advanced = [
    ("BrimT",     "Wall + 1 mm",       "Brim thickness"),
    ("CollarT",   "Wall * 2 / 3",      "Brim collar wall thickness (inside crown)"),
    ("CollarH",   "3 * BrimT",         "Brim collar height above brim"),
    ("BandH",     "CrownH / 5",        "Hatband height"),
    ("BandT",     "1 mm",              "Hatband thickness"),
    ("Ease",      "5 mm",              "Fit allowance added to circumference"),
    ("FlatW",     "6 mm",              "Flat brim margin beside crown before curl"),
    ("KeyNeck",   "BrimW * 0.15",      "Dovetail neck width (at seam)"),
    ("KeyHead",   "KeyNeck * 1.6",     "Dovetail head width"),
    ("KeyDepth",  "KeyNeck * 0.8",     "Dovetail depth past seam"),
    ("RibR",      "Wall * 0.4",        "Alignment rib height (into crown wall slot)"),
    ("RibW",      "6 mm",              "Alignment rib width"),
    ("RibWFront", "RibW + 4 mm",       "Wide front-right rib (sets crown orientation)"),
    ("Snap",      "Wall * 0.2",        "Snap ridge height on collar"),
    ("SnapH",     "Snap * 5",          "Snap ridge height along Z"),
    ("HeadClear", "90 mm",             "Top of head above brim underside (from the head gauge)"),
    ("HeadGap",   "10 mm",             "Space kept between the head and cage rails/sliders"),
    ("CageT",     "CollarT",           "Cage shell thickness (cage inner = head opening)"),
    ("CageRingH", "6 mm",              "Cage top/bottom ring height"),
    ("LipH",      "6 mm",              "Wedge lip height: lower 40% lead-in taper, upper 60% press band"),
    ("LipPress",  "0.2 mm",            "Finger squeeze: lip-to-wall gap at the top is CageT minus this"),
    ("LipLead",   "1 mm",              "Lip lead-in: clearance to the finger tips at the lip bottom"),
]
derived = [
    ("Ka", "pi * (3 * (1 + Oval) - sqrt((3 + Oval) * (1 + 3 * Oval)))",
           "Ellipse perimeter factor: P = a * Ka (Ramanujan)"),
    ("A0", "(HeadCirc + Ease) / Ka", "Head opening half-length (front/back)"),
    ("B0", "A0 * Oval",              "Head opening half-width (side)"),
    ("CA", "A0 + CollarT + Clr",     "Crown inner half-length at base"),
    ("CB", "B0 + CollarT + Clr",     "Crown inner half-width at base"),
    ("HatSizeUS", "(HeadCirc / 25.4 mm) / pi", "US hat size (inches / pi)"),
    ("CrownTopA", "(CA + Wall) * Flare", "Crown top outer half-length"),
    ("CrownTopB", "(CB + Wall) * Flare", "Crown top outer half-width"),
    ("CrownFit45", "2 * sqrt((CrownTopA ^ 2 + CrownTopB ^ 2) / 2)",
                   "Crown footprint turned 45 deg on bed"),
    ("CurlY0", "CB + Wall + Clr + BandT + FlatW", "Curl starts at |y| beyond this"),
    ("CurlD",  "B0 + BrimW - CurlY0",       "Curl run from start to side edge"),
    ("CurlR",  "(CurlD ^ 2 + Curl ^ 2) / (2 * Curl)", "Curl arc radius"),
    ("BrimQX", "A0 + BrimW + KeyDepth", "Brim quadrant footprint X"),
    ("BrimQY", "B0 + BrimW + KeyDepth", "Brim quadrant footprint Y"),
    ("CageZ0", "BrimT + CollarH",           "Cage bottom (rests on collar top)"),
    ("CageZ1", "CrownH - Wall - Clr",       "Cage top (just under crown top)"),
    ("LipS0",  "1 + (Flare - 1) * (CrownH - Wall - LipH - BrimT - CollarH - 1 mm) / (CrownH - Wall - BrimT - CollarH - 1 mm)",
               "Crown inner scale at the lip bottom"),
    ("LipS1",  "1 + (Flare - 1) * (CrownH - Wall - 0.6 * LipH - BrimT - CollarH - 1 mm) / (CrownH - Wall - BrimT - CollarH - 1 mm)",
               "Crown inner scale where the press band starts"),
    ("LipMidA", "CA * LipS1 - CageT + LipPress", "Wedge lip outer half-length where the press band starts"),
    ("LipMidB", "CB * LipS1 - CageT + LipPress", "Wedge lip outer half-width where the press band starts"),
    ("LipBotA", "CA * LipS0 - Clr - CageT - LipLead", "Wedge lip outer half-length at its bottom"),
    ("LipBotB", "CB * LipS0 - Clr - CageT - LipLead", "Wedge lip outer half-width at its bottom"),
    ("LipTopA", "CA * Flare - CageT + LipPress", "Wedge lip outer half-length at the crown top"),
    ("LipTopB", "CB * Flare - CageT + LipPress", "Wedge lip outer half-width at the crown top"),
]
row = 1
for title, items in (("Main", main), ("Advanced", advanced), ("Derived", derived)):
    sh.set(f"A{row}", title); sh.set(f"B{row}", "Value"); sh.set(f"C{row}", "Note")
    sh.setStyle(f"A{row}:C{row}", "bold")
    for alias, val, note in items:
        row += 1
        sh.set(f"A{row}", alias); sh.set(f"B{row}", f"={val}"); sh.set(f"C{row}", note)
        sh.setAlias(f"B{row}", alias)
    row += 2
doc.recompute()

# --- Geometry helpers -----------------------------------------------------
def ellipse(name, major, minor, z):
    e = doc.addObject("Part::Ellipse", name)
    e.setExpression("MajorRadius", major)
    e.setExpression("MinorRadius", minor)
    e.setExpression(".Placement.Base.z", z)
    return e

def loft(name, sections):
    l = doc.addObject("Part::Loft", name)
    l.Sections = sections
    l.Solid = True
    l.Ruled = False
    return l

def extrude(name, base, length):
    x = doc.addObject("Part::Extrusion", name)
    x.Base = base
    x.DirMode = "Custom"
    x.Dir = App.Vector(0, 0, 1)
    x.setExpression("LengthFwd", length)
    x.Solid = True
    return x

def boolean(kind, name, base, tool):
    c = doc.addObject(f"Part::{kind}", name)
    c.Base = base
    c.Tool = tool
    return c

def rot_z(deg):
    return App.Placement(App.Vector(), App.Rotation(App.Vector(0, 0, 1), deg))

P = "Params."

# --- Crown: open bottom, seats on brim top, slides over collar ------------
z0 = f"{P}BrimT"
outer = loft("CrownOuter", [
    ellipse("OuterBot", f"{P}CA + {P}Wall", f"{P}CB + {P}Wall", z0),
    ellipse("OuterTop", f"{P}CrownTopA", f"{P}CrownTopB", f"{P}CrownH"),
])
# Inner wall stays straight over the collar so the snap fit keeps its grip
inner = loft("CrownInner", [
    ellipse("InnerBot", f"{P}CA", f"{P}CB", f"{P}BrimT - 1 mm"),
    ellipse("InnerMid", f"{P}CA", f"{P}CB", f"{P}BrimT + {P}CollarH + 1 mm"),
    ellipse("InnerTop", f"{P}CA * {P}Flare", f"{P}CB * {P}Flare",
            f"{P}CrownH - {P}Wall"),
])
inner.Ruled = True
crown_body = boolean("Cut", "CrownBody", outer, inner)

# --- Hatband: follows crown flare, Clr gap inside, BandT thick -----------
# Slides on from the crown's narrow bottom end before the crown meets the
# brim; gravity seats it on the brim top.
def scale_at(z):
    return f"(1 + ({P}Flare - 1) * (({z}) - {P}BrimT) / ({P}CrownH - {P}BrimT))"

zb, zt = f"{P}BrimT", f"{P}BrimT + {P}BandH"

def band_loft(name, offset):
    return loft(name, [
        ellipse(f"{name}Bot", f"({P}CA + {P}Wall) * {scale_at(zb)} + {offset}",
                f"({P}CB + {P}Wall) * {scale_at(zb)} + {offset}", zb),
        ellipse(f"{name}Top", f"({P}CA + {P}Wall) * {scale_at(zt)} + {offset}",
                f"({P}CB + {P}Wall) * {scale_at(zt)} + {offset}", zt),
    ])

band_outer = band_loft("BandOuter", f"{P}Clr + {P}BandT")
band_inner = band_loft("BandInner", f"{P}Clr")
band = boolean("Cut", "Hatband", band_outer, band_inner)

# --- Brim sheet: flat centre band, sides curl up along a cylinder arc ----
# Curl arc is tangent to the flat band at |y| = CurlY0, axis parallel to X.
def box(name, x, y, z, px, py, pz):
    b = doc.addObject("Part::Box", name)
    for prop, v in (("Length", x), ("Width", y), ("Height", z),
                    (".Placement.Base.x", px), (".Placement.Base.y", py),
                    (".Placement.Base.z", pz)):
        b.setExpression(prop, v)
    return b

def x_cylinder(name, radius):
    c = doc.addObject("Part::Cylinder", name)
    c.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0, 1, 0), 90))
    c.Height = 600
    c.setExpression("Radius", radius)
    c.setExpression(".Placement.Base.x", "-300 mm")
    c.setExpression(".Placement.Base.y", f"{P}CurlY0")
    c.setExpression(".Placement.Base.z", f"{P}CurlR")
    return c

flat = box("BrimFlat", "600 mm", f"2 * {P}CurlY0", f"{P}BrimT",
           "-300 mm", f"-{P}CurlY0", "0 mm")
tube = boolean("Cut", "CurlTube", x_cylinder("CurlOuterCyl", f"{P}CurlR"),
               x_cylinder("CurlInnerCyl", f"{P}CurlR - {P}BrimT"))
curl_clip = box("CurlClip", "600 mm", f"{P}CurlR", f"{P}CurlR + 1 mm",
                "-300 mm", f"{P}CurlY0", "-1 mm")
curl_pos = boolean("Common", "CurlPos", tube, curl_clip)
curl_neg = doc.addObject("Part::Mirroring", "CurlNeg")
curl_neg.Source = curl_pos
curl_neg.Normal = App.Vector(0, 1, 0)
sheet = doc.addObject("Part::MultiFuse", "BrimSheet")
sheet.Shapes = [flat, curl_pos, curl_neg]
sheet.Refine = True

# --- Brim ring with collar ------------------------------------------------
brim_prism = extrude("BrimPrism", ellipse("BrimEdge", f"{P}A0 + {P}BrimW",
                                          f"{P}B0 + {P}BrimW", "-1 mm"),
                     f"{P}Curl + {P}BrimT + 10 mm")
brim_disc = boolean("Common", "BrimDisc", sheet, brim_prism)
collar = extrude("CollarSolid", ellipse("CollarEdge", f"{P}A0 + {P}CollarT",
                                        f"{P}B0 + {P}CollarT", "0 mm"),
                 f"{P}BrimT + {P}CollarH")
brim_hole = extrude("BrimHole", ellipse("BrimHoleEdge", f"{P}A0", f"{P}B0", "-1 mm"),
                    f"{P}BrimT + {P}CollarH + 2 mm")

# --- Brim-to-crown joint --------------------------------------------------
# Ribs: one per brim quadrant on the collar, mid-arc (off the seams), engaging
# vertical slots in the crown wall. Q1 rib is wider so the crown fits one way.
# Snap: ramped ridge round the collar clicks into a groove in the crown wall.
CO_A, CO_B = f"({P}A0 + {P}CollarT)", f"({P}B0 + {P}CollarT)"

def rib(name, t, width, grow, z_lo, height):
    ang = f"atan2({CO_A} * sin({t}), {CO_B} * cos({t}))"
    w = f"({width} + 2 * {grow})"
    b = doc.addObject("Part::Box", name)
    b.Placement = rot_z(1)  # axis Z; angle driven by expression
    for prop, v in (
        ("Length", f"1 mm + {P}RibR + {grow}"),
        ("Width", w),
        ("Height", height),
        (".Placement.Rotation.Angle", ang),
        (".Placement.Base.x", f"{CO_A} * cos({t}) - 1 mm * cos({ang}) + {w} / 2 * sin({ang})"),
        (".Placement.Base.y", f"{CO_B} * sin({t}) - 1 mm * sin({ang}) - {w} / 2 * cos({ang})"),
        (".Placement.Base.z", z_lo),
    ):
        b.setExpression(prop, v)
    return b

def snap_ring(name, grow):
    zm = f"({P}BrimT + {P}CollarH / 2)"
    secs = []
    for i, (dz, bump) in enumerate(((f"- {P}SnapH / 2 - {grow}", "0 mm"),
                                    ("", f"{P}Snap + {grow}"),
                                    (f"+ {P}SnapH / 2 + {grow}", "0 mm"))):
        secs.append(ellipse(f"{name}Sec{i}", f"{CO_A} + {grow} + {bump}",
                            f"{CO_B} + {grow} + {bump}", f"{zm} {dz}"))
    l = loft(name, secs)
    l.Ruled = True
    return l

rib_angles = [45, 135, 225, 315]  # one per quadrant Q1..Q4
ribs, slots = [], []
for q, t in enumerate(rib_angles, start=1):
    width = f"{P}RibWFront" if q == 1 else f"{P}RibW"
    ribs.append(rib(f"Rib{q}", t, width, "0 mm", f"{P}BrimT", f"{P}CollarH"))
    slots.append(rib(f"Slot{q}", t, width, f"{P}Clr", f"{P}BrimT - 1 mm",
                     f"{P}CollarH + {P}Clr + 1 mm"))
ridge = snap_ring("SnapRidge", "0 mm")
groove = snap_ring("SnapGroove", f"{P}Clr")

crown_tool = doc.addObject("Part::MultiFuse", "CrownJointCuts")
crown_tool.Shapes = slots + [groove]
crown_cut = boolean("Cut", "CrownCut", crown_body, crown_tool)

# Wedge lip: hangs from the crown top just inside the cage finger tips. Its
# lower 40% is a lead-in taper (LipLead clearance at the bottom), its upper
# 60% a press band running parallel to the wall CageT - LipPress away. Seating
# the crown on the brim drives the lip down inside the tips and presses them
# flat to the wall. Prints on the inner face (crown prints top-down), so
# nothing shows outside.
lip_zb = f"({P}CrownH - {P}Wall - {P}LipH)"
lip_zm = f"({lip_zb} + 0.4 * {P}LipH)"


def lip_loft(name, inset, ext):
    """Lip surface `inset` inside the outer face, extended `ext` past its ends."""
    secs = [ellipse(f"{name}Bot", f"{P}LipBotA - {inset}", f"{P}LipBotB - {inset}", f"{lip_zb} - {ext}"),
            ellipse(f"{name}Mid", f"{P}LipMidA - {inset}", f"{P}LipMidB - {inset}", lip_zm),
            ellipse(f"{name}Top", f"{P}LipTopA - {inset}", f"{P}LipTopB - {inset}",
                    f"{P}CrownH - {P}Wall + {ext} + 0.5 mm")]
    l = loft(name, secs)
    l.Ruled = True
    return l


lip_outer = lip_loft("CageLipOuter", "0 mm", "0 mm")
lip_inner = lip_loft("CageLipInner", f"{P}CageT", "1 mm")
lip = boolean("Cut", "CageLip", lip_outer, lip_inner)
crown = doc.addObject("Part::MultiFuse", "Crown")
crown.Shapes = [crown_cut, lip]
crown.Refine = True

brim_solid = doc.addObject("Part::MultiFuse", "BrimSolid")
brim_solid.Shapes = [brim_disc, collar, ridge] + ribs
brim_ring = boolean("Cut", "BrimRing", brim_solid, brim_hole)

# --- Dovetail keys --------------------------------------------------------
# Seam k lies on the ray at k*90 deg. Wedge local frame: X = radial along seam,
# Y = across seam (neck at Y=0, head at Y=KeyDepth), Z = thickness.
# Seam k tongue belongs to quadrant k (CCW owner) and enters quadrant k+1.
def key(name, seam, grow, z_lo, z_hi):
    radius = f"{P}A0" if seam % 2 == 0 else f"{P}B0"
    mid = f"({radius} + {P}CollarT + ({P}BrimW - {P}CollarT) / 2)"
    w = doc.addObject("Part::Wedge", name)
    w.Placement = rot_z(seam * 90)
    w.setExpression("Ymin", f"-1 mm - {grow}")
    w.setExpression("Ymax", f"{P}KeyDepth + {grow}")
    w.setExpression("Xmin", f"{mid} - {P}KeyNeck / 2 - {grow}")
    w.setExpression("Xmax", f"{mid} + {P}KeyNeck / 2 + {grow}")
    w.setExpression("X2min", f"{mid} - {P}KeyHead / 2 - {grow}")
    w.setExpression("X2max", f"{mid} + {P}KeyHead / 2 + {grow}")
    for p, v in (("Zmin", z_lo), ("Z2min", z_lo), ("Zmax", z_hi), ("Z2max", z_hi)):
        w.setExpression(p, v)
    return w

pieces = []
for q in range(1, 5):
    box = doc.addObject("Part::Box", f"QuadBox{q}")
    box.Length = box.Width = 600
    box.Height = 300
    box.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0, 0, 1), (q - 1) * 90))
    box.Placement.Base = box.Placement.Rotation.multVec(App.Vector(0, 0, -100))
    quad = boolean("Common", f"BrimQ{q}Base", brim_ring, box)
    owned, incoming = q % 4, q - 1  # seam indices
    # Keys are tall prisms clipped to the brim, so they follow the curl
    z_top = f"{P}Curl + {P}BrimT + 2 mm"
    tongue = boolean("Common", f"Key{q}", brim_ring,
                     key(f"KeyPrism{q}", owned, "0 mm", "-2 mm", z_top))
    socket = key(f"Socket{q}", incoming, f"{P}Clr", "-2 mm", z_top)
    keyed = boolean("Fuse", f"BrimQ{q}Keyed", quad, tongue)
    keyed.Refine = True
    piece = boolean("Cut", f"BrimQ{q}", keyed, socket)
    piece.Refine = True
    pieces.append(piece)

doc.recompute()

if App.GuiUp:
    import FreeCADGui as Gui
    keep = {"Params", "Crown", "Hatband"} | {p.Name for p in pieces}
    for o in doc.Objects:
        if o.Name not in keep and hasattr(o, "ViewObject") and o.ViewObject:
            o.ViewObject.Visibility = False
    crown.ViewObject.ShapeColor = (0.05, 0.05, 0.05)
    band.ViewObject.ShapeColor = (0.45, 0.05, 0.08)
    shades = [(0.12, 0.12, 0.12), (0.22, 0.22, 0.25)]
    for i, p in enumerate(pieces):
        p.ViewObject.ShapeColor = shades[i % 2]
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
