# Stone sourcing check

Run this before showing any piece. Every stone has to be something you can buy as a stock calibrated stone at that species and size.

    python scripts/check_stones.py --jewelry pieces.json        # kit units are mm
    python scripts/check_stones.py --furniture-cm pieces.json   # furniture kit units are cm (x10)

Verdicts:
- **OK:** a stock calibrated size.
- **LARGE:** sold only as a one-off collector stone. It will be hard to match, and pricing is per stone.
- **NO:** not realistically obtainable faceted at that size. Swap it.

Largest common calibrated faceted size, by species (rough sourcing guidance, Nov 2026, not quotes):

| Species | Stock up to | One-off up to | Rough $/ct | Notes |
|---|---|---|---|---|
| Amethyst, citrine (quartz) | 20 mm | 40 mm | 1-10 | Large clean stones are cheap. This is the go-to family for big stones. |
| Sky or swiss blue topaz | 18 mm | 35 mm | 1-8 | Treated. Large sizes are common. |
| London blue topaz | 16 mm | 30 mm | 2-15 | Treated. |
| Aquamarine | 10 mm | 18 mm | 15-300 | Price climbs steeply with size. Swap to sky blue topaz for size. |
| Garnet (almandine, rhodolite) | 10 mm | 14 mm | 5-60 | Large stones go nearly black. Use lab ruby for a big red. |
| Moonstone | 8 mm | 14 mm | 5-40 | Usually cut as a cabochon. Faceted stones are small. |
| Labradorite | 10 mm | 20 mm | 2-20 | Cut as a cabochon. |

Traps that have already happened:
- **Furniture scale.** The jewelry stone helpers think in mm. A furniture piece built in cm turns a "5" stone into 50 mm, about 450 ct. Cap furniture stones with STONE_CAP_CM (scripts/sawhorse/sawmoth.py), keep them round, and run the furniture check.
- **Big blue.** For a large blue stone, choose london or sky topaz. Never use a big aquamarine.
- **Cost.** At jewelry scale the cost driver is how many stones there are, not their size. Each stone is also a setting charge. Note the stone count on the sheet when it passes about 20.

## Furniture caps: snap in furniture units
`moira.prong` snaps rounds in mm and clips them to 1.5 to 10. In a cm furniture kit that turned every cap under 1.5 cm back into a 15 mm stone, so 1.0 and 0.8 cm caps didn't hold. The sawhorse's `_capped_prong` (scripts/sawhorse/sawmoth.py) now caps at `STONE_CAP_CM`, snaps down to a stock round in cm (`CAL_R_CM`, 1.5 to 20 mm) and sets it with `v2.claws` directly. Use the same pattern for any kit that isn't in mm, then confirm with `check_stones.py --furniture-cm` on the written stones json.

## Client colour preference (18 Nov 2026)
the client finds deep stones "a lil dark". Default to the light end of each species: rhodolite or malaya garnet over
almandine, sky or swiss blue topaz over london blue, pale (rose de France) amethyst, light aquamarine, morganite.
All of these are stock calibrated and cheap to mid-priced.
