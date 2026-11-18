"""Round 2 (Nov 16): whole wings instead of single feathers, and a stronger hyodomachine hand.
angel_wing - Moira's layered wing: scale-like coverts, secondaries, a fan of long primaries, carried on a
             liquid chrome bone (hyodomachine) that runs past the tip as a needle and rolls into a hook at the root.
vein_wing  - hyodomachine insect wing: open chrome venation, needle overshoots, no fill (negative space).
All take a mapper m (kit.Flat / kit.Cyl): layouts are drawn in (x, y) and pushed onto the surface."""
import math
import numpy as np
import sculpt as K
import moira as Mo
import motifs as M
from kit import Flat, Cyl, smooth
from sdf import resample

F0 = Flat()


def _rot(p, a):
    c, s_ = math.cos(a), math.sin(a); p = np.asarray(p, float)
    return np.stack([p[..., 0] * c - p[..., 1] * s_, p[..., 0] * s_ + p[..., 1] * c], -1)


def place(p, root, ang, sx):
    p = np.asarray(p, float) * [sx, 1]
    return _rot(p, ang * sx) + np.asarray(root, float)


def mfeather(s, m, p2, d2, L, z=0.0, W=None, bend=0.0, seed=1.0):
    """A carved feather laid on mapper m: base p2, direction d2 (in the layout plane)."""
    p2 = np.asarray(p2, float); d2 = np.asarray(d2, float); d2 = d2 / np.linalg.norm(d2)
    base = m.P(p2[0], p2[1], z); u, v = m.T(p2[0], p2[1]); n = m.N(p2[0], p2[1])
    d3 = u * d2[0] + v * d2[1]
    wrap = -(d2[0] ** 2) / (m.R + z) if isinstance(m, Cyl) else 0.0
    Mo.feather(s, base, d3, n, L, W=W, bend=bend, wrap=wrap, seed=seed)


def angel_wing(s, m, st, root, span, ang=0.0, sx=1, z=0.0, rng=None, n_prim=None, n_sec=None, coverts=True, bone=True,
               hook=True, bead_kind="garnet", needle=True, lift=0.0):
    """Layered wing. root = shoulder; it spreads along +x (mirrored by sx) rotated by ang. Returns key points."""
    rng = rng or np.random.default_rng(0)
    S = span
    LE = np.array([(0, 0), (0.18, 0.15 + lift), (0.4, 0.23 + lift), (0.58, 0.21 + lift * 0.8), (0.79, 0.11 + lift * 0.4), (1.0, -0.02)]) * S
    le = resample(smooth(LE, 10), 0.2)[:, :2]
    cs = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(le, axis=0), axis=1))]); cs /= cs[-1]

    def at(u):
        i = int(np.clip(np.searchsorted(cs, u), 0, len(le) - 1)); return le[i]

    def dirl(deg):
        a = math.radians(deg); return np.array([math.cos(a), math.sin(a)])

    def put(p, deg, L, zz, W=None, bend=0.0):
        P = place(p, root, ang, sx)
        D = _rot(dirl(deg) * [sx, 1], ang * sx)
        mfeather(s, m, P, D, L, z=zz, W=W, bend=bend * sx, seed=float(rng.uniform(0, 60)))

    n_prim = n_prim or int(rng.integers(6, 9)); n_sec = n_sec or int(rng.integers(6, 9))
    # primaries: a fan from the wrist, longest at the tip
    for i in range(n_prim):
        f = i / max(1, n_prim - 1)
        u = 0.62 - 0.14 * f
        deg = -12 - 62 * f
        L = S * (0.52 - 0.16 * f) * rng.uniform(0.94, 1.04)
        put(at(u) + np.array([0, -0.03 * S]), deg, L, z + 0.06 * i, W=L * 0.15, bend=-0.25 / S * (0.6 + f))
    # secondaries: hang from the arm, shorter toward the shoulder
    for i in range(n_sec):
        f = i / max(1, n_sec - 1)
        u = 0.48 - 0.38 * f
        deg = -82 - 14 * f
        L = S * (0.36 - 0.1 * f) * rng.uniform(0.94, 1.04)
        put(at(u) + np.array([0, -0.02 * S]), deg, L, z + 0.4 + 0.05 * i, W=L * 0.19, bend=-0.3 / S)
    # coverts: short scale-like feathers shingled along the leading edge
    if coverts:
        nc = int(max(5, round(S / 3.2)))
        for i in range(nc):
            f = i / max(1, nc - 1)
            u = 0.06 + 0.56 * f
            L = S * (0.15 + 0.05 * math.sin(math.pi * f)) * rng.uniform(0.9, 1.1)
            put(at(u) + np.array([0, -0.01 * S]), -60 - 25 * (1 - f), L, z + 0.85 + 0.03 * i, W=L * 0.24, bend=-0.6 / S)
    # the bone: a liquid chrome stroke along the leading edge, overshooting the tip as a needle
    tipP = place(at(1.0), root, ang, sx)
    rootP = place(le[0], root, ang, sx)
    if bone:
        ext = [le[-1] + (le[-1] - le[-6]) / np.linalg.norm(le[-1] - le[-6]) * S * 0.12 * (1 if needle else 0.01)]
        path = place(np.vstack([le[::3], ext]), root, ang, sx)
        zz = z + 1.25 + 0.5 * np.sin(np.linspace(0, math.pi, len(path)))
        K.ribbon(s, np.column_stack([path, zz]), m=m, w=max(0.38, S * 0.028), thin=0.5, ends=(0.0, 0.3 if needle else 0.05),
                 wkeys=[(0, 1.2), (0.25, 1.0), (0.55, 0.85), (1, 0.45)], twist=[(0, 0), (0.5, 0.5 * sx), (1, 0.1)], k=0.3)
        if hook:
            # the root rolls back into a hook holding a bead (hyodomachine)
            a_back = math.atan2(*(place(le[6], root, ang, sx) - rootP)[::-1]) + math.pi
            M.hook(s, m, st, rootP + np.array([math.cos(a_back), math.sin(a_back)]) * S * 0.02, a_back + math.pi, S * 0.22,
                   cd=-sx, kind=bead_kind, z=z + 1.25, w=max(0.36, S * 0.026))
    return dict(root=rootP, tip=tipP, wrist=place(at(0.58), root, ang, sx), elbow=place(at(0.3), root, ang, sx))


