"""Parametric plague doctor mask (PLA, 220 x 220 mm bed).

Builds PlagueMask.FCStd (face shell, beak, eye inserts, bezel, face reference)
and PlagueMaskTests.FCStd (fit frame and fit coupons), and writes STLs to
stl/. Run inside FreeCAD:

  exec(open(os.path.expanduser("~/src/github.com/mkoelle/printables/plaguemask/mask.py")).read())

Coordinates (mm): origin midway between the pupils, X to the wearer's left,
Y forward out of the face (y = 0 at the front of the eyes), Z up.

The face is modelled as a loft of rounded-rectangle-like (superellipse)
cross-sections at brow, eye, cheekbone, mouth and chin height, sized from the
measurements in MAIN. The shell sits FaceGap outside it. The nose sits inside
the beak socket; the beak is hollow and open to the mask, with nostril vents.
"""
import math
import os
import FreeCAD as App
import Part
import MeshPart
from FreeCAD import Vector as V

DIR = os.path.expanduser("~/src/github.com/mkoelle/printables/plaguemask")
BED = 220.0

# --- Parameters -------------------------------------------------------------
# Face measurements (README table). Defaults are typical adult values:
# replace them with your own.
MAIN = {
    "FaceW":     (140.0, "Face width across the cheekbones"),
    "TempleW":   (135.0, "Temple width at eye level"),
    "FaceL":     (130.0, "Eyebrow line to bottom of chin"),
    "EyeSpace":  (63.0,  "Pupil to pupil"),
    "EyeH":      (110.0, "Bottom of chin to pupils"),
    "NoseProj":  (30.0,  "Nose tip forward of the cheeks"),
    "ChinDepth": (120.0, "Chin tip back to front of ear"),
    "HatClear":  (25.0,  "Eyebrow line up to the top hat brim"),
    # design
    "BeakL":     (180.0, "Beak length from the mask"),
    "BeakDroop": (0.25,  "Beak tip drop as a fraction of BeakL"),
    "Clr":       (0.2,   "Print clearance for all fits"),
}
ADVANCED = {
    "Wall":      (2.4,  "Shell and beak wall thickness"),
    "FaceGap":   (12.0, "Space between face and shell"),
    "EarClear":  (25.0, "Shell side edge stops this far in front of the ear"),
    "EyeR":      (19.0, "Eye opening radius (clear view)"),
    "EyeClear":  (16.0, "Lens distance in front of the eye"),
    "DiscT":     (0.5,  "Lens sheet or mesh thickness"),
    "Snap":      (0.5,  "Snap ridge height (eye inserts, beak)"),
    "BeakW":     (52.0, "Beak base width"),
    "BeakH":     (50.0, "Beak base height"),
    "BeakPiece": (190.0, "Longest beak section printed in one piece"),
    "NoseZ":     (-40.0, "Beak socket centre height (below the pupils)"),
    "StrapW":    (20.0, "Elastic strap width"),
    "StrapT":    (3.5,  "Strap slot thickness"),
}
P = {k: v for k, (v, _) in {**MAIN, **ADVANCED}.items()}
g = P.__getitem__
T, Clr, gap = g("Wall"), g("Clr"), g("FaceGap")

# Derived face levels: (z, half width, y of face front at the centre line)
brow_z = g("FaceL") - g("EyeH")             # eyebrow line above the pupils
z_top = max(brow_z + 5, brow_z + g("HatClear") - 5)  # 5 mm below the hat brim
z_bot = -g("EyeH") - 15                     # 15 mm below the chin
y_cut = 3 - g("ChinDepth") + g("EarClear")  # side edges (chin tip at y ~ 3)
JawW, ChinW = 0.82 * g("FaceW"), 0.45 * g("FaceW")
LEVELS = [
    (z_top + 12, g("TempleW") / 2, -10),
    (z_top, g("TempleW") / 2, -6),
    (brow_z, g("TempleW") / 2, 2),
    (0.0, (g("TempleW") + g("FaceW")) / 4, 0),
    (-15.0, g("FaceW") / 2, 0),
    (-0.6 * g("EyeH"), JawW / 2, 8),
    (-g("EyeH"), ChinW / 2, 3),
    (z_bot - 12, ChinW / 2 * 0.9, -8),
]
DEPTH = g("ChinDepth")                      # section depth (front to back)
SUPER = 2.6                                 # cross-section squareness
SEC_PTS = 24                                # points per cross-section


