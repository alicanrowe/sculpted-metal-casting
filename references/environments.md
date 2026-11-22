# Environments: scenes around the pieces (reels, worlds, landscapes)

Studio squares use the white tent in `render-fidelity.md`. This file is for everything else: a world built around
the work for a reel or a hero still (the reel's grass field and river, a room, a landscape). It came from
breaking down a reference reel of furniture shown in rendered 70s interiors (a Blender room series: one skylight,
deep falloff, a satin teal floor, film grain). We measured it frame by frame, then rebuilt a frame of our jewelry reel (white grass, black river, black sky) with
the same techniques (22 Nov 2026). The old v10 look (even grey light, a 16 mm lens, the camera hovering over the
grass) read flat and CG next to it. Every rule below fixed something on that side-by-side.

Worked example: `scripts/env/field_env.py` (scene, `before` or `after` look) and `scripts/env/env_grade.py`
(finish). Tone guard: `scripts/env_check.py`.

## What makes the reference look expensive
1. **One motivated light, and everything else falls off.** Every room has one source (a skylight, a cove, a slot),
   and the light dies off into near-black. There is no fill you can see and no even ambient light.
2. **Exposed for the highlights, with shadows that keep their detail.** The skylight clips and the floor near the
   camera sits at about 5 to 7% luminance. It's dark, but you can still see the floor, so it isn't crushed.
3. **A satin mirror floor.** Roughness of about 0.1 to 0.2, with a soft pool of the light and blurred reflections of
   the objects. It doubles the light and anchors the objects.
4. **Low camera, normal lens.** The camera sits at about seat height, with a 24 to 35 mm look. The compositions are
   one-point or symmetric, and 30 to 50% of the frame is dark negative space.
5. **Two colours that fight**: warm rust wood against cool teal. Everything else is neutral.
6. **Material detail you only notice up close**: vertical fluting, speckled floor texture, worn edges. It reads as
   "real" before you know why.
7. **A film finish**: fine luminance grain, halation glow around the brightest source, a soft vignette, warm
   highlights and cooler shadows. Slow gliding camera moves with motion blur.

## Rules for our environments
**Light**
- One key, aimed. Use an area light with `spread` at 25 to 40 deg to throw a pool on the subject's ground. The pool
  should fall off before the frame edges and before the horizon. Keep fill at 5% of the key or less, from the
  camera side, slightly cool.
- **Light-link the key off mirror surfaces** (water, polished floors): `light.light_linking.receiver_collection`
  = everything except the water. The river then mirrors the lit grass and the piece, not a blown-out disc of the
  lamp. Don't use `visible_glossy = False` on the key instead: the silver loses its highlight.
- **Silver needs something to reflect.** On a black-sky scene, give the world a faint top-lit gradient that
  camera rays can't see (Light Path > Is Camera Ray > 0). Without it, polished silver reflects the red or black
  water and renders red or grey.
- Thin things pass light: grass and petals get a transmission weight of about 0.35, so backlit blades glow.
- Grazing back-light makes dark rough ground glint white. Set the soil's `Specular IOR Level` to about 0.05.

**Atmosphere**
- Use **ground-hugging mist only**: a volume whose density falls off with height,
  `0.02 * exp(-z / 0.14 m)`, anisotropy 0.6. A box of even fog lights up the whole sky grey and breaks the
  black-sky look.
- The jewelry reel's sky stays black with no clouds (client direction, 21 Nov). Depth comes from the light pool, the mist and
  defocus, not from a sky.

**Ground and scatter**
- Build grass as mesh blades from numpy (3 tapered segments, random lean, height and width), not hair particles:
  665k blades build in seconds. Hair particle length set from Python in Blender 4.2 gave metre-long strands.
  Keep blades denser near the camera and thin them with distance.
- Vary every instance: tone 0.45 to 1.0 (as a colour attribute), height and lean. Make about 6% tall tufts that
  break the horizon line. Without tone variation, the lit pool reads as a flat white carpet.
- Ground under the scatter follows the same height function as the blades, so nothing floats at the river banks.
- Run the clipping check on the piece and anything it touches. The scatter must not pass through the piece.

**Camera**
- Put the camera low, at about 0.3 to 0.7 m for a human-scale field, or at the eye height of the subject's
  world, with a 28 to 35 mm lens. 16 mm bends the horizon and shrinks the piece.
- Use one leading line into the pool (river, path, row of columns). Put the piece in the pool, with 40 to 50%
  negative space above it.
- Depth of field at f/2.8, focused on the piece. Let the foreground blades go soft so they frame the shot.
- For motion: slow constant glides (dolly or crane), one move per shot, with motion blur on for finals. Check what
  motion blur costs on the farm first (see "Environment scenes" in the `render-farm` skill).

**Finish** (`env_grade.py`, after the render, before captions)
- Use AgX with the Medium High Contrast look in Blender. Then in post: halation bloom from highlights over 0.8
  linear, blurred in float (an 8-bit blur leaves a visible box around small bright pieces), an oval vignette, a
  small black point, a warm/cool split, and luminance grain that's stronger in the midtones.
- The grade goes on every frame of a reel the same way. Never grade one shot by eye.

## The check loop for an environment
1. Render a 405x720 test at about 48 spp on a cloud machine (about 1 to 2 min on 4 cores). Never render on the Mac.
2. Grade it, then put it side by side with the named reference frame and with the current version of our scene.
3. Run `python3 -I scripts/env_check.py OURS.png REF.png`. Fix any CRUSHED, GREY or CLIPPED flag. The numbers are
   a guard. The side-by-side is the verdict.
4. Go through these questions one at a time. Where is the one light? Does it fall off before the edges? Is the
   lamp itself mirrored anywhere? Does the silver read as silver? Is the sky still black? Does the lit grass show
   blades? Is anything floating or clipping?
5. Fix it, re-render, and repeat. Only a frame that passes gets rendered at full size or sent to the farm.

## Excuses that don't count
| The excuse | What to do instead |
|---|---|
| "It's lit, you can see everything" | Seeing everything is the flat look. Use one key with a pool, and let the rest fall off. |
| "A bit of fog will add depth" | Use height-falloff mist only. A fog box turns a black sky grey. |
| "The water reflection is just bright" | Light-link the key off the water. A mirrored lamp disc is a fail. |
| "Wide lens shows more of the world" | Use 28 to 35 mm, low. 16 mm bends the horizon and shrinks the piece. |
| "Grain/bloom is a gimmick" | It's what separates the reference from a CG frame. Run `env_grade.py` on every frame, the same way each time. |
