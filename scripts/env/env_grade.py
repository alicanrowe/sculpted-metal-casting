"""Reel-style finish for env renders: halation bloom, soft vignette, black point, slight warm/cool split, film grain.
python3 env_grade.py in.png out.png [strength 0..1]"""
import sys, numpy as np
from PIL import Image, ImageFilter
src, dst = sys.argv[1], sys.argv[2]; k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
im = Image.open(src).convert("RGB"); W, H = im.size
a = np.asarray(im).astype(np.float32) / 255
lin = a ** 2.2
# halation: blur only the bright part, tint it warm, add back (the reel's skylight glow)
hi = np.clip(lin - 0.8, 0, None)
def fblur(ch, f):  # float blur by down/up-sampling (no 8-bit banding)
    im_ = Image.fromarray(ch.astype(np.float32), "F"); sm = im_.resize((max(1, W // f), max(1, H // f)), Image.BILINEAR)
    return np.asarray(sm.resize((W, H), Image.BICUBIC)).astype(np.float32)
blur = np.stack([0.5 * fblur(hi[..., c], 12) + 0.5 * fblur(hi[..., c], 32) for c in range(3)], 2)
lin = lin + k * 0.35 * blur * np.array([1.0, 0.9, 0.8])
# vignette (oval, soft)
yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.48) / (H / 2)) ** 2)
lin *= (1 - k * 0.38 * np.clip(d - 0.35, 0, None) ** 1.6)[..., None]
out = np.clip(lin, 0, 1) ** (1 / 2.2)
# black point + gentle S, warm highlights / cool shadows
out = np.clip((out - 0.025 * k) / (1 - 0.025 * k), 0, 1)
out = out + k * 0.06 * (out - 0.5) * (1 - np.abs(out - 0.5) * 2)
lum = out.mean(2, keepdims=True)
out = out + k * (lum - 0.5) * np.array([0.018, 0.0, -0.018])
# grain: luminance grain, stronger in mids, like the reel's fine film texture
rng = np.random.default_rng(1); g = rng.normal(0, 1, (H, W, 1)).astype(np.float32)
g = np.asarray(Image.fromarray(((g * 0.25 + 0.5).clip(0, 1)[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32)[..., None] / 255 - 0.5
out = out + k * 0.07 * g * (0.4 + lum * (1 - lum) * 2.4)
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(dst)
