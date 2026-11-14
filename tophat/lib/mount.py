"""Mounting interface between the cage's rail sliders and the components in
mounts/ (PLA).

Each component stands on one rail: a locking slider at its bottom, whose
tab hangs below the component, and on taller components a guide slider (no
tongue) at the top that stops it rocking. The base has a shoe for each: a
plate in front of the slider, clear of the detent tongue, with two cheeks
whose ridges snap into the V grooves along the slider sides
(rail.GROOVE_Y). Push a component straight onto its sliders to fit it,
pull it off to remove it. To move it, pull the tab under it and slide.

Mount frame: the slider's rail-local frame (rail.py). X across the rail,
Y inward toward the hat axis (y=0 at the rail backing face), Z up the rail,
z=0 at the bottom of the locking slider. Components build from the mount face
y=Y_MOUNT inward. Rail mounts print standing on their z=0 end, so keep their
geometry at z >= 0 and overhangs at 45 deg or steeper.

A component is a module in mounts/ with:
  PURPOSE                  one line for the catalogue
  VARIANTS                 optional: option dicts, one printed part each
  base_height(val, **opts) height of its base, mount.base(h): sets whether
                           it gets a guide slider (GUIDE_MIN)
  parts(val, **opts)       [(part name, shape, *print turns)], mount frame
  payload(val, **opts)     [(label, envelope shape, grams)]: what it holds,
                           for the clearance, weight and balance checks
val reads TopHat's Params; opts come from VARIANTS or the layout entry.
"""
import importlib.util
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part
from FreeCAD import Vector as V

import rail
from common import PROJECT, box, fuse

MOUNTS = PROJECT / "mounts"

GAP = 1.8         # slider front to shoe plate: room for the tongue to flex (DEPTH + CLR = 1.4)
PLATE_T = 2.0     # shoe plate thickness
CHEEK_T = 1.2     # cheek thickness (3 perimeters)
CHEEK_CLR = 0.1   # cheek to slider side
RIDGE = 0.4       # ridge depth; the cheek flexes RIDGE + CHEEK_CLR to snap on
TIP = 1.2         # cheek length past the ridge
GUIDE_MIN = 36.0  # bases this tall or taller get a guide slider at the top
CUT_GAP = 2.0     # full cheek kept past each slider end
CUT_KEEP = 1.2    # cheek strip kept along the plate between the sliders

X_CHEEK = rail.X_OUT + CHEEK_CLR
HALF_W = X_CHEEK + CHEEK_T         # shoe half-width
Y_PLATE = rail.Y_OUT + GAP         # shoe plate back face
Y_MOUNT = Y_PLATE + PLATE_T        # mount face: components build from here
Y_TIP = rail.GROOVE_Y - RIDGE - TIP


def slider_set(h):
    """[(z, locking)] of the sliders under a base of height h."""
    assert h >= rail.SLIDER_L, f"base {h} mm is shorter than a slider"
    guide = [(h - rail.SLIDER_L, False)] if h >= GUIDE_MIN else []
    return [(0.0, True)] + guide


def sliders(h):
    """Slider shapes under a base of height h, in the mount frame."""
    return [(rail.slider() if lock else rail.guide()).translated(V(0, 0, z))
            for z, lock in slider_set(h)]


