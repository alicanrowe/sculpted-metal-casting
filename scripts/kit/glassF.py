"""Round 3 (Nov 17): breed from the client's picks.
Picks: stained-glass round (split-wing barbell, crescent nest / bar, four roses, rose lancet, rose drop,
lancet drop) and round 2 (garnet moth with feather antennae, angel-wing barbell, vein rings, wing-cell
earring, angel ring, moth cuff). New: the glass bug, a moth / butterfly whose wing cells are glazed with
stones like the stained-glass pieces, carried on the hyodomachine bead body."""
import math
import numpy as np
from sdf import Scene
import wisp  # noqa: patches lead / nib / vein_wing before anything below binds them
from kit import PAL, Flat, nib, lead, spike, glaze, rose, lancet, lancet_outline, stalk, thorns, wing as kwing, \
    ear_wire, jump, bail, buckle_back, smooth, xform
import moira as Mo
import motifs as M
import wings2 as W2
import glassE as E
from glassB import crescent, split_wing
from glass64 import pair, bar

F = Flat()
PIECES = {}
PALS3 = [PAL["night"], PAL["bruise"], PAL["tide"], PAL["ember"], PAL["dusk"],
         ["garnet", "amethyst"], ["londonblue", "aquamarine"], ["aquamarine", "moonstone", "topaz"]]
SHAPES = {"moth": (W2.MOTH_F, W2.MOTH_H), "butterfly": (W2.BFLY_F, W2.BFLY_H)}


# ---------------------------------------------------------------- the glass bug
def glass_bug(s, m, st, c, size, kind, rng, pal, z=0.0, antennae=True, tail=True):
    """Head toward +y. Wings: kit stained-glass wing on moth / butterfly outlines; body: bead spine."""
    c = np.asarray(c, float)
    fo, ho = SHAPES[kind]
    tf, th = rng.uniform(0.0, 0.42), -rng.uniform(0.05, 0.5)
    jf, jh = rng.uniform(0.82, 1.18), rng.uniform(0.75, 1.25)     # seeds vary the silhouette, not only the stones
    for mir in (False, True):
        sg = -1 if mir else 1
        for out, span, tilt, dy, k in ((fo, 0.55 * jf, tf, 0.05, 0), (ho, (0.42 if kind == "moth" else 0.48) * jh, th, -0.06, 1)):
            ext = np.ptp(np.asarray(out, float)[:, 0])
            sc = size * span / ext
            kwing(s, m, st, outline=out, sx=sc, sy=sc, rot=sg * tilt, t=(c[0] + sg * size * 0.03, c[1] + size * dy),
                  mirror=mir, pal=pal[k:] + pal[:k], costa=max(0.6, size * 0.022), seed=int(rng.integers(1, 999)),
                  thorn_tips=rng.random() < 0.6, vein_w=max(0.35, size * 0.009))
    D = size * 0.12
    Mo.prong(s, st, m.P(c[0], c[1] + size * 0.02, z + D * 0.5 + 0.8), D, pal[0], L=D * 1.3, normal=m.N(*c), spin=math.pi / 2, n=4)
    s.ellipsoid(m.P(c[0], c[1] + size * 0.02, z + 0.6), (D * 0.6, D * 0.75, D * 0.4), k=0.5)
    s.sphere(m.P(c[0], c[1] + size * 0.13, z + 1.0), size * 0.04, k=0.3)
    if tail:
        tl = size * 0.42
        from abdomen import abdomen
        abdomen(s, m, c - [0, size * 0.04], (0, -1), tl * 1.1, size * 0.06, z=z + 0.9, rng=rng)
    if antennae:
        for sx in (1, -1):
            a0 = c + [sx * size * 0.02, size * 0.14]
            ad = np.array([sx * math.sin(0.45), math.cos(0.45)])
            if kind == "moth":
                W2.mfeather(s, m, a0, ad, size * 0.24, z=z + 1.0, W=size * 0.045, bend=-sx * 1.5 / size, seed=float(rng.uniform(0, 40)))
            else:
                wisp.wisp(s, m, a0, ad, size * 0.38, w=max(0.42, size * 0.014), z=z + 1.0, curl=-sx * 2.4, bead=True, rng=rng)


def g_bug_clip(rng, pal):
    s = Scene(); st = []; size = rng.uniform(40, 52)
    glass_bug(s, F, st, (0, 0), size, rng.choice(["moth", "moth", "butterfly"]), rng, pal)
    E._clipbar(s, (0, size * 0.02), (0, -size * 0.36)); s.units = [0.0]; return s, st


