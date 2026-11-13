"""Generic sled: a flat plate on the rail sliders with a ledge along its
bottom edge and rubber-band hooks along both sides. Stand an item on the
ledge and strap it to the plate with bands across it, hooked on either side.

Sizes are options: w across the rail, l along it (mm), plus optional
item=(w, l, depth, grams) to check an item's fit and weight in the layout.
VARIANTS lists the sizes that get exported. It stands on a locking slider,
plus a guide slider at the top when it is mount.GUIDE_MIN or longer. One
locking slider holds about 50 g. Prints standing on its ledge end; every
feature is prismatic along the rail or has a 45 deg underside.
"""
import Part
from FreeCAD import Vector as V

import mount
from common import box, fuse

PURPOSE = "Plate with a bottom ledge and rubber-band hooks; straps any item on"
VARIANTS = [dict(w=40, l=60), dict(w=60, l=90), dict(w=80, l=110)]

PLATE_T = 2.4      # plate thickness (shoe plate plus 0.4)
LEDGE = 6.0        # ledge depth from the plate face
LEDGE_T = 2.0
HOOK_PITCH = 20.0  # hook spacing along each side
HOOK_W = 5.0       # hook width along the rail
HOOK_H = 6.0       # hook height from the plate face
HOOK_T = 1.6       # stem and lip thickness
LIP = 2.0          # lip reach outward past the plate edge


def base_height(val, w=60, l=90, **opts):
    return l


def face():
    """Plate front face: items rest against it."""
    return mount.Y_PLATE + PLATE_T


def _hook(sx, x_edge, zc):
    """J hook at a plate side edge, centred at zc, lip pointing outward."""
    yf = face()
    x_in = x_edge - sx * HOOK_T
    stem = [(x_in, yf - 0.01), (x_edge, yf - 0.01), (x_edge, yf + HOOK_H - HOOK_T),
            (x_edge + sx * LIP, yf + HOOK_H - HOOK_T), (x_edge + sx * LIP, yf + HOOK_H),
            (x_in, yf + HOOK_H)]
    z0 = zc - HOOK_W / 2 - HOOK_H
    pts = [V(x, y, z0) for x, y in stem]
    h = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, HOOK_W + HOOK_H))
    # 45 deg underside, rising from the plate face to the hook tip
    xs = sorted((x_in, x_edge + sx * LIP))
    cut = [V(xs[0] - 1, yf - 0.02, z0 - 0.01), V(xs[0] - 1, yf + HOOK_H + 0.01, z0 - 0.01),
           V(xs[0] - 1, yf + HOOK_H + 0.01, z0 + HOOK_H + 0.02)]
    wedge = Part.Face(Part.makePolygon(cut + [cut[0]])).extrude(V(xs[1] - xs[0] + 2, 0, 0))
    return h.cut(wedge)


def name(w=60, l=90, **opts):
    return f"sled_{w:g}x{l:g}"


def parts(val, w=60, l=90, **opts):
    hw = max(w / 2, mount.HALF_W)
    yf = face()
    plate = box(-hw, hw, mount.Y_PLATE, yf, 0, l)
    ledge = box(-hw, hw, yf - 0.01, yf + LEDGE, 0, LEDGE_T)
    hooks = []
    k = int((l - LEDGE_T - HOOK_H - HOOK_W) // HOOK_PITCH)  # hooks per side
    z_first = l - HOOK_W / 2 - k * HOOK_PITCH
    for sx in (-1, 1):
        hooks += [_hook(sx, sx * hw, z_first + i * HOOK_PITCH) for i in range(k + 1)]
    return [(name(w=w, l=l), fuse([mount.base(l), plate, ledge] + hooks))]


def payload(val, w=60, l=90, item=None, **opts):
    if not item:
        return []
    iw, il, depth, grams = item
    yf = face()
    return [("item", box(-iw / 2, iw / 2, yf, yf + depth, LEDGE_T, LEDGE_T + il), grams)]
