# Production and delivery: who makes what (client Q&A, 18 Nov 2026)

Use this when designs are final and the client asks how to get them made and shipped. Nothing here is a quote;
re-check lead times and prices with real quotes when the designs are ready. Never upload files, create accounts
or place orders without the client's explicit OK (it spends money and shares the designs).

## Split of work
| Part | Who makes it | Client does |
|---|---|---|
| Furniture frames (17-4PH H1150, investment cast from printed patterns) | Xometry (client's preferred vendor, used before). Casting RFQ: upload STL/STEP, state alloy, heat treat H1150, finish | Nothing to the metal |
| Frames too big for one print (printed maraging steel) | Xometry prints in sections and welds/grinds/finishes as one part (write that on the RFQ). Fallback: redesign the split as hidden stainless bolted joints | Client cannot weld: never leave a weld for them |
| Small castings on straps (buckles, toggles) | Same Xometry order | Fit to straps |
| Jewelry in sterling | Kaprielian (NYC, upload STL/3DM, rush 3-5 business days, standard 7-10, human-reviewed, no API). Fallback i.materialise (instant quote, ~8 business days + shipping from Belgium, max 88 x 88 x 125 mm) | Buy the stones and ship them to the caster |
| Stone setting, jewelry | Caster's setter (Kaprielian: prong, bezel, pave, channel) | - |
| Leather seats and straps | Client, by hand | Print patterns, make cardstock templates, cut and stitch |
| Bought hardware | McMaster-Carr: felt or nylon glides (~20 mm) for feet, screws, turnbuckles/rods | Screw on |

## Rules that came out of this
- **Stones on steel furniture.** Do not set stones in steel claws: hardened 17-4PH won't bend over a stone and the
  H1150 age (~620 C) would cook topaz and amethyst. Make each furniture stone a small separate sterling cup, cast
  and set by the jewelry caster, that screws into a threaded socket cast into the frame. Design the sockets in once
  the client OKs the change.
- **Nothing the client must weld or sand.** Everything joins by screws or bolts with hand tools. Ask the vendor for
  the finish (blasted matte is standard; mirror polish on carved frames is costly hand work: quote it as a line item,
  fallback a local metal polisher).
- **Leather patterns.** Flatten seat and straps to 1:1 PDFs with stitch lines, slots, holes and leather thickness
  (3 mm / 7-8 oz veg-tan straps). Put a 10 cm test square on every page. Offer both one true-scale sheet
  (engineering/blueprint print at a print shop) and letter-size tiles with alignment marks.
- **Stone shopping list.** Output species, cut, calibrated mm size and count per piece; buy from GemSelect (online)
  or a wholesale coloured-stone dealer, ship straight to the setter.
- **Instant-quote limits.** Shapeways, i.materialise, Sculpteo, Craftcloud are small-part services; Protolabs' largest
  metal printer (~800 x 400 x 500 mm) is still too small/costly for a ~80 x 36 x 76 cm frame. Furniture frames need an
  RFQ (Xometry) or a foundry with 3D-printed sand molds (ExOne sand network, molds in 3-5 days) if the alloy allows sand casting.
- **Automation.** Shapeways and Sculpteo have upload/order APIs; Craftcloud, Xometry and i.materialise have web upload
  only. In practice: prepare files, fill the forms, client approves the order.

## The jeweler package (Bombyx, 21 Nov 2026: "reaching out to a jewler with CAD files and stones selected?")
A collection isn't finished until each piece can go to a caster and setter as is. The package holds, per piece:
- **Casting STL**: watertight, one body (an earring pair is two files' worth in one STL: two bodies, cast as two),
  in mm, zipped. Decimate the voxel mesh with a quadric simplifier only while it stays watertight, one body and
  within 0.3% of the original volume (`cast_export.py`); jewelers want tens of MB, not hundreds.
- **Stone sheet**: species, cut, calibrated mm size, count and setting type (claws, bezel, bead) per piece, from the
  piece's stone JSON. The client buys and ships the stones to the setter, who sets after polish.
- **Findings**: earring drops get a cast loop (about 2 mm inside) for a bought French ear wire; studs get a flat pad
  for a soldered post and butterfly; hair clips get two flat solder pads for a bought French barrette (pad spacing
  matched to a stock length). Name the stock part and its metal.
- **Metal and finish**: sterling 925 (or brass for a cheaper first run), lost-wax cast, high polish on raised
  surfaces, light oxidise in engraved veins if wanted. Minimum section 0.4 to 0.5 mm at points, 0.8 mm on wires and
  claws; flag anything thinner for the caster.
- **README** saying what's in the folder and the order of work: cast, clean up, solder findings, polish, set, final polish.

## Rough timing (Nov 2026 estimates, not quotes)
- Investment-cast 17-4PH frames: 5 to 8 weeks to the door. Sand cast (if alloy allows): 3 to 6 weeks.
- Sterling jewelry: about 1 to 1.5 weeks via rush; 2.5 weeks via i.materialise.
- Crated 30-50 kg frame ships by ground parcel (FedEx Ground takes up to ~68 kg) in 2 to 3 days within the US Northeast.

## Before ordering
1. Export repaired STLs (jewelry meshes had non-manifold edges; frames must pass the watertight edge check).
2. Get the client's OK on the stone-cup sockets.
3. Get the client's OK before any upload or quote request.
