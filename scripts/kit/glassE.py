"""moiraxmel for hyodomachine: Moira's hand leads, hyodomachine is the muse (refs/research/RESEARCH.md)."""
import math
import numpy as np
from sdf import Scene
from kit import Cyl
import moira as Mo
import motifs as M

PIECES = {}


def piece(kind):
    def deco(fn):
        PIECES[fn.__name__] = (fn, kind); return fn
    return deco


def cylpt(R, ang, y, r_off=0.0):
    """Point, outward normal and tangent (direction of increasing ang) on a finger/wrist cylinder about y."""
    p = np.array([(R + r_off) * math.sin(ang), y, (R + r_off) * math.cos(ang)])
    n = np.array([math.sin(ang), 0, math.cos(ang)]); t = np.array([math.cos(ang), 0, -math.sin(ang)])
    return p, n, t


def ring_feathers(s, R, specs):
    """specs: (start_ang, y, dir_sign, L, tilt, lift, seed). Feathers wrap the finger following its curvature."""
    for a0, y, sg, L, tilt, lift, sd in specs:
        p, n, t = cylpt(R, a0, y, lift)
        d = Mo.nrm(t * sg * math.cos(tilt) + np.array([0, 1.0, 0]) * math.sin(tilt))
        Mo.feather(s, p, d, n, L, W=L * 0.105, wrap=-0.97 * math.cos(tilt) ** 2 / (R + lift), bend=0.0, seed=sd)


# ================================================================ calibration studies
@piece("flat")
def e_study_moira_choker():
    """Pure Moira: two feathers meet at the throat holding an oval aquamarine, a pear drop below."""
    s = Scene(); st = []
    for sd in (1, -1):
        d = Mo.nrm([sd * math.cos(0.32), math.sin(0.32), 0])
        Mo.feather(s, (sd * 3.5, -1.0, 0), d, (0, 0, 1), 46, bend=0.012 * sd, seed=2 + sd)
        Mo.feather(s, (sd * 5.5, -3.2, -0.5), Mo.nrm([sd * math.cos(0.12), math.sin(0.12), 0]), (0, 0, 1), 34,
                   bend=0.02 * sd, seed=5 + sd)
        tip = np.array([sd * 46 * math.cos(0.32) + sd * 3.5, 46 * math.sin(0.32) + 2.5, 0])
        Mo.chain(s, [tip - np.array([sd * 3, 1.2, 0]), tip + np.array([sd * 6, 4, 0]), tip + np.array([sd * 14, 9, 0])])
    s.cone((-5, -1.5, 0.4), (5, -1.5, 0.4), 1.6, 1.6, k=0.6, flat=1.8)
    Mo.prong(s, st, (0, -1.0, 4.4), 8.0, "aquamarine", L=10.0, spin=math.pi / 2)
    Mo.pear(s, st, (0, -7.5, 0.6), 4.0, 6.0, "aquamarine")
    s.units = [0.0]
    return s, st


@piece("ring")
def e_study_moira_wing_ring():
    """Pure Moira: individually placed feathers wrap the finger as a wing, an emerald-cut aquamarine tucked in."""
    s = Scene(); st = []
    R = 9.3
    specs = [(-0.2, -2.5, 1, 30, 0.25, 0.2, 1.0), (-0.5, -3.0, 1, 26, 0.3, 0.75, 2.3), (-0.8, -1.0, 1, 21, 0.15, 1.3, 3.1),
             (0.4, 2.5, -1, 27, -0.25, 0.3, 4.4), (0.75, 3.0, -1, 22, -0.3, 0.9, 5.2)]
    ring_feathers(s, R, specs)
    s.torus((0, 0, 0), R - 0.2, 0.75, normal=(0, 1, 0), k=0.4)
    p, n, t = cylpt(R, 0.05, 0.2, 3.6)
    Mo.prong(s, st, p, 6.0, "aquamarine", L=8.0, normal=n, spin=0.3)
    s.units = [0.0]
    return s, st


@piece("hang")
def e_study_hyodo_cross():
    """Pure hyodomachine: liquid chrome cross fleury, a graded bead row and a needle."""
    s = Scene(); st = []
    Mo.cross_fleury(s, st, (0, 0), 26)
    Mo.bead_row(s, [(0, -22), (0.8, -27), (0, -33)], r0=1.4, r1=0.7, n=5, z=0.4)
    Mo.needle(s, (0, -33), (0, -1), 9, w=0.6, z=0.4, curl=0.6)
    s.torus((0, 11.5, 0.4), 1.6, 0.5, normal=(1, 0, 0), k=0.3)
    s.units = [0.0]
    return s, st


@piece("flat")
def e_study_parts():
    """Parts sampler: petal, thorn heart, star comet, gate scroll."""
    s = Scene(); st = []
    Mo.petal(s, st, (-22, 10, 0), 6.5, "garnet")
    Mo.thorn_heart(s, st, (2, 10, 0), 20, "amethyst")
    Mo.comet(s, (24, 16, 0), (0.3, -1, 0), 22, 3.2, count=4)
    Mo.gate_scroll(s, (-22, -14), 18)
    Mo.gate_scroll(s, (-12, -14), 18, mirror=True)
    s.units = [-22.0, 2.0, 24.0, -17.0]
    return s, st


@piece("flat")
def e_study_feather():
    s = Scene(); st = []
    Mo.feather(s, (-25, -4, 0), Mo.nrm([1, 0.25, 0]), (0, 0, 1), 52, bend=0.018, seed=3)
    s.units = [0.0]
    return s, st


# ================================================================ the 256
PALS = [("aquamarine", "moonstone"), ("garnet", "amethyst"), ("londonblue", "aquamarine"), ("amethyst", "garnet"),
        ("aquamarine", "garnet"), ("topaz", "aquamarine"), ("garnet", "moonstone"), ("amethyst", "aquamarine")]
UP = np.array([0, 0, 1.0])


def accent(s, st, rng, a, down, size, pal, z=0.4):
    """One hyodomachine accent hanging off point a: graded bead row to a needle, a small cross fleury,
    a pear drop, or a comet of stars."""
    a = np.asarray(a, float)[:2]; d = Mo.nrm(np.asarray(down, float)[:2]); nn = np.array([-d[1], d[0]])
    kind = rng.choice(["beads", "cross", "pear", "beads_pear", "comet"], p=[0.3, 0.2, 0.2, 0.2, 0.1])
    if kind in ("beads", "beads_pear"):
        L = size * rng.uniform(0.9, 1.4); bend = rng.uniform(-0.15, 0.15)
        pts = [a, a + d * L * 0.5 + nn * L * bend, a + d * L]
        Mo.bead_row(s, pts, r0=size * 0.09, r1=size * 0.045, n=int(rng.integers(4, 7)), z=z)
        e = a + d * L
        if kind == "beads": Mo.needle(s, e, d, size * 0.6, w=size * 0.035, z=z, curl=rng.uniform(-0.8, 0.8))
        else: Mo.pear(s, st, Mo.v3(e, z), size * 0.28, size * 0.4, pal[1], down=Mo.v3(d))
    elif kind == "cross":
        Mo.chain(s, [Mo.v3(a, z), Mo.v3(a + d * size * 0.3, z)], link=1.3)
        Mo.cross_fleury(s, st, a + d * (size * 0.3 + size * 0.42), size * 0.85, normal_rot=math.atan2(d[1], d[0]) + math.pi / 2, z=z,
                        long_foot=1.5)
    elif kind == "pear":
        Mo.pear(s, st, Mo.v3(a, z), size * 0.3, size * 0.45, pal[0], down=Mo.v3(d))
    else:
        Mo.comet(s, Mo.v3(a + d * size * 0.15, z), Mo.v3(d), size * 1.1, size * 0.16, count=4, seed=int(rng.integers(9)))
    return kind