FORE = [(0, 0), (7, 3.2), (16, 6.2), (25, 8.8), (33, 10.6), (39, 11.4), (42.5, 10.2), (40.5, 6.0), (36, 0.8),
        (30, -3.6), (23, -6.4), (15.5, -7.2), (8.5, -5.6), (3, -2.6)]
DRAGON = [(0, 0), (8, 2.4), (18, 3.6), (28, 4.4), (37, 4.8), (42, 4.0), (43.5, 1.6), (41, -1.6), (33, -3.2),
          (22, -3.8), (12, -3.6), (5, -2.4), (1.5, -1.0)]
HINDW = [(0, 0), (9, 1.6), (19, 1.2), (27, -1.6), (30, -6.5), (27, -11.5), (19, -13.5), (10.5, -11.0), (4, -5.8)]


def _poly_at(P, f):
    c = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); c /= c[-1]
    i = int(np.clip(np.searchsorted(c, f), 1, len(P) - 1)); t = (f - c[i - 1]) / max(c[i] - c[i - 1], 1e-9)
    return P[i - 1] * (1 - t) + P[i] * t


def vein_wing(s, m, st, root, span, ang=0.0, sx=1, z=0.0, rng=None, beads=True, kind="moonstone", shape="fore", stones=0,
              pal=("aquamarine", "moonstone")):
    """hyodomachine bug wing: a chrome leading edge that swells and twists, a fine trailing rim, longitudinal veins
    fanning from the root, cross-veins making open cells, veins breaking the margin as needles; beads at the root.
    stones: a few small claw-set stones dropped into the larger cells (Moira's setting)."""
    rng = rng or np.random.default_rng(0)
    base = _shape(shape)
    ext = np.asarray(base, float); sc = span / np.linalg.norm(ext, axis=1).max()
    o = resample(smooth(ext * sc, 10, closed=True), 0.2)[:, :2]
    tip_i = int(np.argmax(np.linalg.norm(o, axis=1)))
    w = max(0.34, span * 0.026)
    lead = o[:tip_i + 1]
    Lp = place(lead, root, ang, sx)
    K.ribbon(s, np.column_stack([Lp, z + 0.6 + 0.6 * np.sin(np.linspace(0, math.pi, len(Lp)))]), m=m, w=w * 1.25, thin=0.5,
             ends=(0.0, 0.08), wkeys=[(0, 1.2), (0.5, 0.9), (1, 0.5)], twist=[(0, 0), (0.5, 0.5 * sx), (1, 0)], k=0.3)
    trail = np.vstack([o[tip_i:], o[:1]])
    Tp = place(trail, root, ang, sx)
    K.ribbon(s, np.column_stack([Tp, np.full(len(Tp), z + 0.3)]), m=m, w=w * 0.5, thin=0.8, ends=(0.0, 0.0), k=0.2)
    # longitudinal veins: from points near the root on the leading edge out to the trailing rim
    nv = int(rng.integers(3, 6)) if shape != "dragon" else int(rng.integers(2, 4))
    veins = [lead]
    for j, f in enumerate(np.linspace(0.12, 0.82, nv)[::-1]):
        e = _poly_at(trail, f)
        a0 = _poly_at(lead, 0.08 + 0.1 * (nv - 1 - j) / max(1, nv - 1)) * 0.6
        mid = a0 * 0.45 + e * 0.55 + rng.uniform(-1, 1, 2) * span * 0.02
        veins.append(np.array([a0, mid, e]))
    veins.append(trail[::-1])
    for j, v in enumerate(veins[1:-1]):
        e = v[-1]; dd = (e - v[1]) / np.linalg.norm(e - v[1])
        vv = np.vstack([v, e + dd * span * rng.uniform(0.06, 0.12)])
        P = place(vv, root, ang, sx)
        K.ribbon(s, np.column_stack([P, np.full(len(P), z + 0.35)]), m=m, w=w * 0.48, thin=0.8, ends=(0.0, 0.45),
                 wkeys=[(0, 1.0), (0.7, 0.85), (1, 0.6)], k=0.2)
        if beads:
            q = place(v[0], root, ang, sx); s.sphere(m.P(q[0], q[1], z + 0.55), w * 0.95, k=0.25)
    # cross-veins: rungs between neighbouring veins, slightly bowed
    cells = []
    for a, b in zip(veins[:-1], veins[1:]):
        A = resample(np.column_stack([smooth(a, 8), ]), 0.2)[:, :2] if len(a) > 2 else a
        B = resample(np.column_stack([smooth(b, 8), ]), 0.2)[:, :2] if len(b) > 2 else b
        nr = int(rng.integers(2, 4))
        prev = 0.25
        for f in np.sort(rng.uniform(0.3, 0.9, nr)):
            p, q = _poly_at(A, f), _poly_at(B, f * rng.uniform(0.9, 1.05))
            if np.linalg.norm(p - q) < span * 0.04: continue
            mid = (p + q) / 2 + rng.uniform(-1, 1, 2) * span * 0.01
            P = place(np.array([p, mid, q]), root, ang, sx)
            K.ribbon(s, np.column_stack([P, np.full(3, z + 0.32)]), m=m, w=w * 0.3, thin=0.85, ends=(0.0, 0.0), k=0.15)
            cells.append(((_poly_at(A, (prev + f) / 2) + _poly_at(B, (prev + f) / 2)) / 2, np.linalg.norm(p - q), f - prev))
            prev = f
    # Moira's touch: a few claw-set stones sitting in the biggest cells
    if stones:
        cells.sort(key=lambda c: -c[1])
        for i, (cc, gap, df) in enumerate(cells[:stones]):
            D = float(np.clip(gap * 0.55, 1.2, 5.0))
            P = place(cc, root, ang, sx)
            nrm = m.N(P[0], P[1])
            Mo.prong(s, st, m.P(P[0], P[1], z + D * 0.45 + 0.2), D, pal[i % len(pal)], normal=nrm, n=4, wire=max(0.26, D * 0.08))
    return dict(root=place(o[0], root, ang, sx), tip=place(o[tip_i], root, ang, sx))


