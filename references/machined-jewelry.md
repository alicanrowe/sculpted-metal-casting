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

## Round 2 lessons: liquid lines joined to turned parts
Round 1 was all prismatic CSG and the client called every piece ugly, even though the concept was loved. Round 2
fixed it by drawing the flowing part (here the oil) as SDF strokes that swell and taper (`oil.py`: `line`,
`sdf_part`), with the machine only at the nodes as small exact CSG parts, joined with exact booleans.
- `sdf_part` meshes, Taubin-smooths and merges into a Manifold. If marching cubes leaves a non-manifold vertex,
  re-mesh at a slightly shifted voxel size; drop crumbs under 0.5 mm3.
- Cut bores *after* the union, or the liquid line fills them and the spool clips.
- A stroke with a fast radius change shows creases at its segment joints, which read as little dashes in the
  render. Use more points (n 24) and a small joint blend (`kseg` 0.08).
- A flat polished face (a gear, a back plate) reflects the studio as one white sheet and the piece washes out.
  Turn fine V-grooves into the ground under it so the antique darkens it, and cross out gears with curved spokes.
- Antique finish: an AO-driven mix (dark in recesses only) reads far better than black-painted parts.
- A flat lozenge reads solid where a thin line with beads reads cheap: widen the line (r 4 or more, flat 3) and
  set turned parts flush into it inside a narrow groove.
- Check chains against famous designs: a link with a bar across its waist reads as one luxury house's anchor
  chain. Use your own device (here a crimped hose ferrule) and graduate the links so the chain itself swells.

## Round 3 lessons: real chain, one machined part, forged finish
Round 2 was still called ugly. The client pointed at a maker of plain men's chain bracelets: real cable, ball and
square-wire chain, or a plain heavy band, broken by one small machined part (a bar, a plate), hand-forged and
distressed with a grey patina. Round 3 followed that and dropped all liquid or sculpted form.
- **One disruption per piece.** The chain stays plain; a single gearbox part (spool bar, riveted ID plate, ring
  gear, detent ring) does all the talking. A second feature makes it a gadget again.
- **Model chain as it is photographed** (`chains.py`): exact CSG links (two half tori plus straight bars), reused
  by transform, laid in slots round a closed loop on the table. Neighbours lean +45 and -45 degrees about the
  chain's line so they sit 90 degrees apart, all at one common axis height. Pitch = 0.88 x mean inner length; a
  slot can set its own pitch.
- **The slot count must be even** or two neighbours share a lean and clip. Flip the clasp's lean to suit.
- **A straight bar or plate cannot sit on a curve:** flatten only the front half of the loop (superellipse `e`)
  or insert a true straight run (`straight`), and loosen the slack to about 0.97 for the slots each side of it.
- **A bar's lean must differ from its neighbour link**, and its eyes are links in the same alternation.
- **Flush ruby:** one 1.5 to 2.0 mm ball in a spherical seat with a swaged lip at 0.86 of the ball radius, so a
  little under half shows. A flat seat floor overlaps the ball.
- **Forged material:** ambient occlusion times a noise rub (keep the rub minimum near 0.72 or it reads as marble),
  dark base, hammer-dent and scratch bump. Machined parts stay brighter (`forged_hi`) so they read as the job.
- **Plain bands need a crown.** A flat leaf or flat-sectioned cuff read as sheet metal; a crowned, tapering
  section (D-section, rounded tip) lifted both by about two points.
- **Swept bands:** hull three consecutive section rings per segment, or a long sweep falls apart into hundreds of
  bodies.
- **Close-up hero view:** for a long necklace, frame the pendant with a 7-element view (direction, centre, size).
- **Measure every chain's length before the final render** (`loop.L` from `lay`). A men's bracelet wants about
  19 cm on the chain's line; two pieces came out at 15 and 16 cm and fit no wrist. Nested strands also need room
  between loops or the leaning links of one clip the next: grow the outer strand, not the inner one.
- **Fan-out jobs that share a temp kit folder must not run on one machine at once**; one job's setup deletes the
  other's kit. Run them one after another or give each its own folder.