def g_bug_pendant(rng, pal):
    s = Scene(); st = []; size = rng.uniform(30, 38)
    glass_bug(s, F, st, (0, 0), size, rng.choice(["moth", "butterfly"]), rng, pal)
    bail(s, F, (0, size * 0.42), R=2.0, r=0.6); lead(s, F, [(0, size * 0.15), (0, size * 0.36)], r=0.5)
    s.units = [0.0]; return s, st


def g_bug_ear(rng, pal):
    size = rng.uniform(15, 19); kind = rng.choice(["moth", "butterfly"]); seed = int(rng.integers(0, 999))
    def one(s, m, st, sx):
        glass_bug(s, m, st, (0, -size * 0.45), size, kind, np.random.default_rng(seed), pal, antennae=False)
        lead(s, m, [(0, -size * 0.3), (0, -1.5)], r=0.45); jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, size * 1.25)


# ---------------------------------------------------------------- stained-glass picks, bred
def g_split_bar(rng, pal):
    s = Scene(); st = []; bar(s, F)
    sx = rng.uniform(0.62, 0.74); y = rng.uniform(1.0, 3.0); mir = rng.random() < 0.5
    split_wing(s, F, st, sx=sx, t=((16 if mir else -16), y), mirror_=mir, pal=pal, gap=rng.uniform(1.0, 1.8), costa=1.0,
               seed=int(rng.integers(1, 99)), sizes=[("marquise", 5, 2.5), ("pear", 4, 2.8), ("round", 2.5, 2.5), ("round", 2, 2), ("round", 1.5, 1.5)])
    for x in (-13, 13): lead(s, F, [(x, y), (x, 0)], r=0.55)
    return s, st


def g_split_brooch(rng, pal):
    s = Scene(); st = []; sx = rng.uniform(1.0, 1.3)
    split_wing(s, F, st, sx=sx, t=(-23 * sx, 4), rot=rng.uniform(-0.15, 0.15), pal=pal, gap=rng.uniform(1.8, 2.8), costa=1.4, seed=int(rng.integers(1, 99)))
    buckle_back(s, F, 40 * sx, 26 * sx); return s, st


def g_crescent_nest(rng, pal):
    s = Scene(); st = []; R = rng.uniform(21, 27); ang = rng.choice([0.0, math.pi / 2, -math.pi / 2, rng.uniform(-0.4, 0.4)])
    crescent(s, F, st, 0, 0, R, kind=list(pal), ang=ang, w=R * 0.1, fill=rng.uniform(0.55, 0.65), seed=int(rng.integers(1, 99)))
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(int(rng.integers(2, 5))):
        u, v = rng.uniform(0.15, 0.45) * R, rng.uniform(-0.45, 0.45) * R
        x, y = u * ca - v * sa, u * sa + v * ca
        thorns(s, F, st, (x, y), rng.uniform(2.8, 4.2), pal[i % len(pal)], n=4, reach=(0.6, 1.8), seed=int(rng.integers(1, 99)))
        lead(s, F, [(x, y), (-R * 0.42 * ca - v * sa * 1.1, -R * 0.42 * sa + v * ca * 1.1)], r=0.5)
    buckle_back(s, F, R * 1.6, R * 1.35); return s, st


def g_crescent_bar(rng, pal):
    s = Scene(); st = []; bar(s, F); r = rng.uniform(4.8, 6.2); n = int(rng.choice([2, 2, 3]))
    xs = [-9, 9] if n == 2 else [-12, 0, 12]
    for i, x in enumerate(xs):
        ang = 0.0 if (i % 2 == 0) else math.pi
        crescent(s, F, st, x, 0, r if n == 2 else r * 0.85, kind=pal[i % len(pal)], ang=ang, w=0.7, seed=int(x + 20),
                 sizes=[("marquise", 3.5, 1.8), ("round", 2, 2), ("round", 1.5, 1.5)])
        lead(s, F, [(x - r, 0), (x + r, 0)], r=0.45)
    return s, st


def g_crescent_drop(rng, pal):
    R = rng.uniform(6.5, 8.0); seed = int(rng.integers(1, 99)); n = int(rng.integers(3, 6))
    def one(s, m, st, sx):
        crescent(s, m, st, 0, -10, R, kind=list(pal[:2]), ang=math.pi / 2, w=0.8, seed=seed)
        for j, x in enumerate(np.linspace(-2.4, 2.6, n)):
            L = 3.0 + 3.5 * (1 - abs(x) / 3); big = j == n // 2
            stalk(s, m, st, (x, -10 - R * 0.6 + 2.5), (x * 1.2, -10 - R * 0.6 + 2.5 - L), d=1.4 if big else 1.0, kind=pal[0] if big else None, r=0.26, bend=0.12)
        lead(s, m, [(0, -1.5), (0, -3.2)], r=0.45); jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, 24)


