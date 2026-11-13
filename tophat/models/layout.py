"""Place components on the cage rails and check that they all fit.

LAYOUT lists what goes where: (component in mounts/, rail t in degrees,
rack step, options). Step 0 is the lowest slider seat; each step is 2.4 mm
up the rail. Builds build/Layout.FCStd (crown, cage, head, sliders,
components and their items) and checks:
  - each component's sliders stay on its rail
  - components, sliders and items stay clear of the crown, the cage, each
    other and the head (HeadKeepOut: the head dome raised by HeadGap)
then prints the weight on the rails and where its centre of mass sits.
"""
import importlib
import sys
from pathlib import Path
import FreeCAD as App
from FreeCAD import Vector as V

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
from common import check

LAYOUT = [
    ("breadboard", 60, 20, {}),
    ("sled", 300, 6, dict(w=60, l=90, item=(45, 70, 12, 40))),
]

hat = common.open_model("TopHat")
cage = common.open_model("CageFingers")
val = common.reader(hat.Params)
frames = mount.rail_frames(cage)
fixed = [("Crown", hat.Crown.Shape), ("CageFingers", cage.CageFingers.Shape),
         ("HeadKeepOut", cage.HeadKeepOut.Shape)]

items = []  # (label, shape, grams, colour)
for name, t, step, opts in LAYOUT:
    mod = mount.load(name)
    frame, length, _ = frames[t]
    h = mod.base_height(val, **opts)
    top = mount.max_step(length, h)
    tag = f"{name}@{t}"
    check(0 <= step <= top, f"{tag} step {step} on its rail (0..{top})")
    print(f"{tag}: step {step} of 0..{top}, {len(mount.slider_set(h))} slider(s)")
    for i, s in enumerate(mount.sliders(h)):
        sl = mount.to_hat(s, frame, step)
        items.append((f"{tag} {'slider' if i == 0 else 'guide'}", sl, common.grams(sl), (0.6, 0.6, 0.6)))
    for part, shape, *_ in mod.parts(val, **opts):
        p = mount.to_hat(shape, frame, step)
        items.append((f"{tag} {part}", p, common.grams(p), (0.2, 0.6, 0.3)))
    for label, shape, grams in mod.payload(val, **opts):
        items.append((f"{tag} {label}", mount.to_hat(shape, frame, step), grams, (0.9, 0.7, 0.2)))


def overlap(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume


for label, s, _, _ in items:
    for fname, f in fixed:
        v = overlap(s, f)
        check(v < 0.01, f"{label} clear of {fname} ({v:.2f} mm3)")
for i, (la, a, _, _) in enumerate(items):
    for lb, b, _, _ in items[i + 1:]:
        v = overlap(a, b)
        check(v < 0.01, f"{la} clear of {lb} ({v:.2f} mm3)")

grams = sum(g for _, _, g, _ in items)
com = V()
for _, s, g, _ in items:
    com += s.Solids[0].CenterOfMass * g  # transformed shapes lose the Solid type
com = com * (1 / grams) if grams else com
print(f"on the rails: {grams:.0f} g, centre of mass {com.x:.0f}, {com.y:.0f} mm off the axis "
      f"(x front, y side) at {com.z:.0f} mm")

doc = common.new_model("Layout")
for fname, s, colour, transparency in (("Crown", hat.Crown.Shape, (0.1, 0.1, 0.1), 85),
                                       ("CageFingers", cage.CageFingers.Shape, (0.2, 0.45, 0.75), 60),
                                       ("HeadDome", cage.HeadDome.Shape, (0.85, 0.7, 0.6), 75)):
    o = doc.addObject("Part::Feature", fname)
    o.Shape = s
    if App.GuiUp:
        o.ViewObject.ShapeColor, o.ViewObject.Transparency = colour, transparency
for label, s, _, colour in items:
    o = doc.addObject("Part::Feature", label.replace(" ", "_").replace("@", "_"))
    o.Label = label
    o.Shape = s
    if App.GuiUp:
        o.ViewObject.ShapeColor = colour
common.save_model(doc)
common.summary("layout")
