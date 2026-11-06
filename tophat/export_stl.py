"""Export print-ready STLs from the open TopHat document.

Each part is placed for the square bed in Params.Bed: lowest point at z=0,
centred on the origin. Crown is flipped (top on bed); crown and hatband are
turned 45 deg so their long oval fits the bed diagonal; each brim segment is
turned to its smallest footprint and written with its breakaway curl fins
(BrimQ<n>Support) in the same STL.
Writes to <document folder>/stl/. The hatband is a visual reference for a
fabric band, so it is only exported when EXPORT_HATBAND is set to True
before running this script.
"""
import importlib
import os
import sys
import FreeCAD as App
import MeshPart
import Part

sys.path.insert(0, os.path.expanduser("~/src/github.com/mkoelle/printables/tophat"))
import common
importlib.reload(common)
EXPORT_HATBAND = globals().pop("EXPORT_HATBAND", False)

doc = App.getDocument("TopHat")
out = os.path.join(os.path.dirname(doc.FileName), "stl")
os.makedirs(out, exist_ok=True)
BED = doc.Params.Bed.Value  # printer bed size, mm (square)
SEGS = int(doc.Params.BrimSegs)

def place(shape, flip=False, turn=0):
    s = shape.copy()
    if flip:
        s.rotate(App.Vector(), App.Vector(1, 0, 0), 180)
    if turn:
        s.rotate(App.Vector(), App.Vector(0, 0, 1), turn)
    bb = s.optimalBoundingBox()
    s.translate(App.Vector(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    return s



def best_turn(shape):
    """Turn (deg) giving the smallest square footprint. Uses
    optimalBoundingBox: the loose BoundBox misjudges the curled segments."""
    def side(t):
        bb = place(shape, turn=t).optimalBoundingBox()
        return max(bb.XLength, bb.YLength)
    return min(range(0, 180, 2), key=side)


jobs = [("Crown", True, 45)] + ([("Hatband", False, 45)] if EXPORT_HATBAND else []) + \
       [(f"BrimQ{q}", False, best_turn(doc.getObject(f"BrimQ{q}").Shape)) for q in range(1, SEGS + 1)]
for name, flip, turn in jobs:
    shape = doc.getObject(name).Shape
    sup = doc.getObject(f"{name}Support")
    if sup and sup.Shape.Solids:  # breakaway fins print with the piece
        shape = Part.makeCompound([shape, sup.Shape])
    s = place(shape, flip, turn)
    mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05,
                                  AngularDeflection=0.1, Relative=False)
    path = os.path.join(out, f"tophat_{name.lower()}.stl")
    mesh.write(path)
    bb = s.optimalBoundingBox()
    fits = bb.XLength <= BED and bb.YLength <= BED
    common.check(fits, f"{name} fits the bed")
    print(f"{name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm "
          f"fits={fits} -> {path}")
common.summary("export_stl")