def g_four_roses(rng, pal):
    s = Scene(); st = []; lay = rng.choice(["2x2", "3x1", "1x3"])
    pos = {"2x2": [(-14, 11), (14, 11), (-14, -11), (14, -11)], "3x1": [(-19, 0), (0, 0), (19, 0)], "1x3": [(0, 19), (0, 0), (0, -19)]}[lay]
    W, H = {"2x2": (28, 22), "3x1": (29, 11), "1x3": (11, 29)}[lay]
    R = 8.8; n = int(rng.choice([6, 8]))
    nib(s, F, smooth([(-W, -H), (W, -H), (W, H), (-W, H)], 4, closed=True)[:, :2], w=1.6, closed=True, taper=(0, 0), hair=0.5)
    for i, (x, y) in enumerate(pos):
        rose(s, F, st, x, y, R, n=n, kinds=(pal[i % len(pal)], pal[(i + 1) % len(pal)]), w=0.8, seed=int(rng.integers(1, 99)))
    if lay == "2x2":
        lead(s, F, [(-W, 0), (W, 0)], r=0.7); lead(s, F, [(0, -H), (0, H)], r=0.7)
        thorns(s, F, st, (0, 0), 5.0, pal[0], n=4, reach=(0.6, 1.4), seed=2)
    else:
        for (x, y) in pos:
            if lay == "3x1": lead(s, F, [(x, R), (x, H)], r=0.5); lead(s, F, [(x, -R), (x, -H)], r=0.5)
            else: lead(s, F, [(R, y), (W, y)], r=0.5); lead(s, F, [(-R, y), (-W, y)], r=0.5)
    for sx in (1, -1):
        for sy in (1, -1):
            spike(s, F, (sx * W, sy * H), (sx * (W + 5), sy * (H + 6)), r0=1.2, bend=0.3)
    buckle_back(s, F, W * 1.5, H * 1.4); return s, st


def g_rose_lancet(rng, pal):
    s = Scene(); st = []; a = rng.uniform(14, 18); h = rng.uniform(42, 52)
    o = lancet_outline(a, h) + [0, -h / 2]
    nib(s, F, o, w=1.9, closed=True, taper=(0, 0), hair=0.5, pen=0.3)
    yr = h / 2 - a * 1.0; Rr = a * 0.6
    rose(s, F, st, 0, yr, Rr, n=int(rng.choice([6, 8])), kinds=tuple(pal), w=0.9, seed=int(rng.integers(1, 99)))
    yl = yr - Rr - 1.5
    lead(s, F, [(-a + 0.5, yl), (a - 0.5, yl)], r=0.6); lead(s, F, [(0, yl - 1.5), (0, -h / 2)], r=0.6)
    for sx in (1, -1):
        cell = np.array([(sx * 1.0, yl - 1), (sx * (a - 1), yl - 1), (sx * (a - 0.5), -h / 2 + 1), (sx * 1.0, -h / 2 + 1)])
        glaze(s, F, st, cell, list(pal[::-1]), root=(0, yl), margin=0.8, seed=int(rng.integers(1, 99)))
        lead(s, F, [(sx * Rr * 0.95, yr + 1), (sx * (a - 0.5), yr - 2)], r=0.5)
    spike(s, F, (0, h / 2), (0, h / 2 + 8), r0=1.3)
    buckle_back(s, F, a * 1.8, h * 0.85); return s, st


def g_rose_drop(rng, pal):
    R = rng.uniform(5.8, 7.2); n = int(rng.choice([6, 8])); seed = int(rng.integers(1, 99))
    legs = [(x, rng.uniform(4, 10), rng.uniform(-0.25, 0.25)) for x in np.linspace(-2.6, 2.6, int(rng.integers(3, 6)))]
    def one(s, m, st, sx):
        rose(s, m, st, 0, -3.5 - R, R, n=n, kinds=tuple(pal[:2]), w=0.55, seed=seed)
        nib(s, m, [(0, -1.5), (0, -3.5)], w=0.55, hair=0.8, pen=1.57, taper=(0, 0))
        top = -3.5 - 2 * R + 0.3
        for j, (x, L, b) in enumerate(legs):
            big = L == max(l for _, l, _ in legs)
            stalk(s, m, st, (x, top), (x * 1.3, top - L), d=1.5 if big else 1.0, kind=pal[1] if big else None, bend=b, r=0.3)
        jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, 22)


