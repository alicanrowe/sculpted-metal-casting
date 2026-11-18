"""The 256 set: generated from the motif library (motifs.py) against AESTHETIC.md."""
import math
import numpy as np
from sdf import Scene
from kit import Flat, Cyl, bead, pane, stud_post, pin, ear_wire, jump, bail, shank
from glass64 import F, top, saddle, bar
import motifs as M

PIECES = {}


def piece(kind):
    def deco(fn):
        PIECES[fn.__name__] = (fn, kind); return fn
    return deco


@piece("flat")
def zz_motif_test():
    s = Scene(); st = []
    M.hook(s, F, st, (-30, 14), 0.3, 14, cd=1)
    M.crescent(s, F, st, (-8, 18), 6, ang=math.pi / 2)
    M.rose(s, F, st, (12, 18), 6)
    M.lancet(s, F, st, (30, 10), 5, 14, kind="amethyst", apex_bead="garnet")
    M.split_wing(s, F, st, (-30, -8), 0.6, 16)
    M.drop(s, F, st, (-8, -10), (0.1, 1), 2.4, 9)
    M.cage(s, F, st, (6, -6), 2.2, 8)
    M.vertebrae(s, F, st, [(18, -2), (22, -10), (20, -18)], 3, 5)
    M.moth(s, F, st, (36, -10), 9)
    M.crown(s, F, (-30, -26), 1.2, 6)
    M.volute(s, F, st, (-10, -24), (-6, -27), cw=1, w=1.2)
    M.whip(s, F, [(4, -22), (12, -28), (22, -24), (30, -30)], w=1.4)
    M.beadcurl(s, F, st, (38, -28), 2.5)
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


# =============================================================== generator
PALS = [("garnet", "amethyst"), ("londonblue", "aquamarine"), ("amethyst", "moonstone"), ("garnet", "topaz"),
        ("aquamarine", "moonstone"), ("londonblue", "garnet"), ("peridot", "citrine"), ("topaz", "londonblue"),
        ("amethyst", "garnet"), ("moonstone", "labradorite")]
HEROES = ["crescent", "rose", "lancet", "cage", "moth", "split_wing", "hook_pair", "vertebrae", "drop", "volute"]


def hero(s, m, st, name, c, size, rng, pal, z=0.0, ang=math.pi / 2):
    """Place one hero motif centred at c with overall size ~size (mm). Returns attach points."""
    c = np.asarray(c, float)
    k1, k2 = pal
    if name == "crescent":
        M.crescent(s, m, st, c, size * 0.5, ang=ang + rng.uniform(-0.5, 0.5), kinds=(k1, k2, k1), z=z, n=int(rng.integers(1, 4)))
        return [c + np.array([0, size * 0.5])]
    if name == "rose":
        M.rose(s, m, st, c, size * 0.48, n=int(rng.choice([5, 6, 7])), kinds=(k1, k2), centre=k1 if k1 != "moonstone" else "garnet", z=z,
               swirl=rng.uniform(0.2, 0.5))
        return [c + np.array([0, size * 0.45])]
    if name == "lancet":
        top_ = M.lancet(s, m, st, (c[0], c[1] - size * 0.42), size * 0.24, size * 0.72, kind=k1, z=z, apex_bead=k2 if rng.random() < 0.6 else None,
                        grain=size > 12)
        return [np.array(top_)]
    if name == "cage":
        M.cage(s, m, st, c, size * 0.16, size * 0.55, kind=k1, n=int(rng.integers(4, 7)), z=z)
        return [c + np.array([0, size * 0.28])]
    if name == "moth":
        M.moth(s, m, st, c, size * 0.62, ang=ang, z=z, kind=k2)
        return [c + np.array([0, size * 0.3])]
    if name == "split_wing":
        a = ang + rng.uniform(-0.6, 0.6)
        root = c - np.array([math.cos(a), math.sin(a)]) * size * 0.4
        M.split_wing(s, m, st, root, a, size * 0.85, z=z, kind=k1, gap=rng.uniform(0.25, 0.45))
        return [root]
    if name == "hook_pair":
        root = c + np.array([0, -size * 0.42])
        for sd in (1, -1):
            M.hook(s, m, st, root + np.array([sd * 0.3, 0]), math.pi / 2 - sd * 0.42, size * 0.66, cd=sd, kind=k1 if sd > 0 else k2, z=z)
        s.sphere(m.P(root[0], root[1], z + 0.2), max(0.45, size * 0.05), k=0.3)
        return [root]
    if name == "vertebrae":
        n = int(rng.integers(2, 4))
        M.vertebrae(s, m, st, [c + np.array([0, size * 0.45]), c + np.array([size * 0.08, 0]), c - np.array([0, size * 0.45])],
                    n, size * 0.42, kinds=(k1, k2), z=z)
        return [c + np.array([0, size * 0.45])]
    if name == "drop":
        M.drop(s, m, st, c - np.array([0, size * 0.25]), (rng.uniform(-0.2, 0.2), 1), size * 0.17, size * 0.6, kind=k1, z=z,
               curl=rng.uniform(-0.9, 0.9))
        return [c + np.array([0, size * 0.32])]
    if name == "volute":
        cd = 1 if rng.random() < 0.5 else -1
        M.volute(s, m, st, c + np.array([size * 0.3 * cd, size * 0.1]), c, cw=cd, w=size * 0.065, z=z, kind=k1)
        return [c + np.array([size * 0.3 * cd, size * 0.1])]
    raise ValueError(name)


