# Kit map (`scripts/kit/`)

Units are millimetres for jewelry (centimetres in the sawhorse). Z is up. Every piece builder returns `(Scene, stones)`.

| Module | What it does |
|---|---|
| `sdf.py` | Signed-distance modelling (numba): tapered round-cone strokes, flattened blades, spheres, ellipsoids, tori, smooth union and subtraction, Catmull-Rom curves, narrow-band marching cubes to STL with Taubin smoothing. |
| `v2.py` | Engraved blades (`blade`), claw settings (`claws`), stone packing, ring bands, faceted stone meshes and materials, the photoreal render look (`realism`). |
| `kit.py` | 2D design on a mapper (flat plane or cylinder for bands and cuffs): leads, nibs, spikes, roses, lancets, wings, stone calibration (`calibrate`). |
| `sculpt.py` | Liquid forms instead of tubes: `ribbon` (a lens-section stroke that swells, twists and ends in needles), drops, C and S scrolls. |
| `moira.py` | Carved feathers that wrap the body, petals with spiky leaves, thorned hearts, gate scrolls, stars, claw prongs (`prong`). |
| `motifs.py` | A motif library on top of `sculpt.py` that draws on any mapper. |
| `wings.py`, `wings2.py` | Gem wings and whole layered wings on a liquid bone. |
| `wisp.py` | The organic layer. Inside `with wisp.organic():` the shared stroke helpers bow, swell and taper instead of drawing even, straight lines. Keep it on. |
| `abdomen.py` | The carved insect abdomen (one tapering stroke with plate lines). |
| `detail.py` | Hand-finish details: engraved barbs, acanthus chasing, splitting hooks. Milgrain is in here too; leave it off. |
| `glass64.py`, `glassB.py` to `glassF.py`, `devel.py` | The worked collection: about a thousand registered pieces across rounds (stained-glass, motif-generated, influence studies, round 3 and 4 breeds, development passes). Read a few builders before writing your own. |
| `fidelity.py` | The photographic look (`LOOK=fidelity`): oxidised sterling, low sun with sky fill, white sweep that keeps the cast shadow, macro depth of field. See `render-fidelity.md`. |
| `make.py` | Build one piece: mesh, bridge floating metal, drop debris, print bodies and grams, then render (`preview`, `local4`), export (`stl`) or save a render-farm `.blend` (`farm`). `python make.py list` prints every piece. |
| `check.py` | Castability report over a folder of STLs. |
| `layer.py` | The insert-and-layer kit: `RingBlank` (plan coordinates on a ring blank), `crescent` (the sculpted element), `place`, `stipple`, `Packer` (flow-field placement, near-miss rule), `Gate`, `union`, `find_handles` and `close_handle` (tunnels), `bezel_cut`. See `insert-layer.md`. |
| `dome_layer.py` | Worked example for `layer.py`: the dome ring with a pinwheel of sweeps, stippled ground and a bezel. `python dome_layer.py <outdir>` writes the exact union as STL, JSON and NPZ (mesh plus ground mask). |
| `finish.py` | The DynaMesh step for a layer-kit piece: voxel remesh (`vox.py`), close each pinhole tunnel, remesh, repeat to genus 1, re-cut the bezel seats. |
| `vox.py` | Voxel remesh (Blender, OpenVDB) of a layer-kit mesh; keeps the main body and the ground mask. |
| `clipcheck.py` | Metal inside any stone's volume, for a layer-kit NPZ. |
| `thick.py`, `thin_class.py` | Wall thickness with radial rays, then the thin readings sorted into band edge, crevice and flap (check.py's normal rays misread relief). |
| `render_mesh.py` | Fidelity render of a layer-kit mesh; the ground mask takes the oxide. `PRES PSPP FSTOP SHARP ZOOM`. |
| `square.py` | Compose four views into the Instagram square. |
| `jlib.py` | Blender helpers: scene reset, the white studio. |

Piece names follow `<round>_<family>_<nn>`, for example `g4_vein_ring_03`. Families register as `(builder, view kind, count)`; the view kind (`flat`, `ring`, `cuff`, `hang`) picks the four camera angles.

## Enamel helpers (HELIUM kit; inlay v3, 25 Nov 2026)
- Colour is always a cast cell filled with cold enamel: read `enamel-cells.md`. `inlay()` (oval window) and
  `band()` / `coat()` (long pill down a tube) only record cells; `scripts/kit/cells.py` cuts them from the finished
  mesh with booleans and builds the enamel 0.1 mm under the rim. The old grazing-angle coat groove is retired.
- filigree(): a thin barbed tendril for fine linework against chunky forms.
