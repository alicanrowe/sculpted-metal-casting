# Render fidelity: why real cast silver photographs look better than our renders

Written after the client held up a phone reel of a maker's real pieces (a carved feather-and-eye cuff, a
double-cupid pendant, filigree rings, a winged hand piece) and asked how to reach that fidelity (21 Nov 2026).
Those are photographs of real castings, not renders. That tells us what "fidelity" means here: a render has to
pass as a photo of a real, finished, worn piece of sterling. Every gap below is something the photo has that our
squares did not.

## The seven gaps, in order of how much each one costs us

| # | What the photo has | What our square had | Fix |
|---|---|---|---|
| 1 | **Oxidised finish.** Liver-of-sulphur black left in every recess, cut and undercut; high points rubbed back to bright, slightly worn polish. This is most of the "detail" you see: the black is what draws every feather barb. | One uniform near-mirror silver. Engraving only showed where it happened to catch a reflection, so fine detail vanished. | `kit/fidelity.py` `oxidised_sterling()`: mask = ambient occlusion over about 0.6 mm x convexity, broken up by a slow noise so it reads hand-rubbed. Default for any carved or engraved piece. A piece meant to be bright polished all over says so in its brief. |
| 2 | **Detail density at the 0.1 to 0.5 mm scale.** Hundreds of individual feather barbs, layered and overlapping, each one cut deep enough to hold black. Several depths of relief stacked (barbs over feathers over wings). | Big smooth swooping members, shallow engraving (often under 0.1 mm deep, which oxide can't fill and light can't find). | Carve to hold patina: engraved lines 0.15 to 0.3 mm deep with a V or U section, not scratched skins. Build at least three relief depths on the focal area. Mesh small pieces at VOX 0.027 or finer and keep `SMOOTH` at 3 or less, since mesh smoothing eats exactly this scale. Check in a 4x close-up crop before showing. |
| 3 | **One hard, low, warm light.** Late sun at about 20 to 30 degrees: crisp specular stars on high points, black shadow in every cut, a long cast shadow. | A soft white light tent. Great for e-commerce, but it flattens relief and makes silver read as grey chrome. | `sun_and_sky()`: a 1.2-degree sun at 22 degrees elevation, warm (about 5000 K), plus a sky fill whose lower band is dark so polished planes mirror something dark, the way they mirror asphalt outdoors. |
| 4 | **The piece sits somewhere.** A hand or a surface, a contact shadow, scale you can feel. | Floating on transparent then flattened to white: no shadow, no ground, no scale. | `white_sweep()`: the background stays white (the client's rule), but it is a real sweep that keeps the cast shadow. An in-hand or on-surface shot is a separate, optional hero that needs the client's OK, since it breaks the white rule. |
| 5 | **Lens.** Close focus with shallow depth of field: the near edge sharp, the far side softening. | Everything pin-sharp at 100 mm and infinite depth of field, which reads as CG. | Macro depth of field focused on the piece's centre. Scene units are mm, so `FSTOP 0.035` is about f/16 on a real macro. |
| 6 | **Resolution and samples.** Every barb resolves. | 720 px per view at 24 samples, then denoised, so micro detail smeared into mush. | Final squares at `PRESO 1400` or more and `PSPPO 96` or more with adaptive sampling. Previews may stay cheap; anything shown may not. |
| 7 | **Tone.** Deep blacks, bright clipped glints, a little warmth. | Standard or neutral AgX, mid-grey silver, no true blacks. | AgX Medium High Contrast, exposure about +0.4 on the white sweep. |

What does *not* close the gap: more bounces, a different HDRI on the same soft tent, or a sharper denoiser. The
first two rows are geometry and finish, and they matter more than all the lighting put together.

## How to use it
- `LOOK=fidelity PRESO=1400 PSPPO=96 bash scripts/render_square.sh <piece>` renders the four views with the
  photographic look; `square.py` turns the paper into alpha so the shadow blends onto the page white.
- Tuning is by env (see the top of `fidelity.py`). Start with the defaults; nudge `CAV_LO`/`CAV_HI` and
  `AO_LO`/`AO_HI` per collection, never per piece within a collection.
- Pointiness on its own fails on very dense meshes (every smooth convex surface reads as an edge; see the
  check-loop note). Here it only gates the cavity side and AO carries the mask, which held up at VOX 0.027.

## Check (add to every pass of the loop)
1. Put the hero next to a real photo of cast, oxidised sterling at a similar scale. Ask: could this pass as a
   photo? If no, name which row above fails.
2. Crop the focal area at 4x. Every engraved line must show as a dark line with a bright edge. If it shows as
   nothing, the cut is too shallow (row 2), not too dimly lit.
3. The background is white, but there is a cast shadow and the piece is not floating.
4. Flat open faces stay bright: if whole petals or blades go grey, the cavity window is too wide.

## Before/after (21 Nov 2026)
The worked example rendered one existing piece (a carved lotus pendant) both ways
from the same mesh and camera. The oxidised finish and the low sun alone made the engraved petals read; the
remaining gap was row 2 (the petal engraving is too shallow to hold much black), which is a modelling fix.