def anchor(s, n0, m, p):
    """Nearest point of the metal added since prim n0 to the wish point p (plane coords), so a
    following element always grows out of something real."""
    P = s.array()[n0:]
    P = P[P[:, 1] == 0]
    if not len(P): return np.asarray(p, float)
    cen = (P[:, 19:22] + P[:, 22:25]) / 2
    o = np.asarray(m.o); u = np.asarray(m.u); v = np.asarray(m.v)
    loc = np.stack([(cen - o) @ u, (cen - o) @ v], 1)
    j = int(np.argmin(np.linalg.norm(loc - np.asarray(p, float), axis=1)))
    return loc[j]


def accent(s, m, st, kind, p, ang, size, rng, pal, z=0.0, n0=None):
    """Small secondary element growing from p toward ang (snapped onto metal added since n0)."""
    if n0 is not None: p = anchor(s, n0, m, p)
    p = np.asarray(p, float); d = np.array([math.cos(ang), math.sin(ang)]); n = np.array([-d[1], d[0]])
    cd = 1 if rng.random() < 0.5 else -1
    if kind == "whip":
        pts = [p, p + d * size * 0.35 + n * size * 0.12 * cd, p + d * size * 0.7 - n * size * 0.05 * cd, p + d * size + n * size * 0.18 * cd]
        M.whip(s, m, pts, w=size * 0.07 + 0.25, z=z, rise=size * 0.08, ends=(0.0, 0.3), twist=rng.uniform(0.4, 1.2))
    elif kind == "hook":
        o = p + d * size
        M.hook(s, m, st, o, ang + math.pi, size, cd=cd, kind=pal[1], z=z)
    elif kind == "feather":
        M.feather(s, m, p, ang, size, size * 0.13, z=z + 0.2, bend=0.1 * cd)
    elif kind == "crown":
        M.crown(s, m, p, ang, size * 0.5, n=int(rng.integers(2, 4)), lean=cd, z=z)
    elif kind == "beadcurl":
        q = p + d * size * 0.55
        M.hook(s, m, st, p + d * 0.0, ang, size * 0.7, cd=cd, kind=pal[0], z=z)
    elif kind == "drop":
        M.drop(s, m, st, p + d * size * 0.75, -d, size * 0.14 + 0.5, size * 0.75, kind=pal[1], z=z, curl=0.6 * cd)


NAMES = dict(crescent="crescent", rose="rose", lancet="lancet", cage="cage", moth="moth", split_wing="split_wing",
             hook_pair="hooks", vertebrae="spine", drop="drop", volute="volute")


def _reg(prefix, i, kind, hname, aname, fn):
    nm = f"{prefix}{i:02d}_{NAMES[hname]}_{aname}"
    fn.__name__ = nm; fn.__doc__ = f"{hname} with {aname}"
    PIECES[nm] = (fn, kind)


def gen():
    rng0 = np.random.default_rng(256)
    plan = [("r", 40, "ring"), ("b", 24, "flat"), ("c", 32, "cuff"), ("s", 32, "flat"), ("d", 40, "hang"),
            ("a", 16, "flat"), ("k", 16, "flat"), ("n", 16, "flat"), ("i", 16, "flat"), ("p", 24, "flat")]
    for prefix, count, kind in plan:
        for i in range(1, count + 1):
            seed = int(rng0.integers(1, 10 ** 6))
            r = np.random.default_rng(seed)
            hname = HEROES[(i - 1 + {"r": 0, "b": 3, "c": 5, "s": 2, "d": 7, "a": 1, "k": 4, "n": 6, "i": 8, "p": 9}[prefix]) % len(HEROES)]
            aname = ["whip", "hook", "feather", "crown", "beadcurl", "drop"][int(r.integers(0, 6))]
            pal = PALS[int(r.integers(0, len(PALS)))]
            fn = (lambda prefix=prefix, seed=seed, hname=hname, aname=aname, pal=pal: BUILD[prefix](seed, hname, aname, pal))
            _reg("m" + prefix, i, kind, hname, aname, fn)


