"""Planted cases for check_members.py (Bombyx review 2, 21 Nov 2026). Each fault the client found by eye is
built here in miniature; the check must flag the bad one and pass its clean twin.
run: python3 scripts/tests/test_check_members.py"""
import os, sys, math
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_here), "kit")); sys.path.insert(0, os.path.dirname(_here))
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/nbcache")
import numpy as np
import sdf, moira as Mo
import check_members as CM
CM.a.ring_r = 9.0
fails = 0


def kinds(s, st=(), kind="flat"):
    return sorted({f["kind"] for f in CM.check_scene(s, list(st), kind, band_rows=1)})   # the band is drawn first


def expect(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(("ok  " if ok else "FAIL"), name, "got", got, "want", want)


# NUB: a stroke that stops blunt in air ("this nub in buyao is ugly") vs one drawn to a point
s = sdf.Scene(); s.ellipsoid((0, 0, 0), (4, 4, 1.2), k=0.5)
s.stroke(np.array([(2, 0, 0.5), (6, 0, 0.6), (10, 0, 0.6)]), np.array([0.9, 0.85, 0.8]), k=0.4)
expect("blunt cap in air", kinds(s), ["NUB"])
s = sdf.Scene(); s.ellipsoid((0, 0, 0), (4, 4, 1.2), k=0.5)
s.stroke(np.array([(2, 0, 0.5), (6, 0, 0.6), (10, 0, 0.6)]), np.array([0.9, 0.6, 0.2]), k=0.4)
expect("stroke drawn to a point", kinds(s), [])

# CROSS: a stem laid over a carved leaf away from its root ("zhang qians vine") vs a stem leaving the root
leaf = lambda s: Mo.feather(s, np.array([0.0, 0.0, 0.3]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0]), L=20, W=6, notches=0)
s = sdf.Scene(); leaf(s)
s.stroke(np.array([(-6, 11, 0.6), (0, 11, 0.8), (6, 11, 0.6)]), np.array([0.2, 0.7, 0.2]), k=0.3)
expect("stem across the leaf face", kinds(s), ["CROSS"])
s = sdf.Scene(); leaf(s); s.ellipsoid((0, 0, 0.6), (1.6, 1.6, 0.9), k=0.5)     # the root knot
s.stroke(np.array([(0, 0.3, 0.5), (0.3, -4, 0.4), (0.5, -8, 0.4)]), np.array([0.7, 0.6, 0.2]), k=0.3)
expect("stalk leaving from the root", kinds(s), [])

# BOLT: a short needle cone started inside a wide body ("feitan needs more smoothing") vs the body's own taper
s = sdf.Scene(); s.ellipsoid((0, 0, 0), (3, 3, 1.0), k=0.3); s.cone((2.4, 0, 0), (5.5, 0, 0), 0.5, 0.1, k=0.2)
expect("needle bolted on a body", kinds(s), ["BOLT"])
s = sdf.Scene(); s.stroke(np.array([(-3, 0, 0), (0, 0, 0), (3, 0, 0), (6, 0, 0)]), np.array([0.3, 1.5, 0.8, 0.12]), k=0.3)
expect("member tapering to its own point", kinds(s), [])

# HOLE: metal below the band's inner face ("spikes in the finger hole") vs a motif on top of the band
def band(s):
    s.torus((0, 0, 0), 9.9, 0.9, normal=(0, 1, 0))
s = sdf.Scene(); band(s); s.sphere((0, 0, 11.2), 1.6, k=0.3); s.sphere((7.5 * math.sin(1.0), 0, 7.5 * math.cos(1.0)), 1.0, k=0.3)
expect("bead inside the finger hole", kinds(s, kind="ring"), ["HOLE"])
s = sdf.Scene(); band(s); s.sphere((0, 0, 11.2), 1.6, k=0.3)
expect("motif on top of the band", [k for k in kinds(s, kind="ring") if k == "HOLE"], [])

print("check_members tests:", "all passed" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
