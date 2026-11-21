# Physics: does it stand, and does it hang right?

Two checks borrowed from game-engine physics (Bullet, which Blender and Ammo.js both run). Both happen before the
render, on the cloud machine, never on the client's own computer.

## 1. Rest check (every piece that stands or lies on something)
`python scripts/check_rest.py MODEL --units mm|cm|m|in --up z|y --feet N` (needs `pip install trimesh numpy scipy shapely`)

A rigid piece on a flat floor rests on its lowest points. It stands still only if its centre of mass falls inside
the polygon those points make, and it rocks if a foot it should stand on hangs above the floor. The script finds the
feet (patches of bottom faces), the gap under each, the footprint, the centre of mass (uniform density, solid
volume for watertight parts) and the lean at which it tips over.

- **FAIL ROCKS**: one of the N feet is more than `--tol` (0.3 mm) off the floor. A table with one leg 1.5 mm short
  rocks across the diagonal. Level the feet in the model.
- **FAIL TIPS OVER**: the centre of mass is outside the footprint. **FAIL ROLLS**: it touches on a point or a line.
- **WARN TIPPY**: tips at under 10 deg of lean. For seating, the full tipping check is the seating-load-check skill.
- A Blender GLB is metres, Y up (`--units m --up y`). Run it on the exact file the render uses, in the pose the
  render shows it in, so a render never shows a piece standing in a way it can't.
- Tested 21 Nov 2026: a level 4-leg table passes; the same table with one leg 1.5 mm short fails ROCKS; a lamp
  with its head hung off a 30 mm base fails TIPS OVER; the Krenov sawhorse vB passes (tips at 14 deg).

## 2. Settle anything that hangs or drapes (chains, cords, straps, a pendant on a form)
Never hand-pose drape. A hand-placed chain floats off the neck in one spot and sinks into it in another, and a
hand-bent strap reads stiff. Let the simulator place it, then check it:

1. In Blender (headless, `blender -b -P`), make the body, form or stand a **passive** rigid body (mesh shape) or a
   cloth **collision** object. Chains: each link an **active** rigid body (convex hull), with the links' own
   geometry interlocked, no constraints needed; mass from the metal (sterling 10.36 g/cm3). Cords and straps: a
   cloth sim on the strap mesh with the leather or cord thickness, pinned where it attaches (a vertex group).
2. Bake 120 to 250 frames at the scene's real scale (scale applied, 1 unit = 1 m) until it stops moving, then apply
   the last frame as the pose (`Apply > Visual Transform`, or apply the cloth modifier) and save a new version.
3. Run the clipping check on the settled pose (metal through skin or glass, cord through ferrule). A sim with too
   few substeps lets thin parts tunnel; raise substeps (rigid body world: 20 to 60; cloth quality 10 to 15) rather
   than pushing parts apart by hand.
4. The settled pose is what the render, the reel and the site viewer all show.

This is about posing what really hangs. It doesn't loosen the taste rule that nothing thin dangles, flaps or floats
free in the design itself.