# ---------------------------------------------------------------- per type
def build_ring(seed, hname, aname, pal):
    r = np.random.default_rng(seed); s = Scene(); st = []
    Rb, _ = shank(s, top_w=float(r.uniform(1.6, 2.4))); saddle(s, Rb, 4.0, 3.0)
    m = top(Rb, 0.5)
    size = float(r.uniform(11, 15))
    hero(s, m, st, hname, (0, 0), size, r, pal, z=0.0, ang=math.pi / 2 if r.random() < 0.5 else 0.0)
    cy = Cyl(Rb + 0.25)
    for sd in (1, -1):
        if r.random() < 0.75 or sd > 0:
            yy = float(r.uniform(-1.5, 1.5))
            pts = [(sd * 3.0, yy * 0.3), (sd * 7.0, yy + 1.2 * sd), (sd * 11.0, yy - 0.8), (sd * 14.5, yy * 0.5 + 1.0)]
            M.whip(s, cy, pts, w=0.75, z=0.2, rise=0.6, ends=(0.0, 0.35), twist=float(r.uniform(0.4, 1.1)))
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


def build_buckle(seed, hname, aname, pal):
    r = np.random.default_rng(seed); s = Scene(); st = []
    cd = 1 if r.random() < 0.5 else -1
    hc = np.array([cd * float(r.uniform(3, 6)), float(r.uniform(-4, 2))])
    size = float(r.uniform(26, 32))
    n0 = len(s.array()); att = hero(s, F, st, hname, hc, size, r, pal, z=1.6)
    a = att[0]
    # the wrapping whiplash: needle in the far corner, swelling up past the hero's head (touching it),
    # over the top and down into a volute holding a garnet
    W = [(-cd * 25, -27), (-cd * 21, -11), (-cd * 13, 6), (a[0] - cd * 3.0, a[1] + 1.5), (a[0] + cd * 6, a[1] + 6.5),
         (cd * 19, a[1] + 2.0), (cd * 21, a[1] - 8.0)]
    M.whip(s, F, W, w=2.3, z=0.8, rise=2.0, ends=(0.22, 0.0), twist=1.3,
           wk=[(0, 0.35), (0.25, 1.0), (0.5, 0.45), (0.75, 0.6), (1, 0.8)])
    M.volute(s, F, st, (cd * 21, a[1] - 8.0), (cd * 17.2, a[1] - 11.5), cw=cd, w=1.7, z=0.8, kind=pal[1])
    s.sphere(np.array([a[0] - cd * 0.8, a[1] + 0.6, 2.4]), 1.1, k=0.5)
    # accent off the lower edge of the hero, toward the open side
    accent(s, F, st, aname, hc + np.array([0, -size * 0.42]), -math.pi / 2 + cd * 0.5, size * 0.5, r, pal, z=1.6, n0=n0)
    Nz = np.array([0, 0, 1.0])
    p = np.array([-cd * 18.5, -4.0, 0.0]); s.cone(p, p - Nz * 5.0, 1.0, 0.85, k=0.6); s.sphere(p - Nz * 5.2, 1.3, k=0.4)
    q0 = np.array([hc[0], hc[1] - 3, 1.0]); q1 = np.array([hc[0], hc[1] + 3, 1.0])
    for q in (q0, q1): s.cone(q, q - Nz * 5.0, 0.95, 0.85, k=0.5)
    s.cone(q0 - Nz * 5.0, q1 - Nz * 5.0, 0.85, 0.85, k=0.5)
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


