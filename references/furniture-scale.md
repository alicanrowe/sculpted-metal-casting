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

5. **Nothing above the work line with the seat off (client flag, 18 Nov 2026).** The bare frame is judged as a
   sawhorse: from leg to leg along the whole rail, no horn, needle, curl, stone or chain may rise above the flat
   top (74.3 cm). Anything that cradles the seat either stays below that line or belongs to the seat assembly
   and lifts off with it (for example a cast cradle with the horns that the bolster straps to). Keep stones,
   chains and fine carving off the leg heads and rail, where saws and boards hit them; put them on the
   stretcher. Check: `max z of metal within |x| <= rail half length` must equal the top height.

9. **Strength: check the rock, not just the load (client question, 18 Nov 2026: "could it support the weight of
   a man").** Straight-down load is rarely the problem: an adult (100 kg, x2 for dropping onto the seat) puts
   about 1000 N on each of two legs. The failure case is a front-to-back rock: 200 N sideways at seat height is
   about 75 Nm bending at each leg base. Size the leg base so bending stress (M / section modulus) stays under
   half the alloy's yield (cast sterling yields at roughly 120 to 140 MPa). Loose parallel strands each bend on
   their own: tie them into one column with collars or bindings, or thicken them. Thread's 3 loose 12 mm strands
   reached about 125 MPa and needed both.

10. **Bought hardware is named, not cast (client question, 18 Nov 2026: "would these wires be purchased?").**
    Tension rods, cables, turnbuckles, levelling pads and screws are bought stock, not castings. On the sheet,
    label each one with what you'd order (for example: 6 mm stainless threaded rod or 6 mm wire rope with swaged
    ends, M6 stainless turnbuckle, M8 levelling pad) and list them in a hardware line with the casting weight.
11. **No fragile spikes at furniture scale (client flag, 18 Nov 2026: "this spike seems fragile").** Needles and
    hooks that stick out where knees, clamps and boards hit them need a thick root and a blunted tip: root at least
    as thick as the member it grows from, tip radius at least 2 mm, length under about 4x the root thickness.
    Turn them down or back toward the frame, not out into the room.

12. **Furniture alloy (client decision, 18 Nov 2026): pick the metal to fit the design, not the other way round.**
    the client's rules: it must hold a person's weight, production must be automatable, and the design should stay as
    drawn if at all possible. Cast sterling (yield about 120 MPa) is jewelry only: Thread hit 570 MPa on a plain sit.
    For each piece, run the seating check at its current geometry up this ladder and take the first that passes
    (113 kg, 2x drop-in, safety factor 1.5, fatigue at the rail, deflection): 17-4PH H1150 investment cast from
    printed patterns (yield about 725 MPa), then 17-4PH H900 (about 1170), then Ti-6Al-4V printed (about 880, lighter),
    then maraging steel 1.2709 laser-printed and aged (about 1900). Thicken a member only when nothing on the ladder
    passes, and then only the smallest local swell (stress goes as 1/d^3, so +10% diameter takes about 25% off).
    Parts bigger than one build or pattern are made in sections joined at hidden welds or bolts. Finish: polished
    steel, or rhodium or silver plate where it must read as silver.
