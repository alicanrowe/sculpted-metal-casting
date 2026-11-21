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

## Design taste (moved to the shared design-taste skill, 21 Nov 2026)
The client's cross-project taste (dark and gothic over pretty, never literal, one language head to toe, the motif
is the structure, solid not flimsy, no nubs, light stones, liked changes go everywhere, and the rest) now lives in
one place: the `design-taste` skill (`../design-taste/` next to this skill, github.com/alicanrowe/design-taste).
Read its `principles.md` and `banned-moves.md` before any design, and score every render with its `rubric.md`
before showing it. The metal-specific picks (stitched-cord grips, the liked feet) stay in `client-picks.md`.

**Self-improving rule.** Any critique of how something looks goes into design-taste's `critique-log.md` with the
client's words in the same session, then into its principles or rubric, then publish it with
`_publish/sync.sh design-taste`. Pins on jewelry sheets also go in `client-picks.md` here as before.

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
- Root cause, found on the first cloud renders: `_feather` in `sdf.py` cut a hard-coded 0.09 serration into the
  vane edge (0.09 mm in jewelry, 0.9 mm in a cm kit), whatever the pitch. Fixed in the kit (all three copies of
  sdf.py): the serration now scales with min(1, pitch / 0.28), so jewelry (pitch 0.28 or more) is unchanged and a
  cm feather with pitch 0.05 gets a smooth edge. Narrow vanes (W about 0.13 to 0.17 x L) read as feathers; broad
  ones (0.2 x L and up) read as leaves even with a smooth edge.
- At cm scale leave `notches` at 0. A split notch on a 2 to 4 cm feather reads as a sawtooth (palm leaf), and where
  it cuts through a thin vane it punches a round hole. Keep ragged ends for a deliberate tear only.
- Five feathers or points radiating evenly in a ring read as a pentagram (Thorn rose round 2). Use an uneven count
  (seven) and unequal lengths, or turn them all one way.
- A moth hanging head-down reads only when something says "hanging": hooked claws gripping the top member like a
  bat's feet, a slim abdomen and a clearly bigger head. Feather plumes beside the abdomen read as ears.
- Radiating separate feathers (a star of them) also read as a leaf. Shingle them (each overlapping the next), or
  turn them all the same way round a centre like rose-window mouchettes, and keep it to five or fewer.
- A frame with straight jambs that run down below the subject and end in hooks reads as a stool or a table. End
  jambs on the mounting surface in a short point.

