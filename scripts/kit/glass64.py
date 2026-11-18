"""The 64 stained-glass pieces.
Each returns (Scene, stones). Units mm. Flat pieces face +z; rings: finger along y, top +z."""
import math
import numpy as np
from sdf import Scene, resample, profile
from kit import *   # noqa
from kit import TIP, blade

PIECES = {}


def piece(kind):
    def deco(fn):
        PIECES[fn.__name__] = (fn, kind); return fn
    return deco


F = Flat()


def top(Rb, lift=0.6):
    return Flat(o=(0, 0, Rb + lift))


def saddle(s, Rb, w=4.5, l=3.2):
    s.ellipsoid((0, 0, Rb + 0.2), (w, l, 1.3), k=1.0)


def mirror(fn):
    for sx in (1, -1): fn(sx)


# =============================================================== RINGS
@piece("ring")
def r01_lancet():
    """Lancet: an upright chapel window on the band; calligraphic mullions, flicks at the base."""
    s = Scene(); st = []
    Rb, _ = shank(s); saddle(s, Rb)
    m = Flat(o=(0, 0, Rb + 0.4), u=(1, 0, 0), v=(0, 0, 1))
    lancet(s, m, st, 0, 0, 5.2, 15, lights=3, kind=["garnet", "amethyst", "garnet"], w=0.85)
    mirror(lambda sx: nib(s, m, [(sx * 4.5, 0.6), (sx * 8.5, 2.8), (sx * 10.5, 7.5), (sx * 8.6, 10.5)], w=1.2, pen=0.4 * sx, taper=(0.05, 0.5)))
    mirror(lambda sx: stalk(s, m, st, (sx * 8.0, 2.0), (sx * 11.5, 0.5), d=1.6, kind="garnet", bend=0.2))
    return s, st


@piece("ring")
def r02_folded_wing():
    """Folded Wing: the wing wraps the finger; its costa is the band, its tip a hooked blade."""
    s = Scene(); st = []
    Rb, R0 = shank(s, top_w=1.8)
    m = Cyl(Rb + 0.4)
    wing(s, m, st, sx=0.82, sy=0.62, rot=0.0, t=(-14, 2.5), pal=["citrine", "peridot", "aquamarine"], costa=1.15, seed=4)
    spike(s, m, (24.5, 4.8), (30, 0.5), r0=1.0, bend=0.35)
    stalk(s, m, st, (-13, 2.0), (-17, 6.5), d=1.8, kind="citrine", bend=0.3)
    return s, st


@piece("ring")
def r03_rose_signet():
    """Rose Signet: the face is a rose window, the dogwood notch carried by the tracery."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=3.0)
    s.ellipsoid((0, 0, Rb + 0.4), (8.5, 8.0, 1.6), k=1.2)
    m = top(Rb, 1.9)
    rose(s, m, st, 0, 0, 7.6, n=6, kinds=("aquamarine", "topaz", "londonblue"), w=0.85)
    mirror(lambda sx: curl(s, Flat(o=(0, 0, Rb + 0.6)), st, sx * 9.8, 0, 2.4, a0=math.pi if sx > 0 else 0, w=0.9, cw=sx))
    return s, st


@piece("ring")
def r04_caught_stone():
    """Caught Stone: an oval garnet fallen into a briar of uneven thorns on a twisted band."""
    s = Scene(); st = []
    R0 = (14.0 + 0.8128 * 7) / 2
    th = np.linspace(0, 2 * math.pi, 181)
    for ph in (0, math.pi):          # two wrought strands twisting round each other
        tw = 6 * th + ph
        rr = R0 + 1.0 + 0.55 * np.cos(tw)
        pts = np.stack([rr * np.sin(th), 0.75 * np.sin(tw), -rr * np.cos(th)], 1)
        s.stroke(pts, np.full(len(pts), 0.75), k=0.3)
    Rb = R0 + 1.6
    s.ellipsoid((0, 0, Rb + 0.6), (4.2, 3.2, 1.6), k=1.0)
    m = top(Rb, 0.6)
    thorns(s, m, st, (0, 0), 7.0, "garnet", L=9.0, n=5, seed=3, reach=(0.6, 1.6))
    for a in (0.6, 2.2, 3.9, 5.2):
        p = (math.cos(a) * 4.5, math.sin(a) * 4.5)
        spike(s, m, p, (math.cos(a + 0.4) * 9, math.sin(a + 0.4) * 9), r0=0.85, bend=0.25, z1=0.8)
    stalk(s, m, st, (-3.5, -2.5), (-7.5, -6.0), d=1.6, kind="garnet", bend=-0.3)
    return s, st


@piece("ring")
def r05_shutter():
    """Shutter: an oval topaz under a hinged lid of moth-wing tracery, shown half open."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=3.0)
    s.ellipsoid((0, 0, Rb + 0.6), (7.0, 5.6, 1.8), k=1.2)
    m = top(Rb, 1.2)
    nib(s, m, arc(0, 0, 6.2, 0, 2 * math.pi, 50), w=0.9, closed=True, taper=(0, 0), hair=0.5)
    thorns(s, m, st, (0, 0), 7.5, "topaz", L=9.5, n=4, reach=(0.6, 0.9), seed=2)
    for x in (-3.5, 0, 3.5):        # hinge knuckles along the +y edge
        s.cone(m.P(x - 1.4, 6.3, 0.6), m.P(x + 1.4, 6.3, 0.6), 0.75, 0.75, k=0.3)
    lid = hinge(Flat(o=m.P(0, 0, 5.4)), (0, 6.3), (1, 0), -0.75)
    for x in (-3.5, 3.5):           # hinge posts up to the lid's knuckle line
        s.cone(m.P(x, 6.3, 0.6), m.P(x, 6.3, 5.4), 0.7, 0.6, k=0.3)
    s.cone(m.P(-4.5, 6.3, 5.4), m.P(4.5, 6.3, 5.4), 0.7, 0.7, k=0.3)
    lw = [(0, 0), (6, 3), (12, 4), (15, 0), (12, -4), (6, -3)]
    for mr, tx in ((False, -6.4), (True, 6.4)):
        wing(s, lid, st, outline=lw, sx=0.42, sy=1.0, t=(tx, 0.5), mirror=mr, pal=["topaz", "londonblue"], costa=0.8,
             sizes=[("round", 2, 2), ("round", 1.5, 1.5)], thorn_tips=False, seed=9 + mr)
    return s, st


