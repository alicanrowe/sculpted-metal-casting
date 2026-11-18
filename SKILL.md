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
1. Read `references/style-rules.md` and `references/casting-rules.md`.
2. Look for a project aesthetic brief (for example `AESTHETIC.md`). If there is none, write one from `references/brief-template.md` with the client's words and the named reference artists. Never copy a reference: borrow its hand, not its pieces.
3. Set up Python 3.13: `pip install bpy==5.3.0 numpy scipy scikit-image trimesh manifold3d pillow numba`. `numba` is required (`sdf.py` uses it). Run shell scripts with `bash`.
4. If the brand has a theme (fonts, colours, logo), use it for every sheet and caption you make.

## Workflow
1. **Brief and influences.** Write down which influences lead and by how much (for example 50 / 30 / 20). For a set of variants, give each variant one lead influence and push it hard; see `references/influence-weighting.md`.
2. **Build in the kit.** A piece is a Python function that returns `(Scene, stones)`. Build it from strokes that swell and taper (`sculpt.ribbon`, `v2.blade`), carved feathers and petals (`moira.py`), wings (`wings2.py`), the carved abdomen (`abdomen.py`) and calibrated stones (`kit.calibrate`, `moira.prong`, `v2.claws`). Register it in a `PIECES` dict. `references/kit-map.md` lists what each module does.
3. **Mesh and count bodies.** `python make.py <piece> stl` meshes the SDF, bridges floating metal to the main body, drops cut debris under 1 mm³, and prints `bodies N`. A single piece must print `bodies 1`. An earring pair prints `bodies 2`, one per earring. Anything else is a defect: fix it in the generator, never by hand.
4. **Check the casting.** `python -I check.py <folder>` reports watertightness, size, volume, sterling grams and dwt, and ray-sampled thickness (5th percentile and minimum). Hold the floors in `references/casting-rules.md` (0.8 to 1.0 mm minimum on veins, wires and prongs).
5. **Render.** `bash scripts/render_square.sh <piece>` renders four views (hero plus three angles) in a white light tent with real silver and faceted stones, and composes an Instagram square. It keeps the full build log in `<OUTSQ>/_logs/<piece>.txt`.
6. **Check against the references (the loop).** Put the square next to the named references and list what reads robotic. `references/check-loop.md` has the checklist and the flags that keep coming back. Fix, re-render, repeat. Show the client only squares that passed.
7. **Fan out, frozen.** For more than a few pieces, freeze the shared code (`python scripts/codeversion.py freeze r4 <files> > CODE_VERSION.txt`), give each piece its own machine, and follow `references/render-farm.md`. Render jobs never edit shared files. They report flags, and one owner fixes the kit centrally, bumps the version (fix1, fix2, fix3) and names the pieces to re-render.
8. **Sheet.** Assemble the passed squares into one comparison sheet, the client's picks first.

## Furniture-scale castings
Read `references/furniture-scale.md`. The worked example (`scripts/sawhorse/`) keeps the proportions of a classic wooden sawhorse, recasts the frame in metal with the same kit, and adds a removable leather seat that drops over the rail on a slot. The rules: the bare frame must still work (flat rail top at the original height, nothing above that line), the metal is one watertight casting, and every sheet shows the seat on and off. For anything people sit or stand on, also run a load and tipping check.

## Rules that are easy to break
- No bead rows anywhere: no strung beads, ladder ticks, dot rows, milgrain, rope or knurled rims. They read machined.
- Every stroke swells and ends in a needle. No even-gauge tubes, no ball ends, no straight rods.
- Stones are stock calibrated sizes. Rounds of 2 mm and under are bead-set, centre ovals and drops get claws, wing panes sit in 0.7 mm open-backed bezels.
- Join members in the geometry so they fuse; `make.bridge` struts are a safety net, not a design tool.
- Don't edit shared code while renders that import it are running.
- One piece per machine when rendering in bulk.
