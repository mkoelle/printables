"""Breadboard holders: a shallow pocket the board presses into, held by snap
clips over its side edges (no glue). The board stands along the rail, its
long side vertical, contacts facing the hat axis.

Sizes (size option), by their usual names:
  mini   170 tie-points, 47 x 35 mm
  half   400 tie-points (half size), 84 x 55 mm; makers range 82-84 x
         54.5-55 mm
Boards are 8.5 mm thick bare and 9.3-10 mm with adhesive foam on the back;
board_h defaults to 9.3 (with foam, which the clips compress slightly).
The floor is a diamond lattice (mount.lattice) with a solid border.
To fit a board, rest its bottom edge on the bottom rim and press it in past
the side clips; spread the clips to remove it. Prints standing on its
bottom end: the clips are prismatic along the rail and the top rim has a
45 deg underside.
"""
import Part
from FreeCAD import Vector as V

import mount
from common import box, fuse

PURPOSE = "Breadboard pocket with snap clips over the side edges (mini 170 / half 400 tie-points)"
SIZES = {"mini": (35.0, 47.0, 1), "half": (55.0, 84.0, 2)}  # width, length, clips per side
GRAMS = {"mini": 10, "half": 30}   # board, without parts or wires
VARIANTS = [dict(size="mini"), dict(size="half")]

FIT = 0.3       # pocket clearance each side
RIM_H = 3.0     # bottom, side and top rim height above the floor
CLIP_T = 1.2    # clip wall thickness (3 lines)
CLIP_L = 10.0   # clip length along the rail
CLIP_GAP = 1.0  # gap either side of a clip, so it flexes on its own
LIP = 0.7       # clip overlap onto the board's front face
LIP_T = 1.2     # lip thickness over the board


def _dims(val, size="half", board_h=9.3, **opts):
    w, l, clips = SIZES[size]
    rim = val("Nozzle") * 4
    hw = w / 2 + FIT
    z0, z1 = rim, rim + l + 2 * FIT
    return w, l, board_h, clips, hw, z0, z1


def base_height(val, **opts):
    return _dims(val, **opts)[-1] + RIM_H


def _clip(sx, hw, zc, yb):
    """Side clip at x = sx * hw, centred at zc (CLIP_L long at the lip). Its
    lip's underside at yb holds the board; its sloped top face is the
    lead-in that spreads it. The bottom end slopes at 45 deg down to the
    floor, so it prints without support."""
    y0 = mount.Y_MOUNT - 0.01
    xo = hw + CLIP_T
    ys = yb + LIP_T - y0                      # clip height above the floor
    zb = zc - CLIP_L / 2 - ys                 # foot of the 45 deg end
    prof = [(hw, y0), (xo, y0), (xo, yb + LIP_T), (hw - LIP, yb), (hw, yb)]
    pts = [V(sx * x, y, zb) for x, y in prof]
    c = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, CLIP_L + ys))
    xs = sorted((sx * (hw - LIP - 1), sx * (xo + 1)))
    w = [V(xs[0], y0 - 0.01, zb - 0.01), V(xs[0], y0 + ys + 0.01, zb - 0.01), V(xs[0], y0 + ys + 0.01, zb + ys)]
    return c.cut(Part.Face(Part.makePolygon(w + [w[0]])).extrude(V(xs[1] - xs[0], 0, 0)))


def parts(val, size="half", **opts):
    w, l, board_h, clips, hw, z0, z1 = _dims(val, size=size, **opts)
    h = z1 + RIM_H
    y0, y1 = mount.Y_MOUNT, mount.Y_MOUNT + RIM_H
    xo = hw + CLIP_T
    rib = val("Nozzle") * 4
    floor = box(-xo, xo, mount.Y_PLATE, y0, 0, h).cut(
        mount.lattice(hw - rib, z0 + rib, z1 - rib, y0 - mount.Y_PLATE, rib=rib))
    bottom = box(-xo, xo, y0 - 0.01, y1, 0, z0)
    # top rim with a 45 deg underside, so it prints without support
    pts = [V(-xo, y0 - 0.01, z1), V(-xo, y0 - 0.01, h), V(-xo, y1, h)]
    top = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(2 * xo, 0, 0))
    yb = y0 + board_h + 0.2
    foot = yb + LIP_T - y0  # the clip's 45 deg end reaches this far below its lip
    zcs = [z0 + (i + 0.5) * (z1 - z0) / clips for i in range(clips)]
    edges = [z0] + [e for zc in zcs
                    for e in (zc - CLIP_L / 2 - foot - CLIP_GAP, zc + CLIP_L / 2 + CLIP_GAP)] + [z1]
    extras = []
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hw, sx * xo))
        # low side rims between the clips locate the board
        extras += [box(x0, x1, y0 - 0.01, y1, za, zb)
                   for za, zb in zip(edges[::2], edges[1::2]) if zb - za > 1]
        extras += [_clip(sx, hw, zc, yb) for zc in zcs]
    return [(f"breadboard_{size}", fuse([mount.base(h), floor, bottom, top] + extras))]


def payload(val, size="half", **opts):
    w, l, board_h, clips, hw, z0, z1 = _dims(val, size=size, **opts)
    board = box(-w / 2, w / 2, mount.Y_MOUNT, mount.Y_MOUNT + board_h, z0 + FIT, z0 + FIT + l)
    return [("breadboard", board, GRAMS[size])]
