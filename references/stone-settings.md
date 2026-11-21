# Stone settings

## Calibrated sizes only
Every stone snaps to a stock calibrated size (`kit.calibrate`, `moira.prong`). Odd sizes can't be bought and the setter can't use them.
- Marquise: 4x2 to 8x4 mm
- Pear: 4x3 to 7x5 mm
- Round: 1.5 to 4 mm
- Oval: stock oval sizes from the same supplier list

## Which setting where
| Stone | Setting |
|---|---|
| Centre ovals, big rounds, drops | Claws (4 to 6), thorn-shaped, rising out of the strokes, not catalogue posts |
| Rounds 2 mm and under | Bead setting cut into the metal |
| Wing panes (marquise, pear, glass) | 0.7 mm open-backed bezel walls |

A 3.4 mm bead-set stone is wrong twice: it is over the 2 mm bead limit and not a stock size.

## Placement
- Stones sit where strokes converge, in the counter of a curl, or held by twig prongs that grow from the design.
- Stones never touch. Leave a wall between seats, and check the hero and top views for crowding.
- Avoid stiff symmetric grids of stones. Vary sizes inside a cluster and let one lead.
- Clear glass or pale stones can vanish on a white render. If a pane disappears, darken the bezel edge or raise the stone's absorption so it reads.

## Small pears at furniture scale (moth case gable motifs, 18 Nov 2026)
- A 6 x 4 mm pear on cm-kit claws fails `check_settings.py` HOLD: at that size the claws and the bail merge into
  2 or 3 holds, whatever the claw count (4, 5, 6 all failed). 7 x 5 mm with 5 claws passes. Use 7 x 5 as the
  smallest pear drop on furniture pieces; "unequal" drops differ in chain length and colour, not stone size.
- `v2.claws`' gallery ring sits about 0.3 to 0.4 mm inside the girdle of stones under 6 mm and fails CLEAR. After
  setting, cut a thin girdle band (ellipsoid L/2 x D/2 x 0.35 mm, op=1) at the girdle, as a setter would cut a
  seat (`gem()` in `moth-build/gems/moth_gems.py`).
- A bail cone that runs into the pear's tip buries the stone: stop it 0.5 mm above the tip.


## Crater bezels and sprinkles (HELIUM, 21 Nov 2026)
A crater bezel is a smooth rounded rim pulled up out of the surface around the stone, not a separate collet. It
reads as part of the piece. For 2 mm accent stones ("sprinkles"), sample the surface point and normal of the body
the stone sits on (not the piece's overall up), seat the stone along that normal, and keep it clear of any enamel.