def g_lancet_drop(rng, pal):
    a = rng.uniform(4.2, 5.4); h = rng.uniform(17, 22); lights = int(rng.choice([2, 3]))
    def one(s, m, st, sx):
        lancet(s, m, st, 0, -h - 4, a, h, lights=lights, kind=list(pal[:2]), w=0.7, sizes=[("marquise", 6, 3), ("round", 2, 2), ("round", 1.5, 1.5)])
        nib(s, m, [(0, -2), (0, -5)], w=0.55, hair=0.8, pen=1.57, taper=(0, 0))
        for sd in (1, -1): stalk(s, m, st, (sd * a * 1.05, -h - 4), (sd * a * 1.4, -h - 8.5), d=1.4, kind=pal[0] if sd > 0 else None, bend=0.2)
        jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, 24)


# ---------------------------------------------------------------- round 2 picks, bred
def r2_moth_clip(rng, pal):
    s = Scene(); st = []; size = rng.uniform(44, 56)
    W2.bug(s, W2.F0, st, (0, 0), size, "moth", ang=math.pi / 2 + rng.uniform(-0.2, 0.2), rng=rng, pal=pal, stones=int(rng.integers(2, 4)))
    E._clipbar(s, (-size * 0.25, 0), (size * 0.25, 0)); s.units = [0.0]; return s, st


def r2_angel_bar(rng, pal):
    s = Scene(); st = []
    s.cone((-19, 0, -1.2), (19, 0, -1.2), 0.75, 0.75, k=0.3)
    for sx in (-1, 1): s.sphere((sx * 20.3, 0, -1.2), 1.8, k=0.3)
    sx = rng.choice([1, -1])
    W2.angel_wing(s, W2.F0, st, (sx * 14, 0), rng.uniform(22, 27), ang=math.pi - 0.15 if sx > 0 else 0.15 - math.pi, sx=1, rng=rng, bead_kind=pal[0])
    s.units = [0.0]; return s, st


def _pal2(pal): return (pal[0], pal[1 % len(pal)])


def wrap(fn):
    return lambda rng, pal: fn(rng, _pal2(pal))


PLAN3 = [("g3_bug_clip", g_bug_clip, "flat", 6), ("g3_bug_pendant", g_bug_pendant, "hang", 4), ("g3_bug_ear", g_bug_ear, "hang", 4),
         ("g3_split_bar", g_split_bar, "flat", 5), ("g3_split_brooch", g_split_brooch, "flat", 3),
         ("g3_crescent_nest", g_crescent_nest, "flat", 3), ("g3_crescent_bar", g_crescent_bar, "flat", 3), ("g3_crescent_drop", g_crescent_drop, "hang", 2),
         ("g3_four_roses", g_four_roses, "flat", 3), ("g3_rose_lancet", g_rose_lancet, "flat", 3), ("g3_rose_drop", g_rose_drop, "hang", 3),
         ("g3_lancet_drop", g_lancet_drop, "hang", 2),
         ("g3_moth_clip", wrap(r2_moth_clip), "flat", 4), ("g3_angel_bar", wrap(r2_angel_bar), "flat", 3),
         ("g3_vein_ring", wrap(E.W_r_vein), "ring", 4), ("g3_bug_ring", wrap(E.W_r_bug), "ring", 2),
         ("g3_vein_ear", wrap(E.pair_of(E.we_vein, 30)), "flat", 3),
         ("g3_angel_ring", wrap(E.W_r_angel), "ring", 4), ("g3_moth_cuff", wrap(E.W_c_bug), "cuff", 3)]


def _register3():
    i = 0
    for pre, fn, kind, n in PLAN3:
        for j in range(n):
            seed = 77000 + i * 23; pal = PALS3[(i * 5) % len(PALS3)]
            def mk(fn=fn, seed=seed, pal=pal):
                with wisp.organic():
                    s, st = fn(np.random.default_rng(seed), list(pal))
                if getattr(s, "units", None) is None: s.units = [0.0]
                return s, st
            name = f"{pre}_{j + 1:02d}"; mk.__name__ = name; PIECES[name] = (mk, kind); i += 1
    return i


N_GEN3 = _register3()