def _ridge(sx, z0, z1):
    gy = rail.GROOVE_Y
    pts = [V(sx * (X_CHEEK + 0.01), gy - RIDGE, z0), V(sx * (X_CHEEK - RIDGE), gy, z0),
           V(sx * (X_CHEEK + 0.01), gy + RIDGE, z0)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


def base(h=rail.SLIDER_L, upside_down=False):
    """Plate and cheeks from z=0 to h (at least one slider long), with snap
    ridges over each slider (slider_set). upside_down: for a part printed top
    down, the cheek cut's 45 deg edge goes at its bottom."""
    parts = [box(-HALF_W, HALF_W, Y_PLATE, Y_MOUNT, 0, h)]
    zs = slider_set(h)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * X_CHEEK, sx * HALF_W))
        cheek = box(x0, x1, Y_TIP, Y_PLATE + 0.01, 0, h)
        if len(zs) > 1:
            # cut the cheek back to a strip between the sliders, so only the
            # ridge zones flex; the cut's top edge rises at 45 deg
            za, zb = rail.SLIDER_L + CUT_GAP, zs[1][0] - CUT_GAP
            ys = Y_PLATE - CUT_KEEP
            rise = ys - Y_TIP + 1
            if zb - rise > za:
                if upside_down:
                    pts = [V(x0 - 1, Y_TIP - 1, za), V(x0 - 1, ys, za + rise), V(x0 - 1, ys, zb),
                           V(x0 - 1, Y_TIP - 1, zb)]
                else:
                    pts = [V(x0 - 1, Y_TIP - 1, za), V(x0 - 1, ys, za), V(x0 - 1, ys, zb - rise),
                           V(x0 - 1, Y_TIP - 1, zb)]
                cheek = cheek.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(x1 - x0 + 2, 0, 0)))
        parts.append(cheek)
        parts += [_ridge(sx, z, z + rail.SLIDER_L) for z, _ in slider_set(h)]
    return fuse(parts)


def lattice(x_out, z0, z1, thick, cell=8.0, rib=1.6):
    """Cutter for a staggered diamond lattice in a plate behind the mount
    face (y from Y_PLATE, `thick` deep), either side of the base: from
    HALF_W + rib out to x_out, z0 to z1. 45 deg ribs `rib` wide on a `cell`
    pitch print without support and keep the plate stiff; leave solid
    borders by choosing x_out, z0 and z1 inside them."""
    d = (cell - rib * math.sqrt(2)) / 2       # diamond half-diagonal
    cuts = []
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (HALF_W + rib), sx * x_out))
        if x1 - x0 < 2 * d or z1 - z0 < 2 * d:
            continue
        nx = int((x1 - x0 - 2 * d) // (cell / 2))
        xa = (x0 + x1) / 2 - nx * cell / 4    # centre the columns
        for i in range(nx + 1):
            for j in range(int((z1 - z0 - 2 * d) // (cell / 2)) + 1):
                if (i + j) % 2:
                    continue
                xc, zc = xa + i * cell / 2, z0 + d + j * cell / 2
                pts = [V(xc - d, Y_PLATE - 1, zc), V(xc, Y_PLATE - 1, zc - d),
                       V(xc + d, Y_PLATE - 1, zc), V(xc, Y_PLATE - 1, zc + d)]
                cuts.append(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, thick + 2, 0)))
    return Part.makeCompound(cuts)


def slider_z(step):
    """Rail-local z of a slider seated `step` rack steps above the first seat."""
    return rail.seat_offset() + step * rail.PITCH


def max_step(length, h):
    """Highest step for a base of height h on a rail of this length, keeping
    every slider on the rail."""
    return int((length - rail.seat_offset() - h) // rail.PITCH)


# --- Rails in the hat ---------------------------------------------------------
def rail_frames(cage_doc):
    """{t: (matrix, length, z_start)} from the Rails sheet cage.py saves."""
    sheet, frames, row = cage_doc.getObject("Rails"), {}, 2
    while sheet.getContents(f"A{row}"):
        v = [float(sheet.get(f"{chr(65 + k)}{row}")) for k in range(15)]
        frames[round(v[0])] = (App.Matrix(*v[3:], 0, 0, 0, 1), v[1], v[2])
        row += 1
    return frames


def mount_matrix(frame, step):
    """Mount frame to hat coordinates, for a mount at `step` on a rail."""
    local = App.Matrix()
    local.move(V(0, rail.BASE_T / 2, slider_z(step)))  # as cage.py places the rail
    return App.Matrix(frame).multiply(local)


def to_hat(shape, frame, step):
    """Copy of a mount-frame shape placed on a rail frame at `step`."""
    return shape.transformGeometry(mount_matrix(frame, step))


# --- Catalogue ------------------------------------------------------------------
def catalogue():
    """Component names: the modules in mounts/."""
    return sorted(p.stem for p in MOUNTS.glob("*.py") if not p.stem.startswith("_"))


def load(name):
    """The mounts/<name>.py module, freshly loaded."""
    path = MOUNTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"tophat_mount_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.NAME = name
    return mod
