# Insert-and-layer ornament (`scripts/kit/layer.py`)

Use this for dense, carved-looking ornament over a heavy form: signets, domed heads, wide bands, cuff fronts.
It is the method behind the best cast-silver CAD work we have studied: a plain heavy blank, a few ornament
elements sculpted once, and hundreds of copies laid on by hand in layers over a matte ground, then fused into
one body. The SDF kit's strokes can't reach that density and crispness; this kit can.

## What the reference maker does (and what we copy)
1. A paper sketch first: where the lead sweeps go and which way the whole surface flows.
2. A heavy, plain blank (signet, dome, thick band) built from simple deformed primitives.
3. An element library of two or three shapes, sculpted once: a crescent "swirl" that is pointed at both ends,
   swollen in the middle and round in section, and a fan or leaf for accents.
4. Placement by hand in tiers: a few big lead sweeps first, then medium strokes that follow them, then small
   fill. Each copy is its own group and can be scaled, bent and mirrored. Later strokes ride over earlier ones.
5. The ground left between strokes is stippled (a matte, pitted texture), so it holds the oxide and reads black.
6. Everything is fused into one mesh (DynaMesh, millions of points), then decimated for printing.

## The kit
- `RingBlank(Ri, band_w, band_t, Rh, drum, H, rim, edge_lo)`: the blank. `plan(a, x)` gives a point and normal on
  the outer surface, where `a` is arc length round the ring and `x` is arc length across the surface. Place in
  these plan coordinates, never in raw angles: equal steps then look equal on the dome and on the band.
  `stretch(a, x)` is the correction for the radius change between the bore and the surface.
- `crescent(L, W, H, bend, curl, ...)`: the element. The spine turns by `bend*u + curl*u^3` (a C with a hooked
  tail when curl has the other sign), the width profile goes to a point at both ends, and the section is a bell
  (`rnd=1.3`).
- `place(blank, V, a0, x0, rot, mirror, k)`: drapes an element over the blank. Every vertex goes through the plan,
  so a long stroke bends over the dome and down the shoulder instead of sticking out flat.
