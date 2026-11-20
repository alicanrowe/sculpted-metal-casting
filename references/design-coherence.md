# Design coherence: every part speaks the piece's language

Physical checks (work line, spikes, casting, stones) can all pass while one part looks like it came from a different
piece. That happened on a carved-feather sawhorse (20 Nov 2026). Client: "i think this part of carved doesnt fit the
rest of the piece".

## How it got through
1. **A fix for one rule stripped the language from one part.** To keep nothing above the work line, a pass removed
   the rail feathers and carving from the leg heads and made the horns "plain polished". The rule was met by deleting
   the style, not by carrying the style in a form that obeys the rule. Smooth chrome hooks were then left on a piece
   that is carved feathers everywhere else.
2. **The spike rule was met with a jewelry bead.** "Tip radius >= 2 mm" was satisfied by a 4 to 5 mm ball on the end
   of a tapering stalk. That is a flash-sheet bead accent. It passes the number, but it reads as a separate part stuck
   on, and it was flagged twice (as a "lumpy spike", then as "doesn't fit").
3. **Nobody looked at every part on its own.** The checks ran on the whole mesh, and the make-and-check loop compared
   whole-piece heroes against references. The parts that got changed (moth, feet) had close-ups. The rail ends were
   only ever seen small in a hero or in the corner of the buckle detail, and they kept passing.

## The check (run it before every pass is shown)
1. **Part inventory.** List every member the piece is made of (for a sawhorse: rail top, rail ends, leg heads, horns,
   legs, stretcher motif, feet, hardware, seat). Give each one one line: what it is made of in the piece's language
   ("carved feather, barbs engraved", "twisted feather shafts"). Put the list in the piece json under `"parts"`.
2. **Odd one out.** Any part whose line says "plain", "smooth", "polished", "bead", "ball", or names another language
   (petal, bone, chain) on a piece that is otherwise one language is a fail. The fix is to carry the language into that
   part, not to argue it. Exception: bought hardware (buckles, glides), which is named as bought.
3. **Close-up of every part.** Render one close-up per part in the inventory at about 30 cm framing (cheap: 500 px,
   12 spp) and put them on one contact sheet next to a close-up of the piece's signature part (the wing, say). Look for
   the one that doesn't belong. Hero views hide this.
4. **Style through the rule, not instead of it.** When a rule forbids raised relief somewhere (the work line, a seat
   contact face, a hand grip), cut the language INTO the surface: engraved barbs placed on the real surface by walking
   the SDF (step along the face normal and take the last point where the SDF is negative), not proud feathers and not a plain zone.
5. **Blunt ends in the part's own section.** Satisfy the tip rule by keeping the section at 4 mm or more right to the
   end and rounding it off. Never use a sphere on a thin stalk unless the piece's language is beads.

## Engraving on a flat-sectioned blade
`v2.blade(grooves=...)` places its barbs on an ellipse estimate of the section. On flat (rounded-rectangle) sections
the real surface is further out, so the barbs end up buried and nothing shows. Place each barb point with
a surface walk (point + t * face_normal, last t where the SDF < 0) instead, then cut (`op=1`) with radius about 0.08 to 0.1 cm at furniture scale, 30 or
so per 12 cm, sweeping back toward the root. Coarser or sparser than the piece's other carving reads as ribs.