# butterfly and moth outlines (root at the origin, spreading along +x; forewing up, hindwing down)
BFLY_F = [(0, 0), (6, 4.5), (14, 10.5), (22, 16.5), (29, 21), (34, 22.5), (37, 20), (37.5, 14), (34, 6.5), (28, 1.2),
          (20, -1.8), (12, -2.4), (5, -1.6)]
BFLY_H = [(0, 0), (8, -0.4), (17, -1.8), (25, -5.5), (29, -11), (28, -17), (24.5, -21), (22, -27), (19.5, -21.5),
          (13.5, -20), (7, -14), (2.5, -6.5)]
MOTH_F = [(0, 0), (8, 3.2), (18, 7.2), (28, 11.4), (37, 13.4), (41, 11.6), (40, 6.2), (35, 0.4), (27, -3.2),
          (17, -4.6), (8, -3.8), (2.5, -2.0)]
MOTH_H = [(0, 0), (8, -0.6), (16, -2.6), (22, -6.4), (24, -11.6), (20.5, -16.2), (13.5, -16.4), (7, -12), (2.4, -5.6)]
for _k, _v in dict(bfly_f=BFLY_F, bfly_h=BFLY_H, moth_f=MOTH_F, moth_h=MOTH_H).items():
    pass


def _shape(shape):
    return {"fore": FORE, "dragon": DRAGON, "hind": HINDW, "bfly_f": BFLY_F, "bfly_h": BFLY_H, "moth_f": MOTH_F, "moth_h": MOTH_H}[shape]


