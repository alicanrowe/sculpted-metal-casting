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
| `make.py` | Build one piece: mesh, bridge floating metal, drop debris, print bodies and grams, then render (`preview`, `local4`), export (`stl`) or save a render-farm `.blend` (`farm`). `python make.py list` prints every piece. |
| `check.py` | Castability report over a folder of STLs. |
| `square.py` | Compose four views into the Instagram square. |
| `jlib.py` | Blender helpers: scene reset, the white studio. |

Piece names follow `<round>_<family>_<nn>`, for example `g4_vein_ring_03`. Families register as `(builder, view kind, count)`; the view kind (`flat`, `ring`, `cuff`, `hang`) picks the four camera angles.