- `stipple(blank, V, mask_fn)`: the matte ground, a jittered grid of pits (never rows).
- `bezel_cut(zg, R)`: the seat of a bezel for a round stone (bearing cut to the pavilion's profile).
- `Packer`: the flow-field placement with spacing and the near-miss rule (below).
- `Gate`: an exact check of each element before it is kept: it must reach the blank and must not make a tunnel
  with it. (Its pair check, `pairs=True`, also refuses elements that make a tunnel with a neighbour. Leave it off:
  it threw out 55 of 309 elements, the lead sweeps among them, and the dome read as scattered sequins.
  `finish.py` deals with those tunnels instead.)
- `union(parts)`: one exact boolean (manifold3d batch union).
- `finish.py <piece_L.npz> <out_prefix>`: the DynaMesh step. It voxel-remeshes the union at 0.03 mm (`vox.py`),
  which closes the hairline pinholes, then finds each tunnel that is left (`find_handles`), closes it locally
  (`close_handle`: a 10 micron voxel closing with a 0.12 mm ball inside a 1 mm box, adding about 0.01 to 0.03 mm3
  each), remeshes again, and repeats until the genus is 1. Last it re-cuts every bezel seat exactly. Prints
  `FINAL genus ... PASS` or `FAIL`. Run it on every piece (about 10 minutes for the dome ring).
- `clipcheck.py <piece.npz>`: metal inside any stone's volume (must be 0).
- `thin_class.py <piece.npz>` after `thick.py`: sorts the thin readings into band edge, crevice between strokes,
  and flap (thin metal with air beyond). Only flaps matter; on the dome ring the only two were the bezel lip.
- `thick.py <piece.npz>`: thickness with radial rays (see "Checks" below).
- `render_mesh.py <stl> <json> <outprefix> [views]`: the fidelity render for a layer-kit mesh. It reads the NPZ's
  `ground` mask so the stippled ground takes the oxide hard and the polished strokes stand bright.
- `dome_layer.py <outdir>`: the worked example (the Bombyx dome ring redone). Read it before writing a piece.

## Placement order (from the worked example)
1. Corolla: a ring of short rays round the setting.
2. Lead sweeps: a pinwheel of 5 to 7 long strokes out from the setting, placed by hand (`force=True`).
3. Dome fill at two smaller scales, following a flow field (a swirl on the dome, tangent on the flank).
4. Flank: strokes sampled in arc between the rim moulding and 0.86 of the half-width.
5. Shank: three big S-sweeps per shoulder, mirrored four ways, then fill at three scales following a meander.
   Mirror candidates are checked against each other as well as against what is already placed.
Strokes that cross an earlier one get a little extra height, so the layering reads.

## Rules learned (dome ring, 22 Nov 2026)
- **The ring must come out at genus 1.** More means hidden tunnels: casting porosity, trapped investment, a weak
  spot. "One body, watertight" says nothing about them. The first pass came out at genus 334.
- **Undersides follow the ground.** An element's underside is a full row of points sunk `sink` below the
  surface across its whole width (`conform=True`, the default). A flat two-point chord bridged the curved shank
  and left air pockets under every wide stroke: one big S-sweep alone gave the ring genus 9.
- **Bury at varied depths.** Every element's buried part goes 0 to 0.06 mm deeper at random (`place(deep=...)`).
  All at exactly the same depth, overlapping elements share coincident faces under the ground, and the exact
  union turns those into slivers and pinholes.
- **Then remesh and close.** Even with every rule above, a dense layer unions to dozens of tunnels (84 on the
  final dome ring): the remesh leaves 9, two rounds of local closing leave none. Raising the ground under them
  does not work: most sit 0.1 to 1 mm up, where two strokes lean together.
- **Cut the stone's bearing to the pavilion.** A flat ledge under a bezel put 0.66 mm3 of metal inside the stone,
  and a straight cone still put 0.1 mm3 in (the brilliant's pavilion is fuller near the girdle). `bezel_cut` uses
  the pavilion's own profile, 1.5% oversize, and `finish.py` cuts it again after the remesh. Run `clipcheck.py`.
- **Fuse or stay clear, never nearly touch.** Two strokes whose closest gap is between -0.12 and +0.10 mm leave a
  hairline crevice that closes into a pinhole. The Packer refuses those pairs, measuring tips at their true width.
- **Edges dive 0.15 mm under the ground** (`EDGE_DIVE`), deeper than any stipple pit. An edge lying on the blank
  leaves coincident skins; one passing over a pit leaves a tunnel.
- **Fix the winding after mirroring.** Mirrored elements come out inside out and silently vanish from the union.
  `to_manifold` flips any mesh with negative signed volume.
- **Drop zero-volume slivers** after the union (decompose, keep bodies over 0.01 mm3), then re-union.
- **Keep elements inside 0.87 of the half-width** and check both footprint edges (`edges_ok`), or tabs stand off
  the edge of the head.
- **Bell section, no grooves.** A flat-topped section reads as stamped sequins; a groove down the middle reads as
  streaks. Slim, long strokes read carved; short wide ones read like scales.
- **Smooth shading.** Render with `SHARP=180`. Auto-sharp at 40 degrees breaks the bell sections into facets.

## Checks
- `check.py` misreads this mesh: its rays go along the surface normal, so on relief they measure across a ridge
  and report 0.16 mm walls that are not there. Use `thick.py` (radial rays from outward-facing points) for the
  wall, and the genus for hidden holes.
- `check_settings.py` and `check_stones.py` work as for any piece (the builder writes the stone JSON).
- The clipping check still runs on every design: metal clear of the stone's crown and pavilion.
- Weight: dense layering adds metal fast (the dome ring went from 3.1 g to about 9.5 g). Say the weight in the
  report and core out the head from inside if the brief has a budget.

## Hard-surface lessons (for machined pieces, from a three.js robot-eye comparison)
The best of three AI-built hard-surface models won on: real internal parts you can see (lens stacks, gears,
boards, wire runs), panel seams and small bevels on every edge, polished chrome against black with one warm
accent metal, a soft studio light with a contact shadow, and an exploded view that shows how it goes together.
See `machined-jewelry.md`.

## Linked units (from a brooch reel)
One small cast unit (a four-petal form with a centre vein), repeated in a grid and linked by jump rings so the
piece moves; satin finish; hung from a stick pin with a screw-on end cap. Cast the unit once, check it alone,
then check the jump-ring clearances. See `buildable.md`.