# ---------------------------------------------------------------- round 4 (Nov 18): the client picked the wispy vein pieces
# (moth cuffs, vein-wing earrings, vein rings). Breed only in that language, always with the organic layer on.
def g4_vein_clip(rng, pal):
    s = Scene(); st = []; sx = rng.choice([1, -1])
    for i, shp in enumerate(["moth_f" if rng.random() < 0.5 else "fore", "moth_h" if rng.random() < 0.5 else "hind"]):
        W2.vein_wing(s, W2.F0, st, (0, -i * 3), rng.uniform(44, 56) * (1 - 0.25 * i), ang=rng.uniform(0.1, 0.4) - 0.6 * i, sx=sx, rng=rng,
                     shape=shp, stones=int(rng.integers(1, 3)), pal=pal, z=0.4 * (1 - i))
    M.hook(s, W2.F0, st, (sx * -2, -10), math.pi / 2, 14, cd=sx, kind=pal[1], z=0.8)
    E._clipbar(s, (sx * 2, -2), (sx * 24, 4)); s.units = [0.0]; return s, st


def g4_vein_stud(rng, pal):
    s = Scene(); st = []
    for sx in (1, -1):
        W2.vein_wing(s, W2.F0, st, (sx * 1.0, 0), rng.uniform(10, 14), ang=rng.uniform(0.2, 0.6), sx=sx, rng=rng,
                     shape=rng.choice(["fore", "moth_f", "bfly_f"]), stones=0, pal=pal)
    # one centre stone only (no wing stones crowding it), sitting in a molten swelling that the wing roots melt into
    s.ellipsoid((0, 0, 1.0), (2.6, 3.0, 1.3), k=1.0)
    Mo.prong(s, st, (0, 0, 2.0), 3.5, pal[0]); E._post(s, 0, 0); s.units = [0.0]; return s, st


PLAN4 = [("g4_moth_cuff", wrap(E.W_c_bug), "cuff", 10), ("g4_vein_ring", wrap(E.W_r_vein), "ring", 10),
         ("g4_vein_ear", wrap(E.pair_of(E.we_vein, 30)), "flat", 9), ("g4_bug_necklace", wrap(E.W_n_bug), "hang", 9),
         ("g4_vein_clip", wrap(g4_vein_clip), "flat", 9), ("g4_vein_stud", wrap(g4_vein_stud), "flat", 9),
         ("g4_split_bar", g_split_bar, "flat", 8)]   # the client also picked g3_split_bar_01 (carved glass wing barbell)


def _register4():
    i = 0
    for pre, fn, kind, n in PLAN4:
        for j in range(n):
            seed = 55000 + i * 29; pal = PALS3[(i * 3 + 1) % len(PALS3)]
            def mk(fn=fn, seed=seed, pal=pal):
                with wisp.organic():
                    s, st = fn(np.random.default_rng(seed), list(pal))
                if getattr(s, "units", None) is None: s.units = [0.0]
                return s, st
            name = f"{pre}_{j + 1:02d}"; mk.__name__ = name; PIECES[name] = (mk, kind); i += 1
    return i


N_GEN4 = _register4()


# round 4b (Nov 18): the client also picked the glass bugs (pendant_03, butterfly clip_06, bug earrings 01/02).
def g4_glass_clip(rng, pal):
    s = Scene(); st = []; size = rng.uniform(40, 52)
    glass_bug(s, F, st, (0, 0), size, rng.choice(["butterfly", "butterfly", "moth"]), rng, pal)
    E._clipbar(s, (0, size * 0.02), (0, -size * 0.36)); s.units = [0.0]; return s, st   # hidden under the abdomen


PLAN4B = [("g4_glass_pendant", g_bug_pendant, "hang", 8), ("g4_glass_clip", g4_glass_clip, "flat", 8), ("g4_glass_ear", g_bug_ear, "hang", 8)]


def _register4b():
    i = 0
    for pre, fn, kind, n in PLAN4B:
        for j in range(n):
            seed = 66000 + i * 31; pal = PALS3[(i * 3 + 2) % len(PALS3)]
            def mk(fn=fn, seed=seed, pal=pal):
                with wisp.organic():
                    s, st = fn(np.random.default_rng(seed), list(pal))
                if getattr(s, "units", None) is None: s.units = [0.0]
                return s, st
            name = f"{pre}_{j + 1:02d}"; mk.__name__ = name; PIECES[name] = (mk, kind); i += 1
    return i


N_GEN4B = _register4b()
