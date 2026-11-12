"""Export print-ready STLs from the open TopHat document.

Each part is placed for the printer in Params (Bed, BedH): lowest point at
z=0, centred on the origin. Crown is flipped (top on bed) and turned 45 deg
so its long oval fits the bed diagonal; each brim segment stands on end on
its socket seam face (use a slicer plate brim, and slicer supports under the
curl). Writes to <document folder>/stl/.
"""
import importlib
import os
import sys
import FreeCAD as App
from FreeCAD import Vector as V

sys.path.insert(0, os.path.expanduser("~/src/github.com/mkoelle/printables/tophat"))
import common
importlib.reload(common)
from common import FLIP, place, size, turn, write_stl

doc = App.getDocument("TopHat")
out = os.path.join(os.path.dirname(doc.FileName), "stl")
os.makedirs(out, exist_ok=True)
BED, BED_H = doc.Params.Bed.Value, doc.Params.BedH.Value
SEGS = int(doc.Params.BrimSegs)

# brim piece q spans (q-1)*360/SEGS to q*360/SEGS deg; its socket seam is the
# first: turn that seam plane onto XZ, then stand the piece on it
jobs = [("Crown", (FLIP, turn(45)))] + \
       [(f"BrimQ{q}", (turn(-(q - 1) * 360 / SEGS), (V(1, 0, 0), 90))) for q in range(1, SEGS + 1)]
for name, turns in jobs:
    s = place(doc.getObject(name).Shape, *turns)
    path = os.path.join(out, f"tophat_{name.lower()}.stl")
    bb = write_stl(s, path, name, BED, BED_H)
    print(f"{name}: {size(bb)} -> {path}")
common.summary("export_stl")
