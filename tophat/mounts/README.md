# Rail components

Things that mount inside the hat on the cage's rail sliders. Each file here
is one component. `models/mounts.py` builds them all into
`build/Mounts.FCStd` and `stl/mounts/mount_<part>.stl`. `models/layout.py`
places them on the rails and checks that everything fits.

| Component | Part(s) | Purpose | Sliders | Status |
|-----------|---------|---------|---------|--------|
| `breadboard.py` | `breadboard_mini`, `breadboard_half` | Pocket for a breadboard, held by snap clips over its side edges (no glue), on a lattice floor. mini: 170 tie-points, 47 x 35 mm. half: 400 tie-points (half size), 84 x 55 mm, which also fits 82-83.5 x 54-55 mm boards. Board thickness 9.3 mm with adhesive foam; set `board_h` for others (8.5 mm bare) | lock + guide | half printed 2026-11-14, not yet tested; mini designed |
| `sled.py` | `sled_40x60`, `sled_60x90`, `sled_80x110` | Plate with a bottom ledge and rubber-band hooks on both sides; stand an item on the ledge and strap it on. Any size: add it to `VARIANTS` | lock, + guide from 36 mm long | 80x110 printed 2026-11-14, not yet tested |
| `bottle.py` | `bottle` | C ring a bottle cap snaps into from the side; the cap's lip rests on the ring, flush under the crown top, and the bottle hangs below. Defaults: cap 23 x 15 mm, lip 25 x 8 mm, bottle 33 mm across; sizes are layout options | lock + guide | 2 printed 2026-11-14, not yet tested |
| (`lib/rail.py`) | `slider`, `guide` | The sliders components stand on: one locking `slider` each, plus a `guide` for any 36 mm or taller (all current ones) | - | 4 of each printed 2026-11-14; grooves, bottom tab and guide not yet tested |

## How a component attaches

Every component stands on one rail, on the shoes in `lib/mount.py`:

- a **locking slider** at its bottom. Its tab hangs below the component, so
  you can pull it to release the detent and slide the component up or down
  without taking it off.
- on components 36 mm or taller (`GUIDE_MIN`), a **guide slider** at the
  top: the same body without tongue or tab. It slides freely and stops the
  component rocking on the rail.

Each shoe has a plate in front of the slider, clear of its detent tongue,
and two cheeks whose ridges snap into V grooves along the slider's sides.
Push the component straight onto its sliders to fit it; pull it off to
remove it. Between the two sliders the cheeks are cut back to a strip, so
only the ridge zones flex. Only the locking slider holds the position,
about 50 g.

Print the sliders from `stl/mounts/mount_slider.stl` and `mount_guide.stl`.
They are the same parts as `test_slider` and `test_guide` in `stl/tests/`.
Print those with the `mount_shoe` coupon and `test_rail` first (see
`TESTING.md`) and check the snap before printing components.

## Adding a component

Add `mounts/<name>.py`, using `breadboard.py` or `sled.py` as a template. It
defines:

- `PURPOSE`: one line for this table and the build output.
- `VARIANTS` (optional): a list of option dicts. Each one is exported as its
  own part.
- `base_height(val, **opts)`: height of its base (`mount.base(h)`), which
  decides whether it gets a guide slider. Keep the total under about 50 g:
  one locking slider holds it.
- `parts(val, **opts)`: `[(part name, shape, *print turns)]` in the mount
  frame (`lib/mount.py`). Build from the mount face `mount.Y_MOUNT`
  inward, starting from `mount.base(base_height(...))`. Mounts print standing on their
  bottom end, so keep geometry at z >= 0 and overhangs at 45 deg.
- `payload(val, **opts)`: `[(label, envelope shape, grams)]` for what it
  holds, used for the clearance, weight and balance checks.

Then add a row here and an entry to `LAYOUT` in `models/layout.py`, and run
`mise run layout`.

## Where things fit

- **Height matters most.** Low on the rails, the head limits depth: the
  rails start where a slider still clears the head by `HeadGap`. Above
  about 100 mm (head top plus `HeadGap`), the whole crown is free up to the
  top of the rails at about 169 mm. Put deep items high.
- **Width along the wall** is limited by the crown's curve. It is tightest at
  the front and back rails (t = 0, 180) and gentlest at the sides.
- **Too big for one rail:** a 150 x 75 x 14 mm power bank. It only fits
  lying flat under the crown top, across the front and back rails, which
  needs a part that spans two rails (not designed yet).
- **Bottle:** at the top of the back rail (step 29), the lip sits 0.3 mm
  under the crown top. Bottles up to about 65 mm below the cap clear the
  head; 67 mm does not. Mind the weight: 60 g with liquid is above what one
  locking slider holds (about 50 g), so test it.
- **Balance:** `layout.py` prints the centre of mass of everything on the
  rails. Keep it near the axis, for example heavy items on opposite rails.
