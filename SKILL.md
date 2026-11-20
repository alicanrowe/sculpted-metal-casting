---
name: sculpted-metal-casting
description: Design sculptural cast-metal pieces (sterling jewelry from castable wax, and furniture-scale castings like a metal sawhorse) with an SDF sculpting kit, check them for casting, render photoreal squares, and run the make-and-check loop against named reference artists.
---

# Sculpted metal casting

Use this skill to design cast-metal pieces that have to look hand-carved and liquid, not CAD-made, and that have to cast. It covers two scales that share one kit:

- **Jewelry** (rings, cuffs, ear pieces, clips, studs, pendants, necklaces) printed in castable wax and cast in sterling.
- **Furniture-scale castings** (the worked example is a sawhorse with a removable leather seat) built with the same kit in centimetres.

The code is in `scripts/`. The rules that came out of real review rounds are in `references/`. Read the references before you design anything. They hold every correction a client has already had to make once.

## Before you start
1. **Do what was asked, no more.** Quote the client's words for the job before you start. "Match X's close-ups", "same layout as X" or "re-render" means new views of the current model: no geometry change. Change geometry only where the client's words ask for it ("fix the moth rig", "the feet look like elf shoes"), keep everything else, and say in the report which parts changed. A brief written for another thread quotes the client and lists what must not change.
2. Read `references/style-rules.md`, `references/casting-rules.md`, `references/buildable.md` and `references/client-picks.md` (details the client has said they love: reuse them, don't check them away). Check every design against the **Design taste** list at the end of `style-rules.md` before showing it.
3. Look for a project aesthetic brief (for example `AESTHETIC.md`). If there is none, write one from `references/brief-template.md` with the client's words and the named reference artists. Never copy a reference: borrow its hand, not its pieces.
4. Set up Python 3.13: `pip install bpy==5.3.0 numpy scipy scikit-image trimesh manifold3d pillow numba`. `numba` is required (`sdf.py` uses it). Run shell scripts with `bash`.
5. If the brand has a theme (fonts, colours, logo), use it for every sheet and caption you make.

## Workflow
1. **Brief and influences.** Write down which influences lead and by how much (for example 50 / 30 / 20). For a set of variants, give each variant one lead influence and push it hard; see `references/influence-weighting.md`.
2. **Build in the kit.** A piece is a Python function that returns `(Scene, stones)`. Build it from strokes that swell and taper (`sculpt.ribbon`, `v2.blade`), carved feathers and petals (`moira.py`), wings (`wings2.py`), the carved abdomen (`abdomen.py`) and calibrated stones (`kit.calibrate`, `moira.prong`, `v2.claws`). Register it in a `PIECES` dict. `references/kit-map.md` lists what each module does.
3. **Mesh and count bodies.** `python make.py <piece> stl` meshes the SDF, bridges floating metal to the main body, drops cut debris under 1 mm³, and prints `bodies N`. A single piece must print `bodies 1`. An earring pair prints `bodies 2`, one per earring. Anything else is a defect: fix it in the generator, never by hand.
4. **Check the casting.** `python -I check.py <folder>` reports watertightness, size, volume, sterling grams and dwt, and ray-sampled thickness (5th percentile and minimum). Hold the floors in `references/casting-rules.md` (0.8 to 1.0 mm minimum on veins, wires and prongs).
5. **Check the stones.** Run `python scripts/check_stones.py` on the piece's stone list (`--jewelry` for mm, `--furniture-cm` for furniture kits). Every stone must come back OK, which means it is a stock calibrated size you can buy. Swap any LARGE or NO stone before rendering, using `references/stone-sourcing.md`.
5b. **Check the settings can be made.** `python scripts/check_settings.py OUT/<piece>.stl OUT/<piece>.json` (add `--units cm` for furniture). Every stone must be held (3+ claws or beads with no gap of 180 deg, 4+ for fancy shapes, or a bezel), seated, clear of metal, and 0.3 mm from its neighbours. Leather, straps and closures on furniture pieces: `python scripts/check_soft_parts.py` (see `references/buildable.md`). **Every non-rigid part** (leather, laces, straps, cushions, foam, the board inside a cushion) also gets a build spec (material, thickness, how it is cut, how it attaches and with what fasteners, how it is tensioned, how it opens, what load it takes, how it is replaced) and must pass `python scripts/check_soft_build.py --frame FRAME.stl --spec SPEC.json`, with an exploded build diagram on the sheet. A soft part with no spec fails. Fix FAILs in the generator before rendering. Multi-part pieces (tools, cages, stands) also run the assembly check in `references/buildable.md`, and its clipping check (check 5, `scripts/check_assembly.py`) runs on every piece before every render, changed or not: nothing may pass visibly into anything else.
6. **Render, on a cloud machine.** Never on the client's own computer: `render_square.sh` refuses to run on a Mac. Big jobs (animations) go to a render farm. `bash scripts/render_square.sh <piece>` renders four views (hero plus three angles) in a white light tent with real silver and faceted stones, and composes an Instagram square. It keeps the full build log in `<OUTSQ>/_logs/<piece>.txt`.
7. **Check against the references (the loop).** Put the square next to the named references and list what reads robotic. `references/check-loop.md` has the checklist and the flags that keep coming back. Fix, re-render, repeat. Show the client only squares that passed.
8. **Fan out, frozen.** For more than a few pieces, freeze the shared code (`python scripts/codeversion.py freeze r4 <files> > CODE_VERSION.txt`), give each piece its own machine, and follow `references/render-farm.md`. Render jobs never edit shared files. They report flags, and one owner fixes the kit centrally, bumps the version (fix1, fix2, fix3) and names the pieces to re-render.
9. **Sheet.** Assemble the passed squares into one comparison sheet, the client's picks first. Copy every square the client picks into a `picks/` folder that no re-render writes to, so a later round can't lose it (nine picks lost their images on 18 Nov).
10. **Public text.** Notes, sheets and site copy describe each piece on its own terms: no reference artists' names, file names or "inspired by" lines. The brief keeps the influences; the public never sees them.

## Furniture-scale castings
Read `references/furniture-scale.md`. The worked example (`scripts/sawhorse/`) keeps the proportions of a classic wooden sawhorse, recasts the frame in metal with the same kit, and adds a removable leather seat that drops over the rail on a slot. The rules: the bare frame must still work (flat rail top at the original height, nothing above that line), the metal is one watertight casting, and every sheet shows the seat on and off. For anything people sit or stand on, also run a load and tipping check. Before showing any pass, run the design-coherence check (`references/design-coherence.md`): every part listed with its language, one close-up per part, no plain or bead-tipped part on a carved piece.

## Getting it made
When designs are final, read `references/production-and-delivery.md`: who casts, prints, sets stones and finishes each part, what the client does by hand (leather), bought hardware, and the stone-cup rule for steel furniture.

## Rules that are easy to break
- No bead rows anywhere: no strung beads, ladder ticks, dot rows, milgrain, rope or knurled rims. They read machined.
- Every stroke swells and ends in a needle. No even-gauge tubes, no ball ends, no straight rods.
- Stones are stock calibrated sizes you can actually buy (run check_stones.py). Furniture kits are in cm, so cap their stones. Rounds of 2 mm and under are bead-set, centre ovals and drops get claws, wing panes sit in 0.7 mm open-backed bezels.
- Join members in the geometry so they fuse; `make.bridge` struts are a safety net, not a design tool.
- Don't edit shared code while renders that import it are running.
- One piece per machine when rendering in bulk, always on cloud machines.
- Straps and ties are constant-thickness leather that a person could cut, sew and buckle; anything round the frame opens or is sewn on (`check_soft_parts.py`).
- Claws reach over the girdle and seats stay clear (`check_settings.py`); a stone a setter can't set doesn't go on a sheet.
- No ball joints, umbrella ribs or wire outlines that no caster could make in one pour.

## Keep this skill improving
When a client flags something, or a check misses a problem, write the rule into the matching reference file in the same session (taste remarks go in the Design taste list in `style-rules.md` and, with the client's words, in `client-picks.md`; style, casting, buildable, stone settings, render farm, client picks), add a planted case to `scripts/tests/` if a check should have caught it, and run `python3 scripts/tests/test_check_settings.py && python3 scripts/tests/test_check_soft_parts.py && python3 scripts/tests/test_check_soft_build.py`. Then publish the skill.
