"""Stained-glass kit: the shared parts every one of the 64 pieces is built from.

Design is done in 2D on a *mapper* (a flat plane anywhere in space, or a cylinder for
bands and cuffs) and realised into an sdf.Scene:
  nib      broad-nib calligraphic stroke: width follows the pen angle (hairline <-> swell),
           ends taper to a needle point (hyodomachine flash)
  spike    curved tapered flick / thorn / horn
  glaze    pack calibrated fancy stones into a closed cell and set them flush, open-backed
  lead     plain lead line
  bead     a glossy round gem bead in a cup ; stalk = stem + ball or bead
  thorns   thorn claws: a faceted stone held by uneven thorns that curl over the crown
  lancet / rose / fleur / wing / spine / curl   composite motifs
Mounts: shank, stud post, labret pin, ear wire, jump ring, bail, buckle back.
"""
import math
import numpy as np
from sdf import Scene, catmull, resample, arclen, profile, tangents
import v2
from v2 import nrm, blade, set_fancy, pack_stones, claws, ring_band, TIP

PAL = dict(
    ember=["garnet", "amethyst", "citrine"], tide=["aquamarine", "topaz", "londonblue"],
    bruise=["amethyst", "garnet", "londonblue"], venom=["peridot", "citrine", "aquamarine"],
    night=["londonblue", "amethyst", "moonstone"], dusk=["garnet", "citrine", "topaz"])


# ---------------------------------------------------------------- mappers
class Flat:
    """A plane: origin o, in-plane axes u, v (normal = u x v)."""
    def __init__(self, o=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0)):
        self.o = np.asarray(o, float); self.u = nrm(u); v = np.asarray(v, float)
        self.n = nrm(np.cross(self.u, v)); self.v = np.cross(self.n, self.u)

    def P(self, x, y, z=0.0):
        return self.o + self.u * x + self.v * y + self.n * z

    def N(self, x, y): return self.n
    def T(self, x, y): return self.u, self.v

    def rot(self, ang):            # same plane, rotated in-plane
        c, s = math.cos(ang), math.sin(ang)
        return Flat(self.o, self.u * c + self.v * s, -self.u * s + self.v * c)


def hinge(m, p, axis, ang):
    """Plane m rotated by ang about an in-plane line through 2D point p along 2D axis."""
    o = m.P(*p); a = nrm(m.u * axis[0] + m.v * axis[1])
    def R(v):
        v = np.asarray(v, float)
        return v * math.cos(ang) + np.cross(a, v) * math.sin(ang) + a * np.dot(a, v) * (1 - math.cos(ang))
    f = Flat(o + R(m.o - o), R(m.u), R(m.v))
    return f


class Cyl:
    """Cylinder of radius R about the y axis, x = arc length (0 at the top, +z), z = outward."""
    def __init__(self, R, o=(0, 0, 0)):
        self.R = R; self.o = np.asarray(o, float)

    def P(self, x, y, z=0.0):
        t = x / self.R; r = self.R + z
        return self.o + np.array([r * math.sin(t), y, r * math.cos(t)])

    def N(self, x, y):
        t = x / self.R; return np.array([math.sin(t), 0.0, math.cos(t)])

    def T(self, x, y):
        t = x / self.R; return np.array([math.cos(t), 0.0, -math.sin(t)]), np.array([0.0, 1.0, 0.0])


# ---------------------------------------------------------------- curves
def smooth(pts, n=10, closed=False):
    p = np.asarray(pts, float)
    if p.shape[1] == 2: p = np.column_stack([p, np.zeros(len(p))])
    return catmull(p, n, closed)


def arc(cx, cy, r, a0, a1, n=24):
    t = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1)


def spiral(cx, cy, r0, r1, a0, turns, n=40):
    t = np.linspace(0, 1, n); a = a0 + turns * 2 * math.pi * t
    r = r0 + (r1 - r0) * t
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1)


def lancet_outline(a, h, R=None, n=18):
    """Pointed (lancet) arch, half width a, total height h, springing at the base y=0..ys."""
    R = R or 1.6 * 2 * a
    rise = math.sqrt(R * R - (R - a) ** 2)
    ys = max(0.0, h - rise)
    phi = math.acos((R - a) / R)
    right = [(a, 0.0)] + [(a - R + R * math.cos(t), ys + R * math.sin(t)) for t in np.linspace(0, phi, n)]
    left = [(-x, y) for x, y in right[::-1]]
    return np.array(right + left[1:])