@piece("ring")
def r06_counter_knot():
    """Counter Knot: one broad-nib stroke loops and knots; its counters are glazed."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.0); saddle(s, Rb)
    m = top(Rb, 0.6)
    path = [(-9, -3), (-6, 3), (-1.5, 4.8), (1.5, 0), (-1.5, -4.8), (-5.5, -2.5), (-4.5, 1.5), (0, 1.0), (4.5, -1.5),
            (5.5, 2.5), (1.5, 4.8), (-1.5, 0), (1.5, -4.8), (6, -3), (9, 3)]
    nib(s, m, path, w=1.25, pen=0.7, hair=0.22, taper=(0.12, 0.12), n=8)
    pane(s, m, st, (-3.3, 0.7), "round", 3, 3, "amethyst")
    pane(s, m, st, (3.3, -0.7), "round", 3, 3, "amethyst")
    pane(s, m, st, (0, 2.6), "marquise", 4, 2, "citrine")
    pane(s, m, st, (0, -2.6), "marquise", 4, 2, "citrine")
    mirror(lambda sx: stalk(s, m, st, (sx * 9, 3 * sx), (sx * 11.5, 6.5 * sx), d=1.3, bend=0.3))
    return s, st


@piece("ring")
def r07_horn_bypass():
    """Horn Bypass: two horns sweep opposite ways and meet at a pear; their inner faces glitter."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.4); saddle(s, Rb, 4, 4)
    m = top(Rb, 0.8)
    for sx in (1, -1):
        h = spike(s, m, (sx * 1.0, -sx * 1.5), (sx * 12.0, sx * 9.5), r0=2.4, bend=0.35, side=-sx, z0=0.6, z1=3.5)
        for f in (0.22, 0.34, 0.46):
            j = int(f * len(h)); p = h[j]
            pane(s, m, st, (p[0], p[1]), "round", 1.5, 1.5, "garnet", vein=0.25)
    s.ellipsoid(m.P(0, 0, 0.4), (3.6, 3.0, 1.3), k=0.8)
    pane(s, m, st, (0, 0), "pear", 8, 5, "garnet", ang=0.6, vein=0.55)
    return s, st


