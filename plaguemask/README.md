# Plague doctor mask

Wearable full-face plague doctor mask for costume use, parametric in FreeCAD,
printed in PLA on a 220 x 220 mm bed. Style parts (beaks, eye bezels, trims)
are swappable on one base mask.

Status: **pre-design**. Nothing modelled yet; waiting on face measurements.

## Requirements (agreed 2026-10-18)

| Topic | Decision |
|-------|----------|
| Coverage | Full face: forehead to chin, cheek to cheek |
| Wear | Costume use, comfortable for hours; worn together with the top hat (`../tophat`), so the mask's top edge and straps stay below the hat brim |
| Fit | Parametric from face measurements (below), with a printable fit test first |
| Glasses | Not worn under the mask; eye area can sit close to the face |
| Mounting | Two 20 mm elastic straps: one round the head at temple level, one over the top of the head (lies flat under the hat) |
| Styles | All four, as swappable parts on one base: classic leather, steampunk, minimal, skull |
| Beak | Parametric length and droop; default medium, about 180 mm from the face |
| Eyes | Snap-in eye inserts sharing one socket: a lens ring (clamps a clear or tinted acetate/PETG disc) and a mesh ring (clamps fabric mesh) |
| Airflow | Hidden passive vents only: beak "nostrils", under the beak base and along the chin edge. No electronics |
| Material | PLA for every part |

## Planned parts

| Part | Notes |
|------|-------|
| Face shell, upper | Brow, eye sockets, nose bridge, temples, strap slots. Eye sockets take the snap-in inserts; beak socket at the front |
| Face shell, lower | Cheeks, mouth cover, chin, chin-edge vents. Keyed and snapped to the upper shell (split needed for the bed and for printing without supports) |
| Beak socket | Shared interface on the face shell so every beak style fits. Snap or bayonet lock |
| Beaks | Leather (stitched-seam panels), skull (bone ridges), steampunk (bands and rivets), minimal (smooth or faceted). Printed in sections of 200 mm or less, joined with spigots and snaps; hidden nostril vents |
| Eye inserts | Lens ring and mesh ring, same snap-in fit; plus a flat cutting template so the disc and mesh are cut to the right size |
| Eye bezels | Decorative outer rings per style (plain, steampunk goggle with rivets, bone) |
| Trims | Optional snap-on or glue-on details: rivet strips, gear medallions at the temples, stitch-line overlays |
| Strap anchors | Slots for 20 mm elastic at both temples and at the top of the forehead |

A style setting in the build script chooses which beak, bezels and trims to
export.

## Face measurements needed

Take these with a ruler or calipers, in mm (a friend helps). Relaxed face,
looking straight ahead.

| # | Name | How to measure |
|---|------|----------------|
| 1 | Face width | Widest point across the cheekbones |
| 2 | Temple width | Across the sides of the head at eye level, just in front of the ears |
| 3 | Face length | Eyebrow line to bottom of the chin |
| 4 | Eye spacing | Centre of one pupil to the other (your glasses prescription may list it as PD) |
| 5 | Eye height | Bottom of the chin to the pupils |
| 6 | Nose projection | Tip of the nose forward of the cheeks (hold a ruler flat across both cheeks under the eyes, measure to the nose tip) |
| 7 | Chin depth | Chin tip back to the front of the ear, along the jaw |
| 8 | Hat clearance | Eyebrow line up to where the top hat brim sits when worn |

Optional: a photo of your face from the front and from the side with a ruler
in view, to check the shape.

## Test plan (before the full mask)

1. **Face fit frame**: thin outline of the shell edge, eye sockets and nose
   bridge. Checks the measurements and where it touches your face.
2. **Eye socket coupon**: one socket with a lens ring and a mesh ring. Checks
   the snap fit and the disc and mesh clamping.
3. **Beak socket coupon**: the socket plus the first few cm of a beak. Checks
   the lock and the swap between beak styles.
4. **Strap slot coupon**: one slot with 20 mm elastic threaded. Checks the
   slot fit and edge comfort.

## Open questions (later)

- Finish: paint scheme per style (leather brown, brass, bone)?
- Beak sections: glued for good, or snapped so they come apart for transport?
- Weight budget for a long beak, and whether the over-the-top strap needs
  padding.