def heart_outline(w, h, n=60):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    return np.stack([x / 32 * w, (y + 5) / 29 * h], 1)


WING = [(0, 0), (8, 3.2), (20, 6.0), (33, 8.0), (43, 8.4), (47, 5.6), (46.5, 0.5), (43, -6.5), (37, -13.5),
        (30, -16.0), (24, -14.0), (16, -9.5), (8, -5.0), (2, -2.2)]
HIND = [(0, 0), (10, 2.0), (22, 1.5), (31, -3.0), (33, -9.0), (28, -16.0), (19, -19.0), (10, -15.0), (3, -7.0)]


def xform(pts, sx=1.0, sy=1.0, rot=0.0, t=(0, 0), mirror=False):
    p = np.asarray(pts, float)[:, :2] * [sx, sy]
    if mirror: p = p * [-1, 1]
    c, s = math.cos(rot), math.sin(rot)
    p = p @ np.array([[c, s], [-s, c]])
    return p + np.asarray(t, float)


# ---------------------------------------------------------------- strokes
def nib(s, m, pts, w=1.0, pen=0.75, hair=0.2, z=0.0, thick=0.62, taper=(0.12, 0.2), tip=None, n=10,
        closed=False, k=0.35, rise=None, wkeys=None, op=0, engrave=0.0, mitre=True):
    """Broad-nib stroke. Half width = w * (hair + (1-hair)|sin(dir - pen)|), tapering to a
    needle at the ends; thickness = thick * width (min 0.32 so it casts)."""
    tip = TIP if tip is None else tip
    c = smooth(pts, n, closed) if len(pts) > 2 else np.column_stack([np.asarray(pts, float)[:, :2], np.zeros(2)])
    c = resample(c, 0.25)
    if closed: c = np.vstack([c, c[:1]])
    tg = tangents(c); ang = np.arctan2(tg[:, 1], tg[:, 0])
    u = arclen(c); u = u / max(u[-1], 1e-6)
    W = w * (hair + (1 - hair) * np.abs(np.sin(ang - pen)))
    W = np.convolve(np.pad(W, 3, mode="edge"), np.ones(7) / 7, mode="valid")
    if wkeys: W = W * profile(u, wkeys)
    if not closed:
        t0, t1 = taper
        if t0 > 0: W = np.where(u < t0, tip + (W - tip) * np.sin(np.clip(u / t0, 0, 1) * math.pi / 2), W)
        if t1 > 0: W = np.where(u > 1 - t1, tip + (W - tip) * np.sin(np.clip((1 - u) / t1, 0, 1) * math.pi / 2), W)
    W = np.maximum(W, tip)
    zz = np.full(len(c), z) if rise is None else z + profile(u, rise)
    P = np.array([m.P(x, y, zv) for (x, y, _), zv in zip(c, zz)])
    N = np.array([m.N(x, y) for x, y, _ in c])
    T = np.maximum(W * thick, np.minimum(W, 0.32))
    if engrave and op == 0:
        Lc = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum()); ng = int(Lc / engrave)
        blade(s, P, W, T, normal=N, k=k, op=op, grooves=ng, both=True, gr=min(0.11, float(np.median(W)) * 0.09 + 0.03),
              barb=0.7, groove_span=(0.02, 0.98) if closed else (0.08, 0.92))
    else:
        blade(s, P, W, T, normal=N, k=k, op=op)
    if op == 0 and SHARP and mitre:
        _miters(s, m, pts, c, W, closed, z)
    return c[:, :2], W


SHARP = True


def _miters(s, m, pts, c, W, closed, z, min_turn=0.7):
    """Pull every sharp corner of a stroke's path out to a true point (a mitre), instead of
    the round outside a fat stroke would otherwise leave."""
    p = np.asarray(pts, float)[:, :2]
    if len(p) < 3: return
    idx = range(len(p)) if closed else range(1, len(p) - 1)
    for i in idx:
        a, b, q = p[i - 1], p[i], p[(i + 1) % len(p)]
        d0, d1 = b - a, q - b
        n0, n1 = np.linalg.norm(d0), np.linalg.norm(d1)
        if n0 < 1e-6 or n1 < 1e-6: continue
        d0, d1 = d0 / n0, d1 / n1
        turn = math.acos(np.clip(d0 @ d1, -1, 1))
        if turn < min_turn or turn > 2.9: continue
        out = d0 - d1; out /= max(np.linalg.norm(out), 1e-6)          # bisector toward the outside of the turn
        j = int(np.argmin(np.linalg.norm(c[:, :2] - b, axis=1)))
        w = float(W[min(j, len(W) - 1)])
        L = w / max(math.cos(turn / 2), 0.35) * 1.15
        spike(s, m, tuple(b), tuple(b + out * L), r0=w * 0.95, bend=0.0, z0=z, z1=z, k=0.2)