# --- Geometry helpers -------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def fuse(shapes):
    s = shapes[0].fuse(shapes[1:]) if len(shapes) > 1 else shapes[0]
    return s.removeSplitter()


def section(z, hw, yf, grow):
    """Closed superellipse wire at height z; front at yf + grow."""
    a, b, yc = hw + grow, DEPTH + grow, yf - DEPTH
    pts = []
    for i in range(SEC_PTS):
        t = 2 * math.pi * i / SEC_PTS
        c, s = math.cos(t), math.sin(t)
        pts.append(V(a * math.copysign(abs(c) ** (2 / SUPER), c),
                     yc + b * math.copysign(abs(s) ** (2 / SUPER), s), z))
    bs = Part.BSplineCurve()
    bs.interpolate(Points=pts, PeriodicFlag=True)
    return Part.Wire([bs.toShape()])


def face_solid(grow):
    return Part.makeLoft([section(z, hw, yf, grow) for z, hw, yf in LEVELS], True, False)


def front_y(solid, x, z):
    """Front surface y of `solid` along the line at (x, z)."""
    c = solid.common(Part.makeLine(V(x, -300, z), V(x, 300, z)))
    return max(v.Point.y for v in c.Vertexes)


def xz_ellipse(a, b, y, zc, x=0.0):
    """Ellipse wire in the plane y = const, half-axes a (X) and b (Z)."""
    e = Part.Ellipse(V(), max(a, b), min(a, b)).toShape()
    if a < b:
        e.rotate(V(), V(0, 0, 1), 90)
    e.rotate(V(), V(1, 0, 0), 90)
    e.translate(V(x, y, zc))
    return Part.Wire([e])


def oval_prism(a, b, y0, y1, zc, x=0.0):
    return Part.Face(xz_ellipse(a, b, y0, zc, x)).extrude(V(0, y1 - y0, 0))


def nose_solid(grow):
    """Nose from the bridge between the eyes to the tip and base, grown by
    `grow` mm. Sections: (z, front y, half width)."""
    secs = []
    for z, yf, w in ((-4, 8, 7), (-20, 0.55 * g("NoseProj"), 11),
                     (-38, g("NoseProj"), 16), (-48, 0.5 * g("NoseProj"), 17)):
        e = Part.Ellipse(V(0, yf - 25, z), 25 + grow, w + grow).toShape()
        e.rotate(V(0, yf - 25, z), V(0, 0, 1), 90)
        secs.append(Part.Wire([e]))
    return Part.makeLoft(secs, True, False)


def tube_y(r_out, r_in, y0, y1, x, z):
    o = Part.makeCylinder(r_out, y1 - y0, V(x, y0, z), V(0, 1, 0))
    return o.cut(Part.makeCylinder(r_in, y1 - y0 + 2, V(x, y0 - 1, z), V(0, 1, 0))) if r_in > 0 else o


import time

# Stages run top to bottom; set MASK_STAGES before exec to run a subset
# (state from earlier runs stays in the FreeCAD session's globals).
MASK_STAGES = globals().get("MASK_STAGES") or ["shell", "eyes", "beak", "slots", "checks", "save", "tests"]
_clock = {"name": None, "t": time.time()}


def want(name):
    if _clock["name"]:
        print(f"[{_clock['name']} {time.time() - _clock['t']:.1f} s]")
    _clock.update(name=name if name in MASK_STAGES else None, t=time.time())
    return name in MASK_STAGES