def bug(s, m, st, c, size, kind="moth", ang=math.pi / 2, z=0.0, rng=None, pal=("aquamarine", "moonstone"), stones=0, open_=1.0):
    """A whole moth / butterfly / dragonfly, seen from above, head toward ang.
    Body: a hyodomachine bead spine (graded beads) with a claw-set stone as the thorax.
    Antennae: moths get two little carved feathers (Moira), butterflies get curled hooks holding beads."""
    rng = rng or np.random.default_rng(0)
    c = np.asarray(c, float); d = np.array([math.cos(ang), math.sin(ang)]); nn = np.array([-d[1], d[0]])
    shapes = {"moth": ("moth_f", "moth_h"), "butterfly": ("bfly_f", "bfly_h"), "dragonfly": ("dragon", "dragon")}[kind]
    for sx in (1, -1):
        tilt_f = (0.18 if kind != "dragonfly" else 0.1) * open_
        tilt_h = -0.22 if kind != "dragonfly" else -0.1
        span_f = size * (0.55 if kind != "dragonfly" else 0.62)
        span_h = size * (0.42 if kind == "moth" else 0.48 if kind == "butterfly" else 0.56)
        for span, tilt, shp, dz, off, nst in ((span_f, tilt_f, shapes[0], 0.4, 0.05, stones), (span_h, tilt_h, shapes[1], 0.0, -0.06, max(0, stones - 1))):
            th = (ang - math.pi / 2 + tilt) if sx > 0 else (ang + math.pi / 2 - tilt)
            A = th if sx > 0 else math.pi - th
            R0 = c + d * size * off - nn * (-sx) * size * 0.0 + np.array([math.cos(th), math.sin(th)]) * size * 0.03
            vein_wing(s, m, st, R0, span, ang=A, sx=sx, z=z + dz, rng=rng, shape=shp, stones=nst, pal=pal, beads=False)
    # body: thorax stone, head bead, graded abdomen beads ending in a needle
    D = size * 0.12
    Mo.prong(s, st, m.P(*(c + d * size * 0.02), z + D * 0.5 + 0.6), D, pal[0], L=D * 1.3, normal=m.N(*c), spin=ang, n=4)
    s.ellipsoid(m.P(*(c + d * size * 0.02), z + 0.4), (D * 0.75, D * 0.6, D * 0.35), xaxis=np.append(d, 0), k=0.5)
    s.sphere(m.P(*(c + d * size * 0.12), z + 0.8), size * 0.04, k=0.3)
    tail = size * (0.42 if kind != "dragonfly" else 0.7)
    from abdomen import abdomen      # Nov 18: one carved abdomen, no bead row
    abdomen(s, m, c - d * size * 0.04, -d, tail * 1.1, size * (0.06 if kind != "dragonfly" else 0.045), z=z + 0.6, rng=rng,
            plates=5 if kind != "dragonfly" else 8)
    # antennae
    for sx in (1, -1):
        a0 = c + d * size * 0.14 + nn * sx * size * 0.02
        ad = d * math.cos(0.45) + nn * sx * math.sin(0.45)
        if kind == "moth":
            mfeather(s, m, a0, ad, size * 0.24, z=z + 0.8, W=size * 0.045, bend=-sx * 1.5 / size, seed=float(rng.uniform(0, 40)))
        elif kind == "butterfly":
            M.hook(s, m, st, a0 + ad * size * 0.32, math.atan2(-ad[1], -ad[0]), size * 0.34, cd=sx, kind=None, z=z + 0.8,
                   w=max(0.3, size * 0.016))
            s.sphere(m.P(*(a0 + ad * size * 0.33), z + 0.8), max(0.5, size * 0.025), k=0.2)
    return c
