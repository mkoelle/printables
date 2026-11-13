"""Export print-ready STLs of the hat from build/TopHat.FCStd.

Each part is placed for the printer in Params (Bed, BedH): lowest point at
z=0, centred on the origin. Crown is flipped (top on bed) and turned 45 deg
so its long oval fits the bed diagonal; each brim segment stands on end on
its socket seam face (use a slicer plate brim, and slicer supports under the
curl). Writes to stl/parts/.
"""
import importlib
import sys
from pathlib import Path
from FreeCAD import Vector as V

LIB = str(Path(__file__).resolve().parents[1] / "lib")
if LIB in sys.path:
    sys.path.remove(LIB)
sys.path.insert(0, LIB)  # first, so these modules win over other projects'
import common
importlib.reload(common)
from common import FLIP, STL_PARTS, place, size, turn, write_stl

doc = common.open_model("TopHat")
BED, BED_H = doc.Params.Bed.Value, doc.Params.BedH.Value
SEGS = int(doc.Params.BrimSegs)

# brim piece q spans (q-1)*360/SEGS to q*360/SEGS deg; its socket seam is the
# first: turn that seam plane onto XZ, then stand the piece on it
jobs = [("Crown", (FLIP, turn(45)))] + \
       [(f"BrimQ{q}", (turn(-(q - 1) * 360 / SEGS), (V(1, 0, 0), 90))) for q in range(1, SEGS + 1)]
for name, turns in jobs:
    s = place(doc.getObject(name).Shape, *turns)
    path = STL_PARTS / f"tophat_{name.lower()}.stl"
    bb = write_stl(s, path, name, BED, BED_H)
    print(f"{name}: {size(bb)} -> {path.relative_to(common.PROJECT)}")
common.summary("export")