def lead(s, m, pts, r=0.42, z=0.05, closed=False, n=8, k=0.3):
    c = smooth(pts, n, closed) if len(pts) > 2 else np.column_stack([np.asarray(pts, float)[:, :2], np.zeros(2)])
    if closed: c = np.vstack([c, c[:1]])
    c = resample(c, 0.4)
    s.stroke(np.array([m.P(x, y, z) for x, y, _ in c]), np.full(len(c), r), k=k)
    return c[:, :2]


def spike(s, m, a, b, r0=0.7, bend=0.25, z0=0.0, z1=0.0, k=0.4, side=1, tip=None):
    """Curved flick from a (fat) to b (needle). bend = sideways bow as a fraction of length."""
    a = np.asarray(a, float); b = np.asarray(b, float); d = b - a; L = np.linalg.norm(d)
    nn = np.array([-d[1], d[0]]) / max(L, 1e-6)
    mid = (a + b) / 2 + nn * bend * L * side
    c = smooth([a, a + (mid - a) * 0.6 + nn * bend * L * 0.25 * side, mid, b], 8)
    c = resample(c, 0.2); u = arclen(c); u /= max(u[-1], 1e-6)
    tip = TIP if tip is None else tip
    W = tip + (r0 - tip) * (1 - u) ** 0.85
    zz = z0 + (z1 - z0) * u
    P = np.array([m.P(x, y, zv) for (x, y, _), zv in zip(c, zz)])
    N = np.array([m.N(x, y) for x, y, _ in c])
    blade(s, P, W, np.maximum(W * 0.8, np.minimum(W, 0.3)), normal=N, k=k)
    return c[:, :2]


def ball(s, m, p, r, z=None, k=0.25):
    s.sphere(m.P(p[0], p[1], r * 0.55 if z is None else z), r, k=k)


def bead(s, m, stones, p, d, kind, z=None, k=0.25):
    """A polished round gem bead seated in a little cup (the flash-sheet glass beads).
    Production rule: bead stones are stock rounds of 2 mm and under; anything bigger is claw-set."""
    d = float(np.clip(math.floor(d * 2 + 1e-6) / 2, 1.5, 10.0))
    if d > 2.0:
        import moira as _Mo
        return _Mo.prong(s, stones, m.P(p[0], p[1], d * 0.45 if z is None else z), d, kind, normal=m.N(*p), n=4)
    c = m.P(p[0], p[1], d * 0.32 if z is None else z); N = m.N(*p)
    s.torus(c - N * d * 0.22, d * 0.36, max(0.22, d * 0.1), normal=N, k=k)
    s.sphere(c - N * d * 0.32, d * 0.33, k=k)
    s.sphere(c, d * 0.5 + 0.02, op=1, k=0.02)
    stones.append(dict(kind=kind, bead=True, c=c.tolist(), n=N.tolist(), e1=m.T(*p)[0].tolist(), D=d, L=d))


def stalk(s, m, stones, a, b, d=1.2, kind=None, r=0.32, bend=0.0, z0=0.0, z1=0.4):
    a = np.asarray(a, float); b = np.asarray(b, float)
    dd = b - a; nn = np.array([-dd[1], dd[0]]) / max(np.linalg.norm(dd), 1e-6)
    mid = (a + b) / 2 + nn * bend * np.linalg.norm(dd)
    c = smooth([a, mid, b], 8); c = resample(c, 0.25)
    zz = np.linspace(z0, z1, len(c))
    s.stroke(np.array([m.P(x, y, z) for (x, y, _), z in zip(c, zz)]), np.linspace(r * 1.5, r, len(c)), k=0.35)
    if kind: bead(s, m, stones, b, d, kind, z=z1 + d * 0.3)
    else: ball(s, m, b, d / 2, z=z1)


# ---------------------------------------------------------------- glass
CALIB = {"marquise": [(4, 2), (5, 2.5), (6, 3), (7, 3.5), (8, 4)],
         "pear": [(4, 3), (5, 3), (6, 4), (7, 5)],
         "round": [(d, d) for d in (1.5, 2, 2.5, 3, 3.5, 4)]}