def wingfan(s, rng, root, ang, L, count, sx=1, z=0.0, spread=(0.14, 0.24), stagger=0.05):
    """Moira's individually placed feathers fanning from a root (flat pieces)."""
    for i in range(count):
        a = ang + sx * (i * rng.uniform(*spread) - 0.1 * spread[1] / 0.24)
        d = np.array([math.cos(a), math.sin(a), 0])
        b = np.asarray(root, float) + np.array([-d[1], d[0], 0]) * sx * i * L * 0.045 + d * i * L * stagger + UP * (z + i * 0.45)
        Mo.feather(s, b, d, UP, L * (0.86 ** i) * rng.uniform(0.95, 1.05), bend=sx * rng.uniform(0.004, 0.02) * (1 + 0.4 * i),
                   seed=float(rng.uniform(0, 50)))


# ---------------------------------------------------------------- necklaces
def b_neck_wings(rng, pal):
    s = Scene(); st = []
    one_side = rng.random() < 0.35
    L = rng.uniform(34, 48)
    for sx in ((1,) if one_side else (1, -1)):
        lift = rng.uniform(0.15, 0.4)
        wingfan(s, rng, (sx * 3.0, -0.8, 0), math.pi / 2 - sx * (math.pi / 2 - lift), L * (1 if sx > 0 else rng.uniform(0.8, 1)),
                int(rng.integers(2, 4)), sx=-sx, spread=(0.03, 0.09), stagger=rng.uniform(0.04, 0.12))
        tip = np.array([sx * L * math.cos(lift) + sx * 2, L * math.sin(lift) + 1, 0])
        Mo.chain(s, [tip - np.array([sx * 4, 1.5, 0]), tip + np.array([sx * 5, 3, 0]), tip + np.array([sx * 12, 7, 0])])
    if one_side:
        Mo.chain(s, [(4, -0.5, 0), (-6, 1.5, 0), (-16, 6, 0)])
    D = rng.uniform(6.5, 9)
    s.ellipsoid((0, -0.8, 0.6), (4.5, 2.2, 1.2), k=0.8)
    Mo.prong(s, st, (0, -0.6, D * 0.5 + 0.9), D, pal[0], L=D * rng.choice([1.0, 1.25, 1.4]), spin=math.pi / 2)
    accent(s, st, rng, (0, -D * 0.55 - 1.5), (rng.uniform(-0.15, 0.15), -1), rng.uniform(11, 15), pal)
    s.units = [0.0]
    return s, st


def b_neck_heart(rng, pal):
    s = Scene(); st = []
    w = rng.uniform(18, 26)
    Mo.thorn_heart(s, st, (0, 0, 0), w, pal[0], seed=int(rng.integers(99)), tail=rng.uniform(0.25, 0.5))
    s.torus((0, w * 0.5 + 1.8, 0.3), 1.7, 0.5, normal=(1, 0, 0), k=0.3)
    if rng.random() < 0.6:
        sx = rng.choice([1, -1])
        wingfan(s, rng, (sx * w * 0.25, w * 0.2, -0.6), math.pi / 2 - sx * rng.uniform(0.9, 1.3), w * rng.uniform(1.0, 1.5),
                int(rng.integers(1, 3)), sx=-sx)
    accent(s, st, rng, (0, -w * 0.62), (0, -1), w * 0.55, pal)
    s.units = [0.0]
    return s, st


def b_neck_cross(rng, pal):
    s = Scene(); st = []
    size = rng.uniform(24, 34)
    Mo.cross_fleury(s, st, (0, 0), size, long_foot=rng.uniform(1.2, 1.9), w=size * rng.uniform(0.04, 0.06))
    centre = rng.choice(["petal", "stone", "heart"])
    if centre == "petal": Mo.petal(s, st, (0, 0, 1.4), size * rng.uniform(0.14, 0.2), pal[0], n_petals=int(rng.choice([4, 5])), rot=rng.uniform(0, 1))
    elif centre == "stone":
        D = size * rng.uniform(0.22, 0.3); Mo.prong(s, st, (0, 0, D * 0.5 + 1.2), D, pal[0], L=D * rng.choice([1, 1.3]), spin=math.pi / 2)
    else: Mo.thorn_heart(s, st, (0, size * 0.02, 1.2), size * 0.42, pal[0], seed=int(rng.integers(99)), thorns=5, tail=0.1)
    nf = int(rng.choice([0, 1, 2, 2, 3]))
    sx0 = rng.choice([1, -1])
    for i in range(nf):
        sx = sx0 if i != 1 else -sx0
        Mo.feather(s, (sx * 1.5, -size * rng.uniform(0.0, 0.2), -0.7 - 0.4 * i), Mo.nrm([sx * 1, rng.uniform(-0.2, 1.1), 0]), UP,
                   size * rng.uniform(0.55, 0.95), bend=-sx * rng.uniform(0.0, 0.03), seed=float(rng.uniform(0, 40)))
    foot = -size * 0.5 * 1.2
    if rng.random() < 0.6: accent(s, st, rng, (0, foot - size * 0.12), (0, -1), size * 0.45, pal)
    s.torus((0, size * 0.43 + 1.6, 0.4), 1.6, 0.5, normal=(1, 0, 0), k=0.3)
    s.units = [0.0]
    return s, st


def b_neck_comet(rng, pal):
    s = Scene(); st = []
    L = rng.uniform(32, 44); sx = rng.choice([1, -1])
    a = math.pi / 2 + sx * rng.uniform(0.3, 0.6)
    wingfan(s, rng, (0, 0, 0), a, L, int(rng.integers(1, 3)), sx=sx)
    Mo.comet(s, (0, -2, 0.6), Mo.nrm([-sx * 0.4, -1, 0]), L * 0.55, L * 0.07, count=int(rng.integers(3, 6)), seed=int(rng.integers(9)))
    D = rng.uniform(5, 7)
    Mo.prong(s, st, (sx * 2, 1.0, D * 0.5 + 0.6), D, pal[0], L=D * 1.35, spin=a)
    tip = np.array([math.cos(a), math.sin(a), 0]) * L * 0.95
    s.torus(tip, 1.5, 0.45, normal=(1, 0, 0), k=0.3)
    s.units = [0.0]
    return s, st


def b_neck_lariat(rng, pal):
    s = Scene(); st = []
    R = rng.uniform(5.5, 7.5)
    Mo.petal(s, st, (0, 0, 0), R, pal[0], n_petals=int(rng.choice([4, 5])), rot=rng.uniform(0, 1))
    for sx in (1, -1):
        Mo.chain(s, [(sx * R * 1.0, R * 0.3, 0), (sx * R * 2.5, R * 1.4, 0), (sx * R * 4.5, R * 3.2, 0)])
    Mo.chain(s, [(0, -R * 1.0, 0), (0.6, -R * 3.0, 0), (0, -R * 5.0, 0)])
    sx = rng.choice([1, -1])
    Mo.feather(s, (sx * R * 0.5, -R * 0.4, -0.8), Mo.nrm([sx * 0.45, -1, 0]), UP, R * rng.uniform(3.4, 4.6), bend=sx * 0.03,
               seed=float(rng.uniform(0, 40)))
    accent(s, st, rng, (0, -R * 5.1), (0, -1), R * 2.0, pal)
    s.units = [0.0]
    return s, st


