"""Build every component in mounts/ (one module each, see lib/mount.py):
build/Mounts.FCStd with the parts in a row, and stl/mounts/mount_<part>.stl
placed for printing. The model also shows the sliders each part snaps onto
(<part>_sliders, see-through); they print separately (stl/tests/). Each part must be a valid single solid that fits the
printer. Re-run after changing a mount, mount.py or rail.py.
"""
import importlib
import sys
from pathlib import Path
from FreeCAD import Vector as V
import FreeCAD as App

LIB = str(Path(__file__).resolve().parents[1] / "lib")
if LIB in sys.path:
    sys.path.remove(LIB)
sys.path.insert(0, LIB)  # first, so these modules win over other projects'
import common
import rail
importlib.reload(common)
importlib.reload(rail)
import mount  # after rail's reload: it reads rail when it loads
importlib.reload(mount)
from common import STL_MOUNTS, check, place, size, write_stl


def placed_like(shape, part, turns):
    """shape moved as place(part, *turns) moves part."""
    r, s = part.copy(), shape.copy()
    for axis, deg in turns:
        r.rotate(V(), axis, deg)
        s.rotate(V(), axis, deg)
    bb = r.optimalBoundingBox()
    s.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    return s


hat = common.open_model("TopHat")
val = common.reader(hat.Params)
BED, BED_H = val("Bed"), val("BedH")

doc = common.new_model("Mounts")
x = 0.0
for name in mount.catalogue():
    mod = mount.load(name)
    for opts in getattr(mod, "VARIANTS", [{}]):
        for part, shape, *turns in mod.parts(val, **opts):
            ok = shape.isValid() and len(shape.Solids) == 1
            check(ok, f"{part} valid single solid")
            s = place(shape, *turns)
            bb = write_stl(s, STL_MOUNTS / f"mount_{part}.stl", part, BED, BED_H, deflection=0.02)
            h = mod.base_height(val, **opts)
            ref = placed_like(common.fuse(mount.sliders(h)), shape, turns)
            for label, shp in ((part, s), (f"{part}_sliders", ref)):
                o = doc.addObject("Part::Feature", label)
                o.Shape = shp
                o.Placement = App.Placement(V(x + bb.XLength / 2, 0, 0), App.Rotation()).multiply(o.Placement)
                if App.GuiUp and label != part:
                    o.ViewObject.ShapeColor, o.ViewObject.Transparency = (0.6, 0.6, 0.6), 60
            x += bb.XLength + 15
            guide = len(mount.slider_set(h)) > 1
            print(f"{part}: valid {shape.isValid()} solids {len(shape.Solids)} {size(bb)} "
                  f"{common.grams(shape):.0f} g, {'lock + guide' if guide else 'lock'} slider - {mod.PURPOSE}")
common.save_model(doc)
common.summary("mounts")
