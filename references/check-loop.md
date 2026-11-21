# The make-and-check loop

Render, compare against the named references, list what's off, fix, repeat until it holds up. Show the client only results that passed.

## Each pass
1. Read the build log (`_logs/<piece>.txt`): bodies, grams, size, dropped debris, errors.
2. Open the square next to two or three reference images, one per lead influence.
3. Write what reads robotic, specifically and by location ("upper-left wing: two stones touch"; "leading edge: eight evenly spaced beads"). Note which shared function causes it if you can tell (for example `vein_wing`, `hyo_flourish`, `_clipbar`, the claw/seat cut).
4. Decide: is it this piece's seed, or the shared generator? Shared problems are fixed once, centrally, then every affected piece re-renders.
5. Run the design-coherence check (`references/design-coherence.md`): a part inventory and one close-up per part on a
   contact sheet. A part in a different language (plain chrome on a carved piece, a ball on a stalk) fails.
6. Re-render and check again. Stop when the list is empty or only has taste calls for the client.

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
| Ball ends | sphere terminal | ribbon `ends` to a needle; at furniture scale keep the section >= 4 mm and round it off |
| One part plain on a carved piece | a rule (work line, spikes) met by deleting the style there | engrave the language into the surface (`design-coherence.md`) |
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

## Modelling the stitched leather cord (client pick 9), what it took to match the photos
Four passes against the shop photos on the Moth saw and fork grips:
- Scale first: cord about 0.16 in across on a 0.4 in grip, thread 0.5 mm. At 0.115 in the thread was half the cord and the
  seam read as rope. Six cords at about 58 deg to the axis just close round the grip (n = 2 pi R cos(angle) / d).
- Each cord is its own tube with a slight hand-rolled wobble in radius. Its seam is a dark cut-edge strip sunk along one
  side, and the seam direction turns round the cord as it goes (about a turn per 1.3 in, random sign) so it shows on some
  cords and hides on others, as in the twisted rope.
- X stitch: per pitch (0.36 x cord diameter, +-15%) two thread segments cross the seam corner to corner, lifted just
  proud; spacing is hand-varied. Too fine a pitch reads as a continuous zigzag braid.
- Colour: tan veg-tan leather (base about 0.36, 0.20, 0.10 linear) with a large mottle and fine grain bump, cut edge much
  darker. Too light reads as peach plastic.
- Ends: tuck the cords 0.075 in under tapered blackened ferrules (core radius flaring to the bundle) with a rope band;
  flat disc collars looked like washers, and tilted tube ends poke out of short collars.

## Collection-scale runs (dozens of pieces at once), lessons from a 64-piece collection
- **Freeze, then fan out one piece per cloud machine.** `codeversion.py freeze` the kit, then run
  `KIT=<frozen kit> OUT=<shared folder> bash scripts/piece_job.sh <piece>` on each machine. The job refuses a Mac and a
  changed kit, meshes, runs check.py, check_stones.py and check_settings.py, renders the square and exports the web GLB,
  and writes one report per piece. Review the reports and squares together before anything is published.
- **Thickness floor for small pieces.** Ribbon strokes thin to `min(W, 0.36)` at their ends, which put earrings and
  small rings at p5 0.53 to 0.55 mm, under the 0.8 mm casting floor. `TFLOOR=0.45` (env, read by sculpt.py) brings
  rings and pendants to p5 0.8 to 0.9 mm with no visible change. Very small studs may still need wider strokes.
- **Watertight retry, then repair.** About one piece in eight left a few open loops where two strokes graze. piece_job.sh
  re-meshes at the voxel x 0.95, 1.06, 0.89 and 1.11. Some pieces stay open at every voxel (the same two 26 to 32 edge
  slits each time); `scripts/repair_stl.py in.stl out.stl` caps each open loop with a fan wound to match its
  neighbours (volume change about 0.01 %) and writes the file only if the result is watertight. The square and GLB
  from the open mesh are the same form; only the casting STL needs the repair.
- **Re-runs must clear the old square.** render_square.sh skips a piece whose square already exists, so a fix round
  silently kept every round-one square. piece_job.sh now moves the old square aside first.