# ---------------------------------------------------------------- earrings (pairs)
def pair_of(fn, gap):
    def build(rng, pal):
        s = Scene(); st = []
        seed = int(rng.integers(1 << 30))
        for sx in (-1, 1):
            r2 = np.random.default_rng(seed)          # same design, mirrored
            fn(s, st, r2, pal, sx, sx * gap / 2)
        s.units = [-gap / 2, gap / 2]
        return s, st
    return build


def _post(s, x, y):
    s.cone((x, y, -0.2), (x, y, -10), 0.75, 0.5, k=0.4)


def e_feather_drop(s, st, rng, pal, sx, ox):
    top = rng.choice(["petal", "star"])
    if top == "petal": Mo.petal(s, st, (ox, 0, 0), 3.4, pal[0], n_petals=int(rng.choice([4, 5])))
    else: Mo.star(s, (ox, 0, 0.5), 3.2, rot=0.1 * sx)
    _post(s, ox, 0)
    L = rng.uniform(26, 36)
    Mo.chain(s, [(ox, -3.0, 0), (ox, -6.5, 0)], link=1.2)
    Mo.feather(s, (ox, -7.0, 0), Mo.nrm([sx * rng.uniform(0.1, 0.35), -1, 0]), UP, L, bend=-sx * rng.uniform(0.01, 0.03),
               seed=float(rng.uniform(0, 40)))
    if rng.random() < 0.6:
        Mo.pear(s, st, (ox + sx * 1.5, -9, 0.8), 3.2, 4.6, pal[1], down=Mo.nrm([sx * 0.8, -1, 0]))


def e_heart(s, st, rng, pal, sx, ox):
    w = rng.uniform(11, 15)
    Mo.thorn_heart(s, st, (ox, 0, 0), w, pal[0], seed=int(rng.integers(99)), tail=rng.uniform(0.3, 0.6), thorns=5)
    _post(s, ox, w * 0.3)
    accent(s, st, rng, (ox, -w * 0.62), (sx * 0.15, -1), w * 0.6, pal)


def e_cross(s, st, rng, pal, sx, ox):
    Mo.prong(s, st, (ox, 0, 2.0), 3.6, pal[0])
    s.sphere((ox, 0, 0.4), 1.8, k=0.4)
    _post(s, ox, 0)
    Mo.chain(s, [(ox, -2.2, 0), (ox, -6, 0)], link=1.2)
    Mo.cross_fleury(s, st, (ox, -6 - rng.uniform(7, 9)), rng.uniform(14, 19), long_foot=rng.uniform(1.4, 1.9))


def e_climber(s, st, rng, pal, sx, ox):
    L = rng.uniform(24, 32)
    a = math.pi / 2 + sx * rng.uniform(0.05, 0.3)
    wingfan(s, rng, (ox, -L * 0.45, 0), a, L, int(rng.integers(2, 4)), sx=sx)
    D = rng.uniform(3.5, 5)
    Mo.prong(s, st, (ox + sx * 0.8, -L * 0.45 + 1.0, D * 0.5 + 0.5), D, pal[0], L=D * rng.choice([1, 1.4]), spin=a)
    _post(s, ox + sx * 0.8, -L * 0.45 + 1.0)
    Mo.bead_row(s, [(ox, -L * 0.45 - 2), (ox + sx * 2, -L * 0.45 - 7), (ox + sx * 1, -L * 0.45 - 12)], r0=0.9, r1=0.5, n=4, z=0.4)


# ---------------------------------------------------------------- piercings
def p_single(rng, pal):
    s = Scene(); st = []
    k = rng.choice(["petal", "star", "cross", "heart", "feather", "comet"])
    if k == "petal":
        Mo.petal(s, st, (0, 0, 0), rng.uniform(3.2, 4.2), pal[0], n_petals=int(rng.choice([4, 5]))); _post(s, 0, 0)
        if rng.random() < 0.5: Mo.bead_row(s, [(0, -4.5), (1.5, -9), (0, -13)], r0=0.8, r1=0.45, n=4, z=0.3)
    elif k == "star":
        for i in range(int(rng.integers(2, 4))):
            Mo.star(s, (i * 3.2 * rng.uniform(0.8, 1.1), -i * 2.6, 0.5 - 0.2 * i), 2.6 * 0.82 ** i, rot=rng.uniform(0, 1))
        Mo.prong(s, st, (1.2, 2.0, 1.8), 2.5, pal[0]); _post(s, 0, 0)
    elif k == "cross":
        Mo.cross_fleury(s, st, (0, 0), rng.uniform(10, 13), long_foot=rng.uniform(1.2, 1.6), kind=pal[0] if rng.random() < 0.5 else None)
        _post(s, 0, 0)
    elif k == "heart":
        Mo.thorn_heart(s, st, (0, 0, 0), rng.uniform(9, 11), pal[0], seed=int(rng.integers(99)), thorns=5); _post(s, 0, 2)
    elif k == "feather":
        L = rng.uniform(14, 20)
        Mo.feather(s, (0, 0, 0), Mo.nrm([rng.uniform(-0.4, 0.4), 1, 0]), UP, L, bend=rng.uniform(-0.04, 0.04), seed=float(rng.uniform(0, 40)))
        Mo.prong(s, st, (0, 0.6, 1.8), 2.8, pal[0]); _post(s, 0, 0.6)
    else:
        Mo.comet(s, (0, 0, 0.5), Mo.nrm([0.5, -1, 0]), 12, 2.4, count=4, seed=int(rng.integers(9)))
        Mo.prong(s, st, (-1.8, 1.4, 1.6), 2.4, pal[0]); _post(s, 0, 0)
    s.units = [0.0]
    return s, st


def p_navel(rng, pal):
    s = Scene(); st = []
    Mo.prong(s, st, (0, 0, 2.2), 4.5, pal[0])
    s.sphere((0, 0, 0.3), 2.1, k=0.4)
    s.cone((0, 1.0, -0.2), (0, 10, -4.0), 0.8, 0.8, k=0.3)          # curved bar up into the navel
    s.sphere((0, 10.5, -4.2), 1.6, k=0.3)
    sx = rng.choice([1, -1])
    wingfan(s, rng, (sx * 1.0, -1.5, -0.4), -math.pi / 2 + sx * rng.uniform(0.15, 0.45), rng.uniform(20, 28), int(rng.integers(1, 3)), sx=sx)
    accent(s, st, rng, (-sx * 1.5, -3.5), (-sx * 0.2, -1), 9, pal)
    s.units = [0.0]
    return s, st


