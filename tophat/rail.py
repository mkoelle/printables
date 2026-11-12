"""Mounting rail system shared by the cage and the test coupons (PLA).

Vertical dovetail rail (45 deg flanks) with a V-tooth rack; sliders wrap
the dovetail and hold position with a flexible detent tongue (push to step,
pull the top tab to release). Chosen over a T-rail after test prints: the
slider lips print without flat overhangs and the slider self-centres.

Sliders print front-down: the tongue lies on the bed (bending runs along
the layer lines) and the detent tooth stands on a post, apex up. Front
edges carry an elephant-foot chamfer; channel mouths have a lead-in.

Rail local frame: X across the rail, Y toward the slider (away from the
backing), Z along the rail. Backing occupies y in [-BASE_T, 0].
"""
import Part
from FreeCAD import Vector as V
from common import box, fuse

CLR = 0.2         # rack, backing and dovetail-face clearance (sets detent engagement)
T_CLR = 0.4       # flange side and flange-front clearance (slide-on fit)
STEM_W = 4.0      # dovetail width at the backing
STEM_H = 2.5      # sets Y_FACE with FLANGE_T
FLANGE_W = 10.0   # dovetail width at the front
FLANGE_T = 2.0    # flange front depth; Y_FACE = STEM_H + FLANGE_T
PITCH = 2.4       # rack tooth pitch (height step per detent)
DEPTH = PITCH / 2 # rack tooth depth (45 deg flanks, print without support)
RACK_W = 4.0      # rack band width (centre of flange)
BASE_T = 3.0      # backing plate thickness behind the rail
BASE_W = 16.0     # backing plate width

SLIDER_L = 12.0   # slider length along rail (half-length won the round-3 prints)
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
# Detent tongue thickness, chosen from the round-3 test prints: the 12 mm
# slider with the 1.4 mm tongue (sample 3) held best. By the beam estimate,
# strain = 3 * t * deflection / (2 * length^2) with deflection = DEPTH + CLR,
# this short tongue reaches about 2.3% at a click, above the ~1% PLA
# guideline, yet it did not crack in testing. The root taper moves the peak strain off
# the slot corners where the first prints snapped.
TONGUE_T = 1.4

Y_FACE = STEM_H + FLANGE_T  # flange front face (rack base)


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


def rail(length):
    """Rail on its backing from z=0 to z=length, rack teeth starting half a pitch up."""
    parts = [dovetail_profile(length), box(-BASE_W / 2, BASE_W / 2, -BASE_T, 0, 0, length)]
    n = int(length / PITCH)
    parts += [tooth(Y_FACE, PITCH / 2 + i * PITCH, +1, RACK_W) for i in range(n)]
    return fuse(parts)


def channel(y_back, y_in):
    """Right half of the slider's rail channel (dovetail, flange, rack band)."""
    rw, fw, sw = RACK_W / 2 + CLR, FLANGE_W / 2 + T_CLR, STEM_W / 2
    front = [V(fw, Y_FACE + T_CLR, 0), V(rw, Y_FACE + T_CLR, 0), V(rw, y_in, 0)]
    # lip face sits CLR behind the rail's 45 deg face (x = sw + y)
    back = [V(sw + y_back - 1 + CLR, y_back - 1, 0), V(fw, fw - sw - CLR, 0)]
    return back + front


def slider():
    """Slider at z=0..SLIDER_L, sitting on a rail whose backing face is y=0."""
    length, tongue_t = SLIDER_L, TONGUE_T
    x_out = FLANGE_W / 2 + T_CLR + SIDE
    y_back, y_in = CLR, Y_FACE + DEPTH + CLR
    y_out = y_in + FRONT
    body = box(-x_out, x_out, y_back, y_out, 0, length)
    half = channel(y_back, y_in)
    body = body.cut(prism(half, length + 2).translated(V(0, 0, -1)))
    # lead-in at both channel mouths
    w = Part.makePolygon(half + [V(-p.x, p.y, 0) for p in reversed(half)] + [half[0]])
    big = w.makeOffset2D(LEAD, 2)
    for z, sz in ((0, 1), (length, -1)):
        mouth = Part.makeLoft([big.translated(V(0, 0, z - sz * 0.01)),
                               w.translated(V(0, 0, z + sz * LEAD))], True, True)
        body = body.cut(mouth)
    # elephant-foot chamfer on the front (bed) edges
    for sx in (-1, 1):
        pts = [V(sx * (x_out - EF), y_out, -1), V(sx * (x_out + 1), y_out, -1),
               V(sx * (x_out + 1), y_out - EF - 1, -1)]
        body = body.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, length + 2)))
    pts = [V(-x_out - 1, y_out - EF, 0), V(-x_out - 1, y_out + 1, 0), V(-x_out - 1, y_out + 1, EF + 1)]
    body = body.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(2 * x_out + 2, 0, 0)))
    # free the tongue: side slots open at the top with round ends at the root
    hw = TONGUE_W / 2
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hw, sx * (hw + SLOT)))
        body = body.cut(box(x0, x1, y_in - 1, y_out + 1, ROOT + SLOT / 2, length + 1))
        body = body.cut(Part.makeCylinder(SLOT / 2, FRONT + 2, V((x0 + x1) / 2, y_in - 1, ROOT + SLOT / 2),
                                          V(0, 1, 0)))
    # tongue flush with the front face: cut behind it, 45 deg off the full
    # plate, then taper from tongue_t + ROOT_T down to tongue_t
    t_root = min(tongue_t + ROOT_T, FRONT)
    y_root = y_out - t_root
    pts = [V(-hw, y_in - 1, ROOT), V(-hw, y_in, ROOT), V(-hw, y_root, ROOT + y_root - y_in),
           V(-hw, y_out - tongue_t, ROOT + TAPER_L), V(-hw, y_out - tongue_t, length + 1),
           V(-hw, y_in - 1, length + 1)]
    body = body.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(2 * hw, 0, 0)))
    # detent tooth on a post reaching back from the tongue to the rack
    z_det = length - PITCH
    post = box(-hw, hw, y_in, y_out - tongue_t + 0.01, z_det - PITCH / 2, z_det + PITCH / 2)
    det = tooth(y_in, z_det, -1, TONGUE_W)
    # tab: tongue continues above the slider and ends in a pinch handle
    tw = x_out + TAB_WING
    ext = box(-hw, hw, y_out - tongue_t, y_out, length - 0.01, length + TAB_EXT)
    grip = box(-tw, tw, y_in, y_out, length + TAB_EXT - TAB_H, length + TAB_EXT)
    return fuse([body, post, det, ext, grip])


def seat_offset():
    """Slider z offset (from rail z=0) that seats its detent in a rack valley."""
    k = int((SLIDER_L - PITCH) / PITCH) + 2
    return k * PITCH - (SLIDER_L - PITCH)