def calibrate(sizes):
    """Snap any requested stone to the nearest stock calibrated size (production plan, Nov 18)."""
    out = []
    for nm, L, W in sizes:
        c = CALIB.get(nm)
        if not c: out.append((nm, L, W)); continue
        Lc, Wc = min(c, key=lambda q: abs(q[0] - L) + abs(q[1] - W))
        if (nm, Lc, Wc) not in out: out.append((nm, Lc, Wc))
    out.sort(key=lambda z: -z[1] * z[2])
    return out


def glaze(s, m, stones, poly, kind, sizes=None, gap=0.55, margin=0.75, vein=0.32, blocked=(), seed=1,
          root=None, res=None, flow=0.0, cap=None):
    """Fill a closed 2D cell with calibrated stones, set flush and open-backed. kind is a
    stone name, a list (cycled by distance from root) or a callable (x, y) -> name."""
    poly = np.asarray(poly, float)[:, :2]
    ext = poly.max(0) - poly.min(0)
    res = res or float(np.clip(min(ext) / 90, 0.025, 0.07))
    root = np.asarray(root if root is not None else poly.mean(0), float)
    if sizes is None:
        sz = min(ext)
        base = [("marquise", 8, 4), ("pear", 7, 5), ("marquise", 6, 3), ("pear", 6, 4), ("pear", 5, 3),
                ("marquise", 5, 2.5), ("round", 4, 4), ("pear", 4, 3), ("marquise", 4, 2), ("round", 3, 3),
                ("round", 2.5, 2.5), ("round", 2, 2), ("round", 1.5, 1.5)]
        sizes = [z for z in base if z[2] <= sz * 0.62]
        if not sizes: sizes = [("round", 1.5, 1.5)]
    if cap: sizes = sizes[:cap] if isinstance(cap, int) else sizes
    sizes = calibrate(sizes)
    rng = np.random.default_rng(seed)
    placed = pack_stones(np.column_stack([poly, np.zeros(len(poly))]), root, rng, gap=gap, res=res, sizes=sizes,
                         tries="fit", margin=margin, flow_curl=flow, blocked=blocked)
    dmax = max(np.linalg.norm(poly - root, axis=1).max(), 1e-6)
    came(s, m, placed, poly, r=max(0.3, vein * 0.95), reach=max(2.6, gap * 5))
    for shape, L, W, c, ang in placed:
        if callable(kind): kd = kind(*c)
        elif isinstance(kind, (list, tuple)):
            kd = kind[min(len(kind) - 1, int(np.linalg.norm(np.asarray(c) - root) / dmax * len(kind)))]
        else: kd = kind
        tu, tv = m.T(*c)
        set_fancy(s, m.P(c[0], c[1], 0.0), 0.0, shape, L, W, kd, stones, vein=vein, normal=m.N(*c),
                  e1=tu * math.cos(ang) + tv * math.sin(ang))
    return placed


def _support(shape, L, W, ang, c, d):
    """Distance from the stone centre to its girdle along unit 2D direction d."""
    o = v2.caps_outline(v2.fancy_caps(shape, L, W), 48)
    ca, sa = math.cos(ang), math.sin(ang)
    o = np.stack([o[:, 0] * ca - o[:, 1] * sa, o[:, 0] * sa + o[:, 1] * ca], 1)
    return float(np.max(o @ d))


def came(s, m, placed, poly, r=0.35, reach=3.0, z=0.05):
    """Lead came: short bars joining neighbouring stones (Delaunay neighbours) and the
    outer stones to the frame, so every pane hangs in one connected lattice."""
    if not placed: return
    from scipy.spatial import Delaunay
    C = np.array([p[3] for p in placed])
    edges = set()
    if len(C) >= 3:
        try:
            tri = Delaunay(C)
            for sx in tri.simplices:
                for a, b in ((0, 1), (1, 2), (0, 2)):
                    edges.add(tuple(sorted((sx[a], sx[b]))))
        except Exception:
            pass
    if len(C) == 2: edges.add((0, 1))
    for i, j in edges:
        d = C[j] - C[i]; L = np.linalg.norm(d)
        if L < 1e-6: continue
        d /= L
        a = C[i] + d * _support(placed[i][0], placed[i][1], placed[i][2], placed[i][4], C[i], d)
        b = C[j] - d * _support(placed[j][0], placed[j][1], placed[j][2], placed[j][4], C[j], -d)
        g = np.linalg.norm(b - a)
        if 0.05 < g < reach and np.dot(b - a, d) > 0:
            nn = np.array([-d[1], d[0]]) * g * 0.12 * (1 if (i + j) % 2 else -1)
            mid = (a + b) / 2 + nn
            s.stroke(np.array([m.P(*(a - d * 0.2), z), m.P(*mid, z + 0.12), m.P(*(b + d * 0.2), z)]), np.array([max(r * 1.25, 0.42), max(r * 0.8, 0.4), max(r * 1.1, 0.42)]), k=0.15)
    P = resample(np.column_stack([poly, np.zeros(len(poly))]), 0.3)[:, :2]
    for i, c in enumerate(C):
        dd = np.linalg.norm(P - c, axis=1); j = np.argmin(dd)
        d = (P[j] - c) / max(dd[j], 1e-6)
        a = c + d * _support(placed[i][0], placed[i][1], placed[i][2], placed[i][4], c, d)
        if np.linalg.norm(P[j] - a) < reach * 1.3:
            s.stroke(np.array([m.P(*(a - d * 0.2), z), m.P(*(P[j] + d * 0.3), z)]), np.array([r, r]), k=0.15)