def p_septum(rng, pal):
    s = Scene(); st = []
    th = np.linspace(-0.25 * math.pi, 1.25 * math.pi, 40)              # horseshoe ring
    R = 5.5
    s.stroke(np.stack([R * np.cos(th), -R * np.sin(th), np.zeros(40)], 1), np.full(40, 0.6), k=0.3)
    for sx in (1, -1): s.sphere((sx * R * math.cos(0.25 * math.pi), R * math.sin(0.25 * math.pi), 0), 1.0, k=0.3)
    k = rng.choice(["heart", "petal", "cross"])
    if k == "heart": Mo.thorn_heart(s, st, (0, -R - 3.5, 0.3), 9, pal[0], seed=int(rng.integers(99)), thorns=5, tail=0.5)
    elif k == "petal":
        Mo.petal(s, st, (0, -R - 1.5, 0.3), 3.4, pal[0])
        Mo.bead_row(s, [(-4, -R - 1.5), (-7, -R - 0.5)], 0.8, 0.5, 3, 0.3); Mo.bead_row(s, [(4, -R - 1.5), (7, -R - 0.5)], 0.8, 0.5, 3, 0.3)
    else: Mo.cross_fleury(s, st, (0, -R - 5.0), 11, long_foot=1.4)
    s.units = [0.0]
    return s, st


def p_industrial(rng, pal):
    s = Scene(); st = []
    s.cone((-19, 0, -1.2), (19, 0, -1.2), 0.75, 0.75, k=0.3)
    for sx in (-1, 1): s.sphere((sx * 20.3, 0, -1.2), 1.8, k=0.3)
    sx = rng.choice([1, -1])
    Mo.feather(s, (sx * 17, -0.5, -0.2), (-sx, rng.uniform(-0.05, 0.12), 0), UP, rng.uniform(28, 34), bend=rng.uniform(-0.01, 0.01),
               seed=float(rng.uniform(0, 40)))
    Mo.prong(s, st, (sx * 15, 0.5, 2.0), 3.6, pal[0])
    Mo.bead_row(s, [(-sx * 2, 0), (-sx * 9, 0.4), (-sx * 15, 0)], 1.0, 0.55, 5, 0.3)
    s.units = [0.0]
    return s, st


def p_earcuff(rng, pal):
    """Feathers that wrap the helix (curl round a 6-7 mm radius), with a stone, star or bead row at the front."""
    s = Scene(); st = []
    R = rng.uniform(6.0, 7.2)
    n = int(rng.integers(1, 4)); a0 = rng.uniform(-1.6, -0.9)
    for i in range(n):
        tl = rng.uniform(-0.35, 0.35)
        p, nn, t = cylpt(R, a0 + i * rng.uniform(0.25, 0.5), (i - n / 2) * rng.uniform(1.2, 2.4), 0.3 + i * 0.5)
        d = Mo.nrm(t * math.cos(tl) + np.array([0, math.sin(tl), 0]))
        Mo.feather(s, p, d, nn, rng.uniform(16, 28) * 0.88 ** i, W=rng.uniform(1.8, 2.6), wrap=-0.92 * math.cos(tl) ** 2 / (R + 0.3 + i * 0.5),
                   seed=float(rng.uniform(0, 40)))
    k = rng.choice(["stone", "star", "beads", "cross"])
    p, nn, t = cylpt(R, rng.uniform(0.6, 1.2), rng.uniform(-1.5, 1.5), 1.4)
    if k == "stone": Mo.prong(s, st, p, rng.uniform(3, 4.2), pal[0], normal=nn)
    elif k == "star": Mo.star(s, p, 2.8, nn, rot=rng.uniform(0, 1))
    elif k == "cross":
        Mo.prong(s, st, p, 3.0, pal[0], normal=nn)
        q, n2, t2 = cylpt(R, 1.6, 0, 0.8); Mo.bead_row(s, [p, q, q + np.array([0, -7, 0])], 0.8, 0.45, 4)
    else:
        q, n2, t2 = cylpt(R, 1.7, 0, 0.6); Mo.bead_row(s, [p - t * 3, p, q], 1.0, 0.5, 5)
    s.torus((0, 0, 0), R - 0.2, 0.55, normal=(0, 1, 0), k=0.3)
    s.units = [0.0]
    return s, st


# ---------------------------------------------------------------- rings
def r_wing(rng, pal):
    s = Scene(); st = []
    R = 9.3; n1 = int(rng.integers(2, 5)); n2 = int(rng.integers(1, 4))
    specs = []
    for i in range(n1):
        tl = rng.uniform(0.05, 0.35)
        specs.append((-0.2 - i * rng.uniform(0.2, 0.35), -tl * 9 + rng.uniform(-1, 1), 1, rng.uniform(22, 31) * 0.92 ** i, tl,
                      0.2 + i * 0.5, float(rng.uniform(0, 40))))
    for i in range(n2):
        tl = rng.uniform(0.05, 0.35)
        specs.append((0.3 + i * rng.uniform(0.2, 0.35), tl * 9 + rng.uniform(-1, 1), -1, rng.uniform(20, 28) * 0.92 ** i, -tl,
                      0.2 + i * 0.5, float(rng.uniform(0, 40))))
    ring_feathers(s, R, specs)
    s.torus((0, 0, 0), R - 0.2, 0.75, normal=(0, 1, 0), k=0.4)
    p, n, t = cylpt(R, rng.uniform(-0.1, 0.15), rng.uniform(-0.5, 0.8), 3.4)
    D = rng.uniform(5.5, 7.5)
    Mo.prong(s, st, p, D, pal[0], L=D * rng.choice([1.0, 1.3, 1.45]), normal=n, spin=rng.uniform(-0.5, 0.5))
    if rng.random() < 0.4:
        p2, n2_, t2 = cylpt(R, rng.choice([1, -1]) * 1.3, 2.5, 0.6)
        Mo.bead_row(s, [p2, p2 + np.array([0, 3, 0]) + n2_ * 0.5, p2 + np.array([0, 6, 0])], 0.9, 0.5, 4)
    s.units = [0.0]
    return s, st


def r_top(rng, pal):
    """Band (often of two feathers) with a top motif: petal, heart, cross or twin petals."""
    s = Scene(); st = []
    R = 9.3
    s.torus((0, 0, 0), R - 0.1, 0.85, normal=(0, 1, 0), k=0.4)
    if rng.random() < 0.6:
        for sg in (1, -1):
            p, n, t = cylpt(R, sg * 0.35, rng.uniform(-1, 1), 0.3)
            Mo.feather(s, p, t * sg, n, rng.uniform(18, 26), wrap=-0.95 / R, seed=float(rng.uniform(0, 40)))
    k = rng.choice(["petal", "heart", "cross", "twin"])
    tz = R + 1.2
    if k == "petal": Mo.petal(s, st, (0, 0, tz), rng.uniform(5.5, 7), pal[0], n_petals=int(rng.choice([4, 5])))
    elif k == "twin":
        Mo.petal(s, st, (-4.2, 0.8, tz - 0.3), 4.4, pal[0]); Mo.petal(s, st, (4.0, -0.8, tz - 0.3), 4.4, pal[1], rot=0.4)
    elif k == "heart": Mo.thorn_heart(s, st, (0, 1.0, tz), rng.uniform(15, 19), pal[0], seed=int(rng.integers(99)), thorns=5, tail=0.25)
    else: Mo.cross_fleury(s, st, (0, 0), rng.uniform(17, 22), z=tz, kind=pal[0], long_foot=1.3)
    s.ellipsoid((0, 0, R + 0.4), (3.5, 3.0, 1.2), k=0.8)
    s.units = [0.0]
    return s, st


