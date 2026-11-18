# Style rules: make it read hand-carved, not machined

These came out of real review rounds. Each one is a correction a client already made once. The worked example's direction was "a carved-feather jeweller makes a collection for a liquid-chrome tattoo artist": carved, layered and melted on one side; liquid chrome that swells to needle points on the other. Swap in your own references, keep the rules.

## Strokes
1. Every element is one continuous stroke: a start, a swell, a needle end. Points are the stroke thinning out, never a cone stuck on.
2. Liquid ribbons that twist in 3D, not round tubes or bent cans. No polygonal or faceted look.
3. Curves accelerate: tight at the head, a long sweep at the tail. No kinks, no even arcs, no straight lines.
4. No even-gauge tubes. Wing rims, veins and spars swell and taper. "Even tube thickness" is the most common robotic flag.
5. Tips swell into a needle. Round ball ends read as stock findings.
6. No bare wire wisps, stubs, bristles or noodle stems running past an outline. They read scratchy and they break in casting.

## Surface
7. Engraving only on feather or blade surfaces, with a polished spine. Never herringbone rope on a tube.
8. **No bead rows anywhere.** No strung beads, graded dot rows, ladder ticks, evenly spaced barbs or notches, milgrain borders, chevron rope rims or knurled edges. Even spacing reads machined, and a graded bead string read as something crude to the client. If barbs or notches are needed, vary their spacing, length and angle.
9. Detail in clusters at joins and terminals, with plain polished fields between, so the eye can rest. Even density across the whole piece.
10. Wings are carved and layered surfaces, not open outline loops or even wireframes.

## Composition
11. Three or four motifs per piece, not everything at once. Negative space and wispy elements.
12. Layer in depth: strokes pass over and under each other. Not planar.
13. Asymmetry with balanced weight.
14. Hardware is designed, not hidden or tacked on. No straight clip bars or pin rods poking out of a thorax; build the clip into the form.
15. Insect abdomens are one carved taper (widest just below the thorax, a long S to a needle, shallow plate lines), never a string of beads. Keep the abdomen in proportion to the wings (one came out three times the wing length with a hard pinch).
16. Variants of one family must change the silhouette, not just the stones. Check that the seeds actually vary the layout.

## Renders
17. Photoreal polished silver on white, in a light tent with soft gradients and grey flags for edges. Instagram square: hero large on top, three smaller angles below, no text.
18. Make sure nothing is cropped in the small views, and that every stone shows in at least one view.

- **No literal motifs (client flag, 18 Nov 2026).** A moth or butterfly is never a flat clip-art outline or a
  symmetric stencil cut from plate. Build it from structure (veins, feathers, wire, carved bodies) and let it be
  abstracted or partial. Tiny repeated motifs that can't carry their detail at viewing distance get scaled up
  into real members or dropped. See `client-picks.md` for what the client loves and flagged.

## Design taste (the client's stated preferences, kept up to date)
Every correction the client makes about how something looks goes here as a rule the same day, with the words they
used in `client-picks.md`. Read this before any design or redesign, and check new work against every line.

- **Dark, scary and gothic beats pretty.** When asked for "the theme", push toward menace: bone, claw, thorn,
  carapace, needle points, black and darkened metal. Tidy, cute or generic ornament is a fail even if it is clean.
- **Never literal.** No clip-art insects, butterfly or moth silhouettes, pictogram bugs at a crossing, or cut-out
  stencils. The creature is suggested by structure (veins, bones, joints, wing membranes that brace) and may be
  partial or abstract. Two strikes on this already (Edge stretcher, Edge X hub).
- **Fit the piece's own world.** New parts (feet, handles, hubs, pulls, hinges) are built from motifs already on
  that piece. Read the piece's model and renders first and name the motifs you are reusing in the brief.
- **One creature, head to foot.** A foot is the leg continuing in the same members (Durumi's crane foot is the
  reference). No stock foot shared across variants, no curled-up "elf shoe" toes.
- **Spikes wind, they don't line up.** Thorns run along vines and long members; never a comb of barbs or spikes on
  the focal point.
- **One focal point and quiet space.** Busy centres get flagged; let crossing members pass clean.
- **Motifs must read at viewing distance**, or get scaled up into real members, or dropped.
- **Variants change the silhouette**, not just the colour or stones.
- **A liked change goes everywhere.** When the client likes an improvement on one piece of a set, roll it out to every
  related piece in that piece's own language, and push it live ("keep the updates eveyrwhere its a rule").
- **No hexagon cages.** A hexagon frame with a block hub on tension rods reads as hardware, not sculpture (Edge r9
  hub: "i hate the hexagon rework").
- **Long spikes and horns taper smoothly.** No lumps, ripples or knuckled bulges along a hanging spike or horn
  ("fix this being lumpy").
- **Liked feet and profiles to reuse:** Thread r9's twisted-strand foot (two strands twisting low to a whipped
  scroll-ball toe on the floor); Edge r9's planted beak T-foot on glides; Edge's side profile, tapered legs flaring
  into a T-foot ("this is a really nice side profile").

Check before showing any design: hold the render next to this list and the pinned picks. If a line fails, fix it
first. If the client says something about taste that isn't here, add it in the same session.

## Asymmetry (client, r4 review)
Small random wing/outline differences read as mistakes. Either mirror the pair, or make the asymmetry big and obvious (one wing clearly reshaped, one dominant element) so it reads as intent. Keep stone colours to one species per piece unless asked.

## No borrowed brand motifs (client, r4 review)
- No gothic cross / dagger / fleur-de-lis terminals. They read as a Chrome Hearts rip-off. Tails end in organic insect forms (tapering abdomen, curl) with no nub.

## Carved feathers at furniture scale (moth case gable motifs, 18 Nov 2026)
- `moira.feather` is tuned in mm: it clips the barb pitch to 0.28 and the depth to 0.15. In a cm kit a 3 cm
  feather gets 3 mm teeth along its edge, and a fan of them reads as a cannabis leaf (first check pass, all three
  gable options). At cm scale call `Scene.feather` directly with pitch about 0.075, depth 0.03, shaft 0.03 x L,
  ridge 0.05, one or two notches, width about 0.2 to 0.27 x L, thickness 0.16 to 0.26 (cast floor). The working
  wrapper is `gfeather` in `moth-build/gems/moth_gems.py`.
- Radiating separate feathers (a star of them) also read as a leaf. Shingle them (each overlapping the next), or
  turn them all the same way round a centre like rose-window mouchettes, and keep it to five or fewer.
- A frame with straight jambs that run down below the subject and end in hooks reads as a stool or a table. End
  jambs on the mounting surface in a short point.

