"""Presentation sheet for the Cast-metal sawhorse. python sheet.py <render_dir> <tag> <out.jpg>"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
D, tag, out = sys.argv[1], sys.argv[2], sys.argv[3]
FT = "/usr/share/fonts/opentype/inter/"
f = lambda w, s: ImageFont.truetype(FT + w, s)
W, H = 3000, 2000
sh = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(sh)


def put(k, box):
    im = Image.open(os.path.join(D, f"sawmoth_{tag}_{k}.png")).convert("RGBA")
    bb = im.getbbox(); im = im.crop(bb)
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    sh.paste(bg.convert("RGB"), (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))


d.text((90, 70), "MB-SH-01  REST", font=f("Inter-Light.otf", 64), fill=(20, 20, 20))
d.text((92, 150), "Cast-metal sawhorse, after the Krenov sawhorse. moiraxmel for hyodomachine.", font=f("Inter-Light.otf", 30), fill=(90, 90, 90))
put("hero", (60, 230, 1500, 1960))
cells = [("front", (1540, 230, 2240, 930)), ("side", (2280, 230, 2960, 930)),
         ("moth", (1540, 960, 2240, 1580)), ("top", (2280, 960, 2960, 1580))]
if os.environ.get("SEATOFF"):
    cells = [("hero_off", (1540, 230, 2240, 930)), ("front_off", (2280, 230, 2960, 930)),
             ("moth", (1540, 960, 2240, 1580)), ("top_off", (2280, 960, 2960, 1580))]
for k, b in cells: put(k, b)
notes = ["Cast and polished metal frame, black leather bolster on the original 29 1/4 in rail line (seat 31 1/2 in).",
         "Feet are carved crescents that curl up into needles. Legs are liquid and smooth, carving only at the base.",
         "Two horns rise from each leg and cradle the leather. The rail ends hook down into needles with beads.",
         "The stretcher is one moth with heavy vein wings, claw-set london blues in the forewings and thorax.",
         "The wing tips run into the legs, so the moth holds the frame. The abdomen is a carved taper, not beads.",
         "Leather: matte bolster, piped ends, two glossier straps with liquid metal buckles.",
         "The seat lifts straight off. Underneath is a flat working rail at the original height, so it still works as a sawhorse."]
y = 1620
for n in notes:
    d.text((1540, y), n, font=f("Inter-Regular.otf", 22), fill=(60, 60, 60)); y += 46
sh.save(out, quality=90)
print(out)