# ---------------------------------------------------------------- cuffs
def c_feather_skin(rng, pal):
    s = Scene(); st = []
    R = 29.0
    n = int(rng.integers(2, 4))
    for i in range(n):
        a0 = -2.1 + i * rng.uniform(0.25, 0.5)
        p, nn, t = cylpt(R, a0, rng.uniform(-6, 6) * (1 - 0.3 * i), 0.4 + i * 0.7)
        d = Mo.nrm(t + np.array([0, rng.uniform(-0.12, 0.12), 0]))
        Mo.feather(s, p, d, nn, rng.uniform(90, 120) * 0.9 ** i, W=rng.uniform(7, 9.5) * 0.9 ** i, wrap=-0.97 / (R + 0.4 + i * 0.7),
                   seed=float(rng.uniform(0, 40)))
    k = rng.choice(["stone", "petal", "cross", "comet"])
    p, nn, t = cylpt(R, rng.uniform(-0.3, 0.4), rng.uniform(-3, 3), 2.0)
    if k == "stone":
        D = rng.uniform(7, 10); Mo.prong(s, st, p + nn * D * 0.4, D, pal[0], L=D * rng.choice([1, 1.3]), normal=nn, spin=math.pi / 2)
    elif k == "petal": Mo.petal(s, st, p, 7.0, pal[0], normal=nn)
    elif k == "comet": Mo.comet(s, p + nn * 0.5, t, 18, 3.2, normal=nn, seed=int(rng.integers(9)))
    else:
        Mo.prong(s, st, p + nn * 2.5, 6.5, pal[0], normal=nn)
        q, n2, t2 = cylpt(R, 1.3, 0, 1.0)
        Mo.bead_row(s, [p + t * 6, q - t2 * 4, q + t2 * 8], 1.3, 0.6, 6)
    s.units = [0.0]
    return s, st


# ---------------------------------------------------------------- hair clips
def h_clip(rng, pal):
    s = Scene(); st = []
    L = rng.uniform(52, 78); n = int(rng.choice([1, 1, 2, 3]))
    a = math.pi / 2 + rng.uniform(-0.25, 0.25)
    wingfan(s, rng, (0, -L * 0.5, 0), a, L, n, sx=rng.choice([1, -1]))
    dd = np.array([math.cos(a), math.sin(a), 0]); b0 = np.array([0, -L * 0.5, -1.4])
    s.cone(b0 + dd * L * 0.06, b0 + dd * L * 0.36, 0.9, 0.7, k=0.3, flat=2.0, zhint=np.cross(dd, UP))   # clip bar hidden underneath
    k = rng.choice(["comet", "beads", "petal", "cross", "stone"])
    q = (0, -L * 0.42)
    if k == "comet": Mo.comet(s, (q[0] + 1, q[1] + 2, 0.8), (rng.uniform(-0.6, 0.6), -1, 0), 16, 3.0, count=4, seed=int(rng.integers(9)))
    elif k == "beads": Mo.bead_row(s, [q, (q[0] + 3, q[1] + 6), (q[0] + 2, q[1] + 14)], 1.3, 0.6, 6, 0.6)
    elif k == "petal": Mo.petal(s, st, (q[0], q[1] + 2, 0.8), 4.5, pal[0])
    elif k == "cross": Mo.cross_fleury(s, st, (q[0], q[1] - 6), 15, kind=pal[0], long_foot=1.5)
    else: Mo.prong(s, st, (q[0], q[1] + 2, 3.0), 6, pal[0], L=8, spin=a)
    s.units = [0.0]
    return s, st


PLAN = [  # (prefix, builder, kind, count)
    ("n_wings", b_neck_wings, "flat", 20), ("n_heart", b_neck_heart, "hang", 10), ("n_cross", b_neck_cross, "hang", 8),
    ("n_comet", b_neck_comet, "hang", 7), ("n_lariat", b_neck_lariat, "hang", 7),
    ("e_feather", pair_of(e_feather_drop, 16), "flat", 12), ("e_heart", pair_of(e_heart, 20), "flat", 10),
    ("e_cross", pair_of(e_cross, 20), "flat", 10), ("e_climber", pair_of(e_climber, 22), "flat", 12),
    ("p_stud", p_single, "flat", 18), ("p_navel", p_navel, "flat", 8), ("p_septum", p_septum, "flat", 6),
    ("p_industrial", p_industrial, "flat", 6), ("p_cuff", p_earcuff, "ring", 6),
    ("r_wing", r_wing, "ring", 28), ("r_top", r_top, "ring", 20),
    ("c_skin", c_feather_skin, "cuff", 32),
    ("h_clip", h_clip, "flat", 36),
]


def _register():
    i = 0
    for pre, fn, kind, n in PLAN:
        for j in range(n):
            seed = 7000 + i * 13; pal = PALS[i % len(PALS)]
            def mk(fn=fn, seed=seed, pal=pal):
                return fn(np.random.default_rng(seed), pal)
            name = f"{pre}_{j + 1:02d}"
            mk.__name__ = name
            PIECES[name] = (mk, kind)
            i += 1
    return i


N_GEN = _register()


# ================================================================ round 2 studies: wings
import wings2 as W2
from kit import Flat as _Flat


@piece("flat")
def w_study_angel():
    s = Scene(); st = []
    for sx in (1, -1):
        W2.angel_wing(s, W2.F0, st, (sx * 2.5, 0), 34, ang=0.12, sx=sx, rng=np.random.default_rng(3 + sx), bead_kind="garnet")
    Mo.prong(s, st, (0, -1, 4.2), 7, "aquamarine", L=9, spin=math.pi / 2)
    s.units = [0.0]
    return s, st


@piece("flat")
def w_study_bugs():
    s = Scene(); st = []
    W2.bug(s, W2.F0, st, (-30, 0), 40, "moth", rng=np.random.default_rng(1), pal=("garnet", "amethyst"), stones=2)
    W2.bug(s, W2.F0, st, (15, 0), 40, "butterfly", rng=np.random.default_rng(2), pal=("aquamarine", "moonstone"), stones=1)
    W2.bug(s, W2.F0, st, (58, 0), 40, "dragonfly", rng=np.random.default_rng(3), pal=("londonblue", "aquamarine"))
    s.units = [-30.0, 15.0, 58.0]
    return s, st


@piece("ring")
def w_study_ring():
    s = Scene(); st = []
    R = 9.3; m = Cyl(R)
    s.torus((0, 0, 0), R - 0.1, 0.8, normal=(0, 1, 0), k=0.4)
    for sx in (1, -1):
        W2.angel_wing(s, m, st, (sx * 3.0, -1.5), 22, ang=0.25, sx=sx, rng=np.random.default_rng(5 + sx), hook=False, z=0.3)
    Mo.prong(s, st, m.P(0, -0.5, 3.6), 6, "garnet", normal=m.N(0, -0.5))
    s.units = [0.0]
    return s, st


