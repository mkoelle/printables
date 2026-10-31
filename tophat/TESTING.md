# Top hat tests

Print these in PLA before printing the full hat. Re-generate them with
`test_kit.py` (run inside FreeCAD) after changing any parameter or `rail.py`.
STLs are in `stl/test_*.stl`.

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
| `test_dovetail_flat_*` | Brim seam, flat area | Pieces press together by hand, top surfaces flush, no gap at seam | Raise or lower `Clr` by 0.05 |
| `test_dovetail_curl_*` | Brim seam, curled area; curl print quality | Same as above, and the curl underside printed cleanly | Turn on tree supports for the brim pieces |
| `test_lip_ring` + `test_finger_tip` | CageFingers tip in the wedge lip | Tip slides onto the lip's lower edge, then wedges tight against the wall with firm push; no rattle, does not crack | Too tight: lower `LipPress` by 0.1; loose: raise it |

## 3. Rail (`RailTests.FCStd`)

| Print | Checks | Pass when | If it fails |
|-------|--------|-----------|-------------|
| `test_rail` + `test_slider2/3*` | Dovetail cage rail and slider detent (1.2 vs 1.4 mm tongue) | Slider slides onto the rail, clicks per 2.4 mm step, holds about 50 g upside down and shaken, pinch handle pulls out to release without cracking the tongue root | Pick the thinner tongue that holds and set `TONGUES` in `rail.py` to it. Tight slide-on: raise `T_CLR`; weak hold: lower `CLR` |
| `test_rail` + `test_slider2/3_half*` | Half-length (12 mm) sliders: more per rail | Same as above | Expected to fail: the short tongue reaches about 2-4% strain at a full click (PLA breaks around 2-3%). If they crack, a 3/4-length (18 mm) slider is the realistic short option |

## Assembly order

Glue the four brim pieces and slide the hatband on from the crown's bottom
end. Fit the cage through the crown's bottom opening (crown upside down):
squeeze the finger tips in and push the cage in until the tips tuck behind
the lip.

Then snap the crown onto the brim collar; the collar top supports the cage.
Pop the crown off the brim to reach the cage.
