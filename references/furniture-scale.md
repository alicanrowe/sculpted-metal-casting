# Furniture-scale castings: the sawhorse example

`scripts/sawhorse/` recasts a classic wooden sawhorse (Krenov-style: two splayed legs on long feet, a top rail, a low stretcher, a cushion with a slot that fits over the rail) as one sculpted metal frame, using the same SDF kit as the jewelry, in centimetres.

- `krenov_model.py`: the wooden original in inches (manifold3d). Its proportions and the cushion are reused.
- `sawmoth.py`: the metal frame (feet, legs with horns, rail, a moth stretcher), the leather seat (cushion with the slot filled, piped ends, straps) and the renderer. `python sawmoth.py mesh` builds and reports the metal; `python sawmoth.py render <tag>` renders the views into `$OUTDIR`. Set `OFF=1` to render with the seat lifted off.
- `sawvar.py`: eight variants as parametric members (leg, foot, rail, moth) with one influence leading each. `python sawvar.py render <a-h> <pass>`.
- `sheet.py`: the presentation sheet (hero, front, side, detail, top, notes). `SEATOFF=1` builds the seat-off sheet.

## Rules
1. **Keep the original's working geometry.** Seat height, rail height and footprint stay. The worked example kept the 29 1/4 in rail top and a 31 1/2 in seat.
2. **Removable seat.** The leather seat lifts straight off. Its underside keeps the slot (or straps that close under the rail's keel), so it drops over the rail and can't slide.
3. **The bare frame is still a sawhorse.** With the seat off, the rail has a flat working top at the original height, and **nothing on the frame rises above that line**: no horns, ribs, finials or hardware. Two variants had to rebuild their members because horns or bone ribs stood above the rail and would have tipped a board.
4. **Horn and cushion clearance.** Anything that cradles the cushion sits outside the cushion's width (the example kept horn tips outside ±5.6 cm), so the seat lifts clear. Check that leather and metal don't overlap anywhere.
5. **One watertight casting.** The metal frame meshes to one body. Carving cuts free small islands; bridge them or remove the cut. Buckles and hardware that live on the straps are separate small castings.
6. **Check structure.** Legs pinched to a waist and liquid tendons look good and can be weak. For anything people sit on, run a seating load and tipping check before calling it done.
7. **Render both ways.** Every sheet shows the seat on and the seat off. Add a lifting-off view if it helps.
8. **Metal volume is a client decision.** Report litres and kilograms in the chosen alloy.

## Lessons from the variant round
- A shared variant script is a starting point. When a variant's lead influence needs different members (knife-edge plate with no horns; crane-leg bones), write its own builder rather than bending the shared one.
- First passes tend to read as plumbing pipe or a zipper (evenly repeated grooves). Concentrate carving at the feet and joins and leave long liquid runs plain.
- Small details vanish at furniture scale: moths too small to read, straps that disappear against the cushion. Scale up, add gloss contrast (matte cushion, glossier straps), and bright honed edges on dark metal.
- Leg-mounted details must face out, not into the leg.
