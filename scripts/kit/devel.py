"""Development passes (Nov 18) on the client's picks: not more variations, the same piece made better.
Pass notes live next to each builder. Everything renders with the organic layer (wisp.py) on."""
import math
import numpy as np
from sdf import Scene
import wisp
from kit import Flat, Cyl, wing as kwing, lead
import sculpt as K
import moira as Mo
import motifs as M
import wings2 as W2
import glassE as E
import glassF as GF

F = Flat()
PIECES = {}


def body(s, m, st, c, size, pal, kind="butterfly", z=0.0, rng=None):
    """Sculpted insect body instead of a bead row on a stick.
    Thorax: one stone in a molten collar. Abdomen: a single liquid stroke, swelling in 5 soft segments,
    drawing to a needle (hyodomachine) and carved across each segment (Moira). Head: a bead the antennae grow from."""
    rng = rng or np.random.default_rng(0)
    c = np.asarray(c, float)
    D = size * 0.13
    Mo.prong(s, st, m.P(c[0], c[1] + size * 0.02, z + D * 0.55 + 1.0), D, pal[0], L=D * 1.35, normal=m.N(*c), spin=math.pi / 2, n=4,
             wire=max(0.3, D * 0.09))
    s.ellipsoid(m.P(c[0], c[1] + size * 0.02, z + 0.8), (D * 0.72, D * 0.95, D * 0.5), k=0.9)
    # abdomen: one carved tapering form with plate lines (abdomen.py), not beads
    from abdomen import abdomen
    L = size * (0.5 if kind == "butterfly" else 0.42)
    abdomen(s, m, c - [0, size * 0.04], (0, -1), L, size * 0.065, z=z + 1.0, rng=rng)
    # head and antennae
    hc = c + [0, size * 0.135]
    s.sphere(m.P(hc[0], hc[1], z + 1.2), size * 0.042, k=0.4)
    for sx in (1, -1):
        a0 = hc + [sx * size * 0.02, size * 0.02]
        ad = np.array([sx * math.sin(0.42), math.cos(0.42)])
        if kind == "moth":
            W2.mfeather(s, m, a0, ad, size * 0.28, z=z + 1.2, W=size * 0.05, bend=-sx * 1.2 / size, seed=float(rng.uniform(0, 40)))
        else:
            wisp.wisp(s, m, a0, ad, size * 0.42, w=max(0.32, size * 0.012), z=z + 1.2, curl=-sx * 2.2, bead=True, rng=rng)


def glass_wings(s, m, st, c, size, kind, rng, pal, z=0.0, sparse=True, p2=False):
    """Pass 1 fix: the forewing and hindwing used to sit almost level, so their straight inner edges and root veins
    lined up into a stiff bar across the body. Now the forewing lifts (~25 deg) and the hindwing drops (~30 deg),
    both roots tuck under the thorax, and the glass is sparse: a few large panes like pendant_03, not a mosaic."""
    fo, ho = GF.SHAPES[kind]
    sizes = ([("pear", 0.16, 0.1), ("marquise", 0.17, 0.075), ("round", 0.06, 0.06)] if sparse else None)
    tf, th = rng.uniform(0.36, 0.5), -rng.uniform(0.42, 0.58)
    if p2:   # pass 2: the 'bar' was the clip showing through; pass-1 tilts pinched the wings into a bow, so open them back up
        tf, th = rng.uniform(0.16, 0.28), -rng.uniform(0.3, 0.4)
    for mir in (False, True):
        sg = -1 if mir else 1
        for out, span, tilt, dy, k in ((fo, 0.56, tf, 0.03, 0), (ho, 0.46 if kind == "butterfly" else 0.4, th, -0.02, 1)):
            ext = np.ptp(np.asarray(out, float)[:, 0]); sc = size * span / ext
            sz = [(n, round(a * size * 2) / 2, round(b * size * 2) / 2) for n, a, b in sizes] if sizes else None
            kwing(s, m, st, outline=out, sx=sc, sy=sc, rot=sg * tilt, t=(c[0] + sg * size * 0.012, c[1] + size * dy), mirror=mir,
                  pal=list(pal[k:]) + list(pal[:k]), costa=max(0.7, size * 0.026), seed=int(rng.integers(1, 999)), sizes=sz,
                  thorn_tips=False, vein_w=max(0.38, size * 0.01))
    if kind == "butterfly":       # swallowtail wisps off the hindwings
        for sg in (1, -1):
            tip = np.array([c[0] + sg * size * 0.22, c[1] - size * 0.36])
            wisp.wisp(s, m, tip, np.array([sg * 0.25, -1.0]), size * 0.22, w=max(0.34, size * 0.012), z=z + 0.4, curl=sg * 1.8, rng=rng)