- **Read the checker's own exit code.** `check_settings.py ... | tail; echo $?` reports tail's exit, which is always 0.
- **Hanging fancy stones need four claws.** Pears hung point-up from a loop (moira.pear) used three claws and failed
  HOLD on every piece; four (five where a strand runs under one claw) pass.
- **Bezel glazes scale badly.** A glazed crescent at radius 7 seats every bezel; at radius 17 to 19 the stock-size
  stones float in cells sized for bigger ones (SEAT fails). Keep glazed motifs small or cap the cell sizes at stock.
- **check_settings needs `rtree`** (trimesh proximity). Install it with the rest, or the settings/clipping check
  silently gets no answer.
- **Web GLB from the kit:** `make.py <piece> glb` decimates the metal in Blender (a DECIMATE modifier to `GLBFACES`;
  trimesh's simplify left a 26 MB file), adds glass stones with the render's colours and IOR, exports metres and Y up;
  then `gltf-transform optimize --compress meshopt` gives about 0.4 to 0.5 MB per piece.
- **Custom vein-panel outlines.** `wings2._shape` takes a list of (x, y) points as well as a named wing, so leaves,
  petals, plumes and shells can use the calm vein panel the owner already approved, instead of new stroke-built shapes
  (the first round, built from bare strokes, read as crude noodles).
- **Mirroring a panel:** pass the unmirrored angle with `sx=-1`. Passing an already-mirrored angle as well flips it back.
  For a shape that must mirror across its own axis (two shell halves), mirror the outline (negate y), not `sx`.
- **Earring pairs:** leave at least 30 mm between the two centres for wide drops, or the pair fuses into one body.
- **Taste loop at collection scale:** render cheap hero previews of every piece (VOX 0.07, 320 px), lay them out as
  contact sheets, and judge each against the owner's past picks (client-picks.md). Rebuild whole motifs in the approved
  language rather than patching single pieces.

## Sameness check (every collection, before anyone sees it)
The client's rule: every piece needs its own silhouette idea, and a new collection must not read as an earlier one
in a new colour. Run it on the finished squares, against every earlier collection and any sibling collection
being built at the same time:

    python3 -I scripts/check_sameness.py --new NEW=squares/ [--new-stl stl/] \
        --ref OLD1=old1/squares --ref OLD2=old2/squares [--ref-stl OLD1=old1/stl] --out reports/sameness

It scores the hero view of each square (shape, outline straightness, tone, colour, edge direction, fine grain,
plus mesh crispness when STLs are given), normalised so 1.0 is a typical difference between two reference pieces.
Flags: SAME (two new pieces under 0.35), NEAR (under 0.55: look), ECHO (a new piece within 0.50 of an old one),
RESKIN (the whole set sits among an old collection: set ratio under 1.10), TYPES (over half the pieces are
ring / earrings / cuff / pendant, or the type mix is an old collection's). Exit 1 on any flag except NEAR. Fix
flagged pieces in the design (a new silhouette idea, not a new seed or stone), re-render, re-run. Put the report
in the collection's reports folder and tell any sibling thread the result.

## Lessons from a 10-piece enamel collection (HELIUM, 21 Nov 2026)
- The watertight check must read the casting body's own entry in checks.json. A grep over the whole file matched the
  enamel mesh's entry and passed a leaky body. Run check.py again after every repair.
- A 0.055 mm voxel on a large piece needs about 14 GB. Add 8 GB of swap on the render machine, run one Blender job at
  a time, and preview at 0.1. Swap-bound jobs vary from 16 to 60 minutes.
- Editing a kit file during a local recheck breaks the code freeze. Re-freeze after every edit, before any job runs.
- Stones placed after a groove or coat can be filled in again when the coat re-unions the shrunk body. Place small
  stones away from coat ranges, and run clip_check and check_settings after every coat change.
- Order matters with sequential SDF ops: add small craters after the main stone crater, or the main cut eats them.
- Sameness: plain silver on white read as a reskin of earlier silver collections (set ratio 1.03 to 1.08) even with
  new silhouettes. Colour and finish (enamel coats, a punchier grade) moved it to 1.11 to 1.30. If a collection
  shares a metal with an earlier one, give it a finish that only it has.
