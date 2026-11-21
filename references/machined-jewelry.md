# Machined jewelry (the second kit)

Use this when the brief asks for precision machining, not carving: turned, milled, knurled, threaded parts, gears,
springs, screws. The worked example is a 12-piece collection after the valve body of an automatic gearbox
(`scripts/machined/pieces.py`). The sculpting kit (`scripts/kit/sdf.py`) cannot do this: an SDF rounds every edge
and a machined piece is all edges. So this kit is exact CSG (manifold3d), and the rules flip.

## What flips
- **Knurling, even rows, straight rods, constant sections and screw heads are the language here, not defects.**
  The carved-collection bans (bead rows, knurled rims, even tubes) apply to carved collections. In a machined
  collection the bans become: no fake machining (knurl that is a printed texture rather than cut teeth, a gear
  that could not mesh, a screw with no thread under it), no generic gadget look (random gears glued on), and no
  part without a job. Every detail is the real part's detail, sized like the real part.
- **Assemblies, not one body.** A piece is a list of separately made parts (rotor, spool, spring, screw, pin), each
  one solid, with clearances. The check is per part plus pairwise clipping, not "bodies 1".
- **Two-tone by finish, not by stone.** bright polished, satin, oxidised black (where the original is cast iron or
  friction lining), stainless for bought springs, pins and screws. Stones only where the real part has a ball:
  precision synthetic ruby or sapphire balls in stock sizes (3.175, 3.969, 4.763 mm ...), seated and held.
- **Finish zones are layers.** A bright chamfer on a black part, a niello inlay, a friction lining: model them as
  `layer=True` parts (same metal, different finish). They are not counted as bodies or walls, and are clip-checked
  only against the part they sit on.

## The kit (`scripts/machined/`)
- `mlib.py`: `lathe(profile)` (turning), `extrude` + `cut` (milling), `drill`, `knurl(kind="diamond"|"straight")`
  from crossed twisted star extrusions, `involute_gear2` (real involute teeth, internal too), `spline2`, `thread`,
  `hex_nut`, `socket_screw`, `helix_spring`, `chamfered_plate` (stepped offset slices that overlap 0.004 mm so they
  fuse), `edge_split` (black core + bright chamfers), `bend_cyl` (wrap a flat part round a wrist; drill holes after
  bending). `Piece.add(label, solid, finish, bought=, probe=, layer=)`, `Piece.ball(c, d, kind)`, `mirror_pair(dx)`.
- `gmake.py <piece> check|preview|local4|glb`: builds, runs the checks, writes STL/JSON, renders with the shared
  studio (`../kit/jlib.py`, `v2.py`, `square.py`), exports a web GLB. It needs `import bpy` for the wall check (BVH
  rays; the trimesh ray check runs out of memory on a bangle).
- Checks, all must pass: every part one closed body; no two parts overlapping (exact intersection volume under
  0.001 mm³); walls at least 0.5 mm at the 5th percentile (the min is printed too, and is always tiny at sharp
  edges: do not chase it), with knurl and gear teeth measured on a `probe` solid without texture; bought parts
  skipped; every ball a stock size, overlapping no metal, seated, and held (it cannot escape along any of 98
  directions).

## Lessons (Nov 2026)
- Mirrored polygons come out empty (winding flips): use `CrossSection.mirror` or reverse the point order.
- A swept-pin gerotor leaves a ring of debris outside the rotor: keep the largest component.
- Bent layers need a 0.012 mm gap or their chords overlap; drop zero-volume slivers before the clip check.
- Black parts read as flat grey holes in a render: give every oxidised part bright cut chamfers (`edge_split`) and
  remove the studio's front-low grey card (`drop_front_flag`), or it reflects across every flat.
- Set Blender sharp edges with bmesh at 32 degrees; smooth shading on CSG gives smeared highlights.
- Renders are fast (30 to 70 s per square at 800 px, 48 samples), so the fan-out is about machine setup, not render time.
- Pick piece types from the brief, one per working part, and never two of a type: the collection read as a set of
  parts from one machine, not a set of rings (see the sameness check in `check-loop.md`).
