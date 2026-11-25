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

## Vendor minimums (enforced)
| Vendor and material | Minimum wall | Notes |
|---|---|---|
| Materialise OnSite, brass (printed wax, lost-wax cast) | **0.8 mm everywhere, tips included** | A Nov 2026 quote came back as "many parts have walls too thin, some too thin to print". Their analysis flags any spot under 0.8 mm. Plating is a ~0.5 µm decorative flash with no warranty, so polish and patina should carry the look. Ships EXW from Belgium, uninsured: split big orders. |

- For a Materialise order, the 0.8 mm floor beats the softer rows above. Needle tips (0.5 mm) and fine cast points (0.3 mm) do not pass. End tips in a 0.8 mm round, or accept the risk with the vendor in writing.
- Before any upload, run `python -I scripts/wall_check.py PART.stl 0.8`. It ray-tests every face (not a sample) and must print `thin 0`. It also lists gaps under 0.6 mm, which fill or fuse in casting.
- If the generator isn't on hand (an STL is the master), `python -I scripts/thicken_walls.py IN.stl OUT.stl 0.8` moves each thin wall's surfaces outward by half its shortfall, fading the offset out over about 0.8 mm so it reads as the same form, then smooth-unions it with the part. Run wall_check again and look at a before/after render. Gaps narrower than about 0.6 mm next to a thin wall fuse shut, as they would in casting. If the design needs one (for example a bell's slit or the gap in a double ring), widen it to 1.0 mm or more in the source instead.
- Don't fix thin walls with balls or beads along the thin spots. The first pass on the Moth case hardware did that and it rendered as warts and a beaded rope. Use the offset.

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

## Openings (client flag, r4 review: "not sure these tight lattices are possible irl")
Wire thickness is checked, but the gaps between wires are not. Tight lattice openings are the real risk: investment between close wires can break or not fill, and the inside can't be cleaned or polished. Keep every opening at least about 1.0 mm across (1.5 mm where it must be polished). Add a gap check to check.py before the next round.

## Braids and twisted bars (19 Nov, cast jail bars)
- **`braid` pitch is a fraction of the path's length, not cm.** Arc length is normalised, so the same pitch twists lazily on a long bar and tightly on a short one. Resample the path densely (about 0.5 cm steps) and pick pitch per member length (0.13 to 0.24 on a 20 cm lancet, 0.45 to 0.6 on a 4 cm one).
- **Twisted pairs must not be near-tangent.** When the twist amplitude is close to the strand radius, the strands only just touch and the mesher leaves non-manifold edges. Keep the amplitude clearly below the radius (0.075 to 0.095 cm for 0.08 to 0.12 cm strands worked) so the strands fuse. Then re-mesh at a slightly shifted VOX (for example 0.033, 0.037 or 0.031 around 0.035) if any edge is still non-manifold. Don't fix it with pymeshfix, which drops volume.
- Guard the retry: retry once over a fixed list of VOX values, then stop. A recursive retry ran out of memory.
