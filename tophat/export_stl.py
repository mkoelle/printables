"""Export print-ready STLs from the open TopHat document.

Each part is placed for a square bed (BED): lowest point at z=0,
centred on the origin. Crown is flipped (top on bed); crown and hatband are
turned 45 deg so their long oval fits the bed diagonal.
Writes to <document folder>/stl/.
"""
import os
import FreeCAD as App
import MeshPart

doc = App.getDocument("TopHat")
out = os.path.join(os.path.dirname(doc.FileName), "stl")
os.makedirs(out, exist_ok=True)
BED = 220.0  # printer bed size, mm (square)

def place(shape, flip=False, turn=0):
    s = shape.copy()
    if flip:
        s.rotate(App.Vector(), App.Vector(1, 0, 0), 180)
    if turn:
        s.rotate(App.Vector(), App.Vector(0, 0, 1), turn)
    bb = s.optimalBoundingBox()
    s.translate(App.Vector(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    return s

jobs = [("Crown", True, 45), ("Hatband", False, 45)] + \
       [(f"BrimQ{q}", False, 0) for q in range(1, 5)]
for name, flip, turn in jobs:
    s = place(doc.getObject(name).Shape, flip, turn)
    mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05,
                                  AngularDeflection=0.1, Relative=False)
    path = os.path.join(out, f"tophat_{name.lower()}.stl")
    mesh.write(path)
    bb = s.optimalBoundingBox()
    fits = bb.XLength <= BED and bb.YLength <= BED
    print(f"{name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm "
          f"fits={fits} -> {path}")
