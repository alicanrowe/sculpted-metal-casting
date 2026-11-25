"""Stained-glass, batch two: 64 more pieces, no repeats of glass64.
New structures: thorn bows, crescents, hook crowns, vertebra bands, cages, split wings, ladders.
Each returns (Scene, stones). Units mm. Flat pieces face +z; rings: finger along y, top +z."""
import math
import numpy as np
from sdf import Scene, resample, profile
from kit import *   # noqa
from kit import TIP, blade
from glass64 import F, top, saddle, mirror, ring_pos, pair, tops, bar

PIECES = {}


def piece(kind):
    def deco(fn):
        PIECES[fn.__name__] = (fn, kind); return fn
    return deco


R7 = (14.0 + 0.8128 * 7) / 2


# ---------------------------------------------------------------- new motifs
def loop_outline(cx, cy, L, H, ang, n=24):
    """A teardrop loop starting at (cx, cy), pointing along ang (a bow loop / petal)."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = L * (1 - np.cos(t)) / 2
    y = H * np.sin(t) * (1 - np.cos(t)) / 2 * 0.9
    c, s_ = math.cos(ang), math.sin(ang)
    return np.stack([cx + c * x - s_ * y, cy + s_ * x + c * y], 1)


def bow(s, m, st, cx, cy, size, kinds=("londonblue", "aquamarine"), knot="londonblue", w=None, tails=True, droop=0.35, glaze_it=True):
    """Thorn bow: two glazed loops, a thorn-claw knot stone, hooked tails with barbs."""
    w = w or size * 0.11
    for sd, kd in ((1, kinds[0]), (-1, kinds[-1])):
        o = loop_outline(cx, cy, size, size * 0.72, (0 if sd > 0 else math.pi) + droop * 0.4 * sd)
        nib(s, m, o, w=w, closed=True, pen=0.6, hair=0.35, taper=(0, 0))
        if glaze_it:
            inner = (o - o.mean(0)) * 0.82 + o.mean(0)
            glaze(s, m, st, inner, kd, margin=max(0.25, size * 0.03), gap=max(0.35, size * 0.04),
                  sizes=[("pear", size * 0.42, size * 0.3), ("marquise", size * 0.36, size * 0.18), ("round", size * 0.16, size * 0.16),
                         ("round", max(1.5, size * 0.11), max(1.5, size * 0.11))], seed=int(size * 10) + sd)
        for f in (0.35, 0.62):
            p = o[int(f * len(o))]; d = p - o.mean(0); d = d / (np.linalg.norm(d) + 1e-9)
            spike(s, m, tuple(p), tuple(p + d * size * 0.28 + np.array([-d[1], d[0]]) * size * 0.1 * sd), r0=w * 0.55, bend=0.2)
        if tails:
            nib(s, m, [(cx, cy), (cx + sd * size * 0.25, cy - size * 0.55), (cx + sd * size * 0.15, cy - size * 1.0),
                       (cx + sd * size * 0.42, cy - size * 1.15)], w=w * 1.1, pen=0.7 * sd, hair=0.25, taper=(0.0, 0.5))
    if knot:
        thorns(s, m, st, (cx, cy), max(2.0, size * 0.32), knot, n=4, reach=(0.6, 1.2), wire=max(0.28, w * 0.4), seed=int(size))
    else:
        ball(s, m, (cx, cy), w * 1.3)


def crescent(s, m, st, cx, cy, R, kind="londonblue", ang=0.0, w=None, fill=0.62, sizes=None, horns=True, seed=0):
    """A calligraphic crescent: swelling outer arc, hairline inner arc, glazed between."""
    w = w or R * 0.12
    a0, a1 = ang + 0.55, ang + 2 * math.pi - 0.55
    outer = arc(cx, cy, R, a0, a1, 40)
    off = R * (1 - fill)
    inner = arc(cx + off * math.cos(ang), cy + off * math.sin(ang), R * fill + off * 0.2, a1 - 0.25, a0 + 0.25, 30)
    o = np.vstack([outer, inner])
    nib(s, m, o, w=w, closed=True, pen=ang + 1.57, hair=0.25, taper=(0, 0))
    glaze(s, m, st, (o - o.mean(0)) * 0.9 + o.mean(0), kind, margin=max(0.25, R * 0.05), gap=max(0.35, R * 0.04), seed=seed,
          sizes=sizes or [("marquise", R * 0.5, R * 0.24), ("pear", R * 0.42, R * 0.3), ("round", R * 0.2, R * 0.2), ("round", max(1.5, R * 0.13), max(1.5, R * 0.13))])
    if horns:
        for a in (a0, a1):
            p = np.array([cx + R * math.cos(a), cy + R * math.sin(a)])
            d = np.array([math.cos(a), math.sin(a)])
            spike(s, m, tuple(p), tuple(p + d * R * 0.35 + np.array([-d[1], d[0]]) * R * 0.25 * (1 if a == a0 else -1)), r0=w * 0.6, bend=0.3)


def hook_crown(s, m, st, cx, cy, R, n=8, kind="amethyst", D=None, w=None, z=0.0, seed=0):
    """A crown of hooked broad-nib strokes curling inward round a claw-set stone."""
    D = D or R * 0.9; w = w or R * 0.14
    thorns(s, m, st, (cx, cy), D, kind, n=4, reach=(0.6, 1.0), wire=max(0.3, w * 0.5), seed=seed)
    for i in range(n):
        a = 2 * math.pi * i / n
        r0 = D * 0.55
        p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a))
        p1 = (cx + R * math.cos(a + 0.2), cy + R * math.sin(a + 0.2))
        p2 = (cx + R * 1.12 * math.cos(a + 0.55), cy + R * 1.12 * math.sin(a + 0.55))
        p3 = (cx + R * 0.88 * math.cos(a + 0.75), cy + R * 0.88 * math.sin(a + 0.75))
        nib(s, m, [p0, p1, p2, p3], w=w, pen=a, hair=0.3, taper=(0.05, 0.6), z=z)


def cage(s, m, st, c, R, H, kind="garnet", n=6, w=0.5, top_ball=True):
    """A thorn cage: n hooked ribs over a loose bead, stood on plane m at c."""
    bead(s, m, st, c, R * 1.25, kind, z=R * 0.8)
    for j in range(n):
        b = 2 * math.pi * j / n
        q0 = (c[0] + R * math.cos(b), c[1] + R * math.sin(b))
        pts = np.array([m.P(*q0, -0.3), m.P(c[0] + R * 1.35 * math.cos(b + 0.3), c[1] + R * 1.35 * math.sin(b + 0.3), H * 0.45),
                        m.P(c[0] + R * 0.4 * math.cos(b + 0.8), c[1] + R * 0.4 * math.sin(b + 0.8), H)])
        s.stroke(pts, np.array([w, w * 0.85, w * 0.3]), k=0.25)
    s.torus(m.P(c[0], c[1], -0.1), R * 1.05, w * 0.9, normal=m.N(*c), k=0.3)
    if top_ball: ball(s, m, c, w * 0.9, z=H)


def _split(o, a, b):
    """Split a closed polygon by the infinite line a->b; returns the two sides (each closed by the cut)."""
    d = b - a
    sd = d[0] * (o[:, 1] - a[1]) - d[1] * (o[:, 0] - a[0])
    n = len(o); out = {1: [], -1: []}; cuts = []
    for i in range(n):
        p, q = o[i], o[(i + 1) % n]; s0, s1 = sd[i], sd[(i + 1) % n]
        out[1 if s0 > 0 else -1].append(p)
        if (s0 > 0) != (s1 > 0):
            x = p + (q - p) * (s0 / (s0 - s1)); out[1].append(x); out[-1].append(x)
    return np.array(out[1]), np.array(out[-1])


def split_wing(s, m, st, sx=1.0, t=(0, 0), rot=0.0, mirror_=False, pal=PAL["night"], gap=1.6, costa=1.2, seed=1, sizes=None):
    """A wing cracked in two across its span; the halves sit a little apart, stitched by leads."""
    o = smooth(xform(WING, sx=sx, sy=sx, rot=rot, t=t, mirror=mirror_), 6, closed=True)[:, :2]
    c = o.mean(0)
    a = np.array(xform([(26, 10)], sx=sx, sy=sx, rot=rot, t=t, mirror=mirror_)[0]); b = np.array(xform([(20, -16)], sx=sx, sy=sx, rot=rot, t=t, mirror=mirror_)[0])
    d = (b - a) / np.linalg.norm(b - a); nrm_ = np.array([-d[1], d[0]])
    halves = []
    for side, P in zip((1, -1), _split(o, a, b)):
        P = P + nrm_ * gap * 0.5 * side
        nib(s, m, P, w=costa, closed=True, pen=0.4, hair=0.4, taper=(0, 0))
        glaze(s, m, st, (P - P.mean(0)) * 0.9 + P.mean(0), pal, root=tuple(o[0]), margin=0.5 * sx + 0.2, seed=seed + side,
              sizes=sizes or [("marquise", 7 * sx, 3.5 * sx), ("pear", 6 * sx, 4 * sx), ("round", 3.5 * sx, 3.5 * sx), ("round", 2.2 * sx, 2.2 * sx), ("round", 1.5, 1.5)])
        halves.append(P)
    ab = [a + (b - a) * f for f in (0.15, 0.45, 0.75)]
    for p in ab:
        lead(s, m, [tuple(p - nrm_ * gap * 1.2), tuple(p + nrm_ * gap * 1.2)], r=0.3 + 0.25 * sx)
    return halves


def vertebra_band(s, m, st, C, n, size, kinds, w=0.7):
    """Spine laid along a Cyl mapper all the way round (closed band of vertebrae)."""
    xs = np.linspace(0, C, n + 1)[:-1]
    nib(s, m, [(x, 0) for x in np.linspace(0, C, 120)], w=w * 0.9, pen=1.57, hair=0.8, taper=(0, 0))
    for i, x in enumerate(xs):
        g = size
        for sd in (1, -1):
            nib(s, m, [(x, 0), (x + g * 0.3, sd * g * 0.9), (x - g * 0.25, sd * g * 1.35), (x - g * 0.55, sd * g * 1.05)],
                w=w, pen=0.9 * sd, hair=0.3, taper=(0.03, 0.5))
        kd = kinds[i % len(kinds)]
        if kd: pane(s, m, st, (x, 0), "round", g * 0.8, g * 0.8, kd, vein=0.4)


# =============================================================== RINGS
@piece("ring")
def r11_thorn_bow():
    """Thorn Bow: a stained-glass bow tied on the finger, a claw-set blue knot, barbed tails."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.2); saddle(s, Rb, 3.5, 3)
    bow(s, top(Rb, 0.7), st, 0, 0.6, 7.0, kinds=("londonblue", "aquamarine"), knot="londonblue", droop=0.25)
    return s, st