def build_cuff(seed, hname, aname, pal):
    r = np.random.default_rng(seed); s = Scene(); st = []
    R = 29.0; m = Cyl(R); X = 2 * math.pi * R * 0.38
    # two liquid ribbons run round the wrist, crossing over and under, ending in hooks
    ph = float(r.uniform(0, math.pi))
    for sd in (1, -1):
        xs = np.linspace(-X, X, 11)
        ys = sd * (3.2 + 1.8 * np.sin(xs / X * 2.4 * math.pi + ph))
        zz = 0.6 + 0.6 * sd * np.sin(xs / X * 2.4 * math.pi + ph + 1.2)
        M.rib(s, m, np.stack([xs, ys], 1), zz, w=1.5, thin=0.4, ends=(0.0, 0.0), twist=[(0, 0), (0.25, 0.9 * sd), (0.5, 0), (0.75, -0.9 * sd), (1, 0)],
              wkeys=[(0, 0.8), (0.3, 1.0), (0.5, 0.75), (0.7, 1.0), (1, 0.8)])
        for e in (0, -1):
            bead(s, m, st, (xs[e], ys[e]), 3.0, pal[1], z=float(zz[e]) + 1.0)
    hero(s, m, st, hname, (0, 0), float(r.uniform(18, 22)), r, pal, z=1.0, ang=math.pi / 2)
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


def build_stud(seed, hname, aname, pal):
    r = np.random.default_rng(seed); size = float(r.uniform(8, 11))
    def one(s, m, st, sx):
        rr = np.random.default_rng(seed)
        n0 = len(s.array()); att = hero(s, m, st, hname, (0, 0), size, rr, pal, z=0.0)
        if aname in ("whip", "crown", "feather") and rr.random() < 0.6:
            accent(s, m, st, aname, att[0], math.pi / 2 + sx * 0.6, size * 0.45, rr, pal, z=0.3, n0=n0)
        p = anchor(s, n0, m, (0, -size * 0.2)); stud_post(s, m, (float(p[0]), float(p[1])))
    s, st = pair(one, 22); s.units = [-11, 11]; return s, st


def build_dangle(seed, hname, aname, pal):
    r = np.random.default_rng(seed); size = float(r.uniform(13, 18))
    def one(s, m, st, sx):
        rr = np.random.default_rng(seed)
        jump(s, m, (0, -0.5)); ear_wire(s, m, (0, 0.9))
        # a small crown of hooks or a bead curl under the hook, then a liquid stem to the hero
        topc = np.array([0, -2.0])
        M.crown(s, m, topc, -math.pi / 2, 3.2, n=2, lean=sx, z=0.0) if rr.random() < 0.5 else s.sphere(m.P(0, -2.0, 0), 0.9, k=0.3)
        hc = np.array([0, -4.5 - size * 0.55])
        n0 = len(s.array()); att = hero(s, m, st, hname, hc, size, rr, pal, z=0.0, ang=-math.pi / 2 if hname == "crescent" else math.pi / 2)
        a = att[0]
        M.whip(s, m, [(0, -1.6), ((a[0]) * 0.5 + sx * 0.8, (a[1] - 1.6) / 2), (a[0], a[1])], w=0.55, z=0.0, rise=0.3, ends=(0.0, 0.0), twist=0.8)
        accent(s, m, st, "drop" if aname in ("crown", "beadcurl") else aname, hc + np.array([0, -size * 0.45]), -math.pi / 2 + sx * 0.25,
               size * 0.6, rr, pal, z=0.0, n0=n0)
    s, st = pair(one, 26); s.units = [-13, 13]; return s, st


def build_top(seed, hname, aname, pal, gap):
    r = np.random.default_rng(seed); size = float(r.uniform(5.5, 8.0))
    small = {"cage": "drop", "vertebrae": "hook_pair", "moth": "split_wing", "lancet": "crescent", "rose": "rose"}
    h = small.get(hname, hname) if size < 6.5 else hname
    def one(s, m, st, sx):
        rr = np.random.default_rng(seed)
        mm = Flat(o=m.o) if sx > 0 else Flat(o=m.o, u=(-1, 0, 0), v=(0, 1, 0))
        hero(s, mm, st, h, (0, 0), size, rr, pal, z=0.0)
    s = Scene(); st = []
    for sx in (-1, 1):
        m = Flat(o=(sx * gap / 2, 0, 0)); one(s, m, st, sx); pin(s, m, (0, 0))
    s.units = [-gap / 2, gap / 2]
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


def build_industrial(seed, hname, aname, pal):
    r = np.random.default_rng(seed); s = Scene(); st = []
    bar(s, F)
    cd = 1 if r.random() < 0.5 else -1
    M.whip(s, F, [(-19, 0.5), (-10, 3.5 * cd), (0, -1.0 * cd), (10, 3.0 * cd), (19, 0.0)], w=1.2, z=0.0, rise=0.8, ends=(0.15, 0.15), twist=1.0)
    hero(s, F, st, hname, (float(r.uniform(-6, 6)), 0.0), float(r.uniform(11, 14)), r, pal, z=0.6)
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