def pane(s, m, stones, p, shape, L, W, kind, ang=0.0, vein=0.38):
    tu, tv = m.T(*p)
    set_fancy(s, m.P(p[0], p[1], 0.0), 0.0, shape, L, W, kind, stones, vein=vein, normal=m.N(*p),
              e1=tu * math.cos(ang) + tv * math.sin(ang))


def thorns(s, m, stones, p, D, kind, L=None, n=5, lift=None, wire=0.42, spin=0.3, seed=0, reach=(0.7, 1.5),
           basket=True, k=0.35):
    """A faceted stone (round or oval) caught in n uneven thorns that curl over the crown."""
    L = L or D; rng = np.random.default_rng(seed)
    lift = D * 0.55 if lift is None else lift
    N = m.N(*p); tu, tv = m.T(*p)
    c = m.P(p[0], p[1], lift)
    e1 = tu * math.cos(spin) + tv * math.sin(spin); e2 = np.cross(N, e1)
    rx, ry = L / 2, D / 2
    for i in range(n):
        t = 2 * math.pi * (i + rng.uniform(-0.18, 0.18)) / n
        d = e1 * math.cos(t) * rx + e2 * math.sin(t) * ry; dn = nrm(d)
        ex = rng.uniform(*reach)
        p0 = c - N * 0.55 * D + d * 0.35
        p1 = c - N * 0.1 * D + d * 1.02 + dn * wire * 0.7
        p2 = c + N * 0.14 * D + d * 0.95
        p3 = c + N * (0.2 + 0.25 * ex) * D + d * (0.95 - 0.25 * ex) + nrm(np.cross(N, dn)) * 0.25 * D * (1 if i % 2 else -1)
        if ex > 1.1:                 # long thorns flick outward past the stone
            p3 = c + N * 0.35 * D + d * (1.0 + 0.45 * ex) + nrm(np.cross(N, dn)) * 0.3 * D
        cv = catmull([p0, p1, p2, p3], 6)
        s.stroke(cv, profile(np.linspace(0, 1, len(cv)), [(0, wire * 1.3), (0.55, wire), (1, TIP * 0.7)]), k=k)
    if basket:
        ring = [c - N * 0.3 * D + e1 * math.cos(t) * rx * 0.8 + e2 * math.sin(t) * ry * 0.8 for t in np.linspace(0, 2 * math.pi, 33)]
        s.stroke(ring, np.full(33, wire * 0.7), k=0.25)
    s.cone(c - N * 0.43 * D, c + N * 0.001, 0.05, 0.5 * D, op=1, k=0.05, flat=max(1, L / D) if L > D else 1,
           zhint=e2 if L > D else N)
    stones.append(dict(kind=kind, c=c.tolist(), n=N.tolist(), e1=e1.tolist(), D=D, L=L))
    return c


# ---------------------------------------------------------------- composite motifs
def curl(s, m, stones, cx, cy, R, a0=0.0, turns=1.15, w=1.0, kind=None, cw=1, tail=None, pen=0.75):
    """A calligraphic curl whose closed counter is glazed with one stone."""
    sp = spiral(cx, cy, R * 0.55, R, a0, turns * cw, 36)[::-1] if cw > 0 else spiral(cx, cy, R * 0.55, R, a0, -turns, 36)[::-1]
    pts = np.vstack([sp, tail]) if tail is not None else sp
    nib(s, m, pts, w=w, pen=pen, taper=(0.06, 0.2))
    if kind:
        d = R * 0.85
        size = max([z for z in (1.5, 2, 2.5, 3, 3.5, 4, 5) if z <= d] or [1.5])
        pane(s, m, stones, (cx, cy), "round", size, size, kind, vein=0.3)