# ================================================================ round 2: 256 wing pieces
def hyo_flourish(s, st, rng, a, d, size, z=0.6, pal=("garnet",)):
    """A stronger hyodomachine gesture: a chrome whiplash ending in a hook with a bead, or a cross, or a bead row needle."""
    a = np.asarray(a, float)[:2]; d = Mo.nrm(np.asarray(d, float)[:2]); nn = np.array([-d[1], d[0]])
    k = rng.choice(["hook", "cross", "beads", "whip"])
    if k == "hook":
        M.hook(s, W2.F0, st, a + d * size, math.atan2(-d[1], -d[0]), size, cd=rng.choice([1, -1]), kind=pal[0], z=z, w=max(0.4, size * 0.07))
    elif k == "cross":
        Mo.chain(s, [Mo.v3(a, z), Mo.v3(a + d * size * 0.25, z)], link=1.2)
        Mo.cross_fleury(s, st, a + d * size * 0.72, size * 0.9, normal_rot=math.atan2(d[1], d[0]) + math.pi / 2, z=z, long_foot=1.6)
    elif k == "beads":
        # was a bead row (read as a crude bead string, Nov 18): now one liquid stroke that swells into a drop and draws to a needle
        import sculpt as _K
        q = [a, a + d * size * 0.45 + nn * size * rng.uniform(-0.15, 0.15), a + d * size * 0.95 + nn * size * rng.uniform(-0.2, 0.2)]
        _K.ribbon(s, np.array([Mo.v3(p_, z) for p_ in q]), m=None, w=max(0.5, size * 0.08), thin=0.75, ends=(0.0, 0.4),
                  wkeys=[(0, 0.8), (0.3, 1.15), (0.6, 0.85), (1, 0.35)], k=0.4)
    else:
        sg = rng.choice([1, -1])
        pts = [a, a + d * size * 0.4 + nn * sg * size * 0.25, a + d * size * 0.8 - nn * sg * size * 0.1, a + d * size * 1.2 + nn * sg * size * 0.2]
        M.whip(s, W2.F0, pts, w=max(0.45, size * 0.07), z=z, rise=0.8, ends=(0.0, 0.35))
    return k


def centre_piece(s, st, rng, c, size, pal, z=0.0):
    k = rng.choice(["stone", "heart", "cross", "petal"], p=[0.35, 0.25, 0.25, 0.15])
    c = np.asarray(c, float)
    if k == "stone":
        D = size * rng.uniform(0.2, 0.28); Mo.prong(s, st, (c[0], c[1], z + D * 0.5 + 0.9), D, pal[0], L=D * rng.choice([1, 1.3]), spin=math.pi / 2)
        s.ellipsoid((c[0], c[1], z + 0.5), (D * 0.55, D * 0.4, 0.9), k=0.6)
    elif k == "heart": Mo.thorn_heart(s, st, (c[0], c[1] - size * 0.05, z + 0.8), size * 0.55, pal[0], seed=int(rng.integers(99)), thorns=5, tail=0.3)
    elif k == "cross": Mo.cross_fleury(s, st, (c[0], c[1] - size * 0.15), size * 0.75, z=z + 0.8, kind=pal[0], long_foot=1.6)
    else: Mo.petal(s, st, (c[0], c[1], z + 0.8), size * 0.16, pal[0])
    return k


def W_n_angel(rng, pal):
    s = Scene(); st = []
    span = rng.uniform(30, 44); a = rng.uniform(-0.05, 0.35); asym = rng.random() < 0.3
    for sx in (1, -1):
        W2.angel_wing(s, W2.F0, st, (sx * span * 0.08, 0), span * (rng.uniform(0.75, 0.9) if asym and sx < 0 else 1), ang=a, sx=sx,
                      rng=rng, bead_kind=pal[1], hook=rng.random() < 0.6, lift=rng.uniform(-0.05, 0.1))
    k = centre_piece(s, st, rng, (0, 0), span * 0.6, pal, z=1.2)
    hyo_flourish(s, st, rng, (0, -span * 0.2), (rng.uniform(-0.1, 0.1), -1), span * 0.35, pal=pal[::-1])
    s.units = [0.0]; return s, st


def W_n_bug(rng, pal):
    s = Scene(); st = []
    size = rng.uniform(32, 44); kind = rng.choice(["moth", "butterfly", "moth", "dragonfly"])
    W2.bug(s, W2.F0, st, (0, 0), size, kind, rng=rng, pal=pal, stones=int(rng.integers(0, 3)))
    s.torus((0, size * 0.22, 0.6), 1.6, 0.5, normal=(1, 0, 0), k=0.3)
    if rng.random() < 0.7: hyo_flourish(s, st, rng, (0, -size * (0.5 if kind != "dragonfly" else 0.8)), (0, -1), size * 0.3, pal=pal[::-1])
    s.units = [0.0]; return s, st


def W_n_spine(rng, pal):
    s = Scene(); st = []
    L = rng.uniform(60, 80); n = int(rng.integers(3, 5))
    Mo.bead_row(s, [(0, 0), (rng.uniform(-3, 3), -L * 0.5), (0, -L)], 1.6, 0.8, int(rng.integers(9, 14)), 0.6)
    kind = rng.choice(["angel", "bug"])
    for i in range(n):
        y = -L * (0.12 + 0.7 * i / max(1, n - 1)); sz = (1 - 0.45 * i / max(1, n - 1))
        for sx in (1, -1):
            if kind == "angel": W2.angel_wing(s, W2.F0, st, (sx * 1.6, y), 22 * sz, ang=rng.uniform(-0.2, 0.25), sx=sx, rng=rng, hook=False, z=0.2)
            else: W2.vein_wing(s, W2.F0, st, (sx * 1.4, y), 20 * sz, ang=rng.uniform(-0.15, 0.3), sx=sx, rng=rng, shape=rng.choice(["fore", "dragon"]), z=0.2)
        Mo.prong(s, st, (0, y, 2.2), 3.4 * sz + 0.8, pal[i % 2])
    Mo.cross_fleury(s, st, (0, -L - 9), 18, long_foot=1.7)
    s.torus((0, 2.0, 0.5), 1.6, 0.5, normal=(1, 0, 0), k=0.3)
    s.units = [0.0]; return s, st


def W_n_cross(rng, pal):
    s = Scene(); st = []
    size = rng.uniform(26, 34)
    Mo.cross_fleury(s, st, (0, 0), size, long_foot=rng.uniform(1.3, 1.8), w=size * rng.uniform(0.045, 0.06), kind=pal[0])
    if rng.random() < 0.5:
        for sx in (1, -1): W2.angel_wing(s, W2.F0, st, (sx * 2, size * 0.05), size * 0.75, ang=0.35, sx=sx, rng=rng, hook=False, z=-1.2, bone=rng.random() < 0.5)
    else:
        for sx in (1, -1):
            W2.vein_wing(s, W2.F0, st, (sx * 2, size * 0.05), size * 0.6, ang=0.3, sx=sx, rng=rng, shape=rng.choice(["moth_f", "bfly_f", "fore"]), z=-1.0,
                         stones=int(rng.integers(0, 2)), pal=pal)
    s.torus((0, size * 0.43 + 1.6, 0.4), 1.6, 0.5, normal=(1, 0, 0), k=0.3)
    s.units = [0.0]; return s, st


def W_n_heart(rng, pal):
    s = Scene(); st = []
    w = rng.uniform(18, 24)
    Mo.thorn_heart(s, st, (0, 0, 0.8), w, pal[0], seed=int(rng.integers(99)), tail=rng.uniform(0.25, 0.45))
    kind = rng.choice(["angel", "bug"])
    for sx in (1, -1):
        if kind == "angel": W2.angel_wing(s, W2.F0, st, (sx * w * 0.38, w * 0.15), w * rng.uniform(1.0, 1.4), ang=rng.uniform(0.1, 0.4), sx=sx, rng=rng, hook=False, z=-0.6)
        else: W2.vein_wing(s, W2.F0, st, (sx * w * 0.38, w * 0.1), w * rng.uniform(0.9, 1.2), ang=rng.uniform(0.15, 0.45), sx=sx, rng=rng, shape=rng.choice(["moth_f", "bfly_f", "fore"]), z=-0.4)
    s.torus((0, w * 0.5 + 1.8, 0.6), 1.7, 0.5, normal=(1, 0, 0), k=0.3)
    hyo_flourish(s, st, rng, (0, -w * 0.6), (0, -1), w * 0.4, pal=pal[::-1])
    s.units = [0.0]; return s, st