@piece("ring")
def r12_vertebra_band():
    """Vertebra Band: the whole band is a spine; a glass bead in every vertebra."""
    s = Scene(); st = []
    m = Cyl(R7 + 1.0)
    vertebra_band(s, m, st, 2 * math.pi * m.R, 11, 2.4, ["garnet", "amethyst", "garnet", "londonblue"], w=0.95)
    return s, st


@piece("ring")
def r13_hook_crown():
    """Hook Crown: an oval amethyst ringed by broad-nib hooks that curl in like a closing hand."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.4); saddle(s, Rb, 4, 4)
    hook_crown(s, top(Rb, 0.8), st, 0, 0, 7.0, n=7, kind="amethyst", D=6.5, w=0.95, seed=4)
    return s, st


@piece("ring")
def r14_crescent_signet():
    """Crescent Signet: a glazed crescent laid across the face, horned, an open counter."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=3.0)
    saddle(s, Rb, 4, 3)
    crescent(s, top(Rb, 0.9), st, 0, 0, 7.5, kind=["londonblue", "aquamarine"], ang=0.3, w=1.0, seed=3)
    return s, st


@piece("ring")
def r15_scythe():
    """Scythe: one swept blade curls half way round the finger; stones channel its inner edge."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.0)
    m = Cyl(Rb + 0.5)
    h = spike(s, m, (-4, -1.5), (24, 6.5), r0=2.6, bend=0.25, side=1, z0=0.3, z1=1.6)
    for f, d in ((0.12, 2.6), (0.26, 2.2), (0.4, 1.9), (0.53, 1.6), (0.65, 1.5)):
        p = h[int(f * len(h))]
        pane(s, m, st, (p[0], p[1] - 0.2), "round", d, d, "garnet", vein=0.35)
    stalk(s, m, st, (-4, -1.5), (-9, -5.5), d=1.6, kind="garnet", bend=-0.3)
    return s, st


@piece("ring")
def r16_cage_ring():
    """Cage Ring: a loose garnet rattles in a cage of hooked ribs; barbs at the shoulders."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.2); saddle(s, Rb, 3.5, 3.5)
    m = top(Rb, 0.4)
    cage(s, m, st, (0, 0), 3.0, 6.5, "garnet", n=6, w=0.6)
    mirror(lambda sx: spike(s, Flat(o=(0, 0, Rb - 0.2)), (sx * 3.0, 0), (sx * 7.5, -1.5), r0=0.8, bend=0.3, z1=1.5))
    return s, st


@piece("ring")
def r17_quatrefoil_band():
    """Quatrefoil Band: leaded quatrefoils all round, each lobe a different glass."""
    s = Scene(); st = []
    m = Cyl(R7 + 0.9)
    C = 2 * math.pi * m.R
    for y in (-3.8, 3.8):
        nib(s, m, [(x, y) for x in np.linspace(0, C, 90)], w=0.75, pen=0.0, hair=0.9, taper=(0, 0))
    n = 7; dx = C / n
    for i in range(n):
        x = (i + 0.5) * dx
        fleur(s, Flat(o=m.P(x, 0, 0), u=m.T(x, 0)[0], v=m.T(x, 0)[1]), st, 0, 0, 3.2,
              kinds=(["garnet", "amethyst"], ["londonblue", "aquamarine"])[i % 2], w=0.38, centre=None, glaze_arms=(0, 2))
        lead(s, m, [(i * dx, -3.8), (i * dx, 3.8)], r=0.45)
    return s, st


