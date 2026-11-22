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

## Soft-part build spec (`scripts/check_soft_build.py`): every non-rigid part
```
python scripts/check_soft_build.py --frame metal.stl --spec saddle_spec.json --units cm
```
check_soft_parts.py checks shapes. This one checks construction, and it runs on every piece with any leather, lace,
strap, cushion, foam or board. Model each soft part as its own mesh (board, foam, cover, flaps, laces, tips), not one
blob, and list it in a spec json (see the script's docstring; Thread's `saddle_r11.py` SPEC is a worked example) with:
material and thickness (or lace diameter); how it is cut and formed; how it attaches (method, to what, fasteners, and
what a staple passes through); how it is tensioned (laces, straps, covers); how it opens (closure type and release);
what load it takes; how it is replaced. Plus the seat height, the cover envelope, and the load paths: the sitter's
weight down to the frame, and the uplift path that keeps the cushion on when the piece is lifted.
It fails on: a missing or placeholder field; a part that does not touch what it is fixed to; leather or laces passing
into the frame or into each other (a lace through a flap where there is no hole); any lace, cord, strap or hardware over
the sitting surface; a board or foam sticking out of the cover; a broken load path.
Rules it encodes:
- A cushion is a board (with a slot or cleats that locate it on the frame), foam, and a cover stretched and stapled
  under the board. Where the frame flares (legs into a rail) the board gets a relief notch, which also stops it sliding.
- Flaps and skirts are fixed: a tab stapled or screwed under the board, sewn to a welt, or riveted. A flap edge buried
  inside a cushion is fixed to nothing.
- Ties go under the rail, never over the seat, and tie off with a knot that unties (a bow). Each end gets a tip.
- Draw the build: an exploded diagram with each part's material and thickness and the fitting steps goes on the sheet.

Why: on 20 Nov 2026 the client could not see how Thread's saddle would work in real life: drawstrings over the seat as
closed rings with fused knots, flaps buried in a solid cushion, no materials. Every shape check had passed it.

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

## Assembly check for multi-part pieces (tools, cages, stands)
Run before every render of a piece built from many parts (each add() of a primitive is one physical part):
1. **Glass.** No part intersects a glass vessel. A cage is bent round blown glass, so straps and tracery stand a fixed
   gap off it (1/32 in) by following the glass profile plus gap plus wire radius. The glass must still be held: a collar
   clamped to the neck and a foot cup under the tip touch it. Model the vessel hollow (outer wall, lip, inner wall) so a
   stopper plug and a dropper sit in the bore without passing through glass.
2. **Nothing loose.** Union-find over parts that intersect or come within 0.004 in; one connected assembly per piece.
   Check contact both ways (a coarse lathe may have no vertex near a fine ring) and count a part fully inside another
   (a pin in a bore) as joined. Typical finds: a crown bud hovering over its cap, a slide ring floating round a shank,
   a trefoil whose lobes don't meet, braid tracery that never touches its frame (add a mullion it crosses, or ties).
3. **Cast detail at least 0.5 mm across.** Floor every swept wire, vein, barb and thorn tip at 0.0099 in radius;
   only steel needle points may go finer.
4. **Stands carry their tools.** Place each tool by settling it: start from the highest lift that is clear of the stand
   (tools go on from the side: a neck into a fork, a bail over a peg), lower until first contact. Then check no tool
   penetrates the stand more than 0.02 in and every tool touches it. A fork hook needs a long enough round neck under the
   collar for the prongs, and its upturned tips must reach past the widest part that hangs above them.
5. **No clipping, ever (client rule: "always run a clipping check for everything").** Run it on every piece before
   every render, whether or not the piece changed. Nothing may pass visibly into anything else:
   - Soft parts (leather, cut edges, thread, cord) never pass into another part beyond leather compression (0.006 in;
     thread 0.0015 in). Lay a stitch ON the surface: sample each leg round the cord's surface (cord radius plus thread
     radius), never a straight chord through it; the over-leg of an X lifts a thread's width where it crosses; legs that
     share a hole end a thread's width apart. Size twisted cords so they lie against each other (no core showing, no
     cord passing into its neighbour) and ride on the core's real profile, bead included.
   - A collar over cord ends is a hollow cup fitted to the cords (measure the cup wall from the cord vertices), with a
     bore fitted to the core; skive the cord ends thin so the cup stays slim. A solid sleeve laid through cords clips.
   - One piece of metal is one surface: a set saw tooth is the plate's own tooth with its tip bent (no second tooth plate
     laid through it, which renders as a line through every tooth); a barb split from a tine starts inside the tine at
     slightly less than the tine's section and draws out to a sharp point (no blunt cone stuck on, no coincident faces).
   - Wound thread or wire: turns at least one diameter apart, the outer layer resting on the inner, the tail one strand
     with its layer, routed round rims and guides rather than through them.
   - Hard parts of different metals or wood that cross must be a real seat (a pin in its bore, a tang in its socket, an
     inlay in its recess). The check lists every such joint with its depth; look at each new one on the render.
   - An ornament (window, rivet, touchmark) must not be covered by another part: keep it clear of necks and collars.

## Linked cast units (22 Nov 2026, from a brooch reel the client sent)
A piece that moves is one small cast unit repeated and linked, not one big casting: a four-petal unit with a centre
vein, cast once, laid in a 2 x 4 grid and joined by jump rings so it swings; satin finish; hung from a stick pin
with a screw-on end cap. Check the unit alone (casting, thickness), then the links: every jump ring passes through
a drilled or cast hole with clearance of at least its wire diameter, units clear each other through the whole swing
(clipping check at both ends of the swing), and the pin and cap are bought findings.