def build_pendant(seed, hname, aname, pal):
    r = np.random.default_rng(seed); s = Scene(); st = []
    size = float(r.uniform(22, 30))
    hc = np.array([0.0, -size * 0.55])
    n0 = len(s.array()); att = hero(s, F, st, hname, hc, size, r, pal, z=0.0)
    a = att[0]
    cd = 1 if r.random() < 0.5 else -1
    M.whip(s, F, [(0, 1.0), (cd * 2.2, (a[1] + 1) / 2), (a[0], a[1])], w=0.9, z=0.0, rise=0.5, ends=(0.0, 0.0), twist=0.8)
    bail(s, F, (0, 3.0), R=2.0, r=0.6)
    accent(s, F, st, aname, hc + np.array([cd * size * 0.25, -size * 0.35]), -math.pi / 2 + cd * 0.5, size * 0.45, r, pal, z=0.3, n0=n0)
    s.units = getattr(s, 'units', None) or [0.0]
    return s, st


from glass64 import pair  # noqa
BUILD = dict(r=build_ring, b=build_buckle, c=build_cuff, s=build_stud, d=build_dangle,
             a=lambda *a: build_top(*a, gap=12), k=lambda *a: build_top(*a, gap=20), n=lambda *a: build_top(*a, gap=14),
             i=build_industrial, p=build_pendant)
gen()


@piece("flat")
def zz_wing_test():
    import wings as Wg
    s = Scene(); st = []
    Wg.gem_wing(s, F, st, t=(0, 0), ang=0.25, scale=1.0)
    s.units = [0.0]
    return s, st


def _antennae(s, st, m, head, size, kind):
    for sd in (1, -1):
        pts = [head, head + np.array([sd * 0.6, 1.2]) * size, head + np.array([sd * 2.0, 2.4]) * size,
               head + np.array([sd * 3.2, 2.5]) * size, head + np.array([sd * 3.6, 1.8]) * size]
        c, W, _ = M.rib(s, m, pts, list(np.linspace(1.0, 1.8, 5)), w=0.42 * size + 0.15, thin=0.5, ends=(0.0, 0.0),
                        wkeys=[(0, 1.0), (0.5, 0.7), (1, 0.85)], twist=[(0, 0), (1, 0.8 * sd)])
        bead(s, m, st, (pts[-1][0], pts[-1][1]), 1.0 * size + 0.6, kind, z=1.8 + 0.5 * size)


@piece("flat")
def x_wing_pendant():
    """Gem-wing pendant: two stone-packed forewings and two small hindwings spread from a liquid
    body; antennae curl into garnet-tipped hooks; the body pours down into a whipped needle."""
    import wings as Wg
    s = Scene(); st = []
    pal = ("londonblue", "aquamarine", "moonstone")
    for sd in (1, -1):
        Wg.gem_wing(s, F, st, t=(sd * 1.6, 1.0), ang=(0.42 if sd > 0 else math.pi - 0.42), scale=0.62, flip=sd < 0, pal=pal,
                    costa_w=1.6, z=0.6, seed=5 + sd, bead_kind="garnet")
        Wg.gem_wing(s, F, st, t=(sd * 1.4, -2.0), ang=(-0.62 if sd > 0 else math.pi + 0.62), scale=0.5, flip=sd < 0, outline=Wg.HIND,
                    pal=("aquamarine", "moonstone"), costa_w=1.1, z=0.3, seed=9 + sd, hook=False, n_veins=3)
    # the body: a liquid drop, head up, tail whipping down into a needle
    import sculpt as K
    K.drop(s, (0, 3.2), (0.0, -1.0), 2.2, 20.0, curl=0.5, z=1.2)
    bead(s, F, st, (0, 3.2), 2.8, "garnet", z=3.0)
    _antennae(s, st, F, np.array([0, 4.8]), 1.0, "garnet")
    s.cone(np.array([0, 4.6, 1.2]), np.array([0, 8.5, 0.6]), 0.8, 0.6, k=0.4)
    bail(s, F, (0, 10.3), R=2.0, r=0.6)
    s.units = [0.0]
    return s, st