def d_butterfly_clip(seed, pal, kind="butterfly", p2=False):
    def build():
        rng = np.random.default_rng(seed)
        with wisp.organic():
            s = Scene(); st = []; size = 50.0
            glass_wings(s, F, st, (0, 0), size, kind, rng, pal, p2=p2)
            body(s, F, st, (0, 0), size, pal, kind=kind, rng=rng)
            if p2: E._clipbar(s, (0, size * 0.02), (0, -size * 0.36))      # hidden under the abdomen
            else: E._clipbar(s, (-size * 0.2, 0), (size * 0.2, 0))
        s.units = [0.0]; return s, st
    return build


def d_moth_cuff(seed, pal, shape="moth_f", p2=False):
    """Pass 1: the old cuff carried a second, smaller bug on top of its own wings (two sets of wings, muddled).
    Now the cuff IS the moth: the big vein wings wrap the wrist, a sculpted body sits at the top, and a graded
    bead spine (hyodomachine) runs down the cuff's centre line from the abdomen's needle."""
    def build():
        rng = np.random.default_rng(seed)
        with wisp.organic():
            s = Scene(); st = []; R = 29.0; m = Cyl(R)
            for sx in (1, -1):
                W2.vein_wing(s, m, st, (sx * 3.5, 3), rng.uniform(52, 58), ang=rng.uniform(0.05, 0.2), sx=sx, rng=rng, shape=shape,
                             stones=int(rng.integers(1, 3)), pal=pal, z=0.3)
                W2.vein_wing(s, m, st, (sx * 3.5, -1), rng.uniform(36, 42), ang=-rng.uniform(0.35, 0.5), sx=sx, rng=rng,
                             shape="moth_h" if shape != "dragon" else "dragon", pal=list(pal[::-1]), z=0.1)
            body(s, Flat(o=(0, 0, R + 0.2)), st, (0, 4), 36 if p2 else 26, pal, kind="moth" if shape == "moth_f" else "butterfly", rng=rng)
            # r4-fix3: the graded bead spine read as a bead string. Now one liquid stroke runs down the cuff from the
            # abdomen's needle, swelling once and drawing to a needle (hyodomachine), laid on the cuff surface.
            ys = np.linspace(-8.5, -24, 24)
            K.ribbon(s, np.array([m.P(0.6 * math.sin((y + 8.5) / 6.0), y, 0.5) for y in ys]), w=1.3, thin=0.6, ends=(0.0, 0.35),
                     wkeys=[(0, 0.6), (0.35, 1.2), (0.7, 0.75), (1, 0.4)], k=0.5)
        s.units = [0.0]; return s, st
    return build


PALS = GF.PALS3
DEV = {
    "d4_butterfly_clip_a": (d_butterfly_clip(2101, ["amethyst", "londonblue", "garnet"]), "flat"),
    "d4_butterfly_clip_b": (d_butterfly_clip(2102, ["londonblue", "aquamarine", "amethyst"]), "flat"),
    "d4_moth_clip_c": (d_butterfly_clip(2103, ["garnet", "amethyst", "citrine"], kind="moth"), "flat"),
    "d4_moth_cuff_a": (d_moth_cuff(3101, ["londonblue", "aquamarine"]), "cuff"),
    "d4_moth_cuff_b": (d_moth_cuff(3102, ["garnet", "amethyst"], shape="bfly_f"), "cuff"),
    "d4_moth_cuff_c": (d_moth_cuff(3103, ["aquamarine", "moonstone"], shape="fore"), "cuff"),
}
DEV.update({
    "d4_butterfly_clip_a_p2": (d_butterfly_clip(2101, ["amethyst", "londonblue", "garnet"], p2=True), "flat"),
    "d4_butterfly_clip_b_p2": (d_butterfly_clip(2102, ["londonblue", "aquamarine", "amethyst"], p2=True), "flat"),
    "d4_moth_clip_c_p2": (d_butterfly_clip(2103, ["garnet", "amethyst", "citrine"], kind="moth", p2=True), "flat"),
    "d4_moth_cuff_a_p2": (d_moth_cuff(3101, ["londonblue", "aquamarine"], p2=True), "cuff"),
    "d4_moth_cuff_b_p2": (d_moth_cuff(3102, ["garnet", "amethyst"], shape="bfly_f", p2=True), "cuff"),
})
PIECES.update(DEV)
