"""Mounting rail system shared by the cage and the test coupons (PLA).

Vertical T-rail with a V-tooth rack; sliders wrap the T and hold position
with a flexible detent tongue (push to step, pull the top tab to release).
dovetail=True swaps the T for a 45 deg dovetail so the slider lips print
without flat overhangs.

Sliders print front-down: the tongue lies on the bed (bending runs along
the layer lines) and the detent tooth stands on a post, apex up.

Rail local frame: X across the rail, Y toward the slider (away from the
backing), Z along the rail. Backing occupies y in [-BASE_T, 0].
"""
import Part
from FreeCAD import Vector as V

CLR = 0.2         # rack, backing and flange-back clearance (sets detent engagement)
T_CLR = 0.4       # T side and flange-front clearance (slide-on fit)
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
ROOT_T = 0.6      # extra tongue thickness at the root, tapering to tongue_t
TAPER_L = 6.0     # taper length; moves peak strain off the root corner
TAB_EXT = 3.0     # tongue extension above slider top (release tab)
TAB_H = 2.0       # pinch handle height at the tab end
TAB_WING = 2.0    # pinch handle overhang past each slider side
EF = 0.5          # elephant-foot chamfer on the bed (front) edges
LEAD = 0.6        # lead-in chamfer at the channel mouths
# Tongue thicknesses to test. PLA flexure strain stays under ~1%
# (strain = 3 * t * deflection / (2 * length^2), deflection = DEPTH + CLR).
# The root taper keeps the peak about the same but moves it to the taper end,
# away from the slot corners where the first prints snapped.
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


def dovetail_profile(length):
    """Dovetail stem+flange: 45 deg from STEM_W at the backing to FLANGE_W."""
    sw, fw = STEM_W / 2, FLANGE_W / 2
    half = [V(sw - 0.01, -0.01, 0), V(fw, fw - sw, 0), V(fw, Y_FACE, 0)]
    return prism(half, length)


def prism(half, length):
    """Extrude along z a polygon mirrored about x=0 (half: x>0 points, bottom up)."""
    pts = half + [V(-p.x, p.y, 0) for p in reversed(half)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, length))


def rail(length, backing=True, dovetail=False):
    """Rail from z=0 to z=length, rack teeth starting half a pitch up."""
    if dovetail:
        parts = [dovetail_profile(length)]
    else:
        parts = [box(-STEM_W / 2, STEM_W / 2, -0.01, STEM_H, 0, length),
                 box(-FLANGE_W / 2, FLANGE_W / 2, STEM_H, Y_FACE, 0, length)]
    if backing:
        parts.append(box(-BASE_W / 2, BASE_W / 2, -BASE_T, 0, 0, length))
    n = int(length / PITCH)
    parts += [tooth(Y_FACE, PITCH / 2 + i * PITCH, +1, RACK_W) for i in range(n)]
    return fuse(parts)


def channel(y_back, y_in, dovetail):
    """Right half of the slider's rail channel (stem, flange, rack band)."""
    rw, fw, sw = RACK_W / 2 + CLR, FLANGE_W / 2 + T_CLR, STEM_W / 2
    front = [V(fw, Y_FACE + T_CLR, 0), V(rw, Y_FACE + T_CLR, 0), V(rw, y_in, 0)]
    if dovetail:
        # lip face sits CLR behind the rail's 45 deg face (x = sw + y)
        back = [V(sw + y_back - 1 + CLR, y_back - 1, 0), V(fw, fw - sw - CLR, 0)]
    else:
        back = [V(sw + T_CLR, y_back - 1, 0), V(sw + T_CLR, STEM_H - CLR, 0),
                V(fw, STEM_H - CLR, 0)]
    return back + front