@piece("ring")
def r18_drip_signet():
    """Drip Signet: a pear slips off the edge of the face, leaving glass drips on stalks."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.6)
    s.ellipsoid((0, 0, Rb + 0.3), (5.5, 5.0, 1.4), k=1.2)
    m = top(Rb, 1.3)
    nib(s, m, smooth([(-5, 4), (5, 4), (5.5, -1), (2, -5), (-3, -5.5), (-5.5, 0)], 8, closed=True)[:, :2], w=0.9, closed=True, taper=(0, 0), hair=0.5)
    pane(s, m, st, (0.5, -0.5), "pear", 8, 5.5, "citrine", ang=-1.9, vein=0.6)
    for x, L, d, kd in ((-3.0, 4.0, 1.5, "citrine"), (-0.6, 6.5, 2.0, "garnet"), (1.8, 3.0, 1.4, None)):
        stalk(s, m, st, (x, -5.0), (x * 1.1, -5.0 - L), d=d, kind=kd, bend=0.15, z1=-1.5)
    return s, st


@piece("ring")
def r19_split_wing():
    """Split Wing: a stained-glass wing cracked in two across the finger, barbs stitching it."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=1.8)
    split_wing(s, Cyl(Rb + 0.4), st, sx=0.42, t=(-9.5, 1.8), pal=PAL["bruise"], gap=1.2, costa=1.9, seed=8,
               sizes=[("marquise", 4, 2), ("round", 2.2, 2.2), ("round", 1.5, 1.5)])
    return s, st


@piece("ring")
def r20_lantern():
    """Lantern: a tiny lancet lantern stands on the band, a moonstone bead burning inside."""
    s = Scene(); st = []
    Rb, _ = shank(s, top_w=2.6); saddle(s, Rb, 4.2, 4.2)
    m = top(Rb, 0.8)
    c = Cyl(3.4, o=m.P(0, 0, 4.2))
    cz = Flat(o=m.P(0, 0, 0), u=(1, 0, 0), v=(0, 0, 1))
    for i in range(6):
        a = 2 * math.pi * i / 6
        p0 = m.P(3.4 * math.cos(a), 3.4 * math.sin(a), 0.2); p1 = m.P(3.4 * math.cos(a), 3.4 * math.sin(a), 7.5)
        s.cone(p0, p1, 0.5, 0.42, k=0.3)
        s.stroke(np.array([p1, m.P(1.6 * math.cos(a), 1.6 * math.sin(a), 9.6), m.P(0, 0, 10.8)]), np.array([0.42, 0.35, 0.3]), k=0.3)
    for z in (0.3, 7.5): s.torus(m.P(0, 0, z), 3.4, 0.5, normal=(0, 0, 1), k=0.3)
    bead(s, m, st, (0, 0), 3.6, "moonstone", z=3.0)
    s.cone(m.P(0, 0, 0.3), m.P(0, 0, 1.4), 0.6, 0.6)
    s.cone(m.P(0, 0, 10.8), m.P(0, 0, 13.5), 0.55, 0.05)
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        pane(s, Flat(o=m.P(3.45 * math.cos(a + 0.52), 3.45 * math.sin(a + 0.52), 3.8), u=(-math.sin(a + 0.52), math.cos(a + 0.52), 0), v=(0, 0, 1)),
             st, (0, 0), "marquise", 5.5, 2.4, ["garnet", "citrine", "garnet"][i], ang=math.pi / 2, vein=0.4)
    return s, st


# =============================================================== BUCKLES
@piece("flat")
def b09_thorn_bow():
    """Thorn Bow: a big stained-glass bow, claw-set sapphire-blue knot, tails hooked like blades."""
    s = Scene(); st = []
    bow(s, F, st, 0, 4, 26, kinds=(["londonblue", "aquamarine"], ["aquamarine", "londonblue"]), knot="londonblue", w=2.2, droop=0.3)
    buckle_back(s, F, 44, 28)
    return s, st


@piece("flat")
def b10_four_roses():
    """Four Roses: a leaded cross of four small rose windows, thorns where the leads meet."""
    s = Scene(); st = []
    nib(s, F, smooth([(-28, -22), (28, -22), (28, 22), (-28, 22)], 4, closed=True)[:, :2], w=1.6, closed=True, taper=(0, 0), hair=0.5)
    lead(s, F, [(-28, 0), (28, 0)], r=0.7); lead(s, F, [(0, -22), (0, 22)], r=0.7)
    for (x, y), ks in (((-14, 11), ("garnet", "citrine")), ((14, 11), ("amethyst", "londonblue")),
                       ((-14, -11), ("amethyst", "londonblue")), ((14, -11), ("garnet", "citrine"))):
        rose(s, F, st, x, y, 8.8, n=6, kinds=ks, w=0.8)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            lead(s, F, [(x + d[0] * 8.8, y + d[1] * 8.8), (x + d[0] * (14 if d[0] else 0) * (1 if d[0] else 0) + d[0] * 0 + (0 if d[0] else 0), y + d[1] * 11)], r=0.5) if False else None
        lead(s, F, [(x + 8.8 * np.sign(-x), y), (0, y)], r=0.5); lead(s, F, [(x, y + 8.8 * np.sign(-y)), (x, 0)], r=0.5)
        lead(s, F, [(x - 8.8 * np.sign(-x), y), (28 * np.sign(x), y)], r=0.5); lead(s, F, [(x, y - 8.8 * np.sign(-y)), (x, 22 * np.sign(y))], r=0.5)
    thorns(s, F, st, (0, 0), 5.0, "garnet", n=4, reach=(0.6, 1.4), seed=2)
    for sx in (1, -1):
        for sy in (1, -1):
            spike(s, F, (sx * 28, sy * 22), (sx * 33, sy * 28), r0=1.2, bend=0.3)
    buckle_back(s, F, 44, 32)
    return s, st


@piece("flat")
def b11_vertebral_cross():
    """Vertebral Cross: two spines cross; a big oval in a claw at the crossing."""
    s = Scene(); st = []
    spine(s, F, st, [(-30, 0), (-8, 0)], n=3, size=4.0, kind=["londonblue", "amethyst"], grade=(0.7, 1.0))
    spine(s, F, st, [(8, 0), (30, 0)], n=3, size=4.0, kind=["amethyst", "londonblue"], grade=(1.0, 0.7))
    spine(s, F, st, [(0, 22), (0, 8)], n=2, size=3.6, kind="aquamarine", grade=(0.7, 1.0))
    spine(s, F, st, [(0, -8), (0, -24)], n=3, size=3.6, kind="aquamarine", grade=(1.0, 0.6))
    s.ellipsoid(F.P(0, 0, -0.4), (8, 7, 1.4), k=1.2)
    thorns(s, F, st, (0, 0), 10.0, "amethyst", L=13.0, n=6, reach=(0.6, 1.8), seed=11)
    buckle_back(s, F, 44, 30)
    return s, st


@piece("flat")
def b12_split_wing():
    """Split Wing: a full stained-glass wing broken along a jagged lead, stitched with barbs."""
    s = Scene(); st = []
    split_wing(s, F, st, sx=1.25, t=(-29, 4), pal=PAL["tide"], gap=2.4, costa=1.4, seed=5)
    buckle_back(s, F, 48, 30)
    return s, st