# --- Face, shell --------------------------------------------------------------
if want("shell"):
    face = face_solid(0)
    inner, outer = face_solid(gap), face_solid(gap + T)
    keep = box(-300, 300, y_cut, 300, z_bot, z_top)
    shell = outer.cut(inner).common(keep)


# --- Eye sockets and inserts ------------------------------------------------
if want("eyes"):
    EyeR, DiscT, Snap = g("EyeR"), g("DiscT"), g("Snap")
    Rd = EyeR + 2.0                 # disc radius
    Rb = Rd + 0.3                   # socket bore radius
    SOCK_T, SHOULDER, INSERT_L = 2.0, 1.6, 6.0
    eyes = [(sx * g("EyeSpace") / 2, 0.0) for sx in (1, -1)]
    sock_parts, sock_holes, inserts_at = [], [], []
    for ex, ez in eyes:
        y_in, y_out = front_y(inner, ex, ez), front_y(outer, ex, ez)
        y_t = max(y_out, g("EyeClear") + SHOULDER + DiscT) + 4     # socket front
        y_disc = y_t - SHOULDER - DiscT                            # disc back face
        y_g = y_disc - INSERT_L / 2                                # snap groove
        tube = tube_y(Rb + SOCK_T, Rb, y_in - 1, y_t - SHOULDER, ex, ez)
        tube = tube.fuse(tube_y(Rb + SOCK_T, EyeR, y_t - SHOULDER, y_t, ex, ez))
        tube = tube.cut(tube_y(Rb + Snap + Clr, 0, y_g - 0.6 - Clr, y_g + 0.6 + Clr, ex, ez))
        sock_parts.append(tube.common(outer.cut(inner).fuse(box(-300, 300, y_out - 3, 300, -300, 300))))
        sock_holes.append(Part.makeCylinder(Rb, 200, V(ex, -100, ez), V(0, 1, 0)))
        inserts_at.append((ex, ez, y_disc, y_g, y_t))
    shell = fuse([shell.cut(sock_holes)] + sock_parts)


    def eye_insert(mesh):
        """C-ring that snaps into the socket from the face side and clamps the
        disc (lens) or fabric mesh against the socket shoulder. Built at the
        origin, axis Y, front face at y = 0."""
        ring = tube_y(Rb - Clr, EyeR, -INSERT_L, 0, 0, 0)
        ring = ring.fuse(tube_y(Rb - Clr + Snap, EyeR, -INSERT_L / 2 - 0.5, -INSERT_L / 2 + 0.5, 0, 0))
        ring = ring.cut(box(-2, 2, -INSERT_L - 1, 1, EyeR - 1, Rb + 2))  # C-gap so it can squeeze in
        if mesh:  # small teeth grip the mesh
            teeth = []
            for i in range(16):
                a = 2 * math.pi * (i + 0.5) / 16
                r = (EyeR + Rb - Clr) / 2
                teeth.append(Part.makeCone(0.7, 0.05, DiscT * 0.8, V(r * math.cos(a), 0, r * math.sin(a)), V(0, 1, 0)))
            ring = ring.fuse(teeth)
        return ring.removeSplitter()


    lens_ring, mesh_ring = eye_insert(False), eye_insert(True)
    disc_template = Part.makeCylinder(Rd, 1.2, V(), V(0, 0, 1)).fuse(box(-3, 3, Rd - 2, Rd + 15, 0, 1.2))
    ex0, ez0, _, _, y_t0 = inserts_at[0]
    bezel = tube_y(Rb + SOCK_T + Clr + 3, Rb + SOCK_T + Clr, y_t0 - 5, y_t0 + 1, ex0, ez0)
    bezel = bezel.fuse(tube_y(Rb + SOCK_T + Clr + 3, EyeR + 1, y_t0, y_t0 + 1, ex0, ez0))