# ---- earrings
def we_wing(s, st, rng, pal, sx, ox):
    span = rng.uniform(18, 26)
    W2.angel_wing(s, W2.F0, st, (ox, 0), span, ang=rng.uniform(0.2, 0.7), sx=sx, rng=rng, bead_kind=pal[0], hook=rng.random() < 0.6)
    _post(s, ox, 0)


def we_bug(s, st, rng, pal, sx, ox):
    Mo.prong(s, st, (ox, 0, 1.8), 3.4, pal[0]); s.sphere((ox, 0, 0.4), 1.6, k=0.4); _post(s, ox, 0)
    size = rng.uniform(18, 24)
    Mo.chain(s, [(ox, -2, 0), (ox, -5.5, 0)], link=1.1)
    W2.bug(s, W2.F0, st, (ox, -5.5 - size * 0.22), size, rng.choice(["moth", "butterfly", "moth", "butterfly", "dragonfly"]), ang=math.pi / 2 + sx * rng.uniform(0, 0.25), rng=rng, pal=pal)


def we_vein(s, st, rng, pal, sx, ox):
    span = rng.uniform(20, 28)
    W2.vein_wing(s, W2.F0, st, (ox, 0), span, ang=-math.pi / 2 + sx * rng.uniform(0.15, 0.5) if sx > 0 else math.pi + math.pi / 2 - rng.uniform(0.15, 0.5),
                 sx=sx, rng=rng, shape=rng.choice(["fore", "dragon", "bfly_f", "moth_f"]), stones=int(rng.integers(1, 3)), pal=pal)
    s.sphere((ox, 0, 0.6), 1.4, k=0.4); _post(s, ox, 0)


def we_hook(s, st, rng, pal, sx, ox):
    L = rng.uniform(16, 22)
    M.hook(s, W2.F0, st, (ox, -L * 1.1), math.pi / 2 + sx * 0.2, L, cd=sx, kind=pal[0], z=0.4)
    W2.vein_wing(s, W2.F0, st, (ox, -L * 0.15), L * rng.uniform(0.6, 0.9), ang=0.5, sx=sx, rng=rng, shape=rng.choice(["fore", "moth_f", "bfly_f"]), z=0.0)
    s.sphere((ox, 0, 0.5), 1.4, k=0.4); _post(s, ox, 0)
    s.cone((ox, 0, 0.4), (ox, -L * 0.3, 0.5), 0.5, 0.5, k=0.3)


# ---- piercings
def W_p_stud(rng, pal):
    s = Scene(); st = []
    k = rng.choice(["moth", "butterfly", "wings", "veinpair"])
    if k in ("moth", "butterfly"): W2.bug(s, W2.F0, st, (0, 0), rng.uniform(13, 17), k, rng=rng, pal=pal)
    elif k == "wings":
        for sx in (1, -1): W2.angel_wing(s, W2.F0, st, (sx * 1.2, 0), rng.uniform(9, 12), ang=rng.uniform(0.1, 0.5), sx=sx, rng=rng, hook=False, coverts=True)
        Mo.prong(s, st, (0, 0, 2.2), 3.4, pal[0])
    else:
        for sx in (1, -1): W2.vein_wing(s, W2.F0, st, (sx * 1.0, 0), rng.uniform(9, 12), ang=rng.uniform(0.2, 0.6), sx=sx, rng=rng, shape="fore")
        Mo.prong(s, st, (0, 0, 2.0), 3.0, pal[0])
    _post(s, 0, 0); s.units = [0.0]; return s, st


def W_p_septum(rng, pal):
    s = Scene(); st = []
    th = np.linspace(-0.25 * math.pi, 1.25 * math.pi, 40); R = 5.5
    s.stroke(np.stack([R * np.cos(th), -R * np.sin(th), np.zeros(40)], 1), np.full(40, 0.6), k=0.3)
    for sx in (1, -1): s.sphere((sx * R * math.cos(0.25 * math.pi), R * math.sin(0.25 * math.pi), 0), 1.0, k=0.3)
    if rng.random() < 0.5: W2.bug(s, W2.F0, st, (0, -R - 3.5), 13, rng.choice(["moth", "butterfly"]), rng=rng, pal=pal)
    else:
        for sx in (1, -1): W2.angel_wing(s, W2.F0, st, (sx * 1.0, -R - 0.5), 9, ang=-0.2, sx=sx, rng=rng, hook=False)
        Mo.prong(s, st, (0, -R - 1.0, 1.8), 3.0, pal[0])
    s.units = [0.0]; return s, st


def W_p_navel(rng, pal):
    s = Scene(); st = []
    Mo.prong(s, st, (0, 0, 2.2), 4.5, pal[0]); s.sphere((0, 0, 0.3), 2.1, k=0.4)
    s.cone((0, 1.0, -0.2), (0, 10, -4.0), 0.8, 0.8, k=0.3); s.sphere((0, 10.5, -4.2), 1.6, k=0.3)
    Mo.chain(s, [(0, -2.5, 0), (0, -6, 0)], link=1.1)
    W2.bug(s, W2.F0, st, (0, -6 - 5), rng.uniform(18, 24), rng.choice(["moth", "butterfly", "moth", "butterfly", "dragonfly"]), rng=rng, pal=pal[::-1], stones=int(rng.integers(0, 2)))
    s.units = [0.0]; return s, st


def W_p_industrial(rng, pal):
    s = Scene(); st = []
    s.cone((-19, 0, -1.2), (19, 0, -1.2), 0.75, 0.75, k=0.3)
    for sx in (-1, 1): s.sphere((sx * 20.3, 0, -1.2), 1.8, k=0.3)
    if rng.random() < 0.5: W2.bug(s, W2.F0, st, (rng.uniform(-6, 6), 0), 22, "dragonfly", ang=rng.choice([0.0, math.pi]), rng=rng, pal=pal)
    else:
        sx = rng.choice([1, -1]); W2.angel_wing(s, W2.F0, st, (sx * 14, 0), 24, ang=math.pi - 0.15 if sx > 0 else 0.15 - math.pi, sx=1, rng=rng, bead_kind=pal[0])
    s.units = [0.0]; return s, st


# ---- rings
def W_r_angel(rng, pal):
    s = Scene(); st = []
    R = 9.3; m = Cyl(R)
    s.torus((0, 0, 0), R - 0.1, 0.8, normal=(0, 1, 0), k=0.4)
    span = rng.uniform(18, 25); a = rng.uniform(-0.1, 0.45)
    sides = (1, -1) if rng.random() < 0.7 else (rng.choice([1, -1]),)
    for sx in sides: W2.angel_wing(s, m, st, (sx * 2.8, rng.uniform(-2, 0)), span, ang=a, sx=sx, rng=rng, hook=rng.random() < 0.4, z=0.3, bead_kind=pal[1])
    D = rng.uniform(5, 7.5); Mo.prong(s, st, m.P(0, -0.3, D * 0.5 + 1.0), D, pal[0], L=D * rng.choice([1, 1.3]), normal=m.N(0, -0.3), spin=math.pi / 2)
    s.units = [0.0]; return s, st


