"""Mini breadboard holder: a shallow pocket for a 170 tie-point breadboard
(35 x 47 x 8.5 mm), whose self-adhesive back sticks to the pocket floor.
The board stands along the rail, its long side vertical, contacts facing
the hat axis. Prints standing on its bottom end.
"""
import Part
from FreeCAD import Vector as V

import mount
from common import box, fuse

PURPOSE = "Mini breadboard (170 tie-points) for prototype circuits"

BOARD_W, BOARD_L, BOARD_H = 35.0, 47.0, 8.5  # across the rail, along it, depth
FIT = 0.3       # pocket clearance each side
RIM_H = 3.0     # rim height above the pocket floor
GRAMS = 10      # board, without parts or wires


def _pocket(val):
    rim_t = val("Nozzle") * 4
    hw = BOARD_W / 2 + FIT
    z0, z1 = rim_t, rim_t + BOARD_L + 2 * FIT
    return rim_t, hw, z0, z1


def base_height(val, **opts):
    return _pocket(val)[3] + RIM_H


def parts(val, **opts):
    rim_t, hw, z0, z1 = _pocket(val)
    y0, y1 = mount.Y_MOUNT, mount.Y_MOUNT + RIM_H
    floor = box(-hw - rim_t, hw + rim_t, mount.Y_PLATE, y0, 0, z1 + RIM_H)
    sides = [box(x0, x0 + rim_t, y0 - 0.01, y1, 0, z1 + RIM_H) for x0 in (-hw - rim_t, hw)]
    bottom = box(-hw, hw, y0 - 0.01, y1, 0, z0)
    # top lip with a 45 deg underside, so it prints without support
    pts = [V(-hw, y0 - 0.01, z1), V(-hw, y0 - 0.01, z1 + RIM_H), V(-hw, y1, z1 + RIM_H)]
    lip = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(2 * hw, 0, 0))
    return [("breadboard", fuse([mount.base(base_height(val)), floor, bottom, lip] + sides))]


def payload(val, **opts):
    _, hw, z0, _ = _pocket(val)
    board = box(-BOARD_W / 2, BOARD_W / 2, mount.Y_MOUNT, mount.Y_MOUNT + BOARD_H,
                z0 + FIT, z0 + FIT + BOARD_L)
    return [("breadboard", board, GRAMS)]