def lancet(s, m, stones, x0, y0, a, h, lights=2, kind="amethyst", w=0.9, finial=True, seed=3, sizes=None):
    o = lancet_outline(a, h) + [x0, y0]
    nib(s, m, o, w=w, pen=0.2, hair=0.45, taper=(0.05, 0.05))
    nib(s, m, [(x0 - a * 1.05, y0), (x0 + a * 1.05, y0)], w=w * 0.9, hair=0.6, taper=(0.1, 0.1))
    cells = []
    if lights <= 1:
        cells.append(o)
    else:
        xs = np.linspace(x0 - a, x0 + a, lights + 1)
        for i in range(1, lights):
            top = y0 + h * (1 - abs(xs[i] - x0) / a * 0.35) - 0.5
            nib(s, m, [(xs[i], y0), (xs[i], top)], w=w * 0.55, pen=0.0, hair=0.5, taper=(0.0, 0.3))
        for i in range(lights):
            hw = (xs[i + 1] - xs[i]) / 2 - 0.15
            cx_ = (xs[i] + xs[i + 1]) / 2
            hh = h * (1 - (abs(cx_ - x0) + hw) / a * 0.3) - 0.8
            cells.append(lancet_outline(hw, hh, R=2.2 * hw) + [cx_, y0])
    for i, c in enumerate(cells):
        kd = kind[i % len(kind)] if isinstance(kind, (list, tuple)) else kind
        glaze(s, m, stones, c, kd, seed=seed + i, sizes=sizes, margin=0.55)
    if finial:
        top = (x0, y0 + h)
        spike(s, m, top, (x0, y0 + h + a * 0.9), r0=w * 0.8)
        for sx in (1, -1):
            spike(s, m, (x0 + sx * a * 0.25, y0 + h * 0.85), (x0 + sx * a * 1.1, y0 + h * 1.02), r0=w * 0.55, bend=0.3, side=sx)
    return o


def rose(s, m, stones, cx, cy, R, n=6, kinds=("aquamarine", "topaz"), center="round", flicks=True, w=0.8, seed=5):
    nib(s, m, arc(cx, cy, R, 0, 2 * math.pi, 64), w=w, pen=0.3, hair=0.55, closed=True, taper=(0, 0))
    rc = R * 0.33
    nib(s, m, arc(cx, cy, rc, 0, 2 * math.pi, 40), w=w * 0.7, hair=0.6, closed=True, taper=(0, 0))
    cz = [z for z in (1.5, 2, 2.5, 3, 3.5, 4, 5) if z <= rc * 1.55]
    if cz: pane(s, m, stones, (cx, cy), "round", cz[-1], cz[-1], kinds[0], vein=0.3)
    for i in range(n):
        a = 2 * math.pi * i / n + math.pi / 2
        b0 = a - math.pi / n
        # tracery spoke with a heart notch where it meets the rim
        p0 = (cx + rc * math.cos(b0), cy + rc * math.sin(b0)); p1 = (cx + R * math.cos(b0), cy + R * math.sin(b0))
        lead(s, m, [p0, p1], r=w * 0.45)
        Lp = (R - rc) * 0.78; Wp = min(Lp * 0.66, 2 * (rc + Lp / 2) * math.sin(math.pi / n) * 0.8)
        pc = (cx + (rc + (R - rc) * 0.5) * math.cos(a), cy + (rc + (R - rc) * 0.5) * math.sin(a))
        kd = kinds[(i + 1) % len(kinds)]
        if Lp >= 2.6: pane(s, m, stones, pc, "pear", round(Lp * 2) / 2, round(Wp * 2) / 2, kd, ang=a + math.pi, vein=max(0.25, w * 0.4))
        else: pane(s, m, stones, pc, "round", max(1.0, round(min(Lp, Wp * 1.3) * 2) / 2), max(1.0, round(min(Lp, Wp * 1.3) * 2) / 2), kd, vein=0.22)
        if flicks:
            q = (cx + R * math.cos(b0), cy + R * math.sin(b0))
            spike(s, m, q, (cx + R * 1.38 * math.cos(b0), cy + R * 1.38 * math.sin(b0)), r0=w * 0.7, bend=0.22)


