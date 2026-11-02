# Top hat tests

Print these in PLA before printing the full hat. Re-generate them with
`test_kit.py` (run inside FreeCAD) after changing any parameter or `rail.py`.
STLs are in `stl/test_*.stl`.

## Print next

Done: rail and slider (12 mm, 1.2 mm tongue), brim-to-crown
joint (joint pieces, collar ring and a full crown), brim seam key (coupon 5,
now `test_dovetail_flat_*`).

Still to test:

1. `test_lip_ring` + `test_finger_tip` (32 g): the cage finger in the wedge
   lip.
2. Optional: `test_dovetail_curl_*` (7 g), the brim seam on the curl.

Then print the brim and the cage. Reprint a settled test only after changing
what it covers (`seam.py` or the `Key*` / `Seam*` parameters for the seam,
`rail.py` for the rail). Print the head-fit pieces if no one has done so
for this wearer.

Use the slicer settings you will use for the hat: fits depend on them.

## 1. Head fit (`TopHatFitTests.FCStd`)

Try-on pieces for the wearer. Do this first: every other part is sized from
the result.

| Print | How to test | Result sets |
|-------|-------------|-------------|
| `test_fit_ring_<circ>` (3 rings) | Rings are the hat opening at `HeadCirc` and one hat size (10 mm) smaller and larger; the circumference is engraved at the front. Put each on at hat-wearing height. Pick the one that sits snugly without pressure points. If the sides pinch but front/back is loose (or the reverse), the oval is wrong | `HeadCirc` = chosen ring; `Oval` up for a rounder head, down for a longer one |
| `test_head_gauge` + `test_gauge_pointer` | Slide the pointer onto the gauge's ruler, push it to the bottom, clip the gauge onto the middle fit ring (forks over the ring sides), and put the ring on. The head pushes the pointer up. Take it off and read the ruler at the pointer's lower edge: ticks every 5 mm, numbers every 20 mm, measured from the brim underside | `HeadClear` = reading + 5 mm |

## 2. Fixtures (`FixtureTests.FCStd`)

Joints between hat parts.

| Print | Checks | Pass when | If it fails |
|-------|--------|-----------|-------------|
| `test_joint_poc_brim` + `test_joint_poc_crown` | Quick check of the brim-to-crown joint before the full rings: a 30 deg arc with collar, snap ridge and one rib, and the matching crown base (groove, rib slot, joint zone) | Rib drops into its slot, crown arc seats flush on the brim, snap ridge engages the groove. An arc is stiffer than a ring, so expect a firmer click than the full joint | Rib binds: raise `Clr` by 0.05. Snap will not engage at all: lower `Snap` by 0.1. Then print the full rings |
| `test_collar_ring` + `test_crown_ring` | Brim-to-crown snap and ribs | Crown ring clicks on with firm thumb pressure, only one orientation (wide rib front-right), no rotation play, pulls off with effort | Too tight or will not click: raise `Clr` by 0.05 or lower `Snap` (Advanced) by 0.1. Too loose: the opposite |
| `tophat_hatband` + `test_crown_ring` | Hatband | Slides on from the crown's bottom end and drops to rest on the brim without wobble | Bump `Clr` by 0.05 |
| `test_dovetail_flat_*` | Brim seam, flat area: the rounded dovetail key (S flanks, `KeyClr` 0.1 mm), chamfered bed edges, collar-end set-back | Pieces press together by hand and hold, top surfaces flush, the seam faces touch with no light through except the thin designed line at the collar end and the coupon's cut edge | Loose: lower `KeyClr` by 0.05. Will not go in: raise it by 0.05. Pinched at the collar end: raise `SeamGap` by 0.1. Put the slicer's perimeter seam at the back or randomise it |
| `test_dovetail_curl_*` | Brim seam, curled area; curl print quality | Same as above, and the curl underside printed cleanly | Turn on tree supports for the brim pieces |
| `test_lip_ring` + `test_finger_tip` | CageFingers tip in the wedge lip | Tip slides onto the lip's lower edge, then wedges tight against the wall with firm push; no rattle, does not crack | Too tight: lower `LipPress` by 0.1; loose: raise it |

## 3. Rail (`RailTests.FCStd`)

| Print | Checks | Pass when | If it fails |
|-------|--------|-----------|-------------|
| `test_rail` + `test_slider` | Dovetail cage rail and the 12 mm slider with the 1.2 mm detent tongue (chosen in round 3) | Slider slides onto the rail, clicks per 2.4 mm step, holds about 50 g upside down and shaken, pinch handle pulls out to release without cracking the tongue root | Tight slide-on: raise `T_CLR`. Weak hold: lower `CLR`. Tongue cracks: lengthen `SLIDER_L` (18 mm halves the strain) or thin `TONGUE_T` |

## Assembly order

Glue the four brim pieces and slide the hatband on from the crown's bottom
end. Fit the cage through the crown's bottom opening (crown upside down):
squeeze the finger tips in and push the cage in until the tips tuck behind
the lip.

Then snap the crown onto the brim collar; the collar top supports the cage.
Pop the crown off the brim to reach the cage.
