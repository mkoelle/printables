"""Bottle holder: a C ring at the top of the mount that a bottle cap snaps
into from the side. The cap's wider lip rests on the ring and the bottle
hangs below, clear of the plate.

The ring top is level with the top of the base, so at the top of a rail the
lip sits just under the crown top: the rails end 8 mm below it (LipH + 2),
about one lip height. Set h (base height) in the layout to bring the lip
flush; the layout's crown check catches a lip that would press into it.

Default sizes: cap 23 mm across and 15 mm tall, lip 25 mm across and 8 mm
tall, bottle about 33 mm across. Prints upside down on its flat top, so the
ring, arm and plate grow straight up from the bed.
"""
import Part
from FreeCAD import Vector as V

import mount
from common import FLIP, box, fuse

PURPOSE = "C ring that holds a bottle by its cap, lip up against the crown top"

FIT = 0.2       # ring bore clearance round the cap
WALL = 2.4      # ring wall (6 lines)
RING_H = 10.0   # ring height (shorter than the cap)
MOUTH = 0.85    # ring opening as a share of the cap diameter (snap-in)
BOTTLE_CLR = 1.5  # bottle to mount face
DEFAULTS = dict(h=38.4, cap_d=23.0, cap_h=15.0, lip_d=25.0, lip_h=8.0,
                bottle_d=33.0, bottle_l=60.0, grams=60.0)


def _opts(opts):
    return {**DEFAULTS, **{k: v for k, v in opts.items() if k in DEFAULTS}}


def _centre(o):
    """Ring centre y: the bottle below hangs BOTTLE_CLR clear of the mount face."""
    return mount.Y_MOUNT + o["bottle_d"] / 2 + BOTTLE_CLR


def base_height(val, **opts):
    return _opts(opts)["h"]


def parts(val, **opts):
    o = _opts(opts)
    h, yc = o["h"], _centre(o)
    r_in = o["cap_d"] / 2 + FIT
    r_out = r_in + WALL
    z0 = h - RING_H
    ring = Part.makeCylinder(r_out, RING_H, V(0, yc, z0))
    arm = box(-r_out, r_out, mount.Y_PLATE, yc, z0, h)
    holder = fuse([ring, arm]).cut(Part.makeCylinder(r_in, RING_H + 2, V(0, yc, z0 - 1)))
    mouth = MOUTH * o["cap_d"] / 2
    holder = holder.cut(box(-mouth, mouth, yc, yc + r_out + 1, z0 - 1, h + 1))
    return [("bottle", fuse([mount.base(h, upside_down=True), holder]), FLIP)]


def payload(val, **opts):
    o = _opts(opts)
    h, yc = o["h"], _centre(o)
    lip = Part.makeCylinder(o["lip_d"] / 2, o["lip_h"], V(0, yc, h))
    cap = Part.makeCylinder(o["cap_d"] / 2, o["cap_h"], V(0, yc, h - o["cap_h"]))
    bottle = Part.makeCylinder(o["bottle_d"] / 2, o["bottle_l"],
                               V(0, yc, h - o["cap_h"] - o["bottle_l"]))
    return [("bottle", fuse([lip, cap, bottle]), o["grams"])]