def fleur(s, m, stones, cx, cy, size, kinds=("garnet",), ang=0.0, glaze_arms=(0, 1, 2, 3), w=0.75, centre="moonstone"):
    """Fleur cross: four lobed arms, each a glazed teardrop cell with two curled side horns."""
    for i in range(4):
        a = ang + i * math.pi / 2
        d = np.array([math.cos(a), math.sin(a)]); q = np.array([-d[1], d[0]])
        c = np.array([cx, cy])
        tip = c + d * size; base = c + d * size * 0.22
        cell = np.array([base + q * size * 0.12, c + d * size * 0.55 + q * size * 0.2, c + d * size * 0.78 + q * size * 0.13,
                         tip, c + d * size * 0.78 - q * size * 0.13, c + d * size * 0.55 - q * size * 0.2, base - q * size * 0.12])
        o = smooth(cell, 6, closed=True)[:, :2]
        nib(s, m, o, w=w, pen=a, hair=0.4, closed=True, taper=(0, 0))
        if i in glaze_arms:
            Lm = size * 0.5; Wm = Lm / 2
            pc = c + d * size * 0.55
            if Lm >= 3: pane(s, m, stones, tuple(pc), "marquise", round(Lm * 2) / 2, round(Wm * 4) / 4, kinds[i % len(kinds)], ang=a, vein=max(0.22, w * 0.45))
            else: pane(s, m, stones, tuple(pc), "round", 1.5, 1.5, kinds[i % len(kinds)], vein=0.22)
        for sd in (1, -1):
            st = c + d * size * 0.6 + q * size * 0.18 * sd
            curlp = [st, st + q * size * 0.25 * sd + d * size * 0.05, st + q * size * 0.32 * sd - d * size * 0.12,
                     st + q * size * 0.2 * sd - d * size * 0.15]
            nib(s, m, curlp, w=w * 0.7, pen=a, taper=(0.1, 0.5))
    if centre:
        bead(s, m, stones, (cx, cy), max(1.5, size * 0.3), centre)


def wing(s, m, stones, outline=WING, sx=1.0, sy=1.0, rot=0.0, t=(0, 0), mirror=False, pal=PAL["ember"],
         sizes=None, veins=True, costa=1.2, thorn_tips=True, seed=7, open_cells=0.0, vein_w=0.5):
    """The stained-glass wing: swelling costa, veins as hairline leads, panes packed in the
    cells and graded in colour from the root; vein ends break the margin as thorn tips."""
    o = xform(smooth(outline, 10, closed=True), sx, sy, rot, t, mirror)
    root = xform([[-1.5, -0.5]], sx, sy, rot, t, mirror)[0]
    nib(s, m, o, w=costa, pen=rot + (math.pi if mirror else 0) + 0.4, hair=0.35, closed=True, taper=(0, 0))
    blocked = []
    sc_ = max(abs(sx), abs(sy))
    if veins:
        sc = sc_
        ext = np.array(outline, float); far = ext[np.argmax(ext[:, 0])]
        ends = [p for p in ext[1:] if np.hypot(*p) > 0.45 * np.hypot(*far)]
        for j, e in enumerate(ends[::2]):
            v = xform([[0.5, -0.2], [e[0] * 0.5, e[1] * 0.5 + 0.06 * e[0]], list(e)], sx, sy, rot, t, mirror)
            c, _ = nib(s, m, v, w=vein_w * sc ** 0.3, pen=0.0, hair=0.7, taper=(0.0, 0.15))
            blocked.append((c, vein_w * 1.6 * sc ** 0.3))
            if thorn_tips:
                d = nrm(np.append(v[-1] - v[-2], 0))[:2]
                spike(s, m, v[-1], v[-1] + d * 2.2 * sc ** 0.6, r0=vein_w * 1.2 * sc ** 0.3, bend=0.18)
    kindf = (lambda x, y: pal[min(len(pal) - 1, int(np.hypot(x - root[0], y - root[1]) /
                                                    (np.linalg.norm(o - root, axis=1).max() + 1e-6) * len(pal)))])
    glaze(s, m, stones, o, kindf, sizes=sizes, seed=seed, root=root, blocked=blocked, margin=float(np.clip(0.9 * sc_, 0.28, 0.9)), gap=float(np.clip(0.55 * sc_ ** 0.5, 0.35, 0.55)))
    return o, root


