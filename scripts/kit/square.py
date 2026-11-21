"""Compose one Instagram square per piece: the hero view large on top, the three other
angles small underneath, pure white, no text.
    python square.py <render_dir> <out_dir>
Inputs: <piece>_v0001.png .. _v0004.png (farm frames, RGBA)."""
import sys, os, glob
from PIL import Image

S = 1080


def paper_alpha(im, white=246, soft=40):
    """Opaque renders on a white sweep (LOOK=fidelity): turn the paper into alpha so the piece and its
    cast shadow blend onto the page white, with no grey tile edge."""
    lum = im.convert("L")
    a = lum.point(lambda v: 255 if v < white - soft else max(0, int((white - v) * 255 / soft)))
    out = im.copy(); out.putalpha(a)
    return out


def fit(im, w, h, pad=0.06):
    if im.getchannel("A").getextrema() == (255, 255):
        im = paper_alpha(im)
    a = im.getchannel("A")
    bb = a.point(lambda v: 255 if v > 6 else 0).getbbox() or (0, 0, im.width, im.height)
    im = im.crop(bb)
    k = min(w * (1 - 2 * pad) / im.width, h * (1 - 2 * pad) / im.height)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    return im


def compose(views, out):
    cv = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    hero_h = 760
    h = fit(views[0], S, hero_h, 0.05)
    cv.alpha_composite(h, ((S - h.width) // 2, (hero_h - h.height) // 2 + 10))
    cw = S // 3; ch = S - hero_h
    for i, v in enumerate(views[1:4]):
        t = fit(v, cw, ch, 0.1)
        cv.alpha_composite(t, (i * cw + (cw - t.width) // 2, hero_h + (ch - t.height) // 2 - 6))
    cv.convert("RGB").save(out, quality=95)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
    names = sorted({os.path.basename(p).rsplit("_v", 1)[0] for p in glob.glob(os.path.join(src, "*_v0001.png"))})
    for n in names:
        fs = [os.path.join(src, f"{n}_v{i:04d}.png") for i in range(1, 5)]
        if not all(os.path.exists(f) for f in fs):
            print("missing views", n); continue
        compose([Image.open(f).convert("RGBA") for f in fs], os.path.join(dst, n + ".jpg"))
        print("ok", n)