@piece("flat")
def b13_crescent_nest():
    """Crescent Nest: a big horned crescent; three thorn stars caught in its open counter."""
    s = Scene(); st = []
    crescent(s, F, st, 0, 0, 25, kind=["garnet", "amethyst", "londonblue"], ang=0.0, w=2.6, fill=0.6, seed=7)
    for (x, y), kd, D in (((6, 6), "garnet", 4.0), ((10, -4), "citrine", 3.0), ((3, -10), "garnet", 3.5)):
        thorns(s, F, st, (x, y), D, kd, n=4, reach=(0.6, 1.8), seed=int(x))
        lead(s, F, [(x, y), (-9 if x < 8 else -8, y * 1.2)], r=0.5)
    buckle_back(s, F, 40, 34)
    return s, st


@piece("flat")
def b14_rose_lancet():
    """Rose Lancet: a lancet arch carrying a rose window in its head, glass below."""
    s = Scene(); st = []
    o = lancet_outline(16, 46) + [0, -24]
    nib(s, F, o, w=1.9, closed=True, taper=(0, 0), hair=0.5, pen=0.3)
    rose(s, F, st, 0, 7, 9.5, n=8, kinds=("londonblue", "aquamarine", "topaz"), w=0.9)
    lead(s, F, [(-15.5, -4), (15.5, -4)], r=0.6); lead(s, F, [(0, -2.5), (0, -24)], r=0.6)
    for sx in (1, -1):
        cell = np.array([(sx * 1.0, -5), (sx * 15, -5), (sx * 15.5, -23), (sx * 1.0, -23)])
        glaze(s, F, st, cell, ["garnet", "amethyst"], root=(0, -5), margin=0.8, seed=30 + sx)
        lead(s, F, [(sx * 9.4, 3), (sx * 15.5, 0)], r=0.5)
    spike(s, F, (0, 22), (0, 30), r0=1.3)
    buckle_back(s, F, 30, 42)
    return s, st


@piece("flat")
def b15_hook_script():
    """Hook Script: two broad-nib hooks interlock like a monogram; their counters are glazed."""
    s = Scene(); st = []
    A = [(-24, -12), (-20, 8), (-8, 18), (4, 12), (2, 0), (-8, -4), (-12, 4), (-6, 8)]
    B = [(24, 12), (20, -8), (8, -18), (-4, -12), (-2, 0), (8, 4), (12, -4), (6, -8)]
    nib(s, F, A, w=3.0, pen=0.78, hair=0.12, taper=(0.1, 0.4))
    nib(s, F, B, w=3.0, pen=0.78, hair=0.12, taper=(0.1, 0.4))
    pane(s, F, st, (-7.5, 2.5), "round", 5, 5, "garnet", vein=0.5)
    pane(s, F, st, (7.5, -2.5), "round", 5, 5, "garnet", vein=0.5)
    pane(s, F, st, (-12, 9), "pear", 7, 5, "amethyst", ang=2.2, vein=0.5)
    pane(s, F, st, (12, -9), "pear", 7, 5, "amethyst", ang=-0.9, vein=0.5)
    lead(s, F, [(-12, 9), (-18, 4)], r=0.6); lead(s, F, [(12, -9), (18, -4)], r=0.6)
    lead(s, F, [(-7.5, 2.5), (-2, 0), (7.5, -2.5)], r=0.6)
    for a, b in (((-24, -12), (-30, -18)), ((24, 12), (30, 18))):
        stalk(s, F, st, a, b, d=2.0, kind="garnet", bend=0.3)
    buckle_back(s, F, 44, 30)
    return s, st


@piece("flat")
def b16_ribbed_oval():
    """Ribbed Oval: an oval frame whose ribs hook inward to clutch one large oval stone."""
    s = Scene(); st = []
    th = np.linspace(0, 2 * math.pi, 60, endpoint=False)
    o = np.stack([30 * np.cos(th), 21 * np.sin(th)], 1)
    nib(s, F, o, w=2.0, closed=True, pen=0.0, hair=0.5, taper=(0, 0))
    s.ellipsoid(F.P(0, 0, -0.6), (9, 7, 1.4), k=1.2)
    thorns(s, F, st, (0, 0), 12.0, "londonblue", L=15.0, n=6, reach=(0.6, 1.6), seed=3)
    for i in range(14):
        a = 2 * math.pi * i / 14
        p = np.array([30 * math.cos(a), 21 * math.sin(a)])
        q = np.array([11 * math.cos(a + 0.12), 8.5 * math.sin(a + 0.12)])
        mid = (p + q) / 2 + np.array([-math.sin(a), math.cos(a)]) * 3.0
        nib(s, F, [tuple(p), tuple(mid), tuple(q), tuple(q * 0.92 + np.array([-math.sin(a), math.cos(a)]) * 1.6)], w=1.1, pen=a, hair=0.3, taper=(0.0, 0.5))
        if i % 2: pane(s, F, st, tuple(mid * 1.0 + (p - q) * 0.12), "marquise", 4, 2, "aquamarine", ang=a + 0.3, vein=0.4)
    buckle_back(s, F, 44, 30)
    return s, st


# =============================================================== BRACELETS
@piece("ring")
def br09_spine_cuff():
    """Spine Cuff: an open cuff that is one long spine; vertebrae grow and fade with the wrist."""
    s = Scene(); st = []
    m = Cyl(29)
    C = 2 * math.pi * 29 * 0.84
    xs = np.linspace(-C / 2, C / 2, 15)
    nib(s, m, [(x, 0) for x in np.linspace(-C / 2, C / 2, 80)], w=1.4, pen=1.57, hair=0.8, taper=(0.04, 0.04))
    for i, x in enumerate(xs):
        g = 3.0 + 2.6 * math.sin(math.pi * i / (len(xs) - 1))
        for sd in (1, -1):
            nib(s, m, [(x, 0), (x + g * 0.3, sd * g * 0.9), (x - g * 0.25, sd * g * 1.35), (x - g * 0.55, sd * g * 1.05)], w=0.95, pen=0.9 * sd, hair=0.3, taper=(0.03, 0.5))
        pane(s, m, st, (x, 0), "round", g * 0.75, g * 0.75, ["londonblue", "amethyst", "garnet"][i % 3], vein=0.45)
    return s, st


@piece("flat")
def br10_lancet_links():
    """Lancet Links: small glazed lancets linked tip to sill by hooked strokes."""
    s = Scene(); st = []
    n = 10; R = 31
    for i in range(n):
        p, a = ring_pos(n, R, i)
        m = Flat(o=F.P(*p)).rot(a)
        lancet(s, m, st, 0, -5.5, 3.8, 11, lights=1, kind=["garnet", "amethyst", "londonblue"][i % 3], w=0.65, finial=False,
               sizes=[("marquise", 6, 3), ("round", 2, 2), ("round", 1.5, 1.5)])
        q, b = ring_pos(n, R, i + 0.5)
        mq = Flat(o=F.P(*q)).rot(b)
        nib(s, mq, [(0, -4.0), (1.4, -1.5), (-1.4, 1.5), (0, 4.0)], w=0.7, pen=0.0, taper=(0.15, 0.15))
        lead(s, F, [tuple(p + (q - p) * 0.0), tuple(q)], r=0.45, z=0.0) if False else None
    return s, st


