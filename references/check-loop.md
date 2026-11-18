# The make-and-check loop

Render, compare against the named references, list what's off, fix, repeat until it holds up. Show the client only results that passed.

## Each pass
1. Read the build log (`_logs/<piece>.txt`): bodies, grams, size, dropped debris, errors.
2. Open the square next to two or three reference images, one per lead influence.
3. Write what reads robotic, specifically and by location ("upper-left wing: two stones touch"; "leading edge: eight evenly spaced beads"). Note which shared function causes it if you can tell (for example `vein_wing`, `hyo_flourish`, `_clipbar`, the claw/seat cut).
4. Decide: is it this piece's seed, or the shared generator? Shared problems are fixed once, centrally, then every affected piece re-renders.
5. Re-render and check again. Stop when the list is empty or only has taste calls for the client.

## Report format (one per piece)
```
<piece>: bodies N, X.X g, size [..] mm, watertight yes/no
Passes: what matches the references
Robotic: 1) ... 2) ... 3) ...
Casting: anything under 0.8 mm, loose bits, odd stone sizes
Shared-code cause (if known): ...
```

## Flags that kept coming back
| Flag | Usual cause | Fix |
|---|---|---|
| Even-width veins and rims | stroke helper with constant radius | width keys that swell and taper (`wisp.organic()` on) |
| Ball ends | sphere terminal | ribbon `ends` to a needle |
| Bead row, ladder ticks, dot rows, milgrain | evenly spaced barbs or notches, `bead_row`, `grain=True` | remove, or randomise spacing and size; `grain=False` |
| Loose chips near stones | seat cut severs a claw tip | move the seat or shorten the cut; re-mesh and count bodies |
| Straight rods through a body | clip bar or pin builder | fold the bar into the form |
| Stones touching or in a grid | packer spacing too tight | wall between seats, varied sizes |
| Same silhouette across a family | seed only drives stones | let the seed drive the layout |
| Stone invisible in renders | clear glass on white, or hidden by metal | darker bezel edge, more absorption, or move the stone |
| Cropped thumbnail | compose margin | re-frame that view |

## Dark-studio renders: flat steel goes black
On a pure black studio (world strength 0), flat polished plates such as saw blades, chisel faces and fleam blades
have nothing to reflect and render as black slabs. Keep the background black to the camera, but give reflections a
soft grey gradient sky: a Light Path "Is Camera Ray" mix in the world. Give the steel roughness 0.3, not 0.2.
Found 18 Nov on the Moth tools v2 quick pass. Frame each view by projecting the bbox corners into camera space, not
from the bbox size alone, or tall pieces seen from an angle get cropped.

## "Crazy low poly": tessellation, edge breaks and the studio for photoreal metal
Client flag on the tools round 1 sheet: fleam blades and a cautery head were "crazy low poly", and the bar became
"recursively check against a photoreal reference until it matches" (a named maker's chisel for a chisel, a sculpted
render set for ornament). What fixed it, in order of effect:
- Tessellate for the final resolution, not the preview: round parts about 3x the old segment counts (lathes 64+,
  ellipsoids 48x24), swept paths resampled on a Catmull-Rom spline with steps under one tube radius. Keep 3/4/6/8
  segments only where the facets are meant (square neck, octagon grip, three-sided needle point).
- Spline smoothing overshoots at sharp corners (a lancet frame's bottom corners dipped 0.6 in below the floor). Give any
  turn over ~50 deg a zero tangent so corners stay corners.
- Nothing has a CG knife edge: a 0.15 mm Bevel modifier (3 segments, angle limit 32 deg, harden normals, clamp) on every
  rigid part, after welding faces built separately and recalculating normals.
- Blades are not plates: build them as slabs whose edge rings step inward and thin to the edge (a ground bevel), and
  limit each ring's inset to under half the local width or sharp points fold over.
- Loft real sections where the reference has them (a bevel-edge chisel is a six-sided section with hairline lands, a
  25 deg primary bevel, and a round neck lofted out of the shoulders). Assign the ground faces to a blackened material
  and the lapped flats to mirror steel, as the reference maker finishes them.
- Pointiness edge-rub stops working on dense meshes (every smooth convex surface reads as an edge, so blackened steel
  turns silver). Move the ramp to 0.6-0.75 and put the patina in the recesses with an AO node instead.
- Polished steel needs something to mirror: give glossy rays a world with strip softboxes (a bright horizon band and a
  high band on dark), keep the camera seeing black. Round steel then shows light-dark-light bands instead of a milky sheen.