# --- Beak socket (collar on the mask) and beak --------------------------------
if want("beak"):
    BW, BH, nz = g("BeakW") / 2, g("BeakH") / 2, g("NoseZ")
    COLLAR_T, COLLAR_L = 2.0, 12.0
    ca, cb = BW - T - Clr, BH - T - Clr        # collar outer half axes
    # shell outer: most forward point round the beak base outline
    y_so = max(front_y(outer, BW * 1.02 * math.cos(2 * math.pi * i / 16), nz + BH * 1.02 * math.sin(2 * math.pi * i / 16))
               for i in range(16))
    y_cf = y_so + COLLAR_L                     # collar front
    collar = oval_prism(ca, cb, y_so - 8, y_cf, nz).cut(oval_prism(ca - COLLAR_T, cb - COLLAR_T, y_so - 20, y_cf + 1, nz))
    collar = collar.fuse(oval_prism(ca + Snap, cb + Snap, y_cf - 4, y_cf - 2.8, nz).cut(
        oval_prism(ca - 1, cb - 1, y_cf - 5, y_cf - 2, nz)))
    collar = collar.cut(inner)                  # nothing inside the shell's inner face
    shell = fuse([shell.cut(oval_prism(ca - COLLAR_T, cb - COLLAR_T, -100, y_cf + 1, nz)), collar])
    # nose bridge hump: shell bulges out over the bridge, NoseGap clear of it
    NG = 6.0
    hump = nose_solid(NG + T).cut(nose_solid(NG)).cut(inner).common(box(-300, 300, -300, 300, nz, 2))
    shell = fuse([shell.cut(nose_solid(NG).common(box(-300, 300, -300, 300, nz, 2))), hump])

    L, droop, yb0 = g("BeakL"), g("BeakDroop"), y_so + 1


    y_taper = y_cf + 2                         # beak stays full size over the collar


    def beak_sections(inset, s_end=0.985, n=10, back=0.0):
        """Beak loft: straight from its base to y_taper, then tapering and
        drooping over the remaining length to the tip."""
        run = yb0 + L - y_taper
        secs = [xz_ellipse(BW - inset, BH - inset, yb0 - back, nz)]
        for i in range(n):
            s = s_end * i / (n - 1)
            k = (1 - s) ** 0.75
            a, b = max(BW * k - inset, 0.8), max(BH * k - inset, 0.8)
            secs.append(xz_ellipse(a, b, y_taper + run * s, nz - droop * L * s * s))
        return Part.makeLoft(secs, True, False)


    beak_outer = beak_sections(0)
    s_in = 1 - ((T + 1.5) / min(BW, BH)) ** (1 / 0.75)  # inner cavity ends where it gets thin
    beak_inner = beak_sections(T, s_end=s_in, back=2)
    beak = beak_outer.cut(beak_inner)
    groove = oval_prism(ca + Snap + Clr, cb + Snap + Clr, y_cf - 4 - Clr, y_cf - 2.8 + Clr, nz)
    beak = beak.cut(groove)
    # nostrils on top near the base, plus two hidden vents underneath
    vents = []
    s_v = 0.2
    yv, zv = y_taper + (yb0 + L - y_taper) * s_v, nz - droop * L * s_v * s_v
    for sx in (1, -1):
        for up in (1, -1):
            c = Part.Face(Part.Wire([Part.Ellipse(V(sx * BW * 0.35, yv, 0), 7, 3.5).toShape()]))
            c.rotate(V(sx * BW * 0.35, yv, 0), V(0, 0, 1), 90)
            vents.append(c.extrude(V(0, 0, up * 100)).translated(V(0, 0, zv)))
    beak = beak.cut(vents)
    VENT_AREA = 4 * math.pi * 7 * 3.5

    # split into printable sections with a sleeve joint
    pieces = []
    n_pieces = max(1, math.ceil(L / g("BeakPiece")))
    cuts_y = [yb0 + L * i / n_pieces for i in range(1, n_pieces)]
    bounds = [-300] + cuts_y + [600]
    for i in range(n_pieces):
        pc = beak.common(box(-300, 300, bounds[i], bounds[i + 1], -300, 300))
        if i < n_pieces - 1:
            ys = bounds[i + 1]
            sleeve = beak_sections(T + Clr, s_end=s_in).cut(beak_sections(T + Clr + 1.6, s_end=s_in))
            pc = pc.fuse(sleeve.common(box(-300, 300, ys - 2, ys + 10, -300, 300)))
        pieces.append(pc.removeSplitter())


