# Enamel and colour on cast metal: cast cells

Client critique (25 Nov 2026, the hyperpop collection): the coloured fields "look kinda messy and unrealistic", and
the client could not tell how they would be made. The old helper lifted a tube and cut the balloon at a grazing
angle, so the colour ran over the curve to a feathered, uneven edge with no metal wall to hold it. No enameller
could fill that.

## The process (say it in these words to the client)
Every colour is cold enamel in a pocket cast into the metal, the way an enamel pin or champlevé enamel is made.
1. Cast the piece with the pockets already in it (printed wax, lost wax), polish, plate (rhodium on brass).
2. Then enamel: a two-part jeweller's cold enamel (Ceramit-type epoxy enamel) laid in with a fine syringe or
   spatula, two thin coats, cured in a low oven (makers quote about 93 to 120 °C) or at room temperature.
   Enamel after plating: epoxy put in before plating can lift off in the bath.
3. Set the stones last, so the oven and the setter's pressure never meet a finished stone.
Vitreous (fired) enamel does not suit brass (zinc bubbles it) and can't survive a later plating; stay with cold
enamel unless the metal is fine silver, copper or gold.

## The specs (hold them in the model)
| What | Spec |
|---|---|
| Pocket depth | 0.6 mm (enamel 0.5 mm) |
| Enamel surface | 0.1 mm under the rim line, following the curve; a 0.05 mm meniscus up the wall |
| Land of metal round each pocket | >= 0.8 mm (to a neighbouring pocket, a stone seat, a neck, a twist) |
| Metal under the floor to any hollow | >= 0.8 mm |
| Narrowest pocket | 1.2 mm |
| Walls | square to the surface (radial on a tube), never undercut |
Never let a colour wrap round a form or fade out at an edge: if a field wants to run further round, make the form
flatter or split the colour into two pockets with a wall between.

## The code
`scripts/kit/cells.py`. A piece records cells instead of cutting them: `band()` for a long pill down a tube's crown
(arc-length by arc-across footprint, radial walls), `inlay()` for an oval window on a lobe (walls along `up`, this
side only). After the metal is meshed and smoothed, `cells.apply(s, mesh, vox, stones)` builds each pocket and its
enamel from the outer skin SDF (hollows excluded) and cuts them with manifold3d booleans, so the rim stays sharp.
It checks clipping (enamel/metal volume), land (walks 0.4 and 0.8 mm along the skin from the edge: no drop-off,
other cell or stone seat), floor thickness over hollows and width; prints `cells PASS`.

Lessons from making it:
- Marching-cubes pocket meshes are huge (one 32 mm band: 6.7M triangles, a 15 GB machine killed). Simplify the
  hidden ones (`Manifold.simplify(0.003)`), but never the visible enamel top: thinned, it shows facet lines.
- Build each cell in its own forked process; the allocator kept chunk memory and a long band grew 0.3 GB a chunk.
- Mesh long bands in overlapping 4 mm chunks and union them; bound each grid round the crown, not the whole tube.
- A boolean can leave two vertices at one point; an STL welds them into a four-face edge. `from_man` nudges them.
- A non-watertight input mesh makes the boolean fail silently: repair it first (`repair_stl.py`).
- Pockets near a stone: keep the pocket's inner edge >= stone radius + roll + 0.8 mm from the stone axis.
- Show the client a cut-through drawing of one pocket (`section.py` in the collection kit): metal, enamel and the
  four numbers. It answers "how is this made" faster than a render.