@piece("ring")
def br11_hook_cuff():
    """Hook Cuff: a cuff of alternating hooks, each cradling a bead in its curl."""
    s = Scene(); st = []
    m = Cyl(29)
    C = 2 * math.pi * 29 * 0.82
    for y in (-7, 7):
        nib(s, m, [(x, y) for x in np.linspace(-C / 2, C / 2, 80)], w=1.0, pen=0.0, hair=0.9, taper=(0.03, 0.03))
    n = 12
    for i in range(n):
        x = -C / 2 + C * (i + 0.5) / n; sd = 1 if i % 2 else -1
        nib(s, m, [(x - 4, -7 * sd), (x + 1, -2 * sd), (x + 2.5, 3 * sd), (x - 0.5, 5.2 * sd), (x - 2, 2.6 * sd)], w=1.2, pen=0.7 * sd, hair=0.25, taper=(0.0, 0.3))
        bead(s, m, st, (x - 0.2, 2.4 * sd), 2.6, ["londonblue", "garnet", "moonstone"][i % 3])
    return s, st


@piece("flat")
def br12_moth_chain():
    """Moth Chain: a ring of small glazed moths holding wing to wing."""
    s = Scene(); st = []
    n = 9; R = 31
    for i in range(n):
        p, a = ring_pos(n, R, i)
        m = Flat(o=F.P(*p)).rot(a - math.pi / 2)
        for mr in (False, True):
            sx = -1 if mr else 1
            wing(s, m, st, sx=0.2, sy=0.2, rot=0.2 * sx, t=(sx * 0.8, 0.3), mirror=mr, pal=PAL["dusk"] if i % 2 else PAL["night"],
                 costa=0.45, veins=False, sizes=[("marquise", 3.5, 1.8), ("round", 2, 2), ("round", 1.5, 1.5)], thorn_tips=False, seed=40 + i)
        s.ellipsoid(m.P(0, -0.5, 0.4), (0.8, 3.0, 0.8), k=0.4)
        q, b = ring_pos(n, R, i + 0.5)
        t = np.array([-math.sin(b), math.cos(b)])
        s.cone(F.P(*(q - 4.2 * t)), F.P(*(q + 4.2 * t)), 0.7, 0.7, k=0.3)
    return s, st