@piece("cuff")
def x_wing_cuff():
    """Gem-wing cuff: four stone-packed wings ride round the arm, alternating in direction, tied
    together by two whiplash ribbons that weave over and under their roots and end in volutes."""
    import wings as Wg
    s = Scene(); st = []
    R = 31.0; m = Cyl(R); X = 2 * math.pi * R * 0.36
    pals = [("garnet", "amethyst", "moonstone"), ("londonblue", "aquamarine", "moonstone")] * 2
    xs = [-X * 0.56, -X * 0.17, X * 0.22, X * 0.61]
    roots = []
    for i, x in enumerate(xs):
        up = 1 if i % 2 == 0 else -1
        t = (x - 11.0, -up * 4.0)
        Wg.gem_wing(s, m, st, t=t, ang=up * 0.3, scale=0.56, flip=up < 0, pal=pals[i], costa_w=1.5, z=0.9, seed=20 + i,
                    bead_kind="garnet" if i % 2 == 0 else "londonblue")
        roots.append(np.array(t))
    # two whiplash ribbons weave the length of the cuff, passing over each wing root
    for sd in (1, -1):
        xx = np.linspace(-X, X, 13)
        yy = sd * 9.0 + 4.0 * np.sin(xx / X * 2.0 * math.pi + (0 if sd > 0 else math.pi))
        for r_ in roots:
            j = int(np.argmin(np.abs(xx - r_[0]))); yy[j] = r_[1] + sd * 0.6
        zz = 0.5 + 0.7 * np.sin(np.linspace(0, 6 * math.pi, 13) + (0 if sd > 0 else math.pi / 2)) ** 2
        M.rib(s, m, np.stack([xx, yy], 1), zz, w=1.15, thin=0.4, ends=(0.0, 0.0),
              wkeys=[(0, 0.7), (0.25, 1.0), (0.5, 0.6), (0.75, 1.0), (1, 0.7)],
              twist=[(0, 0), (0.2, 0.9 * sd), (0.4, -0.5 * sd), (0.6, 0.9 * sd), (0.8, -0.5 * sd), (1, 0)])
        for e in (-1, 1):
            st_ = (e * X, yy[-1 if e > 0 else 0])
            M.volute(s, m, st, st_, (e * (X - 3.2), st_[1] - sd * 2.6), cw=sd * e, w=1.5, z=float(zz[0]), kind="garnet")
    s.units = [0.0]
    return s, st


@piece("flat")
def x_wing_buckle():
    """Gem-wing buckle: a pair of large stone-packed wings spread from a Gothic lancet body
    holding an amethyst; whiplash ribbons fall from the wings' roots and roll into volutes."""
    import wings as Wg
    s = Scene(); st = []
    for sd in (1, -1):
        Wg.gem_wing(s, F, st, t=(sd * 4.2, 4.0), ang=(0.3 if sd > 0 else math.pi - 0.3), scale=0.7, flip=sd < 0,
                    pal=("amethyst", "garnet", "moonstone"), costa_w=1.8, z=1.0, seed=31 + sd, bead_kind="londonblue")
        Wg.gem_wing(s, F, st, t=(sd * 3.6, -1.0), ang=(-0.5 if sd > 0 else math.pi + 0.5), scale=0.55, flip=sd < 0, outline=Wg.HIND,
                    pal=("garnet", "moonstone"), costa_w=1.2, z=0.6, seed=35 + sd, hook=False, n_veins=3)
        M.whip(s, F, [(sd * 3.2, -6.0), (sd * 6.5, -14.0), (sd * 13.0, -18.0), (sd * 19.0, -16.5)], w=1.6, z=0.8, rise=1.0,
               ends=(0.0, 0.0), twist=0.9 * sd, wk=[(0, 0.8), (0.4, 1.0), (1, 0.8)])
        M.volute(s, F, st, (sd * 19.0, -16.5), (sd * 18.6, -13.2), cw=sd, w=1.4, z=0.8, kind="garnet")
    M.lancet(s, F, st, (0, -8.0), 4.6, 18.0, kind="amethyst", z=1.2, apex_bead="garnet", grain=True)
    Nz = np.array([0, 0, 1.0])
    p = np.array([-14.0, 8.0, 0.5]); s.cone(p, p - Nz * 5.0, 1.0, 0.85, k=0.6); s.sphere(p - Nz * 5.2, 1.3, k=0.4)
    q0 = np.array([14.0, 5.0, 0.5]); q1 = np.array([14.0, 11.0, 0.5])
    for q in (q0, q1): s.cone(q, q - Nz * 4.5, 0.95, 0.85, k=0.5)
    s.cone(q0 - Nz * 4.5, q1 - Nz * 4.5, 0.85, 0.85, k=0.5)
    s.units = [0.0]
    return s, st