def spine(s, m, stones, path, n=5, size=3.0, kind="aquamarine", grade=(1.0, 0.6), w=0.75, seed=0, beads=True):
    """Glass vertebrae: along a path, mirrored hooked blades around a stone in each joint."""
    c = resample(smooth(path, 10), 0.2)[:, :2]
    nib(s, m, c, w=w * 0.8, pen=0.0, hair=0.7, taper=(0.05, 0.12))
    u = arclen(np.column_stack([c, np.zeros(len(c))])); u /= u[-1]
    tg = tangents(np.column_stack([c, np.zeros(len(c))]))[:, :2]
    for i in range(n):
        f = (i + 0.5) / n; j = int(np.searchsorted(u, f)); j = min(j, len(c) - 1)
        p = c[j]; d = tg[j]; q = np.array([-d[1], d[0]])
        g = grade[0] + (grade[1] - grade[0]) * f; S = size * g
        for sd in (1, -1):
            a = p + q * S * 0.35 * sd
            nib(s, m, [a, a + q * S * 0.9 * sd + d * S * 0.15, a + q * S * 1.25 * sd - d * S * 0.35,
                       a + q * S * 1.05 * sd - d * S * 0.8], w=w * g, pen=0.6 * sd, taper=(0.05, 0.45))
        dd = [z for z in (1.5, 2, 2.5, 3, 3.5, 4) if z <= S * 0.75]
        if beads: bead(s, m, stones, p, dd[-1] if dd else 1.5, kind[i % len(kind)] if isinstance(kind, (list, tuple)) else kind)
        else: pane(s, m, stones, p, "round", dd[-1] if dd else 1.5, dd[-1] if dd else 1.5,
                   kind[i % len(kind)] if isinstance(kind, (list, tuple)) else kind)


# ---------------------------------------------------------------- mounts
def stud_post(s, m, p, L=10.0, r=0.5):
    a = m.P(p[0], p[1], -0.2); s.cone(a, a - m.N(*p) * L, r * 1.6, r, k=0.4)


def pin(s, m, p, L=3.0):
    """Threaded titanium labret pin under a top (1.2 mm post's 0.8 mm pin)."""
    a = m.P(p[0], p[1], -0.2); s.cone(a, a - m.N(*p) * L, 0.55, 0.4, k=0.3)


def ear_wire(s, m, p, h=13.0, back=7.0):
    a = m.P(p[0], p[1], 0.0); N = m.N(*p); _, v = m.T(*p)
    pts = catmull([a, a + v * 2.5, a + v * h * 0.8 - N * 1.0, a + v * h - N * back * 0.35,
                   a + v * h * 0.75 - N * back * 0.8, a + v * h * 0.15 - N * back], 8)
    # liquid wire: swells off the jump ring and draws down toward the tip (never under 0.8 mm for casting)
    u = np.linspace(0, 1, len(pts))
    s.stroke(pts, 0.4 + 0.14 * np.sin(math.pi * np.clip(u / 0.6, 0, 1)) ** 1.5 * (1 - u), k=0.3)


def jump(s, m, p, R=1.4, r=0.42, axis=None):
    c = m.P(p[0], p[1], 0.0); s.torus(c, R, r, normal=m.T(*p)[0] if axis is None else axis, k=0.25)


def bail(s, m, p, R=2.0, r=0.6):
    c = m.P(p[0], p[1], 0.0); s.torus(c, R, r, normal=m.T(*p)[0], k=0.4)


def buckle_back(s, m, w, h):
    """Belt hook stud and a keeper bar behind the plate."""
    a = m.P(-w * 0.28, 0, -0.4); N = m.N(0, 0)
    s.cone(a, a - N * 4.0, 1.4, 1.0, k=0.6); s.sphere(a - N * 4.2, 1.9, k=0.4)
    for sy in (1, -1):
        s.cone(m.P(w * 0.32, sy * h * 0.36, -0.3), m.P(w * 0.32, sy * h * 0.36, -0.3) - N * 3.5, 1.1, 1.0, k=0.5)
    s.cone(m.P(w * 0.32, h * 0.36, -0.3) - N * 3.5, m.P(w * 0.32, -h * 0.36, -0.3) - N * 3.5, 1.0, 1.0, k=0.5)


def shank(s, size=7, top_w=2.2):
    """Ring shank (US size ~7) fine under the finger, swelling at the shoulders."""
    R0 = (14.0 + 0.8128 * size) / 2
    tl, tr, Rb = ring_band(s, R0=R0, w1=top_w, fork=1.0)
    return Rb, R0