# --- Strap slots ----------------------------------------------------------------
if want("slots"):
    SW, ST = g("StrapW") + 1, g("StrapT")
    slots = [box(-300, -40, y_cut + 8, y_cut + 8 + ST, -SW / 2, SW / 2),
             box(40, 300, y_cut + 8, y_cut + 8 + ST, -SW / 2, SW / 2),
             box(-SW / 2, SW / 2, -300, 300, z_top - 8 - ST, z_top - 8)]
    shell = shell.cut(slots)


# --- Checks -----------------------------------------------------------------
if want("checks"):
    nose = nose_solid(0)
    lashes = [Part.makeCylinder(12, 10, V(ex, 0, ez), V(0, 1, 0)) for ex, ez in eyes]
    parts = {"Shell": shell, "Beak": beak}
    print(f"face levels z: top {z_top:.0f}, brow {brow_z:.0f}, chin {-g('EyeH'):.0f}, bottom {z_bot:.0f}; "
          f"side edge y {y_cut:.0f}")
    for name, s in parts.items():
        print(f"{name}: valid {s.isValid()} solids {len(s.Solids)} {s.Volume / 1000 * 1.24:.0f} g, "
              f"face overlap {s.common(face).Volume:.3f}, nose {s.common(nose).Volume:.3f}, "
              f"eyelash zone {sum(s.common(l).Volume for l in lashes):.3f} mm3")
    sockets = fuse([tube_y(Rb + SOCK_T, 0, -50, 100, ex, ez) for ex, ez in eyes])
    print(f"eye sockets vs beak collar: {sockets.common(collar).Volume:.3f} mm3, "
          f"vs nose hump: {sockets.common(hump).Volume:.3f} mm3 (must be 0)")
    print(f"shell/beak overlap {shell.common(beak).Volume:.3f} mm3; beak in {n_pieces} piece(s); "
          f"beak vents {VENT_AREA:.0f} mm2 plus the open lower edge")
    for i, (ex, ez, y_disc, y_g, y_t) in enumerate(inserts_at):
        ins = lens_ring.translated(V(ex, y_disc, ez))
        print(f"eye {i}: lens {y_disc + DiscT:.1f} mm in front of the eye, insert overlap "
              f"{ins.common(shell).Volume:.3f} mm3 (snap ridge in groove: 0 expected)")