def slider(tongue_t, mark=0, dovetail=False, chamfer=False):
    """Slider at z=0..SLIDER_L, sitting on a rail whose backing face is y=0.

    chamfer adds the elephant-foot chamfer on the front (bed) edges and a
    lead-in at both channel mouths.
    """
    x_out = FLANGE_W / 2 + T_CLR + SIDE
    y_back, y_in = CLR, Y_FACE + DEPTH + CLR
    y_out = y_in + FRONT
    body = box(-x_out, x_out, y_back, y_out, 0, SLIDER_L)
    half = channel(y_back, y_in, dovetail)
    body = body.cut(prism(half, SLIDER_L + 2).translated(V(0, 0, -1)))
    if chamfer:
        w = Part.makePolygon(half + [V(-p.x, p.y, 0) for p in reversed(half)] + [half[0]])
        big = w.makeOffset2D(LEAD, 2)
        for z, sz in ((0, 1), (SLIDER_L, -1)):
            mouth = Part.makeLoft([big.translated(V(0, 0, z - sz * 0.01)),
                                   w.translated(V(0, 0, z + sz * LEAD))], True, True)
            body = body.cut(mouth)
        for sx in (-1, 1):  # long front edges
            pts = [V(sx * (x_out - EF), y_out, -1), V(sx * (x_out + 1), y_out, -1),
                   V(sx * (x_out + 1), y_out - EF - 1, -1)]
            body = body.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, SLIDER_L + 2)))
        pts = [V(-x_out - 1, y_out - EF, 0), V(-x_out - 1, y_out + 1, 0), V(-x_out - 1, y_out + 1, EF + 1)]
        body = body.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(2 * x_out + 2, 0, 0)))
    # free the tongue: side slots open at the top with round ends at the root
    hw = TONGUE_W / 2
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hw, sx * (hw + SLOT)))
        body = body.cut(box(x0, x1, y_in - 1, y_out + 1, ROOT + SLOT / 2, SLIDER_L + 1))
        body = body.cut(Part.makeCylinder(SLOT / 2, FRONT + 2, V((x0 + x1) / 2, y_in - 1, ROOT + SLOT / 2),
                                          V(0, 1, 0)))
    # tongue flush with the front face: cut behind it, 45 deg off the full
    # plate, then taper from tongue_t + ROOT_T down to tongue_t
    t_root = min(tongue_t + ROOT_T, FRONT)
    y_root = y_out - t_root
    pts = [V(-hw, y_in - 1, ROOT), V(-hw, y_in, ROOT), V(-hw, y_root, ROOT + y_root - y_in),
           V(-hw, y_out - tongue_t, ROOT + TAPER_L), V(-hw, y_out - tongue_t, SLIDER_L + 1),
           V(-hw, y_in - 1, SLIDER_L + 1)]
    body = body.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(2 * hw, 0, 0)))
    # detent tooth on a post reaching back from the tongue to the rack
    z_det = SLIDER_L - PITCH
    post = box(-hw, hw, y_in, y_out - tongue_t + 0.01, z_det - PITCH / 2, z_det + PITCH / 2)
    det = tooth(y_in, z_det, -1, TONGUE_W)
    # tab: tongue continues above the slider and ends in a pinch handle
    tw = x_out + TAB_WING
    ext = box(-hw, hw, y_out - tongue_t, y_out, SLIDER_L - 0.01, SLIDER_L + TAB_EXT)
    grip = box(-tw, tw, y_in, y_out, SLIDER_L + TAB_EXT - TAB_H, SLIDER_L + TAB_EXT)
    body = fuse([body, post, det, ext, grip])
    # identification notches on the right side wall
    for i in range(mark):
        body = body.cut(Part.makeCylinder(0.6, 2, V(x_out - 0.6, y_out - 1, 4 + i * 3), V(1, 0, 0)))
    return body


def seat_offset():
    """Slider z offset (from rail z=0) that seats its detent in a rack valley."""
    k = int((SLIDER_L - PITCH) / PITCH) + 2
    return k * PITCH - (SLIDER_L - PITCH)
