# Sculpted metal casting skill

A Claude skill for designing sculptural cast-metal pieces that look hand-carved and liquid rather than CAD-made, and that actually cast: sterling jewelry printed in castable wax, and furniture-scale castings such as a metal sawhorse with a removable leather seat.

It packages a working pipeline: a signed-distance sculpting kit, a mesher that guarantees one casting body, a castability check, a photoreal 4-view render, and a make-and-check loop that compares every render against named reference artists until it stops reading robotic.

## What's in it
- **`SKILL.md`**: the workflow Claude follows: brief, build, mesh and count bodies, check the casting, render, check against references, fan out, sheet.
- **`references/`**
  - `style-rules.md`: 18 rules that make metal read hand-carved (one stroke that swells to a needle, no even tubes, no bead rows, carved wings, designed hardware)
  - `casting-rules.md`: thickness floors (0.8 to 1.0 mm wires and prongs, 0.7 mm bezel walls), one body per piece, weight
  - `stone-settings.md`: calibrated stone sizes, claws vs bead settings vs open-backed bezels, placement
  - `check-loop.md`: the per-piece check, a report format, and a table of the flags that kept coming back with their fixes
  - `render-farm.md`: render settings that held up, and the freeze / render / collect / fix / bump protocol for one piece per machine
  - `furniture-scale.md`: the sawhorse rules (keep the working geometry, removable seat on a slot, nothing above the rail, one watertight casting, seat on and off)
  - `influence-weighting.md`: weighting influences in one piece, and pushing one lead per variant in a set
  - `brief-template.md`, `kit-map.md`
- **`scripts/kit/`**: the sculpting kit and about a thousand registered example pieces. `make.py` builds, meshes, bridges loose metal, drops debris, prints `bodies N` and grams, and renders or exports STL. `check.py` reports watertightness, weight and ray-sampled thickness.
- **`scripts/render_square.sh`**: one piece to a 4-view Instagram square, with the full build log kept.
- **`scripts/codeversion.py`**: freeze the shared code before a render fan-out and check it on each machine.
- **`scripts/sawhorse/`**: the furniture-scale example: the wooden original, the metal frame and leather seat, eight influence-led variants, and the presentation sheet.

## Install
- **Claude.ai / Claude app:** zip this folder and upload it under Settings > Capabilities > Skills.
- **Claude Code:** copy the folder to `~/.claude/skills/sculpted-metal-casting/`.
- Python 3.13: `pip install bpy==5.3.0 numpy scipy scikit-image trimesh manifold3d pillow numba`

## Quick start
```
cd scripts/kit
python make.py list | head                       # registered pieces
OUTDIR=out python make.py g4_vein_stud_01 stl    # casting STL + json, prints "bodies 1"
python -I check.py out                           # thickness, weight, watertight
OUTSQ=squares bash ../render_square.sh g4_vein_stud_01   # 4-view square in squares/
```
Sawhorse:
```
cd scripts/sawhorse
VOX=0.3 python sawmoth.py mesh                   # quick frame build and body count
OUTDIR=r python sawmoth.py render p1             # seat on;  OFF=1 for seat off
python sheet.py r p1 sheet.jpg
```
A full-quality square takes about 20 to 50 minutes of CPU per piece. Render in bulk on cloud machines, one piece each.

## License
MIT
