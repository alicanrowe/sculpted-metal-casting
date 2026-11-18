# Casting rules

Pieces are printed in castable wax or resin (the project used a Formlabs Form 4 with Castable Wax) and lost-wax cast in sterling silver. Piercing posts are titanium findings, not cast. Furniture-scale frames are cast in bronze, steel or silver alloy by a foundry in sections that weld or pin into one body.

## Thickness floors
| Feature | Minimum | Notes |
|---|---|---|
| Veins, wires, antennae, prong wire | 0.8 to 1.0 mm (radius 0.4 to 0.5) | Thinner pieces fail to fill or snap in finishing. An early round ran 0.6 to 0.8 mm and had to be raised. |
| Structural strokes | 1.4 to 2.0 mm | Anything that carries a stone or a clip. |
| Ring shank | 1.6 mm | |
| Needle tips | 0.5 mm at the very end only | The taper reaches 0.5 mm in the last millimetre, not along the stroke. |
| Bezel wall | 0.7 mm, open-backed | Tall enough above the girdle to push over the stone. Thin rim rings are not bezels. |
| Bezel ledge | 0.6 mm | |
| Jump-ring eyes | 1.6 mm hole | For 18 ga rings. |

Measure with `check.py`. It ray-samples the wall and wire thickness and reports the 5th percentile and the minimum. Treat a 5th percentile under 0.8 mm as a flag to look at, not an automatic fail: needle ends pull it down. Look at where the thin samples are.

## One body
- A single piece must mesh to **one body** (`bodies 1` in `make.py`'s printout). An earring pair is **two**, one per earring, and the pair builder declares `s.units` so each earring is bridged on its own.
- `make.py` bridges floating metal to the main body of its unit with a short liquid strut, then drops cut debris under 1 mm³ and prints it as `dropped debris`. Several 0.0 mm³ entries are harmless noise.
- Loose bits usually come from stone-seat cuts that sever a claw tip, or a carved groove that cuts a sliver free. Fix the generator (move the seat, shorten the cut). Don't delete islands by hand on one piece.
- Watertightness: a mesh can be one body and still report `watertight: false` after export. Repair it before printing (for example with manifold3d or a mesh-repair pass in your slicer), and re-check.

## Mesh artifacts
- **Hairline wires in renders.** Taubin smoothing in `sdf.save_stl` can fling the odd non-manifold vertex (where engraved barbs touch) far from the surface, which renders as straight hairlines. `save_stl` now puts back any vertex that moved more than about a voxel. If you still see hairlines, look for touching engraved details.
- **Feather slivers.** The carved feather primitive's field is only a distance near the feather, so it is clipped to the feather's own bounding box. Without that clip it left hairline slivers inside blocks woken by other parts.
- **Pieces cut off on a block seam.** The block mesher used to weld block seams in absolute coordinates, and at some voxel sizes a whole seam plane failed to weld, so a sawhorse's legs came off exactly on a block boundary (VOX 0.09 and 0.10 broke, 0.11 was clean). Seams now weld in lattice units. `sdf.mesh` also checks for a separate piece whose bounding box ends on a seam plane, retries on a shifted grid, and raises if three shifts fail. If you see `mesher dropped a block`, report it rather than hunting for a lucky VOX.
- **Join parts in the geometry, not with struts.** `make.bridge` adds short struts to join floating metal. Treat it as a safety net. A strut where the design didn't ask for one reads as a rod; overlap the members in the builder so they fuse instead.

## Weight
`check.py` and `make.py` report sterling grams (10.36 g/cm³) and pennyweight. Use it to price metal and to catch pieces that are far heavier than they look. A furniture frame can reach several litres of metal (one sawhorse variant came out near 6,600 cm³), which is a cost and weight decision for the client, not a detail.
