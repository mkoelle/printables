"""Mounting rail system shared by the cage and the test coupons (PLA).

Vertical T-rail with a V-tooth rack; sliders wrap the T and hold position
with a flexible detent tongue (push to step, lift the top tab to release).

Rail local frame: X across the rail, Y toward the slider (away from the
backing), Z along the rail. Backing occupies y in [-BASE_T, 0].
"""
import Part
from FreeCAD import Vector as V

CLR = 0.2         # slider-to-rail clearance; tune for your printer
STEM_W = 4.0      # T stem width
STEM_H = 2.5      # stem height (gap behind flange for slider lips)
FLANGE_W = 10.0   # T flange width
FLANGE_T = 2.0    # T flange thickness
PITCH = 2.4       # rack tooth pitch (height step per detent)
DEPTH = PITCH / 2 # rack tooth depth (45 deg flanks, print without support)
RACK_W = 4.0      # rack band width (centre of flange)
BASE_T = 3.0      # backing plate thickness behind the rail
BASE_W = 16.0     # backing plate width

SLIDER_L = 24.0   # slider length along rail
SIDE = 2.0        # slider side wall thickness
FRONT = 2.4       # slider front plate thickness
TONGUE_W = RACK_W # detent tongue width
SLOT = 1.0        # slot width freeing the tongue
ROOT = 2.0        # tongue root height above slider bottom
TAB_EXT = 5.0     # tongue extension above slider top (release tab)
TAB_LIP = 3.0     # tab lip height for fingernail
# Tongue thicknesses to test. PLA flexure strain stays under ~1%
# (strain = 3 * t * deflection / (2 * length^2), deflection = DEPTH + CLR).
TONGUES = [1.0, 1.2, 1.4]

Y_FACE = STEM_H + FLANGE_T  # flange front face (rack base)
DEPTH_TOTAL = Y_FACE + DEPTH  # rail protrusion from backing face


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def fuse(shapes):
    """Fuse in one boolean (chained pairwise fuses can yield invalid solids)."""
    s = shapes[0].fuse(shapes[1:]) if len(shapes) > 1 else shapes[0]
    return s.removeSplitter()


def tooth(y_face, z_mid, sign, width):
    """Triangular V tooth: base on plane y=y_face, apex DEPTH away in sign*y."""
    pts = [V(-width / 2, y_face, z_mid - PITCH / 2),
           V(-width / 2, y_face + sign * DEPTH, z_mid),
           V(-width / 2, y_face, z_mid + PITCH / 2)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(width, 0, 0))


def rail(length, backing=True):
    """Rail from z=0 to z=length, rack teeth starting half a pitch up."""
    parts = [box(-STEM_W / 2, STEM_W / 2, -0.01, STEM_H, 0, length),
             box(-FLANGE_W / 2, FLANGE_W / 2, STEM_H, Y_FACE, 0, length)]
    if backing:
        parts.append(box(-BASE_W / 2, BASE_W / 2, -BASE_T, 0, 0, length))
    n = int(length / PITCH)
    parts += [tooth(Y_FACE, PITCH / 2 + i * PITCH, +1, RACK_W) for i in range(n)]
    return fuse(parts)


def slider(tongue_t, mark=0):
    """Slider at z=0..SLIDER_L, sitting on a rail whose backing face is y=0."""
    x_out = FLANGE_W / 2 + CLR + SIDE
    y_back, y_in = CLR, Y_FACE + DEPTH + CLR
    y_out = y_in + FRONT
    body = box(-x_out, x_out, y_back, y_out, 0, SLIDER_L)
    body = body.cut(box(-STEM_W / 2 - CLR, STEM_W / 2 + CLR, y_back - 1, STEM_H, -1, SLIDER_L + 1))
    body = body.cut(box(-FLANGE_W / 2 - CLR, FLANGE_W / 2 + CLR, STEM_H - CLR, Y_FACE + CLR, -1, SLIDER_L + 1))
    body = body.cut(box(-RACK_W / 2 - CLR, RACK_W / 2 + CLR, Y_FACE, y_in, -1, SLIDER_L + 1))
    # free the tongue: side slots open at the top, thin it to tongue_t
    hw = TONGUE_W / 2
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hw, sx * (hw + SLOT)))
        body = body.cut(box(x0, x1, y_in - 1, y_out + 1, ROOT, SLIDER_L + 1))
    body = body.cut(box(-hw, hw, y_in + tongue_t, y_out + 1, ROOT, SLIDER_L + 1))
    # tab: tongue continues above the slider and ends in an outward lip
    ext = box(-hw, hw, y_in, y_in + tongue_t, SLIDER_L - 0.01, SLIDER_L + TAB_EXT)
    lip = box(-hw, hw, y_in, y_in + tongue_t + TAB_LIP, SLIDER_L + TAB_EXT - 1.5, SLIDER_L + TAB_EXT)
    det = tooth(y_in, SLIDER_L - PITCH, -1, TONGUE_W)
    body = fuse([body, ext, lip, det])
    # identification notches on the right side wall
    for i in range(mark):
        body = body.cut(Part.makeCylinder(0.6, 2, V(x_out - 0.6, y_out - 1, 4 + i * 3), V(1, 0, 0)))
    return body


def seat_offset():
    """Slider z offset (from rail z=0) that seats its detent in a rack valley."""
    k = int((SLIDER_L - PITCH) / PITCH) + 2
    return k * PITCH - (SLIDER_L - PITCH)