@piece("ring")
def r08_antennae_halo():
    """Antennae Halo: an oval peridot in a halo of graded bead stalks, some hooked."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.6); saddle(s, Rb, 4.5, 4)
    m = top(Rb, 0.7)
    thorns(s, m, st, (0, 0), 6.0, "peridot", L=8.0, n=4, reach=(0.6, 0.8), seed=5)
    for i in range(10):
        a = 2 * math.pi * i / 10 + 0.15
        L = 7.5 + 3.5 * (i % 3) / 2
        b = (math.cos(a) * L * 1.15, math.sin(a) * L * 0.85)
        stalk(s, m, st, (math.cos(a) * 3.5, math.sin(a) * 2.8), b, d=2.0 if i % 3 == 0 else 1.4,
              kind=("peridot" if i % 2 else "citrine") if i % 3 == 0 else None, bend=0.25 * (1 if i % 2 else -1), z0=0.5, z1=1.4)
    return s, st


@piece("ring")
def r09_cloister_band():
    """Cloister Band: a wide band of lancet arches all round; every third glazed, rest open."""
    s = Scene(); st = []
    R0 = (14.0 + 0.8128 * 7) / 2
    m = Cyl(R0 + 0.9)
    C = 2 * math.pi * m.R
    for y in (-4.6, 4.6):
        nib(s, m, [(x, y) for x in np.linspace(0, C, 90)], w=0.9, pen=0.0, hair=0.9, taper=(0, 0))
    n = 12; dx = C / n
    for i in range(n):
        x = i * dx
        lead(s, m, [(x, -4.6), (x, 4.6)], r=0.55)
        o = lancet_outline(dx / 2 - 0.2, 8.4) + [x + dx / 2, -4.4]
        nib(s, m, o, w=0.6, hair=0.6, pen=0.0, taper=(0.05, 0.05))
        spike(s, m, (x + dx / 2, 4.0), (x + dx / 2, 5.6), r0=0.5)
        if i % 3 == 0:
            glaze(s, m, st, o, ["amethyst", "londonblue"][(i // 3) % 2], margin=0.4, sizes=[("marquise", 4, 2), ("round", 2, 2), ("round", 1.5, 1.5)])
    return s, st


@piece("ring")
def r10_molten_pane():
    """Molten Pane: a pooled liquid band with two stones sitting in it like melted leading."""
    s = Scene(); st = []
    R0 = (14.0 + 0.8128 * 7) / 2
    rng = np.random.default_rng(4)
    for a in np.linspace(0, 2 * math.pi, 22, endpoint=False):
        tp = 0.5 + 0.5 * math.cos(a)
        r = 1.0 + 1.6 * tp ** 2 + rng.uniform(0, 0.25)
        s.ellipsoid(((R0 + r * 0.8) * math.sin(a), rng.uniform(-0.5, 0.5), (R0 + r * 0.8) * math.cos(a)),
                    (r * 1.4, 1.8 + 2.2 * tp, r), k=1.4)
    m = top(R0, 3.6)
    pane(s, m, st, (-1.8, 1.0), "pear", 7, 5, "amethyst", ang=2.6, vein=0.7)
    pane(s, m, st, (3.0, -1.6), "round", 4, 4, "garnet", vein=0.6)
    for q in ((-8.5, -4.0), (7.0, 6.5)):
        s.ellipsoid(m.P(q[0], q[1], -1.2), (0.9, 0.9, 1.3), k=0.9)
    spike(s, m, (4.2, 2.6), (9.5, 7.5), r0=1.1, bend=0.3, z0=-0.2, z1=0.8)
    return s, st


# =============================================================== BUCKLES (xy plane)
@piece("flat")
def b01_triptych():
    """Triptych: three lancets as an altarpiece; the side panels open like doors."""
    s = Scene(); st = []
    lancet(s, F, st, 0, -16, 10, 34, lights=3, kind=["garnet", "amethyst", "garnet"], w=1.3)
    for sx in (1, -1):
        d = hinge(F, (sx * 11.2, 0), (0, 1), 0.45 * sx)
        lancet(s, d, st, sx * 18.5, -14, 6.8, 26, lights=2, kind=["topaz", "londonblue"], w=1.1, finial=False)
        for y in (-8, 0, 8): s.cone(F.P(sx * 11.4, y - 2.5, 0.4), F.P(sx * 11.4, y + 2.5, 0.4), 0.9, 0.9, k=0.3)
    mirror(lambda sx: nib(s, F, [(sx * 3, -17.5), (sx * 14, -19.5), (sx * 26, -16), (sx * 30, -10)], w=1.5, pen=0.3, taper=(0.1, 0.5)))
    buckle_back(s, F, 50, 30)
    return s, st


@piece("flat")
def b02_spread_moth():
    """Spread Moth: four stained-glass wings in mirror symmetry; the body is the tongue."""
    s = Scene(); st = []
    for mr in (False, True):
        sx = -1 if mr else 1
        wing(s, F, st, sx=0.72, sy=0.72, rot=0.32 * sx, t=(sx * 2.5, 2.0), mirror=mr, pal=PAL["dusk"], seed=3 + mr, costa=1.3)
        wing(s, F, st, outline=HIND, sx=0.62, sy=0.62, rot=-0.15 * sx, t=(sx * 2.5, -1.5), mirror=mr, pal=PAL["dusk"][::-1], seed=5 + mr, costa=1.1)
        stalk(s, F, st, (sx * 0.8, 8), (sx * 6, 16.5), d=1.8, kind="citrine", bend=0.3 * sx)
    for y, r in ((6, 2.2), (2, 2.6), (-3, 2.4), (-8, 2.0), (-12.5, 1.5)):
        s.ellipsoid(F.P(0, y, 1.0), (r, r * 1.15, r * 0.8), k=1.0)
    spike(s, F, (0, -13), (0, -21), r0=1.6)
    buckle_back(s, F, 40, 30)
    return s, st


@piece("flat")
def b03_glazed_gate():
    """Glazed Gate: an open frame of S-scroll bars; only the eye of each scroll is glazed."""
    s = Scene(); st = []
    W, H = 32, 22
    nib(s, F, [(-W, -H), (W, -H), (W, H), (-W, H)], w=1.4, closed=True, taper=(0, 0), hair=0.6, n=2)
    for row, y in enumerate((-11, 0, 11)):
        for i, x in enumerate(np.linspace(-22, 22, 4)):
            sg = 1 if (i + row) % 2 else -1
            kd = ["garnet", "citrine", "peridot"][(i + row) % 3]
            curl(s, F, st, x - 3.2, y + 1.8 * sg, 2.5, a0=0.3, w=0.9, kind=kd, cw=sg,
                 tail=np.array([(x, y), (x + 3.2, y - 1.8 * sg)]))
            curl(s, F, st, x + 3.2, y - 1.8 * sg, 2.5, a0=math.pi + 0.3, w=0.9, cw=sg)
        lead(s, F, [(-W - 1.5, y), (W + 1.5, y)], r=0.5)
    for x in (-W, W):
        for y in (-H, H): ball(s, F, (x, y), 1.5)
    mirror(lambda sx: spike(s, F, (sx * W, H), (sx * (W + 6), H + 7), r0=1.2, bend=0.3))
    buckle_back(s, F, 50, 36)
    return s, st


@piece("flat")
def b04_briar_heart():
    """Briar Heart: an open heart frame; inward thorns are the claws for a ring of pears."""
    s = Scene(); st = []
    o = heart_outline(58, 50) + [0, -22]
    nib(s, F, o, w=1.9, pen=0.6, hair=0.35, closed=True, taper=(0, 0))
    c0 = o.mean(0)
    inner = (o - c0) * 0.62 + c0
    for p in inner[::8][:8]:
        d = c0 - p; d = d / np.linalg.norm(d)
        q = p + d * 0.5
        pane(s, F, st, tuple(q), "pear", 5, 3, "garnet", ang=math.atan2(d[1], d[0]), vein=0.45)
        oo = (q - c0) / 0.62 * 1.0 + c0
        lead(s, F, [tuple(oo), tuple(q - d * 2.2)], r=0.5)
        nn = np.array([-d[1], d[0]])
        spike(s, F, tuple(q - d * 1.0 + nn * 2.0), tuple(q + d * 3.5 + nn * 2.4), r0=0.6, bend=0.2)
    for p in o[::6]:
        d = p - c0; d = d / np.linalg.norm(d)
        spike(s, F, tuple(p), tuple(p + d * 4.5 + np.array([-d[1], d[0]]) * 1.5), r0=0.9, bend=0.25)
    buckle_back(s, F, 40, 34)
    return s, st


@piece("flat")
def b05_blackletter():
    """Blackletter: an abstract broad-nib capital whose counters are glazed."""
    s = Scene(); st = []
    nib(s, F, [(-18, -18), (-16, 6), (-10, 18), (-4, 14), (-6, 0), (0, -6), (6, 0), (4, 14), (10, 18), (16, 6), (18, -18)], w=3.0, pen=0.78, hair=0.12, taper=(0.15, 0.15))
    nib(s, F, [(-26, 4), (-12, 10), (0, 6), (12, 10), (26, 4)], w=2.0, pen=0.78, hair=0.12)
    nib(s, F, [(-22, -20), (-10, -24), (0, -18), (10, -24), (24, -20), (30, -12)], w=2.2, pen=0.78, hair=0.12, taper=(0.1, 0.4))
    for p, z, kd in (((-11, 8), ("pear", 6, 4), "londonblue"), ((11, 8), ("pear", 6, 4), "londonblue"), ((0, 1.5), ("round", 4, 4), "garnet"),
                     ((-12, -8), ("marquise", 6, 3), "amethyst"), ((12, -8), ("marquise", 6, 3), "amethyst")):
        pane(s, F, st, p, z[0], z[1], z[2], kd, ang=math.pi / 2)
    for a, b in (((-26, 4), (-31, 12)), ((30, -12), (34, -4)), ((0, -18), (0, -26))):
        stalk(s, F, st, a, b, d=1.7, kind="garnet" if b[1] < 0 else None, bend=0.3)
    buckle_back(s, F, 44, 30)
    return s, st


@piece("flat")
def b06_horned_shield():
    """Horned Shield: a shield with swept horns, a rose window at its heart, a barbed rim."""
    s = Scene(); st = []
    o = smooth([(-17, 16), (17, 16), (18, 2), (12, -14), (0, -22), (-12, -14), (-18, 2)], 10, closed=True)[:, :2]
    nib(s, F, o, w=1.8, pen=0.3, hair=0.45, closed=True, taper=(0, 0))
    rose(s, F, st, 0, 0, 9.0, n=8, kinds=("aquamarine", "londonblue", "topaz"), w=0.9)
    c0 = o.mean(0)
    for p in resample(np.column_stack([o, np.zeros(len(o))]), 2.4)[:, :2]:
        d = p - c0; d /= np.linalg.norm(d)
        spike(s, F, tuple(p - d * 0.3), tuple(p - d * 3.0 + np.array([-d[1], d[0]]) * 1.2), r0=0.45, bend=0.1, z0=0.5, z1=0.3)
    mirror(lambda sx: spike(s, F, (sx * 15, 14), (sx * 34, 24), r0=3.2, bend=-0.4 * sx, z1=2.0))
    buckle_back(s, F, 36, 30)
    return s, st


@piece("flat")
def b07_hinge_spine():
    """Hinge Spine: the plate folds on a column of vertebrae, a stone in every joint."""
    s = Scene(); st = []
    spine(s, F, st, [(0, -22), (0, 0), (0, 22)], n=6, size=4.2, kind=["aquamarine", "topaz", "londonblue"], grade=(1, 1))
    for sx in (1, -1):
        d = hinge(F, (sx * 6.5, 0), (0, 1), 0.3 * sx)
        o = smooth(np.array([(sx * 7, -18), (sx * 30, -14), (sx * 34, 0), (sx * 30, 14), (sx * 7, 18)]), 8, closed=True)[:, :2]
        nib(s, d, o, w=1.3, closed=True, taper=(0, 0), hair=0.5)
        for y in (-9, 0, 9): lead(s, d, [(sx * 7, y), (sx * 32, y * 0.8)], r=0.45)
        glaze(s, d, st, o, ["aquamarine", "londonblue"], seed=21 + (sx > 0), margin=0.8,
              blocked=[(np.array([(sx * 7, y), (sx * 32, y * 0.8)]), 0.9) for y in (-9, 0, 9)])
    buckle_back(s, F, 50, 30)
    return s, st


@piece("flat")
def b08_comet_glass():
    """Comet Glass: a topaz comet head; its tail is a fan of strokes glazed with graded stones."""
    s = Scene(); st = []
    thorns(s, F, st, (-20, 6), 7.0, "topaz", L=9.0, n=6, reach=(0.6, 1.8), seed=7)
    ends = [(30, 22), (34, 10), (35, -2), (31, -13)]
    nib(s, F, [(-23, 6), (-18, 7), (-13, 6)], w=1.6, hair=0.5, taper=(0.2, 0.0))
    strokes = []
    for e in ends:
        c, _ = nib(s, F, [(-14, 6), ((e[0] - 14) / 2 + 2, (e[1] + 6) / 2 + 2), e], w=1.4, pen=1.2, hair=0.25, taper=(0.05, 0.4))
        strokes.append(c)
    for j, (a, b) in enumerate(zip(strokes[:-1], strokes[1:])):
        cell = np.vstack([a[len(a) // 6:], b[len(b) // 6:][::-1]])
        glaze(s, F, st, cell, ["topaz", "aquamarine", "londonblue"], root=(-14, 6), margin=0.7, seed=40 + j)
    for p in ((-30, 16), (-32, -4), (-10, 20)):
        for a in range(4):
            q = (p[0] + 3.0 * math.cos(a * math.pi / 2 + 0.3), p[1] + 3.0 * math.sin(a * math.pi / 2 + 0.3))
            spike(s, F, p, q, r0=0.7, bend=0.0)
        nib(s, F, [p, ((p[0] - 20) / 2, (p[1] + 6) / 2 + 2), (-20, 6)], w=0.7, hair=0.4, taper=(0.3, 0.1))
    buckle_back(s, F, 44, 30)
    return s, st


# =============================================================== BRACELETS
def ring_pos(n, R, i, off=0.0):
    a = 2 * math.pi * i / n + off
    return np.array([R * math.cos(a), R * math.sin(a)]), a


@piece("flat")
def br01_shutters():
    """Shutters: hinged leaded panes that tilt as the wrist moves; bead-stalk hinge caps."""
    s = Scene(); st = []
    n = 7; R = 31
    for i in range(n):
        p, a = ring_pos(n, R, i, 0.2)
        m = hinge(Flat(o=F.P(*p)).rot(a - math.pi / 2), (0, 0), (1, 0), 0.2 * (1 if i % 2 else -1))
        o = smooth([(-6.5, -7), (6.5, -7), (7, 6), (0, 9.5), (-7, 6)], 6, closed=True)[:, :2]
        nib(s, m, o, w=0.9, closed=True, taper=(0, 0), hair=0.5)
        lead(s, m, [(0, -7), (0, 9.5)], r=0.45)
        glaze(s, m, st, o, PAL["night"][i % 3], seed=30 + i, margin=0.6, blocked=[(np.array([(0, -7), (0, 9.5)]), 0.9)])
        q, b = ring_pos(n, R, i + 0.5, 0.2)
        t = np.array([-math.sin(b), math.cos(b)])
        s.cone(F.P(*(q - 7.0 * t)), F.P(*(q + 7.0 * t)), 1.0, 1.0, k=0.3)
        stalk(s, F, st, tuple(q), tuple(q * 1.16), d=1.5, kind="moonstone" if i % 2 else None, bend=0.2)
    return s, st


@piece("ring")
def br02_rib_cuff():
    """Rib Cuff: curved hooked ribs off a central spine; a stone where each rib crosses."""
    s = Scene(); st = []
    m = Cyl(29)
    C = 2 * math.pi * 29 * 0.82
    nib(s, m, [(x, 0) for x in np.linspace(-C / 2, C / 2, 80)], w=1.5, pen=0.0, hair=0.95, taper=(0.04, 0.04))
    n = 9
    for i in range(n):
        x = -C / 2 + C * (i + 0.5) / n
        for sd in (1, -1):
            nib(s, m, [(x, 0), (x + 3, sd * 9), (x - 2, sd * 17), (x - 6.5, sd * 15.5)], w=1.3, pen=0.9 * sd, taper=(0.03, 0.4))
        pane(s, m, st, (x, 0), "round", 3, 3, ["garnet", "amethyst", "londonblue"][i % 3], vein=0.55)
    return s, st


@piece("ring")
def br03_wing_cuff():
    """Wing Cuff: the stained-glass wing stretched to wrap the wrist; colour turns with the arm."""
    s = Scene(); st = []
    m = Cyl(29)
    wing(s, m, st, sx=2.6, sy=1.05, t=(-60, 3), pal=["garnet", "citrine", "peridot", "aquamarine"], costa=1.8, seed=12,
         sizes=[("marquise", 8, 4), ("pear", 7, 5), ("marquise", 6, 3), ("pear", 6, 4), ("round", 4, 4), ("marquise", 4, 2), ("round", 3, 3), ("round", 2, 2)])
    stalk(s, m, st, (-60, 2), (-66, 9), d=2.2, kind="garnet", bend=0.3)
    return s, st


@piece("flat")
def br04_rosary():
    """Rosary: leaded stations and calligraphic S-links; every fourth station a glazed fleur."""
    s = Scene(); st = []
    n = 12; R = 32
    for i in range(n):
        p, a = ring_pos(n, R, i)
        m = Flat(o=F.P(*p)).rot(a)
        if i % 4 == 0:
            fleur(s, m, st, 0, 0, 6.5, kinds=("amethyst", "garnet"), w=0.65, centre="garnet")
        else:
            nib(s, m, arc(0, 0, 3.4, 0, 2 * math.pi, 30), w=0.7, closed=True, taper=(0, 0), hair=0.6)
            pane(s, m, st, (0, 0), "round", 4, 4, ["amethyst", "londonblue", "moonstone"][i % 3], vein=0.3)
        q, b = ring_pos(n, R, i + 0.5)
        mq = Flat(o=F.P(*q)).rot(b)
        nib(s, mq, [(0, -4.5), (1.6, -2.5), (0, 0), (-1.6, 2.5), (0, 4.5)], w=0.75, pen=0.0, taper=(0.15, 0.15))
    return s, st


@piece("flat")
def br05_briar_chain():
    """Briar Chain: a twisted wrought chain grown thorny; thorn cages hold loose rattling stones."""
    s = Scene(); st = []
    n = 26; R = 31
    for i in range(n):
        p, a = ring_pos(n, R, i)
        t = np.array([-math.sin(a), math.cos(a)])
        ax = np.array([math.cos(a), math.sin(a), 0.0]) if i % 2 else np.array([0, 0, 1.0])
        s.torus(F.P(*p, 0.8), 2.6, 0.7, normal=ax, k=0.0)
        if i % 3 == 0:
            spike(s, F, tuple(p + t * 1.5), tuple(p * 1.12 + t * 1.0), r0=0.6, bend=0.2)
    for i in range(0, n, 5):
        p, a = ring_pos(n, R, i + 0.5)
        c = p * 1.0
        for j in range(5):
            b = a + j * 2 * math.pi / 5
            q0 = c + 2.5 * np.array([math.cos(b), math.sin(b)])
            s.stroke(np.array([F.P(*q0, -0.6), F.P(*(c + 3.4 * np.array([math.cos(b + 0.4), math.sin(b + 0.4)])), 2.0),
                               F.P(*(c + 1.4 * np.array([math.cos(b + 0.9), math.sin(b + 0.9)])), 5.2)]), np.array([0.55, 0.45, 0.15]), k=0.25)
        bead(s, F, st, tuple(c), 3.6, ["garnet", "amethyst", "londonblue", "citrine", "peridot"][(i // 5) % 5], z=1.8)
    return s, st


@piece("ring")
def br06_cloister_bangle():
    """Cloister Bangle: a colonnade of lancets all round; every other one glazed."""
    s = Scene(); st = []
    m = Cyl(31)
    C = 2 * math.pi * 31
    for y in (-6, 6):
        nib(s, m, [(x, y) for x in np.linspace(0, C, 120)], w=1.1, pen=0.0, hair=0.9, taper=(0, 0))
    n = 20; dx = C / n
    for i in range(n):
        x = i * dx
        lead(s, m, [(x, -6), (x, 6)], r=0.6)
        o = lancet_outline(dx / 2 - 0.3, 10.8) + [x + dx / 2, -5.8]
        nib(s, m, o, w=0.65, hair=0.6, pen=0.0, taper=(0.05, 0.05))
        spike(s, m, (x + dx / 2, 5.0), (x + dx / 2, 8.0), r0=0.55)
        if i % 2 == 0:
            glaze(s, m, st, o, ["garnet", "amethyst", "citrine", "londonblue"][(i // 2) % 4], margin=0.45,
                  sizes=[("marquise", 6, 3), ("marquise", 5, 2.5), ("round", 2.5, 2.5), ("round", 2, 2)])
    return s, st


@piece("flat")
def br07_vertebra_line():
    """Vertebra Line: an articulated line of glass vertebrae round the wrist."""
    s = Scene(); st = []
    th = np.linspace(0, 2 * math.pi, 120)
    spine(s, F, st, np.stack([31 * np.cos(th), 31 * np.sin(th)], 1)[:-1], n=18, size=3.4,
          kind=["garnet", "amethyst", "londonblue", "aquamarine", "londonblue", "amethyst"], grade=(1, 1), w=0.7)
    return s, st


@piece("flat")
def br08_one_stroke():
    """One Stroke: an open bangle that is a single swelling pen stroke, its ends crossing."""
    s = Scene(); st = []
    th = np.linspace(-0.25, 2 * math.pi + 0.35, 90)
    R = 31 + 2.5 * np.sin(th * 3)
    pts = np.stack([R * np.cos(th), R * np.sin(th)], 1)
    nib(s, F, pts, w=3.4, pen=0.8, hair=0.15, taper=(0.06, 0.06), rise=[(0, 0.4), (0.5, 2.2), (1, 0.4)])
    e = pts[-1]; b = pts[0]
    thorns(s, F, st, tuple(e * 1.08), 5.0, "amethyst", L=8.0, n=4, reach=(0.6, 1.4), seed=4)
    ball(s, F, tuple(b * 0.95), 2.2)
    for f in (0.2, 0.55, 0.8):
        j = int(f * len(pts)); p = pts[j]; d = p / np.linalg.norm(p); nn = np.array([-d[1], d[0]])
        stalk(s, F, st, tuple(p), tuple(p + d * 5.5 + nn * 2.0), d=1.6, kind="amethyst" if f == 0.55 else None, bend=0.3)
        nib(s, F, [tuple(p), tuple(p - d * 3 + nn * 4), tuple(p - d * 5.5 + nn * 2.5)], w=0.8, taper=(0.1, 0.5))
    return s, st


# =============================================================== STUDS (pairs)
def pair(fn, gap=16):
    s = Scene(); st = []
    for sx in (-1, 1):
        fn(s, Flat(o=(sx * gap / 2, 0, 0)), st, sx)
    s.units = [-gap / 2, gap / 2]          # each earring is its own unit, so make.bridge joins floaters within it
    return s, st


@piece("flat")
def s01_single_lancet():
    def one(s, m, st, sx):
        lancet(s, m, st, 0, -4.5, 3.0, 10, lights=1, kind=["amethyst", "garnet"], w=0.5, sizes=[("marquise", 4, 2), ("round", 1.5, 1.5)])
        nib(s, m, [(0, -5), (2.5 * sx, -6.5), (4.5 * sx, -5)], w=0.55, taper=(0.1, 0.6))
        stud_post(s, m, (0, 0))
    return pair(one, 16)


@piece("flat")
def s02_rose_bud():
    def one(s, m, st, sx):
        rose(s, m, st, 0, 0, 4.6, n=6, kinds=("garnet", "citrine"), w=0.45)
        stud_post(s, m, (0, 0))
    return pair(one, 16)


@piece("flat")
def s03_three_thorns():
    def one(s, m, st, sx):
        thorns(s, m, st, (0, 0), 5.0, "londonblue", n=3, reach=(0.8, 1.7), seed=2 + (sx > 0), wire=0.4)
        stud_post(s, m, (0, 0))
    return pair(one, 14)


@piece("flat")
def s04_wing_climber():
    def one(s, m, st, sx):
        wing(s, m, st, sx=0.32, sy=0.32, rot=1.25 * sx, t=(0, -5), mirror=sx < 0, pal=["aquamarine", "londonblue"], costa=0.6,
             sizes=[("marquise", 4, 2), ("round", 2, 2), ("round", 1.5, 1.5)], vein_w=0.3, seed=2)
        stud_post(s, m, (0, -4))
    return pair(one, 18)


@piece("flat")
def s05_glass_fleur():
    def one(s, m, st, sx):
        fleur(s, m, st, 0, 0, 5.2, kinds=("amethyst", "londonblue"), w=0.45, centre="moonstone")
        stud_post(s, m, (0, 0))
    return pair(one, 16)


@piece("flat")
def s06_horn_cradle():
    def one(s, m, st, sx):
        thorns(s, m, st, (0, 0), 4.0, "garnet", n=4, reach=(0.6, 0.8), seed=1)
        for sd in (1, -1):
            spike(s, m, (sd * 1.6, -2.4), (sd * 4.0, 4.8), r0=1.1, bend=0.45, side=-sd, z1=1.6)
        stud_post(s, m, (0, 0))
    return pair(one, 14)


@piece("flat")
def s07_moth_sleeper():
    def one(s, m, st, sx):
        for sd in (1, -1):
            o = smooth([(0, 2.5), (sd * 3.5, 1), (sd * 4.5, -4), (sd * 1.5, -6.5), (sd * 0.4, -1)], 8, closed=True)[:, :2]
            nib(s, m, o, w=0.45, closed=True, taper=(0, 0), hair=0.5)
            pane(s, m, st, (sd * 2.3, -2.0), "pear", 4, 3, "amethyst", ang=math.pi / 2 + sd * 0.35, vein=0.3)
        s.ellipsoid(m.P(0, -1.5, 0.8), (0.9, 4.0, 0.9), k=0.5)
        for sd in (1, -1): stalk(s, m, st, (sd * 0.4, 2.2), (sd * 2.6, 5.5), d=1.0, bend=0.3 * sd, r=0.25)
        stud_post(s, m, (0, -1))
    return pair(one, 16)


@piece("flat")
def s08_counter():
    s = Scene(); st = []
    for sx, a0, kd in ((-1, 0.3, "citrine"), (1, 2.2, "londonblue")):
        m = Flat(o=(sx * 8, 0, 0))
        curl(s, m, st, 0, 0, 2.4, a0=a0, w=0.7, kind=kd, cw=sx, tail=np.array([(2.5 * sx, -3), (4 * sx, -6.5)]))
        spike(s, m, (-2.2 * sx, 1.0), (-4.5 * sx, 4.5), r0=0.5, bend=0.3)
        stud_post(s, m, (0, 0))
    return s, st


# =============================================================== DANGLES
@piece("hang")
def d01_lantern():
    def one(s, m, st, sx):
        c = Cyl(4.2, o=m.P(0, -12, 0))
        for i in range(6):
            x = 2 * math.pi * 4.2 * i / 6
            nib(s, c, [(x, -7), (x, 5)], w=0.6, pen=0.0, hair=0.6, taper=(0, 0))
        for y in (-7, 5):
            s.torus(m.P(0, -12 + y, 0), 4.2, 0.55, normal=(0, 1, 0), k=0.3)
        for i in (0, 1, 5):
            x = 2 * math.pi * 4.2 * (i + 0.5) / 6
            glaze(s, c, st, lancet_outline(1.6, 9.5) + [x, -6.5], PAL["tide"][i % 3], margin=0.3,
                  sizes=[("marquise", 4, 2), ("round", 2, 2), ("round", 1.5, 1.5)])
        bead(s, m, st, (0, -12.5), 3.2, "garnet", z=0.0)
        for sd in (1, -1):
            nib(s, m, [(sd * 4.2, -7), (sd * 2.5, -3), (0, -1.5)], w=0.6, taper=(0, 0.3))
            spike(s, m, (sd * 4.2, -19), (sd * 1.0, -25), r0=0.6, bend=0.3)
        spike(s, m, (0, -19.5), (0, -26), r0=0.8)
        jump(s, m, (0, 0)); ear_wire(s, m, (0, 1.4))
    return pair(one, 26)


@piece("hang")
def d02_falling_wing():
    def one(s, m, st, sx):
        wing(s, m, st, sx=0.62, sy=0.62, rot=-math.pi / 2 - 0.1 * sx, t=(0, -4), mirror=sx < 0, pal=PAL["venom"], costa=0.9, seed=4 + (sx > 0))
        nib(s, m, [(0, -3), (-2.5 * sx, -1), (-1.5 * sx, 1.5), (0, 0.8)], w=0.8, taper=(0.0, 0.4))
        jump(s, m, (0, 1.6)); ear_wire(s, m, (0, 3.0))
    return pair(one, 30)


@piece("hang")
def d03_glass_vertebrae():
    def one(s, m, st, sx):
        for i in range(4):
            y = -4 - i * 7.5; g = 1 - i * 0.16
            mm = Flat(o=m.P(0, y, 0))
            spine(s, mm, st, [(0, 2.6 * g), (0, -2.6 * g)], n=1, size=4.4 * g, kind=["londonblue", "amethyst", "garnet", "garnet"][i], w=0.8)
            if i < 3: jump(s, m, (0, y - 3.8 * g), R=1.1, r=0.38)
        jump(s, m, (0, -1.2)); ear_wire(s, m, (0, 0.2))
    return pair(one, 26)


@piece("hang")
def d04_bead_bar():
    def one(s, m, st, sx):
        nib(s, m, [(0, -2), (0.6 * sx, -14), (0, -26), (-0.4 * sx, -34)], w=0.55, pen=1.57, hair=0.6, taper=(0.0, 0.25))
        for i, (y, d) in enumerate(((-5, 3.2), (-10.5, 2.8), (-15.5, 2.5), (-20, 2.2), (-24, 1.8), (-27.5, 1.5))):
            bead(s, m, st, (0.3 * sx, y), d, ["moonstone", "aquamarine", "londonblue"][i % 3], z=0.4)
            spike(s, m, (0, y - d * 0.6), (2.6 * sx * (1 if i % 2 else -1), y - d * 0.6 - 1.8), r0=0.4, bend=0.3)
        jump(s, m, (0, -0.8)); ear_wire(s, m, (0, 0.6))
    return pair(one, 20)


@piece("hang")
def d05_tear_pane():
    def one(s, m, st, sx):
        o = smooth([(0, -2), (5.5, -10), (6.5, -17), (3.5, -22), (0, -23), (-3.5, -22), (-6.5, -17), (-5.5, -10)], 8, closed=True)[:, :2]
        nib(s, m, o, w=1.0, closed=True, taper=(0, 0), hair=0.4, pen=0.4)
        lead(s, m, [(0, -3), (0, -12.5)], r=0.45); lead(s, m, [(-6.4, -16), (0, -12.5), (6.4, -16)], r=0.45)
        for cell, kd in ((np.array([(-0.7, -3.8), (-5, -10.5), (-6, -15.3), (-0.7, -12.2)]), "garnet"),
                         (np.array([(0.7, -3.8), (5, -10.5), (6, -15.3), (0.7, -12.2)]), "garnet"),
                         (np.array([(-5.8, -17.0), (0, -13.4), (5.8, -17.0), (3.4, -21.5), (-3.4, -21.5)]), "citrine")):
            glaze(s, m, st, smooth(cell, 6, closed=True)[:, :2], kd, margin=0.45)
        spike(s, m, (0, -23), (0, -28), r0=0.8)
        mirror(lambda sd: spike(s, m, (sd * 5.6, -9.5), (sd * 9.5, -6), r0=0.7, bend=0.3))
        jump(s, m, (0, -0.6)); ear_wire(s, m, (0, 0.8))
    return pair(one, 24)


@piece("hang")
def d06_ribbon_fall():
    def one(s, m, st, sx):
        y = np.linspace(-1, -34, 50)
        x = 3.2 * np.sin(y * 0.22) * sx
        ang = y * 0.18
        P = np.array([m.P(a, b, 0.0) for a, b in zip(x, y)])
        Nn = np.stack([np.sin(ang), np.zeros_like(ang), np.cos(ang)], 1)
        W = profile(np.linspace(0, 1, 50), [(0, 0.8), (0.2, 2.2), (0.7, 2.0), (1, TIP)])
        blade(s, P, W, np.maximum(W * 0.18, 0.32), normal=Nn, k=0.3)
        for f, L, kd in ((0.28, 5, "amethyst"), (0.55, 4, "londonblue"), (0.8, 4, "amethyst")):
            j = int(f * 49)
            pane(s, m, st, (x[j], y[j]), "marquise", L, L / 2, kd, ang=math.pi / 2, vein=0.45)
        jump(s, m, (0, 0)); ear_wire(s, m, (0, 1.4))
    return pair(one, 22)


@piece("hang")
def d07_thorn_chandelier():
    def one(s, m, st, sx):
        nib(s, m, [(0, -1), (0, -30)], w=0.5, pen=1.57, hair=0.8, taper=(0, 0.1))
        for i, (y, R) in enumerate(((-7, 4.5), (-16, 3.6), (-24, 2.8))):
            for j in range(7):
                a = 2 * math.pi * j / 7
                s.stroke(np.array([m.P(0, y, 0), m.P(R * math.cos(a), y + 0.5, R * math.sin(a)),
                                   m.P(R * 1.3 * math.cos(a), y - 2.2, R * 1.3 * math.sin(a))]),
                         np.array([0.6, 0.45, 0.12]), k=0.3)
            bead(s, m, st, (0, y - 2.2), 2.4 - 0.3 * i, ["garnet", "amethyst", "garnet"][i], z=0.0)
        spike(s, m, (0, -30), (0, -34), r0=0.5)
        jump(s, m, (0, 0)); ear_wire(s, m, (0, 1.4))
    return pair(one, 24)


@piece("hang")
def d08_comet_fall():
    def one(s, m, st, sx):
        thorns(s, m, st, (0, -3), 4.0, "topaz", L=6.0, n=5, reach=(0.6, 1.6), seed=6, spin=math.pi / 2)
        strokes = []
        for e in ((-3 * sx, -34), (1.5 * sx, -38), (5 * sx, -32)):
            c, _ = nib(s, m, [(0, -5), (e[0] * 0.5 + 1.5 * sx, (e[1] - 5) / 2), e], w=0.8, pen=1.2, taper=(0.05, 0.4))
            strokes.append(c)
        for f, d in ((0.3, 2.5), (0.5, 2.0), (0.68, 1.5), (0.84, 1.5)):
            j = int(f * len(strokes[1])); p = (strokes[0][min(j, len(strokes[0]) - 1)] + strokes[1][j]) / 2
            pane(s, m, st, tuple(p), "round", d, d, "londonblue", vein=0.3)
        jump(s, m, (0, 0.6)); ear_wire(s, m, (0, 2.0))
    return pair(one, 22)


# =============================================================== PIERCINGS (tops, mirrored pairs)
def tops(fn, gap=12):
    s = Scene(); st = []
    for sx in (-1, 1):
        m = Flat(o=(sx * gap / 2, 0, 0)); fn(s, m, st, sx); pin(s, m, (0, 0))
    return s, st


@piece("flat")
def a01_half_wings():
    return tops(lambda s, m, st, sx: wing(s, m, st, sx=0.2, sy=0.2, rot=0.35 * sx, t=(-1 * sx, -0.5), mirror=sx < 0, pal=["garnet", "amethyst"],
                                         costa=0.42, sizes=[("marquise", 3.5, 1.8), ("round", 2, 2), ("round", 1.5, 1.5)], vein_w=0.25, veins=False, seed=3), 16)


@piece("flat")
def a02_upturned_horns():
    def one(s, m, st, sx):
        spike(s, m, (0, 0), (2.8 * sx, 5.5), r0=1.1, bend=0.4, side=-sx, z1=1.2)
        thorns(s, m, st, (0, 0), 2.0, "garnet", n=4, reach=(0.6, 0.8), wire=0.3, seed=1)
    return tops(one, 10)


@piece("flat")
def a03_fleur_pair():
    return tops(lambda s, m, st, sx: fleur(s, m, st, 0, 0, 3.6, kinds=("londonblue",), glaze_arms=(1,), w=0.38, centre=None), 12)


@piece("flat")
def a04_stalk_pair():
    def one(s, m, st, sx):
        for a, L, kd in ((1.57, 5.5, "aquamarine"), (1.57 + 0.55 * sx, 4.0, None), (1.57 - 0.5 * sx, 3.2, None)):
            stalk(s, m, st, (0, 0), (L * math.cos(a), L * math.sin(a)), d=1.6 if kd else 1.0, kind=kd, bend=0.2 * sx, r=0.28)
        ball(s, m, (0, 0), 0.9)
    return tops(one, 10)


@piece("flat")
def a05_lancet_pair():
    return tops(lambda s, m, st, sx: lancet(s, m, st, 0, -2.6, 2.1, 6.8, lights=1, kind="garnet", w=0.4,
                                            sizes=[("marquise", 4, 2), ("round", 1.5, 1.5)]), 10)


@piece("flat")
def c01_rose_dimples():
    return tops(lambda s, m, st, sx: rose(s, m, st, 0, 0, 3.2, n=6, kinds=("amethyst", "citrine"), w=0.32, flicks=True), 12)


@piece("flat")
def c02_moth_dimples():
    def one(s, m, st, sx):
        for sd in (1, -1):
            for up, sz in ((1, (3.6, 3.2)), (-1, (2.6, 2.4))):
                o = smooth([(sd * 0.4, 0.2 * up), (sd * sz[0], sz[1] * up), (sd * sz[0] * 1.1, 0.2 * up)], 6, closed=True)[:, :2]
                nib(s, m, o, w=0.3, closed=True, taper=(0, 0), hair=0.6)
                pane(s, m, st, (sd * sz[0] * 0.62, sz[1] * 0.42 * up), "round", 1.5, 1.5, "londonblue" if up > 0 else "aquamarine", vein=0.22)
        s.ellipsoid(m.P(0, 0, 0.6), (0.55, 2.2, 0.6), k=0.3)
    return tops(one, 14)


@piece("flat")
def c03_briar_dimples():
    def one(s, m, st, sx):
        thorns(s, m, st, (0, 0), 3.0, "garnet", n=3, reach=(0.6, 0.9), wire=0.32, seed=4)
        for a in (0.4, 2.5, 4.6):
            spike(s, m, (1.4 * math.cos(a), 1.4 * math.sin(a)), (4.0 * math.cos(a + 0.3), 4.0 * math.sin(a + 0.3)), r0=0.45, bend=0.2)
    return tops(one, 14)


@piece("flat")
def c04_swash_dimples():
    return tops(lambda s, m, st, sx: curl(s, m, st, 0, 0, 2.0, a0=0.5, w=0.55, kind="citrine", cw=sx,
                                          tail=np.array([(-2.2 * sx, -2.5), (-1.0 * sx, -4.8)])), 12)


@piece("flat")
def c05_comet_dimples():
    def one(s, m, st, sx):
        for a in range(5):
            b = a * 2 * math.pi / 5 + 0.3
            spike(s, m, (0, 0), (2.2 * math.cos(b), 2.2 * math.sin(b)), r0=0.6, bend=0.0)
        thorns(s, m, st, (0, 0), 2.0, "aquamarine", n=3, reach=(0.6, 0.7), wire=0.28)
        nib(s, m, [(0.8 * sx, -0.8), (3.5 * sx, -2.0), (7 * sx, -2.2)], w=0.55, pen=1.2, taper=(0.05, 0.6))
        for x in (3.6, 5.5):
            pane(s, m, st, (x * sx, -1.1), "round", 1.5, 1.5, "aquamarine", vein=0.22)
    return tops(one, 18)


@piece("flat")
def sb01_glass_fangs():
    def one(s, m, st, sx):
        o = smooth([(-1.9, 1.5), (1.9, 1.5), (1.2, -2.5), (0.2 * sx, -6.0), (-1.2, -2.5)], 6, closed=True)[:, :2]
        nib(s, m, o, w=0.42, closed=True, taper=(0, 0), hair=0.5)
        pane(s, m, st, (0.05 * sx, -1.4), "marquise", 5, 2.5, "garnet", ang=math.pi / 2 + 0.05 * sx, vein=0.3)
    return tops(one, 10)


@piece("flat")
def sb02_hook_pair():
    def one(s, m, st, sx):
        nib(s, m, [(0, 1), (2.5 * sx, -1.5), (4.0 * sx, -4.5), (2.2 * sx, -6.3), (0.8 * sx, -5)], w=0.85, pen=0.6 * sx, taper=(0.0, 0.0))
        bead(s, m, st, (0.8 * sx, -5), 2.0, "londonblue")
        spike(s, m, (1.4 * sx, 0), (4.6 * sx, 2.2), r0=0.5, bend=0.3)
    return tops(one, 12)


@piece("flat")
def sb03_drip_panes():
    def one(s, m, st, sx):
        o = smooth([(0, 2.2), (2.2, -0.5), (1.4, -3.4), (0, -4.0), (-1.4, -3.4), (-2.2, -0.5)], 6, closed=True)[:, :2]
        nib(s, m, o, w=0.4, closed=True, taper=(0, 0), hair=0.5)
        pane(s, m, st, (0, -0.9), "pear", 4, 3, "amethyst", ang=-math.pi / 2, vein=0.3)
        stalk(s, m, st, (0, -4.0), (0.3 * sx, -6.6), d=1.2, r=0.25)
    return tops(one, 10)


@piece("flat")
def sb04_crescent_horns():
    def one(s, m, st, sx):
        nib(s, m, arc(0, 0.6, 3.2, math.pi * 1.05, math.pi * 1.95, 20), w=0.9, pen=1.57, hair=0.3, taper=(0.3, 0.3))
        for sd in (1, -1): spike(s, m, (sd * 3.0, -0.2), (sd * 3.8, 3.5), r0=0.6, bend=0.35, side=-sd)
        thorns(s, m, st, (0, -0.6), 2.5, "garnet", n=3, reach=(0.6, 0.8), wire=0.3, seed=3)
    return tops(one, 12)


@piece("flat")
def sb05_falling_stalks():
    def one(s, m, st, sx):
        ball(s, m, (0, 0), 0.9)
        for x, L, d, kd in ((-1.0, 4.0, 1.5, "aquamarine"), (0.2, 6.0, 2.0, "londonblue"), (1.3, 3.0, 1.5, "aquamarine")):
            stalk(s, m, st, (0, 0), (x * sx, -L), d=d, kind=kd, bend=0.12 * sx, r=0.26)
    return tops(one, 10)


def bar(s, m, L=38):
    s.cone(m.P(-L / 2, 0, -1.2), m.P(L / 2, 0, -1.2), 0.8, 0.8, k=0.3)
    for sx in (-1, 1): s.sphere(m.P(sx * (L / 2 + 1.4), 0, -1.2), 2.0, k=0.3)


@piece("flat")
def i01_glass_spine():
    s = Scene(); st = []
    bar(s, F)
    spine(s, F, st, [(-15, 0), (15, 0)], n=6, size=2.8, kind=["garnet", "amethyst"], grade=(1, 1), w=0.55)
    return s, st


@piece("flat")
def i02_script_bar():
    s = Scene(); st = []
    bar(s, F)
    nib(s, F, [(-16, -0.5), (-11, 2.5), (-9, -0.5), (-5, -2.8), (-1, 0), (3, 2.8), (6, 0.2), (9.5, -2.6), (13, 0), (16, 1)], w=1.2, pen=0.75, hair=0.22, taper=(0.08, 0.08))
    for x, y, kd in ((-10, 0.4, "citrine"), (-1.5, 0.2, "garnet"), (8, -0.6, "citrine")):
        curl(s, F, st, x, y + 2.2, 1.7, a0=-1.0, w=0.5, kind=kd, cw=1 if kd == "garnet" else -1)
    return s, st


@piece("flat")
def i03_membrane_span():
    s = Scene(); st = []
    bar(s, F)
    wing(s, F, st, sx=0.82, sy=0.42, t=(-18, 1.5), pal=["aquamarine", "londonblue", "amethyst"], costa=0.8, seed=6,
         sizes=[("marquise", 5, 2.5), ("marquise", 4, 2), ("round", 2.5, 2.5), ("round", 2, 2), ("round", 1.5, 1.5)], vein_w=0.4)
    return s, st


@piece("flat")
def i04_briar_bar():
    s = Scene(); st = []
    bar(s, F)
    nib(s, F, [(-18, 0), (-6, 0.8), (6, -0.8), (18, 0)], w=0.9, hair=0.8, taper=(0.05, 0.05), z=0.6)
    for i, x in enumerate((-14, -9, -3, 3, 9, 14)):
        sd = 1 if i % 2 else -1
        spike(s, F, (x, 0), (x + 2.0, 3.6 * sd), r0=0.6, bend=0.25)
    for x, kd in ((-6, "garnet"), (7, "amethyst")):
        for j in range(4):
            b = j * math.pi / 2 + 0.4
            s.stroke(np.array([F.P(x + 1.5 * math.cos(b), 1.5 * math.sin(b), -0.4), F.P(x + 2.6 * math.cos(b + 0.4), 2.6 * math.sin(b + 0.4), 1.5),
                               F.P(x + 0.9 * math.cos(b + 0.9), 0.9 * math.sin(b + 0.9), 4.0)]), np.array([0.45, 0.38, 0.12]), k=0.25)
        bead(s, F, st, (x, 0), 3.0, kd, z=1.6)
    return s, st


# =============================================================== PENDANTS
@piece("flat")
def p01_stained_wing():
    """The benchmark: fewer, larger panes; a swelling costa; thorn tips; a hooked-blade bail."""
    s = Scene(); st = []
    wing(s, F, st, sx=1.0, sy=1.0, pal=["garnet", "amethyst", "londonblue"], costa=1.6, seed=7,
         sizes=[("marquise", 8, 4), ("pear", 7, 5), ("marquise", 6, 3), ("pear", 6, 4), ("round", 4, 4), ("round", 3, 3), ("round", 2.5, 2.5)])
    nib(s, F, [(-1, -0.5), (-5, 2), (-8, 6), (-6, 9.5), (-3.5, 8)], w=1.4, pen=0.5, taper=(0.0, 0.3))
    bail(s, F, (-6.2, 11.5), R=2.0, r=0.65)
    for a, b, kd in (((-1, -1.5), (-4, -7.5), "garnet"), ((1.5, -2.5), (0.5, -8.5), None)):
        stalk(s, F, st, a, b, d=1.8 if kd else 1.2, kind=kd, bend=0.25)
    return s, st


@piece("flat")
def p02_whole_moth():
    s = Scene(); st = []
    for mr in (False, True):
        sx = -1 if mr else 1
        wing(s, F, st, sx=0.6, sy=0.6, rot=0.3 * sx, t=(sx * 2.2, 1.5), mirror=mr, pal=PAL["bruise"], seed=13 + mr, costa=1.1)
        wing(s, F, st, outline=HIND, sx=0.52, sy=0.52, rot=-0.12 * sx, t=(sx * 2.2, -1.2), mirror=mr, pal=PAL["bruise"][::-1], seed=15 + mr, costa=0.95)
        stalk(s, F, st, (sx * 0.6, 6.0), (sx * 5.5, 13.5), d=1.6, kind="garnet", bend=0.3 * sx)
    for y, d, kd in ((3.5, 3.5, "garnet"), (-1.5, 3.0, "amethyst"), (-6, 2.5, "garnet")):
        s.ellipsoid(F.P(0, y, 0.2), (d * 0.6, d * 0.65, 0.8), k=0.8)
        bead(s, F, st, (0, y), d, kd, z=0.8)
    spike(s, F, (0, -8), (0, -15), r0=1.1)
    bail(s, F, (0, 9.5), R=1.8, r=0.6)
    return s, st


@piece("flat")
def p03_reliquary():
    s = Scene(); st = []
    o = lancet_outline(9, 30) + [0, -15]
    nib(s, F, o, w=1.4, closed=True, taper=(0, 0), hair=0.6)
    s.ellipsoid(F.P(0, -2, -1.6), (8.0, 13.5, 1.2), k=0.8)
    thorns(s, Flat(o=(0, 0, -0.8)), st, (0, -3), 7.0, "garnet", L=10.0, n=5, reach=(0.6, 1.0), seed=8, spin=math.pi / 2, basket=False)
    d = hinge(Flat(o=(0, 0, 2.2)), (-9.5, 0), (0, 1), 0.85)
    lancet(s, d, st, 0, -15, 9, 30, lights=3, kind=["londonblue", "amethyst", "londonblue"], w=1.1)
    for y in (-10, 0, 9): s.cone(F.P(-9.6, y - 2, 1.0), F.P(-9.6, y + 2, 1.0), 1.0, 1.0, k=0.3)
    mirror(lambda sx: nib(s, F, [(sx * 8.5, -14.5), (sx * 14, -11), (sx * 15, -4), (sx * 12, -1)], w=1.3, pen=0.4 * sx, taper=(0.05, 0.5)))
    spike(s, F, (0, -15.5), (0, -24), r0=1.3)
    bail(s, F, (0, 19.5), R=2.2, r=0.7)
    return s, st
