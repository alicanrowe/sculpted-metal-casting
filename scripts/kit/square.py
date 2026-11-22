"""Compose one Instagram square per piece: the hero view large on top, the three other
angles small underneath, pure white, no text.
    python square.py <render_dir> <out_dir>
Inputs: <piece>_v0001.png .. _v0004.png (farm frames, RGBA)."""
import sys, os, glob
from PIL import Image

S = 1080


def paper_alpha(im, white=None, soft=40):
    """Opaque renders on a white sweep (LOOK=fidelity): turn the paper into alpha so the piece and its
    cast shadow blend onto the page white, with no grey tile edge. The paper level is read from the top rows
    (the far sweep), so a darker exposure that keeps the silver from washing out still lands on page white."""
    lum = im.convert("L")
    if white is None:
        top = sorted(lum.crop((0, 0, im.width, max(4, im.height // 20))).getdata())
        white = top[len(top) // 2] + 3
    a = lum.point(lambda v: 255 if v < white - soft else max(0, int((white - v) * 255 / soft)))
    out = im.copy(); out.putalpha(a)
    return out


def soften_shadow(im, k=0.42):
    """LOOK=fidelity renders the sweep as a shadow catcher: the cast shadow comes out pure black at the shadow's
    opacity, and a hard sun makes that opacity 1. On paper a shadow is grey (the sky fills it), so scale the alpha
    of pure-black pixels by k (piece pixels are never pure black after the tone map)."""
    import numpy as np
    a = np.asarray(im.convert("RGBA")).copy()
    sh = a[..., :3].astype(int).sum(-1) < 6
    # ov4: a long shadow that runs off the render frame ended in a hard straight edge on the page. Fade the shadow
    # (never the piece) to nothing over the outer 14% of the frame, so it dies out softly wherever it reaches.
    H, W = a.shape[:2]; m = 0.14 * min(H, W)
    yy, xx = np.mgrid[0:H, 0:W]
    edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)) / m
    fade = np.clip(edge, 0, 1) ** 1.5
    a[..., 3] = np.where(sh, (a[..., 3] * k * fade).astype(np.uint8), a[..., 3])
    return Image.fromarray(a, "RGBA")


def fit(im, w, h, pad=0.06):
    if im.getchannel("A").getextrema() == (255, 255):
        im = paper_alpha(im)
    elif os.environ.get("LOOK") == "fidelity":
        im = soften_shadow(im)
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