# --- Models + export --------------------------------------------------------
if want("save"):
    def place_y_up(s):
        """Lay a part with its back (min y) on the bed."""
        s = s.copy()
        s.rotate(V(), V(1, 0, 0), 90)
        bb = s.optimalBoundingBox()
        s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
        return s


    def export(shape, name, lay=True):
        s = place_y_up(shape) if lay else shape
        bb = s.optimalBoundingBox()
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.1, Relative=False)
        m.write(os.path.join(DIR, "stl", f"{name}.stl"))
        print(f"  stl {name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm "
              f"fits={bb.XLength <= BED and bb.YLength <= BED} {shape.Volume / 1000 * 1.24:.0f} g")


    def save_model(model, objs):
        if model in App.listDocuments():
            App.closeDocument(model)
        doc = App.newDocument(model)
        sheet = doc.addObject("Spreadsheet::Sheet", "Params")
        row = 1
        for title, items in (("Main", MAIN), ("Advanced", ADVANCED)):
            sheet.set(f"A{row}", title)
            for k, (v, note) in items.items():
                row += 1
                sheet.set(f"A{row}", k); sheet.set(f"B{row}", str(v)); sheet.set(f"C{row}", note)
            row += 2
        for name, s, color, transp in objs:
            o = doc.addObject("Part::Feature", name)
            o.Shape = s
            if App.GuiUp:
                o.ViewObject.ShapeColor = color
                o.ViewObject.Transparency = transp
        doc.recompute()
        if App.GuiUp:
            import FreeCADGui as Gui
            Gui.activeDocument().activeView().viewIsometric()
            Gui.SendMsgToActiveView("ViewFit")
        doc.saveAs(os.path.join(DIR, f"{model}.FCStd"))


    leather, dark, skin = (0.35, 0.22, 0.12), (0.15, 0.15, 0.15), (0.85, 0.7, 0.6)
    model_parts = [("Shell", shell, leather, 0)] + \
        [(f"Beak{i + 1}", p, leather, 0) for i, p in enumerate(pieces)] + \
        [(f"LensRing{i}", lens_ring.translated(V(ex, y_disc, ez)), dark, 0)
         for i, (ex, ez, y_disc, _, _) in enumerate(inserts_at)] + \
        [("Bezel", bezel, dark, 0), ("FaceReference", face.common(keep), skin, 70)]
    save_model("PlagueMask", model_parts)
    os.makedirs(os.path.join(DIR, "stl"), exist_ok=True)
    export(shell, "mask_shell")
    for i, p in enumerate(pieces):
        export(p, f"mask_beak_{i + 1}")
    export(lens_ring, "mask_lens_ring")
    export(mesh_ring, "mask_mesh_ring")
    export(disc_template, "mask_disc_template", lay=False)
    export(bezel, "mask_bezel_plain")


# --- Fit tests ----------------------------------------------------------------
if want("tests"):
    # Coupons and frame are rebuilt from the trimmed wall plus the socket
    # parts: booleans against the finished shell around the eye sockets come
    # back empty.
    wall = outer.cut(inner).common(keep)
    band = wall.cut(box(-300, 300, y_cut + 12, 300, z_bot + 12, z_top - 12))
    eye_rings = wall.common(fuse([Part.makeCylinder(Rb + SOCK_T + 8, 300, V(ex, -150, ez), V(0, 1, 0)) for ex, ez in eyes]))
    strips = wall.common(fuse([box(-8, 8, -300, 300, -300, 300), box(-300, 300, -300, 300, -5, 5)]))
    frame = fuse([band.fuse([eye_rings, strips]).cut(sock_holes)] + sock_parts).cut(slots)
    ex, ez = eyes[0]
    eye_coupon = fuse([wall.common(Part.makeCylinder(Rb + SOCK_T + 10, 300, V(ex, -150, ez), V(0, 1, 0)))
                       .cut(sock_holes[0]), sock_parts[0]])
    beak_coupon_mask = fuse([wall.common(oval_prism(ca + 12, cb + 12, -300, 300, nz))
                             .cut(oval_prism(ca - COLLAR_T, cb - COLLAR_T, -100, y_cf + 1, nz)), collar])
    beak_coupon_beak = pieces[0].common(box(-300, 300, -300, yb0 + 25, -300, 300))
    strap_coupon = shell.common(box(30, 300, y_cut - 5, y_cut + 30, -20, 20))
    tests = [("fit_frame", frame), ("eye_socket", eye_coupon), ("beak_socket", beak_coupon_mask),
             ("beak_base", beak_coupon_beak), ("strap_slot", strap_coupon)]
    print("fit tests:")
    save_model("PlagueMaskTests", [(n, s, leather, 0) for n, s in tests] + [("FaceReference", face.common(keep), skin, 70)])
    for n, s in tests:
        export(s, f"test_mask_{n}")
    print(f"  beak_socket/beak_base overlap {beak_coupon_mask.common(beak_coupon_beak).Volume:.3f} mm3 (must be 0)")


want("end")
