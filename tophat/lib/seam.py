"""Brim seam key for models/hat.py (PLA).

Seam frame: X = radial along the seam (X=0 at the hat axis), Y = across it,
Z up. The tongue belongs to the piece at Y < 0 and enters the piece at
Y > 0, whose socket is the tongue grown by KeyClr. Shapes are built in
Python when the calling script runs, not driven by spreadsheet expressions.

Printed corners bulge (and slicers park the perimeter seam on sharp
corners), which held the test seams open, so no key corner is sharp.
Set-backs at the seam ends (collar end, edge binding) and bed-edge chamfers
for brim pieces printed flat were tried and removed; the pieces print on
end.

The key is a dovetail whose root and head roundings (KeyRootR, KeyHeadR)
nearly meet, so each flank is an S of two exact arcs. Chosen from test
coupons over a plain rounded dovetail, a spline S-curve key and this key at
0.2 mm clearance, which printed loose: its curved flanks meet the seam at a
shallow angle, so pull-apart play is about 2.6 x the clearance. At KeyClr
0.1 mm the play is about 0.26 mm and the printed coupon held.
"""
import math
import Part
from FreeCAD import Vector as V


def _dirs(pts, i):
    """Unit vectors from corner i to its two neighbours."""
    u = pts[i - 1] - pts[i]
    v = pts[(i + 1) % len(pts)] - pts[i]
    u.normalize()
    v.normalize()
    return u, v


def rounded_wire(pts, radii):
    """Closed wire through pts (Vectors) with corner i rounded to radii[i].
    Raises ValueError when two roundings overlap along an edge."""
    n, edges, ends = len(pts), [], []
    for i in range(n):
        a, b = radii[i], radii[(i + 1) % n]
        used = sum(r / math.tan(math.acos(max(-1.0, min(1.0, u.dot(v)))) / 2)
                   for r, u, v in ((a, *_dirs(pts, i)), (b, *_dirs(pts, (i + 1) % n))) if r > 0)
        if used > (pts[(i + 1) % n] - pts[i]).Length + 1e-6:
            raise ValueError(f"key corner radii too big for edge {i}: need {used:.2f} mm, "
                             f"edge is {(pts[(i + 1) % n] - pts[i]).Length:.2f} mm")
    for i in range(n):
        p, r = pts[i], radii[i]
        if r <= 0:
            ends.append((p, p, None))
            continue
        u, v = _dirs(pts, i)
        half = math.acos(max(-1.0, min(1.0, u.dot(v)))) / 2
        bis = u + v
        bis.normalize()
        c = p + bis * (r / math.sin(half))
        t1, t2 = p + u * (r / math.tan(half)), p + v * (r / math.tan(half))
        ends.append((t1, t2, Part.Arc(t1, c - bis * r, t2).toShape()))
    for i in range(n):
        t1, t2, arc = ends[i]
        if arc:
            edges.append(arc)
        nxt = ends[(i + 1) % n][0]
        if (nxt - t2).Length > 1e-6:
            edges.append(Part.makeLine(t2, nxt))
    return Part.Wire(edges)


def key_outline(p, mid, grow):
    """Tongue (grow 0) or socket (grow KeyClr) outline at z=0, with a strip
    reaching back into the owner piece."""
    nk = p["KeyNeck"] / 2 + grow
    hk = p["KeyHead"] / 2 + grow
    d = p["KeyDepth"] + grow
    w = p["KeyHead"] / 2 + 4
    pts = [V(mid - w, -2, 0), V(mid + w, -2, 0), V(mid + w, 0, 0), V(mid + nk, 0, 0),
           V(mid + hk, d, 0), V(mid - hk, d, 0), V(mid - nk, 0, 0), V(mid - w, 0, 0)]
    # head corners convex; root corners concave. The socket rounds both by
    # r + KeyClr: at the root the seam face itself is not offset, so a larger
    # radius is what keeps the socket clear of the tongue.
    r_root, r_head = p["KeyRootR"] + grow, p["KeyHeadR"] + grow
    return rounded_wire(pts, [0, 0, 0, r_root, r_head, r_head, r_root, 0])


def seam_tools(p, r_in, r_out):
    """Tongue solid and socket tool, in the seam frame, for a seam from the
    head opening (r_in) to the brim edge (r_out)."""
    mid = (r_in + p["CollarT"] + r_out) / 2
    z_top = V(0, 0, p["Curl"] + p["BrimT"] + 3)
    prism = lambda grow: Part.Face(key_outline(p, mid, grow)).extrude(z_top).translated(V(0, 0, -1))
    return prism(0), prism(p["KeyClr"])


PARAMS = ("KeyNeck", "KeyHead", "KeyDepth", "KeyRootR", "KeyHeadR", "KeyClr",
          "CollarT", "BrimT", "Curl")


def params(val):
    """The Params values this module reads, via the caller's val(name)."""
    return {n: val(n) for n in PARAMS}
