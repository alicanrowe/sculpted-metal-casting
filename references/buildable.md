# Buildable, not just renderable

A render at hero distance hides parts that can't be made. Everything in a piece must be something a caster, a stone
setter or a leatherworker could actually make and fit, and these checks prove it before anything is shown.

## Stone settings (`scripts/check_settings.py`)
Run on every piece with stones, after `make.py <piece> stl` (the json now carries each stone's centre, table
direction and long axis):
```
python scripts/check_settings.py OUT/<piece>.stl OUT/<piece>.json            # jewelry, mm
python scripts/check_settings.py metal.stl stones.json --units cm             # furniture kits
```
- **HOLD**: metal rises beside and above the girdle in 3 or more separate places with no gap of 180 deg or more (4 or
  more for ovals, pears and marquises), or a continuous bezel wall the setter can push over. Two claws, or claws that
  stop short of the girdle, let the stone fall out.
- **SEAT**: a bearing ledge, gallery or seat under the girdle all the way round.
- **CLEAR**: the stone's own volume is free of metal so it can drop in. A seat cut that a later stroke refilled buries
  the stone.
- **SPACING**: 0.3 mm of metal between neighbouring girdles. Stones that touch chip when set.
- **FLOATING**: no metal at the girdle at all (a stone placed in air or on the far side of a member).
Any FAIL is fixed in the generator (move the stone, lengthen the claws, re-cut the seat after the last stroke), never
by hand on the mesh. Then cut a section by eye through one stone of each setting type.

## Leather, straps, ties and closures (`scripts/check_soft_parts.py`)
```
python scripts/check_soft_parts.py --rigid metal.stl --soft leather.stl --t 0.30 --closure toggles.stl --units cm
```
- Leather is one thickness: model straps, ties and ears as swept sheets of constant thickness (3 mm veg-tan straps,
  1.5 mm lambskin ears), never SDF blobs. A knot is two tails through a keeper, not a fused lump.
- Every strap rests on or wraps the frame without passing through it.
- Anything that goes round the frame either opens (a toggle, buckle or stud closes it) or is sewn on for good. A closed
  ring on the frame can't be put on or taken off.
- The closure touches the strap it fastens and passes through a slot or buttonhole in it. A toggle floating in front
  of the strap fastens nothing.
- "The seat lifts off": undo the closures and nothing is left looped round the rail. Show it on the sheet (seat on and
  off).
- Every soft body is one closed mesh. Cracked meshes show up as black lines in close-ups.

## Moving and joined metal
- No ball joints, umbrella ribs or wire outlines that would need assembly no caster can do in one pour. A part that
  moves is a separate casting with a real pin, clevis or hinge, and the sheet says how it goes together.
- Split a big casting into sections only on planes a welder can reach, and say where.
- Tensioned members (an X of rods) end in real fittings (clevis rod ends, turnbuckles), not in a blob.

## Strength before reshaping
When a piece fails the seating load check and the client likes the design, try a stronger material first (17-4
stainless, silicon bronze, printed maraging steel, titanium) at the current sizes, and only thicken what no material
can save. Say which pieces those are.

## Why this exists
On 18 Nov 2026 a sawhorse seat's knot, ears and tether were fused SDF blobs, the tether was a closed ring that could
not open, the toggle fastened nothing, and mesher cracks showed as black lines. Another variant's moth hung on ball
joints and umbrella ribs. The client had to ask for it to be "recursively resolved until it is physically possible in
real life". The checks above catch each of those on the model.