def W_r_bug(rng, pal):
    s = Scene(); st = []
    R = 9.3
    s.torus((0, 0, 0), R - 0.1, 0.85, normal=(0, 1, 0), k=0.4)
    s.ellipsoid((0, 0, R + 0.4), (3.5, 3.0, 1.2), k=0.8)
    size = rng.uniform(17, 22); kind = rng.choice(["moth", "butterfly", "moth", "butterfly", "dragonfly"])
    W2.bug(s, _Flat(o=(0, 0, R + 0.9)), st, (0, 0), size, kind, ang=rng.choice([math.pi / 2, 0.0, math.pi / 2 + 0.4]), rng=rng, pal=pal, stones=int(rng.integers(0, 2)))
    s.units = [0.0]; return s, st


def W_r_vein(rng, pal):
    s = Scene(); st = []
    R = 9.3; m = Cyl(R)
    s.torus((0, 0, 0), R - 0.1, 0.8, normal=(0, 1, 0), k=0.4)
    shp = rng.choice(["fore", "bfly_f", "moth_f", "dragon"])
    for sx in (1, -1):
        W2.vein_wing(s, m, st, (sx * 2.5, rng.uniform(-1.5, 0.5)), rng.uniform(17, 23), ang=rng.uniform(-0.1, 0.4), sx=sx, rng=rng, shape=shp,
                     stones=int(rng.integers(0, 3)), pal=pal, z=0.3)
    D = rng.uniform(4.5, 6.5); Mo.prong(s, st, m.P(0, 0, D * 0.5 + 1.0), D, pal[0], normal=m.N(0, 0))
    s.units = [0.0]; return s, st


# ---- cuffs
def W_c_angel(rng, pal):
    s = Scene(); st = []
    R = 29.0; m = Cyl(R)
    span = rng.uniform(48, 62)
    for sx in (1, -1): W2.angel_wing(s, m, st, (sx * 5, rng.uniform(-3, 0)), span, ang=rng.uniform(-0.05, 0.3), sx=sx, rng=rng, bead_kind=pal[1], hook=rng.random() < 0.5)
    D = rng.uniform(8, 11); Mo.prong(s, st, m.P(0, -1, D * 0.5 + 1.2), D, pal[0], L=D * rng.choice([1, 1.3]), normal=m.N(0, -1), spin=math.pi / 2)
    s.units = [0.0]; return s, st


def W_c_bug(rng, pal):
    s = Scene(); st = []
    R = 29.0; m = Cyl(R)
    shp = rng.choice(["fore", "bfly_f", "moth_f", "dragon"])
    for sx in (1, -1):
        W2.vein_wing(s, m, st, (sx * 6, 2), rng.uniform(48, 58), ang=rng.uniform(0.0, 0.25), sx=sx, rng=rng, shape=shp, stones=int(rng.integers(1, 4)), pal=pal)
        W2.vein_wing(s, m, st, (sx * 6, -2), rng.uniform(34, 42), ang=-rng.uniform(0.25, 0.5), sx=sx, rng=rng, shape="moth_h" if shp != "dragon" else "dragon", pal=pal[::-1])
    W2.bug(s, _Flat(o=(0, 0, R + 0.6)), st, (0, 0), 16, rng.choice(["moth", "butterfly"]), rng=rng, pal=pal)
    s.units = [0.0]; return s, st


# ---- hair clips
def _clipbar(s, a, b):
    s.cone(np.array([a[0], a[1], -1.4]), np.array([b[0], b[1], -1.4]), 0.9, 0.7, k=0.3, flat=2.0, zhint=(0, 0, 1))


def W_h_wing(rng, pal):
    s = Scene(); st = []
    span = rng.uniform(48, 66)
    k = W2.angel_wing(s, W2.F0, st, (0, 0), span, ang=rng.uniform(-0.2, 0.35), sx=rng.choice([1, -1]), rng=rng, bead_kind=pal[0])
    _clipbar(s, k["root"] * 0.8 + k["wrist"] * 0.2, k["root"] * 0.3 + k["wrist"] * 0.7)
    s.units = [0.0]; return s, st


def W_h_moth(rng, pal):
    s = Scene(); st = []
    size = rng.uniform(44, 58)
    W2.bug(s, W2.F0, st, (0, 0), size, rng.choice(["moth", "butterfly"]), ang=math.pi / 2 + rng.uniform(-0.3, 0.3), rng=rng, pal=pal, stones=int(rng.integers(1, 4)))
    _clipbar(s, (-size * 0.25, 0), (size * 0.25, 0))
    s.units = [0.0]; return s, st


def W_h_dragon(rng, pal):
    s = Scene(); st = []
    if rng.random() < 0.6:
        size = rng.uniform(55, 70)
        W2.bug(s, W2.F0, st, (0, 0), size, "dragonfly", ang=math.pi / 2 + rng.uniform(-0.6, 0.6), rng=rng, pal=pal, stones=int(rng.integers(0, 3)))
        _clipbar(s, (0, -size * 0.1), (0, size * 0.1))
    else:
        sx = rng.choice([1, -1])
        for i, shp in enumerate(["fore", "hind"]):
            W2.vein_wing(s, W2.F0, st, (0, -i * 3), rng.uniform(46, 58) * (1 - 0.25 * i), ang=rng.uniform(0.1, 0.4) - 0.6 * i, sx=sx, rng=rng, shape=shp,
                         stones=int(rng.integers(1, 3)), pal=pal, z=0.4 * (1 - i))
        M.hook(s, W2.F0, st, (sx * -2, -10), math.pi / 2, 14, cd=sx, kind=pal[1], z=0.8)
        _clipbar(s, (sx * 2, -2), (sx * 24, 4))
    s.units = [0.0]; return s, st


PLAN2 = [("w_n_angel", W_n_angel, "flat", 12), ("w_n_bug", W_n_bug, "hang", 12), ("w_n_spine", W_n_spine, "hang", 8),
         ("w_n_cross", W_n_cross, "hang", 10), ("w_n_heart", W_n_heart, "hang", 10),
         ("w_e_wing", pair_of(we_wing, 26), "flat", 12), ("w_e_bug", pair_of(we_bug, 26), "flat", 12),
         ("w_e_vein", pair_of(we_vein, 30), "flat", 10), ("w_e_hook", pair_of(we_hook, 26), "flat", 10),
         ("w_p_stud", W_p_stud, "flat", 16), ("w_p_septum", W_p_septum, "flat", 8), ("w_p_navel", W_p_navel, "flat", 8),
         ("w_p_industrial", W_p_industrial, "flat", 8),
         ("w_r_angel", W_r_angel, "ring", 16), ("w_r_bug", W_r_bug, "ring", 14), ("w_r_vein", W_r_vein, "ring", 14),
         ("w_c_angel", W_c_angel, "cuff", 15), ("w_c_bug", W_c_bug, "cuff", 15),
         ("w_h_wing", W_h_wing, "flat", 16), ("w_h_moth", W_h_moth, "flat", 22), ("w_h_dragon", W_h_dragon, "flat", 8)]


def _register2():
    i = 0
    for pre, fn, kind, n in PLAN2:
        for j in range(n):
            seed = 91000 + i * 17; pal = PALS[(i * 3) % len(PALS)]
            def mk(fn=fn, seed=seed, pal=pal):
                return fn(np.random.default_rng(seed), pal)
            name = f"{pre}_{j + 1:02d}"; mk.__name__ = name; PIECES[name] = (mk, kind); i += 1
    return i


N_GEN2 = _register2()
