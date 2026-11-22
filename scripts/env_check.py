#!/usr/bin/env python3
"""Tone check for an environment frame against a reference frame (the "does it hold the light like the reel" test).

    python3 -I env_check.py OURS.png [REF.png]

Black sky is left out of the tone numbers (pixels under 0.5% luminance), so a black-sky scene is judged on
its ground. Reports: black share, shadow floor (25th percentile of the rest), key (90th percentile), contrast
(key / floor), 99th-percentile highlight, clipped share, and the vertical light profile (mean luminance per
fifth of the frame, top to bottom).

Hard flags (exit 1):
  CRUSHED   shadow floor under 0.01: shadows are dead black with no detail (the earlier v10 grass-field reel frames
            measured 0.012; the reference reel's rooms never went under 0.015)
  GREY      shadow floor over 0.25: nothing falls off into shadow
  CLIPPED   more than 2% of pixels at 255: blown water, glass or lamp reflections

The numbers are a guard, not the verdict. Flat, directionless light can still pass them (calibrated on 16 frames
of the reference reel, 22 Nov 2026: contrast ran 1.7 to 16 because a skylight in frame lifts everything), so the
side-by-side look at the reference stays the real check. Pass REF to print its numbers beside ours.
"""
import sys
import numpy as np
from PIL import Image


def stats(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    rest = lum[lum > 0.005]
    floor = float(np.percentile(rest, 25)) if rest.size else 0.0
    key = float(np.percentile(rest, 90)) if rest.size else 0.0
    rows = np.array_split(lum, 5, axis=0)
    prof = [float(r.mean()) for r in rows]
    clipped = float((a.max(2) >= 0.999).mean())
    return {
        "black_share": float((lum < 0.08).mean()),
        "median": float(np.median(lum)),
        "p99": float(np.percentile(lum, 99)),
        "floor": floor,
        "key": key,
        "contrast": key / (floor + 1e-4),
        "profile": prof,
        "clipped": clipped,
    }


def flags(s):
    f = []
    if s["floor"] < 0.01:
        f.append("CRUSHED")
    if s["floor"] > 0.25:
        f.append("GREY")
    if s["clipped"] > 0.02:
        f.append("CLIPPED")
    return f


def show(name, s):
    prof = " ".join(f"{p:.2f}" for p in s["profile"])
    print(f"{name}: black {s['black_share']:.0%}  p99 {s['p99']:.2f}  "
          f"floor {s['floor']:.3f}  key {s['key']:.2f}  contrast {s['contrast']:.1f}  clipped {s['clipped']:.1%}  rows[{prof}]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ours = stats(sys.argv[1])
    show("ours", ours)
    if len(sys.argv) > 2:
        show("ref ", stats(sys.argv[2]))
    fl = flags(ours)
    print("flags:", " ".join(fl) if fl else "none")
    sys.exit(1 if fl else 0)