@piece("ring")
def br13_comet_cuff():
    """Comet Cuff: a comet head on the top of the wrist; its glazed tail wraps round."""
    s = Scene(); st = []
    m = Cyl(29)
    C = 2 * math.pi * 29 * 0.8
    x0 = -C / 2 + 8
    thorns(s, Flat(o=m.P(x0, 0, 0), u=m.T(x0, 0)[0], v=m.T(x0, 0)[1]), st, (0, 0), 7.0, "topaz", L=9.0, n=6, reach=(0.6, 1.8), seed=5)
    strokes = []
    for e in (-8, -3, 3, 8):
        c, _ = nib(s, m, [(x0 + 3, 0), (x0 + 30, e * 0.6), (C / 2, e)], w=1.3, pen=1.57, hair=0.3, taper=(0.05, 0.3))
        strokes.append(c)
    for j, (a, b) in enumerate(zip(strokes[:-1], strokes[1:])):
        cell = np.vstack([a[len(a) // 5:], b[len(b) // 5:][::-1]])
        glaze(s, m, st, cell, ["topaz", "aquamarine", "londonblue"], root=(x0, 0), margin=0.6, seed=60 + j)
    return s, st


@piece("flat")
def br14_bow_links():
    """Bow Links: a chain of small thorn bows tied knot to knot."""
    s = Scene(); st = []
    n = 8; R = 31
    for i in range(n):
        p, a = ring_pos(n, R, i)
        m = Flat(o=F.P(*p)).rot(a)
        m = Flat(o=F.P(*p)).rot(a + math.pi / 2)
        bow(s, m, st, 0, 0, 5.2, kinds=(["garnet"], ["amethyst"]) if i % 2 else (["londonblue"], ["aquamarine"]), knot=None, tails=False, droop=0.0, w=0.65)
        bead(s, m, st, (0, 0), 2.2, "garnet" if i % 2 else "londonblue")
        q, b = ring_pos(n, R, i + 0.5)
        t = np.array([-math.sin(b), math.cos(b)])
        s.cone(F.P(*(q - 7.5 * t)), F.P(*(q + 7.5 * t)), 0.7, 0.7, k=0.3)
    return s, st


@piece("flat")
def br15_bead_vine():
    """Bead Vine: one broad-nib vine round the wrist; glass beads hang off it on stalks."""
    s = Scene(); st = []
    th = np.linspace(0, 2 * math.pi, 140)
    R = 31 + 1.8 * np.sin(th * 7)
    pts = np.stack([R * np.cos(th), R * np.sin(th)], 1)
    nib(s, F, pts, w=1.5, pen=0.8, hair=0.25, taper=(0, 0), closed=True)
    for i in range(20):
        j = int(i / 20 * 139); p = pts[j]; d = p / np.linalg.norm(p); nn = np.array([-d[1], d[0]])
        if i % 2:
            stalk(s, F, st, tuple(p), tuple(p + d * 6.0 + nn * 2.0), d=2.2, kind=["londonblue", "aquamarine", "moonstone"][i % 3], bend=0.3)
        else:
            spike(s, F, tuple(p), tuple(p - d * 4.5 + nn * 2.5), r0=0.65, bend=0.3)
    return s, st


@piece("ring")
def br16_crescent_bangle():
    """Crescent Bangle: a closed bangle of glazed crescents, horns hooked into each other."""
    s = Scene(); st = []
    m = Cyl(31)
    C = 2 * math.pi * 31
    n = 10; dx = C / n
    for yy in (-6.8, 6.8):
        nib(s, m, [(x, yy) for x in np.linspace(0, C, 100)], w=0.9, pen=0.0, hair=0.9, taper=(0, 0))
    for i in range(n):
        x = (i + 0.5) * dx
        mm = Flat(o=m.P(x, 0, 0), u=m.T(x, 0)[0], v=m.T(x, 0)[1])
        crescent(mm, None, None, 0, 0, 0) if False else None
        crescent(s, mm, st, 0, 0, 6.9, kind=["londonblue", "amethyst"][i % 2], ang=math.pi / 2 if i % 2 else -math.pi / 2, w=0.9, fill=0.6, seed=70 + i, horns=False,
                 sizes=[("marquise", 3.5, 1.8), ("round", 2, 2), ("round", 1.5, 1.5)])
    return s, st


# =============================================================== STUDS
@piece("flat")
def s09_thorn_bow():
    def one(s, m, st, sx):
        bow(s, m, st, 0, 0, 4.2, kinds=(["londonblue"], ["aquamarine"]), knot=None, tails=True, droop=0.2, w=0.45)
        bead(s, m, st, (0, 0), 1.8, "londonblue")
        stud_post(s, m, (0, 0))
    return pair(one, 18)


@piece("flat")
def s10_crescent():
    def one(s, m, st, sx):
        crescent(s, m, st, 0, 0, 4.4, kind="amethyst", ang=math.pi * (0.1 if sx > 0 else 0.9), w=0.55, seed=3,
                 sizes=[("marquise", 3.5, 1.8), ("round", 2, 2), ("round", 1.5, 1.5)])
        lead(s, m, [(0, 0), (-3.0 * (1 if sx > 0 else -1), 0)], r=0.45)
        stud_post(s, m, (-2.6 * (1 if sx > 0 else -1), 0))
    return pair(one, 16)


@piece("flat")
def s11_hook_crown():
    def one(s, m, st, sx):
        hook_crown(s, m, st, 0, 0, 3.4, n=5, kind="garnet", D=3.5, w=0.45, seed=2)
        stud_post(s, m, (0, 0))
    return pair(one, 14)


@piece("flat")
def s12_little_moth():
    def one(s, m, st, sx):
        for mr in (False, True):
            k = -1 if mr else 1
            wing(s, m, st, sx=0.15, sy=0.15, rot=0.3 * k, t=(k * 0.6, 0.6), mirror=mr, pal=["garnet", "amethyst"], costa=0.32, veins=False,
                 sizes=[("marquise", 3, 1.5), ("round", 1.5, 1.5)], thorn_tips=False, seed=5)
        s.ellipsoid(m.P(0, -0.3, 0.5), (0.65, 2.6, 0.7), k=0.4)
        for k in (1, -1): stalk(s, m, st, (k * 0.3, 2.0), (k * 2.4, 4.6), d=0.9, bend=0.3 * k, r=0.22)
        stud_post(s, m, (0, -0.3))
    return pair(one, 18)


@piece("flat")
def s13_vertebra():
    def one(s, m, st, sx):
        spine(s, m, st, [(0, 2.0), (0, -2.0)], n=1, size=4.0, kind="londonblue", w=0.55)
        stud_post(s, m, (0, 0))
    return pair(one, 12)


@piece("flat")
def s14_thorn_star():
    def one(s, m, st, sx):
        for a in range(6):
            b = a * math.pi / 3 + 0.25
            L = 4.8 if a % 2 else 3.0
            spike(s, m, (0, 0), (L * math.cos(b), L * math.sin(b)), r0=0.6, bend=0.18 * sx)
        thorns(s, m, st, (0, 0), 3.0, "topaz", n=3, reach=(0.6, 0.8), wire=0.32, seed=2)
        stud_post(s, m, (0, 0))
    return pair(one, 14)


@piece("flat")
def s15_glass_cage():
    def one(s, m, st, sx):
        cage(s, m, st, (0, 0), 1.6, 3.8, "garnet", n=5, w=0.38)
        stud_post(s, m, (0, 0))
    return pair(one, 12)


@piece("flat")
def s16_swash_pair():
    s = Scene(); st = []
    for sx, kd in ((-1, "amethyst"), (1, "garnet")):
        m = Flat(o=(sx * 9, 0, 0))
        nib(s, m, [(-3.5 * sx, 4), (0, 2.5), (1.5 * sx, -0.5), (-0.5 * sx, -3.5), (-3.5 * sx, -2.5), (-2.5 * sx, 0.5), (0.5 * sx, 0.8)],
            w=0.8, pen=0.75, hair=0.2, taper=(0.1, 0.4))
        pane(s, m, st, (-1.2 * sx, -1.2), "round", 2.5, 2.5, kd, vein=0.35)
        stud_post(s, m, (0, 0))
    return s, st


# =============================================================== DANGLES
@piece("hang")
def d09_spine_fall():
    def one(s, m, st, sx):
        spine(s, m, st, [(0, -2.5), (0.6 * sx, -16), (0, -30)], n=5, size=3.2, kind=["londonblue", "amethyst", "garnet"], grade=(1.0, 0.55), w=0.6)
        spike(s, m, (0, -30), (0, -35), r0=0.6)
        jump(s, m, (0, -0.8)); ear_wire(s, m, (0, 0.6))
    return pair(one, 22)


@piece("hang")
def d10_moth_drop():
    def one(s, m, st, sx):
        mm = Flat(o=m.P(0, -11, 0))
        for mr in (False, True):
            k = -1 if mr else 1
            wing(s, mm, st, sx=0.24, sy=0.24, rot=0.3 * k, t=(k * 0.9, 0.8), mirror=mr, pal=PAL["bruise"], costa=0.5,
                 sizes=[("marquise", 4, 2), ("round", 2, 2), ("round", 1.5, 1.5)], veins=False, thorn_tips=False, seed=21)
            wing(s, mm, st, outline=HIND, sx=0.22, sy=0.22, rot=-0.15 * k, t=(k * 0.9, -0.3), mirror=mr, pal=PAL["bruise"][::-1], costa=0.45,
                 sizes=[("round", 2, 2), ("round", 1.5, 1.5)], veins=False, thorn_tips=False, seed=22)
        s.ellipsoid(mm.P(0, -0.5, 0.5), (0.9, 4.0, 0.9), k=0.4)
        nib(s, m, [(0, -1.5), (0, -7.5)], w=0.5, hair=0.8, pen=1.57, taper=(0, 0))
        spike(s, mm, (0, -4.5), (0, -9.5), r0=0.6)
        jump(s, m, (0, 0)); ear_wire(s, m, (0, 1.4))
    return pair(one, 28)


@piece("hang")
def d11_lancet_drop():
    def one(s, m, st, sx):
        lancet(s, m, st, 0, -24, 4.6, 19, lights=2, kind=["garnet", "amethyst"], w=0.7, sizes=[("marquise", 6, 3), ("round", 2, 2), ("round", 1.5, 1.5)])
        nib(s, m, [(0, -2), (0, -5)], w=0.55, hair=0.8, pen=1.57, taper=(0, 0))
        mirror(lambda sd: stalk(s, m, st, (sd * 4.8, -24), (sd * 6.5, -28.5), d=1.4, kind="garnet" if sd > 0 else None, bend=0.2))
        jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, 24)


@piece("hang")
def d12_hook_chain():
    def one(s, m, st, sx):
        y = -1.5
        for i, kd in enumerate(("londonblue", "garnet", "amethyst")):
            g = 1 - 0.12 * i
            nib(s, m, [(0, y), (2.6 * sx * g, y - 3 * g), (1.0 * sx * g, y - 7 * g), (-1.6 * sx * g, y - 6.4 * g)], w=0.8 * g, pen=0.7 * sx, hair=0.25, taper=(0.0, 0.0))
            bead(s, m, st, (-1.5 * sx * g, y - 6.4 * g), 2.2 * g, kd)
            jump(s, m, (0, y - 8.4 * g), R=1.1, r=0.38) if i < 2 else None
            lead(s, m, [(-1.5 * sx * g, y - 6.4 * g), (0, y - 7.6 * g)], r=0.38) if i < 2 else None
            y -= 9.2 * g
        jump(s, m, (0, 0)); ear_wire(s, m, (0, 1.4))
    return pair(one, 20)


@piece("hang")
def d13_rose_drop():
    def one(s, m, st, sx):
        rose(s, m, st, 0, -10, 6.5, n=6, kinds=("amethyst", "garnet"), w=0.55)
        nib(s, m, [(0, -1.5), (0, -3.5)], w=0.55, hair=0.8, pen=1.57, taper=(0, 0))
        for x, L, kd in ((-2.2, 6, None), (0, 9, "garnet"), (2.2, 5, None)):
            stalk(s, m, st, (x, -16.2), (x * 1.2, -16.2 - L), d=1.5 if kd else 1.0, kind=kd, bend=0.12, r=0.3)
        jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, 22)


@piece("hang")
def d14_bow_drop():
    def one(s, m, st, sx):
        bow(s, m, st, 0, -5, 6.0, kinds=(["garnet"], ["garnet"]), knot="garnet", w=0.7, droop=0.4)
        jump(s, m, (0, -1.0)); lead(s, m, [(0, -2.0), (0, -4.0)], r=0.45); ear_wire(s, m, (0, 0.4))
    return pair(one, 22)


@piece("hang")
def d15_crescent_drop():
    def one(s, m, st, sx):
        crescent(s, m, st, 0, -10, 7.0, kind=["londonblue", "aquamarine"], ang=math.pi / 2, w=0.8, seed=8)
        for x, L in ((-2.0, 4.0), (0.6, 6.5), (2.6, 3.0)):
            stalk(s, m, st, (x, -10 - 7.0 * 0.6 + 2.5), (x, -10 - 7.0 * 0.6 + 2.5 - L), d=1.4 if L > 5 else 1.0, kind="londonblue" if L > 5 else None, r=0.26)
        lead(s, m, [(0, -1.5), (0, -3.2)], r=0.45)
        jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
    return pair(one, 24)


@piece("hang")
def d16_thorn_tassel():
    def one(s, m, st, sx):
        cage(s, Flat(o=m.P(0, -6, 0), u=(1, 0, 0), v=(0, 0, -1)), st, (0, 0), 2.0, 4.5, "amethyst", n=6, w=0.42, top_ball=False)
        for i in range(7):
            a = -math.pi / 2 + (i - 3) * 0.16
            L = 16 + 6 * (1 - abs(i - 3) / 3)
            nib(s, m, [(0.4 * (i - 3), -7.5), (L * 0.5 * math.cos(a) * 0.6, -7.5 + L * 0.5 * math.sin(a)), (L * math.cos(a) * 0.5, -7.5 + L * math.sin(a))],
                w=0.45, pen=1.2, hair=0.3, taper=(0.0, 0.6))
        nib(s, m, [(0, -1.2), (0, -3.5)], w=0.55, hair=0.8, pen=1.57, taper=(0, 0))
        jump(s, m, (0, -0.4)); ear_wire(s, m, (0, 1.0))
    return pair(one, 20)


# =============================================================== ANGEL BITES / CHEEKS / SNAKE BITES
@piece("flat")
def a06_little_bows():
    return tops(lambda s, m, st, sx: bow(s, m, st, 0, 0, 3.2, kinds=(["londonblue"], ["londonblue"]), knot=None, tails=False, droop=0.2, w=0.36, glaze_it=False)
                or bead(s, m, st, (0, 0), 1.6, "londonblue"), 12)


@piece("flat")
def a07_hook_beads():
    def one(s, m, st, sx):
        nib(s, m, [(0, 0), (1.8 * sx, 2.4), (0.4 * sx, 4.6), (-1.2 * sx, 3.6)], w=0.6, pen=0.7 * sx, hair=0.25, taper=(0.0, 0.0))
        bead(s, m, st, (-1.1 * sx, 3.5), 1.8, "garnet")
    return tops(one, 10)


@piece("flat")
def a08_crescent_pair():
    def one(s, m, st, sx):
        crescent(s, m, st, 0, 0.8, 3.4, kind="aquamarine", ang=-math.pi / 2 + 0.4 * sx, w=0.42, seed=2, sizes=[("round", 1.5, 1.5)])
        lead(s, m, [(0, 0), (0, 4.0)], r=0.42)
        bead(s, m, st, (0, 0.2), 1.6, "aquamarine")
    return tops(one, 12)


@piece("flat")
def a09_twin_vertebrae():
    return tops(lambda s, m, st, sx: spine(s, m, st, [(0, 1.6), (0, -1.6)], n=1, size=3.0, kind="amethyst", w=0.42), 10)


@piece("flat")
def a10_thorn_cages():
    return tops(lambda s, m, st, sx: cage(s, m, st, (0, 0), 1.3, 3.0, "garnet", n=5, w=0.32), 10)


@piece("flat")
def c06_hook_crowns():
    return tops(lambda s, m, st, sx: hook_crown(s, m, st, 0, 0, 2.6, n=5, kind="londonblue", D=2.5, w=0.36, seed=1), 12)


@piece("flat")
def c07_split_drops():
    def one(s, m, st, sx):
        for sd in (1, -1):
            o = smooth([(sd * 0.5, 2.0), (sd * 2.6, 0.2), (sd * 2.0, -2.8), (sd * 0.5, -3.6)], 6, closed=True)[:, :2]
            nib(s, m, o, w=0.32, closed=True, taper=(0, 0), hair=0.5)
            pane(s, m, st, (sd * 1.4, -0.6), "pear", 3.0, 2.0, "garnet" if sd > 0 else "amethyst", ang=-math.pi / 2 + 0.25 * sd, vein=0.22)
        lead(s, m, [(-0.6, 0), (0.6, 0)], r=0.35); lead(s, m, [(-0.6, -2.5), (0.6, -2.5)], r=0.32)
    return tops(one, 12)


@piece("flat")
def c08_glass_stars():
    def one(s, m, st, sx):
        for a in range(8):
            b = a * math.pi / 4
            L = 3.6 if a % 2 == 0 else 2.0
            spike(s, m, (0, 0), (L * math.cos(b), L * math.sin(b)), r0=0.45, bend=0.0)
        thorns(s, m, st, (0, 0), 2.0, "topaz", n=4, reach=(0.6, 0.7), wire=0.26)
    return tops(one, 12)


@piece("flat")
def c09_bead_curls():
    def one(s, m, st, sx):
        nib(s, m, spiral(0, 0, 3.0, 1.2, 0.3, 1.1)[:, :2] * [sx, 1], w=0.5, pen=0.7, hair=0.25, taper=(0.1, 0.0))
        bead(s, m, st, (0, 0), 2.0, "aquamarine")
    return tops(one, 12)


@piece("flat")
def c10_little_wings():
    return tops(lambda s, m, st, sx: wing(s, m, st, outline=HIND, sx=0.19, sy=0.19, rot=0.9 * sx, t=(0, 0), mirror=sx < 0,
                                          pal=["londonblue", "aquamarine"], costa=0.4, veins=False, thorn_tips=True,
                                          sizes=[("marquise", 3, 1.5), ("round", 1.5, 1.5)], seed=4)
                or ball(s, m, (0, 0), 0.7), 14)


@piece("flat")
def sb06_bow_fangs():
    def one(s, m, st, sx):
        o = loop_outline(0, 1.0, 5.0, 2.8, -math.pi / 2 + 0.2 * sx)
        nib(s, m, o, w=0.42, closed=True, taper=(0, 0), hair=0.4)
        pane(s, m, st, tuple(o.mean(0)), "marquise", 3.2, 1.6, "londonblue", ang=-math.pi / 2 + 0.2 * sx, vein=0.25)
        ball(s, m, (0, 1.0), 0.6)
    return tops(one, 10)


@piece("flat")
def sb07_crescent_hooks():
    def one(s, m, st, sx):
        nib(s, m, arc(0, 0, 3.0, math.pi * (0.2 if sx > 0 else -0.2) - math.pi / 2 - 1.6, math.pi * (0.2 if sx > 0 else -0.2) - math.pi / 2 + 1.6, 20),
            w=0.8, pen=0.0, hair=0.25, taper=(0.4, 0.4))
        for f in (-0.8, 0.0, 0.8):
            a = -math.pi / 2 + f + (0.2 * math.pi if sx > 0 else -0.2 * math.pi)
            pane(s, m, st, (3.0 * math.cos(a), 3.0 * math.sin(a)), "round", 1.5, 1.5, "garnet", vein=0.22)
        lead(s, m, [(0, 0), (3.0 * math.cos(-math.pi / 2 + (0.2 if sx > 0 else -0.2) * math.pi), 3.0 * math.sin(-math.pi / 2 + (0.2 if sx > 0 else -0.2) * math.pi))], r=0.4)
    return tops(one, 12)


@piece("flat")
def sb08_vertebra_drops():
    def one(s, m, st, sx):
        spine(s, m, st, [(0, 0.5), (0.2 * sx, -6.0)], n=2, size=2.4, kind=["londonblue", "aquamarine"], grade=(1.0, 0.7), w=0.38)
    return tops(one, 10)


@piece("flat")
def sb09_cage_drops():
    def one(s, m, st, sx):
        lead(s, m, [(0, 0), (0, -3.2)], r=0.45)
        cage(s, Flat(o=m.P(0, -3.2, 0)), st, (0, -1.6), 1.4, 3.0, "garnet", n=5, w=0.32)
    return tops(one, 10)


@piece("flat")
def sb10_star_pair():
    def one(s, m, st, sx):
        for a in range(4):
            b = a * math.pi / 2 + 0.6 * sx
            spike(s, m, (0, 0), (3.2 * math.cos(b), 3.2 * math.sin(b)), r0=0.5, bend=0.25 * sx)
        bead(s, m, st, (0, 0), 1.8, "londonblue")
    return tops(one, 10)


# =============================================================== INDUSTRIALS
@piece("flat")
def i05_bow_bar():
    s = Scene(); st = []
    bar(s, F)
    bow(s, F, st, 0, 0, 7.0, kinds=(["londonblue", "aquamarine"], ["aquamarine", "londonblue"]), knot="londonblue", w=0.8, tails=False, droop=0.0)
    for sx in (1, -1): nib(s, F, [(sx * 7, 0), (sx * 12, 1.2), (sx * 17, 0)], w=0.7, hair=0.6, taper=(0.1, 0.1))
    return s, st


@piece("flat")
def i06_crescent_bar():
    s = Scene(); st = []
    bar(s, F)
    for x, kd, ang in ((-9, "amethyst", 0.0), (9, "garnet", math.pi)):
        crescent(s, F, st, x, 0, 5.5, kind=kd, ang=ang, w=0.7, seed=int(x + 20), sizes=[("marquise", 3.5, 1.8), ("round", 2, 2), ("round", 1.5, 1.5)])
        lead(s, F, [(x - 5.5, 0), (x + 5.5, 0)], r=0.45)
    lead(s, F, [(-3.5, 0), (3.5, 0)], r=0.5)
    return s, st


@piece("flat")
def i07_hook_procession():
    s = Scene(); st = []
    bar(s, F)
    for i, x in enumerate(np.linspace(-14, 14, 6)):
        sd = 1 if i % 2 else -1
        nib(s, F, [(x - 1.5, 0), (x + 1.2, 2.6 * sd), (x - 0.4, 4.8 * sd), (x - 2.2, 3.9 * sd)], w=0.7, pen=0.7 * sd, hair=0.25, taper=(0.0, 0.0))
        bead(s, F, st, (x - 2.0, 3.6 * sd), 1.8, ["garnet", "londonblue"][i % 2])
    nib(s, F, [(-18, 0), (18, 0)], w=0.8, hair=0.8, pen=1.57, taper=(0, 0), z=0.3)
    return s, st


@piece("flat")
def i08_split_span():
    s = Scene(); st = []
    bar(s, F)
    split_wing(s, F, st, sx=0.7, t=(-16, 2.0), pal=PAL["venom"], gap=1.3, costa=1.0, seed=6,
               sizes=[("marquise", 5, 2.5), ("round", 2.5, 2.5), ("round", 2, 2), ("round", 1.5, 1.5)])
    for x in (-13, 13): lead(s, F, [(x, 2.0), (x, 0)], r=0.55)
    return s, st


# =============================================================== PENDANTS
@piece("flat")
def p04_bow_reliquary():
    """Bow Reliquary: a thorn bow tied over a lancet locket of glass."""
    s = Scene(); st = []
    o = lancet_outline(9, 26) + [0, -22]
    nib(s, F, o, w=1.3, closed=True, taper=(0, 0), hair=0.5)
    glaze(s, F, st, (o - o.mean(0)) * 0.88 + o.mean(0), ["garnet", "amethyst", "londonblue"], root=(0, 4), margin=0.7, seed=12)
    bow(s, F, st, 0, 5.5, 9.0, kinds=(["londonblue"], ["londonblue"]), knot="londonblue", w=0.9, droop=0.4, glaze_it=False)
    bail(s, F, (0, 9.5), R=2.0, r=0.6)
    return s, st


@piece("flat")
def p05_crescent_moth():
    """Crescent Moth: a moth asleep in the cup of a glazed crescent."""
    s = Scene(); st = []
    crescent(s, F, st, 0, 0, 17, kind=["londonblue", "aquamarine"], ang=math.pi / 2, w=1.6, fill=0.55, seed=9)
    mm = Flat(o=(0, -4, 0.6))
    for mr in (False, True):
        k = -1 if mr else 1
        wing(s, mm, st, sx=0.24, sy=0.24, rot=0.5 * k, t=(k * 0.8, 0.5), mirror=mr, pal=["garnet", "amethyst"], costa=0.5, veins=False,
             sizes=[("marquise", 4, 2), ("round", 2, 2), ("round", 1.5, 1.5)], thorn_tips=False, seed=33)
    s.ellipsoid(mm.P(0, -0.5, 0.4), (0.9, 4.0, 0.9), k=0.4)
    lead(s, F, [(0, -8.5), (0, -16.5)], r=0.6)
    lead(s, F, [(-9.0, 14.2), (0, 15.2), (9.0, 14.2)], r=0.7)
    bail(s, F, (0, 17.4), R=2.0, r=0.6)
    return s, st


@piece("flat")
def p06_hook_monstrance():
    """Hook Monstrance: a sunburst of hooked strokes around a caged garnet, glass between rays."""
    s = Scene(); st = []
    hook_crown(s, F, st, 0, 0, 13.0, n=10, kind="garnet", D=8.0, w=1.3, seed=6)
    for i in range(10):
        a = 2 * math.pi * (i + 0.5) / 10
        pane(s, F, st, (9.5 * math.cos(a), 9.5 * math.sin(a)), "marquise", 4, 2, ["amethyst", "citrine"][i % 2], ang=a, vein=0.45)
        lead(s, F, [(5.5 * math.cos(a), 5.5 * math.sin(a)), (7.5 * math.cos(a), 7.5 * math.sin(a))], r=0.45)
    th = np.linspace(0, 2 * math.pi, 60, endpoint=False)
    lead(s, F, np.stack([12 * np.cos(th), 12 * np.sin(th)], 1), r=0.55, closed=True)
    bail(s, F, (0, 16.0), R=2.0, r=0.6)
    lead(s, F, [(0, 12), (0, 14)], r=0.6)
    return s, st
