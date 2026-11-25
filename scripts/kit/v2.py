"""v2: sculptural pieces built with sdf.py (liquid fused forms, engraved blades,
faceted stones in claw settings). Run with the bpy venv:
    python v2.py <piece> [preview|final]      -> out2/<piece>.stl, out2/<piece>_white*.png
"""
import sys, os, math, json
import numpy as np
import sdf
from sdf import Scene, bezier, catmull, resample, arclen, profile, tangents

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out2"); os.makedirs(OUT, exist_ok=True)
TIP = 0.12            # tip radius: 0.24 mm across; true needle points, finished by hand after casting


def nrm(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)


# ---------------------------------------------------------------- motifs
def blade(s, pts, half_w, half_t, normal=(0, 0, 1), k=0.6, grooves=0, groove_side=1, gr=0.13,
          barb=0.55, groove_span=(0.18, 0.86), both=False, op=0):
    """A sculpted leaf/feather/horn blade along a curve: elliptical section, half width
    `half_w(u)` and half thickness `half_t(u)` (callables or arrays). Optional engraved
    barbs: `grooves` fine cuts angled back from the midrib toward the edge, like a hand
    engraved feather."""
    pts0 = np.asarray(pts, float); u0 = arclen(pts0)
    pts = resample(pts0, 0.2); u = arclen(pts)
    re = lambda a: np.stack([np.interp(u, u0, a[:, j]) for j in range(a.shape[1])], 1) if a.ndim == 2 else np.interp(u, u0, a)
    W = half_w(u) if callable(half_w) else re(np.asarray(half_w, float))
    T = half_t(u) if callable(half_t) else re(np.asarray(half_t, float))
    N = np.asarray(normal, float)
    Ns = np.tile(N, (len(pts), 1)) if N.ndim == 1 else re(N)
    for i in range(len(pts) - 1):
        r1, r2 = W[i], W[i + 1]
        fl = max(1.0, 0.5 * (r1 / T[i] + r2 / T[i + 1]))
        s.cone(pts[i], pts[i + 1], r1, r2, op=op, k=(k if i == 0 else 0.0), flat=fl,
               zhint=(Ns[i] + Ns[i + 1]) / 2)
    if grooves:
        tg = tangents(pts)
        us = np.linspace(groove_span[0], groove_span[1], grooves)
        sides = (1, -1) if both else (groove_side,)
        for uu in us:
            i = int(np.searchsorted(u, uu)); i = min(i, len(pts) - 2)
            m, t, n = pts[i], tg[i], nrm(Ns[i]); b = np.cross(n, t)
            w, th = W[i], T[i]
            for sd in sides:
                line = []
                for q in np.linspace(0.12, 0.98, 6):
                    sx = q * w
                    h = th * math.sqrt(max(0.0, 1 - (sx / w) ** 2))
                    p = m + b * sd * sx - t * barb * q * w + n * h
                    line.append(p)
                s.stroke(np.array(line), np.full(6, gr), op=1, k=0.08)
    return pts


def stem_ball(s, a, b, r_stem, r_ball, k=0.5):
    """A fine stalk ending in a polished sphere (the flash-sheet bead accents)."""
    s.cone(a, b, r_stem * 1.6, r_stem, k=k)
    s.sphere(b, r_ball, k=0.25)


def claws(s, c, D, L=None, normal=(0, 0, 1), spin=0.0, n=4, wire=0.42, k=0.35, gallery=True):
    """Claw (prong) setting for a faceted stone: girdle at c, table along normal.
    Returns the stone record for rendering; also cuts the stone's seat."""
    L = L or D
    N = nrm(normal)
    a1 = nrm(np.cross(N, [0, 1, 0]) if abs(N[1]) < .9 else np.cross(N, [1, 0, 0]))
    a2 = np.cross(N, a1)
    ca, sa = math.cos(spin), math.sin(spin)
    e1, e2 = a1 * ca + a2 * sa, -a1 * sa + a2 * ca
    rx, ry = L / 2, D / 2
    c = np.asarray(c, float)
    angs = np.arange(n) * 2 * math.pi / n + (math.pi / n if n == 4 else 0)
    for t in angs:
        d = e1 * math.cos(t) * rx + e2 * math.sin(t) * ry
        dn = nrm(d)
        p0 = c - N * 0.55 * D + d * 0.45
        p1 = c - N * 0.12 * D + d * 1.0 + dn * wire * 0.8
        p2 = c + N * 0.10 * D + d * 1.0 + dn * wire * 0.55
        p3 = c + N * 0.16 * D + d * 0.86
        s.stroke(catmull([p0, p1, p2, p3], 6), profile(np.linspace(0, 1, 19), [(0, wire * 1.25), (0.6, wire), (1, wire * 0.8)]),
                 k=k)
    if gallery:
        for z, f, r in ((-0.30, 0.78, wire * 0.75), (-0.08, 1.02, wire * 0.6)):
            ring = [c + N * z * D + e1 * math.cos(t) * rx * f + e2 * math.sin(t) * ry * f for t in np.linspace(0, 2 * math.pi, 33)]
            s.stroke(ring, np.full(33, r), k=0.25)
    # seat: cut the stone's own volume out of everything so it drops in
    s.cone(c - N * 0.43 * D, c + N * 0.001, 0.05, 0.5 * D * 1.0, op=1, k=0.05, flat=max(1, L / D) if L > D else 1,
           zhint=e2 if L > D else N)
    return dict(c=c.tolist(), n=N.tolist(), e1=e1.tolist(), D=D, L=L)


def eye(s, c, normal, R=1.25, r=0.55, k=0.3):
    s.torus(c, R, r, normal=normal, k=k)


# ---------------------------------------------------------------- pieces
def ring_band(s, R0=17.35 / 2, fork=0.66, w0=1.15, t0=0.85, w1=2.2, t1=1.45):
    """Shank: fine under the finger, swelling up both sides. Returns the two top ends."""
    Rb = R0 + t0
    th = np.linspace(-math.pi * fork, math.pi * fork, 61)
    band = np.stack([Rb * np.sin(th), np.zeros_like(th), -Rb * np.cos(th)], 1)
    u = np.abs(th) / (math.pi * fork)
    w = profile(u, [(0, w0), (0.45, w0 * 1.1), (1, w1)])
    t = profile(u, [(0, t0), (0.45, t0 * 1.05), (1, t1)])
    radial = np.stack([np.sin(th), np.zeros_like(th), -np.cos(th)], 1)
    # keep the inside true: the band grows outward only
    band = band + radial * (t - t0)[:, None]
    blade(s, band, w, t, normal=radial, k=0)
    return band[-1], band[0], Rb


def mirror_x(fn):
    for sx in (1, -1):
        fn(sx)


def horn_ring():
    """Reliquary ring: the shank forks into four poured strands that lift a cushion
    collet. A 6 mm garnet sits in four claws; two engraved horns curl up and hook in
    over it, and two heart blades fold down the sides of the finger, each pierced."""
    s = Scene(); stones = []
    tl, tr, Rb = ring_band(s)
    zc = Rb + 2.9                                # cushion height
    def strands(sx):
        top = tl if sx > 0 else tr
        for sy in (1, -1):
            s.stroke(catmull([top - [0, 0, 0.4], top + [-0.6 * sx, sy * 1.3, 1.6], [3.2 * sx, sy * 2.3, zc - 0.4]], 8),
                     profile(np.linspace(0, 1, 17), [(0, 1.5), (0.5, 0.95), (1, 1.05)]), k=0.9)
    mirror_x(strands)
    # cushion collet around the stone
    s.torus((0, 0, zc), 3.7, 1.05, normal=(0, 0, 1), k=0.8)
    s.ellipsoid((0, 0, zc - 0.9), (3.4, 3.4, 1.6), k=0.9)
    stones.append(dict(kind="garnet", **claws(s, (0, 0, zc + 1.9), 6.0, normal=(0, 0, 1), spin=math.pi / 4, wire=0.45)))
    def horn(sx):
        h = bezier([[3.9 * sx, 0.2, zc + 0.4], [7.6 * sx, 0.6, zc + 1.0], [9.6 * sx, 1.0, zc + 6.5],
                    [7.4 * sx, 0.4, zc + 9.6], [6.4 * sx, 0.2, zc + 11.0], [4.6 * sx, -0.6, zc + 10.6], [3.6 * sx, -1.2, zc + 8.6]], 30)
        blade(s, h, lambda u: profile(u, [(0, 1.7), (0.3, 1.9), (0.7, 1.0), (1, TIP)]),
              lambda u: profile(u, [(0, 1.4), (0.35, 1.0), (0.75, 0.6), (1, TIP)]),
              normal=(0, 1, 0), k=1.0, grooves=16, groove_span=(0.12, 0.78), groove_side=-1 if sx > 0 else 1, barb=0.8)
        stem_ball(s, [8.9 * sx, 0.8, zc + 4.2], [11.6 * sx, 1.2, zc + 6.0], 0.38, 0.85)
    mirror_x(horn)
    def heart(sx):
        hb = bezier([[3.3 * sx, -1.8, zc - 0.6], [6.4 * sx, -3.6, zc - 1.2], [9.4 * sx, -3.4, zc - 4.6], [8.6 * sx, -1.6, zc - 9.0]], 36)
        blade(s, hb, lambda u: profile(u, [(0, 1.4), (0.38, 2.7), (0.7, 2.0), (1, TIP)]),
              lambda u: profile(u, [(0, 1.2), (0.4, 0.95), (1, TIP)]),
              normal=(0.75 * sx, -0.6, 0.25), k=0.9, grooves=11, groove_span=(0.2, 0.8), both=True, barb=0.55)
        c = hb[int(len(hb) * 0.36)]
        s.ellipsoid(c, (1.4, 0.55, 2.2), xaxis=(0.3 * sx, -0.2, 1), zhint=(0.75 * sx, -0.6, 0.25), op=1, k=0.35)
    mirror_x(heart)
    # a short spine behind the stone
    s.stroke(catmull([[0, 2.6, zc + 0.2], [0, 3.6, zc + 3.0], [0, 3.2, zc + 6.5]], 8),
             profile(np.linspace(0, 1, 17), [(0, 1.2), (0.4, 0.9), (1, TIP)]), k=0.8)
    s.cone((0, -14, 0), (0, 14, 0), 17.35 / 2, 17.35 / 2, op=1, k=0.0)
    cam = dict(view=(0.35, -1.0, 0.38), lens=100, margin=1.12)
    return s, stones, cam


def wing_ring():
    """Wing ring: nine hand-carved feathers wrap the finger in layers like a folded wing,
    longest at the back; an 8x6 oval aquamarine sits in four claws at the root."""
    s = Scene(); stones = []
    R = 17.35 / 2
    # hidden band under the wing
    th = np.linspace(0, 2 * math.pi, 73)
    band = np.stack([(R + 0.8) * np.sin(th), np.zeros_like(th) + 1.0, (R + 0.8) * np.cos(th)], 1)
    blade(s, band, np.full(73, 1.5), np.full(73, 0.85), normal=np.stack([np.sin(th), 0 * th, np.cos(th)], 1), k=0)
    # fan of feathers from one root, shingled: first ones lie lowest
    root_phi, root_y = math.radians(-52), -2.6
    fan = [  # (angle from the circumference toward +y deg, length, width, seed, base y)
        (2, 19, 2.8, 11, -4.6), (8, 25, 3.1, 12, -3.4), (13, 31, 3.4, 13, -2.2), (18, 35, 3.6, 14, -1.0),
        (23, 36, 3.6, 15, 0.2), (28, 33, 3.4, 16, 1.4), (33, 28, 3.2, 17, 2.6), (38, 22, 2.9, 18, 3.6),
        (43, 16, 2.6, 19, 4.4)]
    for j, (al, Lf, Wf, seed, by) in enumerate(fan):
        a_ = math.radians(al)
        rr = R + 1.15 + 0.3 * j
        f = root_phi - 0.02 * j
        base = np.array([rr * math.sin(f), by, rr * math.cos(f)])
        nrm_ = np.array([math.sin(f), 0, math.cos(f)])
        circ = np.array([math.cos(f), 0, -math.sin(f)])
        d = circ * math.cos(a_) + np.array([0, 1, 0]) * math.sin(a_)
        s.feather(base, d, nrm_, Lf, Wf, T=0.48, skew=0.72, pitch=0.46, depth=0.18, slope=1.15,
                  bend=-0.008, wrap=-math.cos(a_) ** 2 / (rr + 0.2), seed=seed, notches=3, quill=0.12, k=0.3)
    # root knot: a poured mound where the quills gather, carrying the stone
    f = root_phi
    n = np.array([math.sin(f), 0, math.cos(f)])
    c = np.array([(R + 5.4) * math.sin(f), root_y + 1.0, (R + 5.4) * math.cos(f)])
    s.ellipsoid(c - n * 3.0, (4.2, 3.6, 2.4), xaxis=(0, 1, 0), zhint=n, k=1.2)
    stones.append(dict(kind="aquamarine", **claws(s, c, 6.0, L=8.0, normal=n, spin=math.pi / 2, wire=0.48)))
    # two small covert feathers sweeping back over the root
    for sd, (al, Lf, sdd) in enumerate([(200, 11, 21), (215, 9, 22)]):
        a_ = math.radians(al)
        circ = np.array([math.cos(f), 0, -math.sin(f)])
        d = circ * math.cos(a_) + np.array([0, 1, 0]) * math.sin(a_)
        rr = R + 2.4 + 0.5 * sd
        base = np.array([rr * math.sin(f), root_y + 0.5, rr * math.cos(f)]) - circ * 0.5
        s.feather(base, d, n, Lf, 2.2, T=0.45, pitch=0.42, depth=0.16, wrap=-math.cos(a_) ** 2 / rr, seed=sdd,
                  notches=1, quill=0.15, k=0.3)
    s.cone((0, -16, 0), (0, 16, 0), R, R, op=1, k=0.0)
    cam = dict(view=(-0.55, -0.8, 0.55), lens=100, margin=1.1)
    return s, stones, cam


def heart_pendant():
    """Moth heart: a thick spikey heart outline with scroll curls in its lobes; a moth
    sits inside, its thorax an 8x6 garnet in claws, four carved feather wings reaching
    out to the frame, a beaded abdomen dropping into the heart's dagger point."""
    s = Scene(); stones = []
    H = [(0, 8.6), (3.6, 13.6), (8.8, 15.2), (13.0, 11.6), (13.0, 4.4), (9.6, -3.4), (4.6, -9.4), (0, -15.0)]
    right = np.array([[x, y, 0] for x, y in H]); left = right[::-1][1:-1] * [-1, 1, 1]
    loop = catmull(np.vstack([right, left]), 10, closed=True)
    yv = loop[:, 1]
    rad = np.interp(yv, [-15, -8, 0, 10, 16], [0.95, 1.15, 1.45, 1.6, 1.5])
    blade(s, np.vstack([loop, loop[:1]]), np.append(rad, rad[0]), np.append(rad, rad[0]) / 1.35, normal=(0, 0, 1), k=0)
    s.stroke([[0, -14.6, 0], [0, -18.0, 0], [0, -21.5, 0]], [1.1, 0.7, TIP], k=0.6)
    def side(sx):
        # scroll curl in the lobe, ending in a bead
        cur = catmull([[3.0 * sx, 12.6, 0.3], [5.6 * sx, 11.0, 0.5], [4.8 * sx, 7.8, 0.5], [2.8 * sx, 8.4, 0.5], [3.3 * sx, 10.0, 0.5]], 8)
        s.stroke(cur, profile(np.linspace(0, 1, len(cur)), [(0, 1.05), (0.6, 0.75), (1, 0.6)]), k=0.6)
        s.sphere(cur[-1], 0.85, k=0.3)
        # thorns round the outside of the lobe and down the side
        tg = tangents(loop)
        for yy, ln, back in ((14.9, 3.6, 0.5), (13.4, 4.4, 0.7), (8.0, 4.6, 0.8), (1.0, 4.2, 0.9), (-5.5, 3.6, 0.9), (-11.0, 2.8, 1.0)):
            cand = np.where((loop[:, 0] * sx > 0.5))[0]
            i = cand[np.argmin(np.abs(loop[cand, 1] - yy) + (0 if yy < 14 else 0) + np.where(loop[cand, 1] > 13.8, 0, 0))]
            if yy > 14: i = cand[np.argmin(np.abs(loop[cand, 0] - 7.5 * sx) + np.abs(loop[cand, 1] - 15.0))]
            p = loop[i]; t = tg[i]; n = np.array([t[1], -t[0], 0])
            if np.dot(n, p - [0, 2, 0]) < 0: n = -n
            dn = -np.sign(p[1] - 2.0) if abs(p[1] - 2) > 3 else -1
            down = np.array([0, -1, 0.0])
            q = catmull([p, p + n * ln * 0.45 + down * back * 0.3, p + n * ln + down * back * 1.4], 6)
            s.stroke(q, profile(np.linspace(0, 1, len(q)), [(0, 1.0), (0.5, 0.6), (1, TIP)]), k=0.55)
        # wings: carved feathers reaching from the thorax to the frame
        s.feather([1.6 * sx, 3.6, 0.2], [0.86 * sx, 0.6, 0.05], (0, 0, 1), 13.2, 2.8, T=0.5, skew=0.85, pitch=0.42,
                  depth=0.16, bend=0.02 * sx, seed=31 + sx, notches=2, quill=0.1, k=0.5)
        s.feather([1.6 * sx, 0.6, 0.2], [0.78 * sx, -0.62, 0.05], (0, 0, 1), 11.4, 2.4, T=0.48, skew=0.85, pitch=0.4,
                  depth=0.15, bend=-0.03 * sx, seed=41 + sx, notches=2, quill=0.1, k=0.5)
        # antennae curling up into the cleft
        an = catmull([[0.8 * sx, 5.8, 1.2], [1.6 * sx, 7.6, 1.0], [1.2 * sx, 8.6, 0.6], [0.4 * sx, 8.7, 0.3]], 6)
        s.stroke(an, np.linspace(0.55, 0.5, len(an)), k=0.4)
    mirror_x(side)
    # thorax / abdomen
    s.ellipsoid([0, 2.2, -0.2], (3.0, 4.6, 1.6), xaxis=(0, 1, 0), k=0.8)
    for y, r in ((-3.4, 1.45), (-5.7, 1.3), (-7.9, 1.12), (-9.9, 0.95), (-11.7, 0.8), (-13.3, 0.7)):
        s.sphere([0, y, 0.15], r, k=0.45)
    stones.append(dict(kind="garnet", **claws(s, (0, 2.2, 1.7), 6.0, L=8.0, normal=(0, 0, 1), spin=math.pi / 2, wire=0.45)))
    # bail
    s.torus([0, 12.4, 0], 1.9, 0.75, normal=(1, 0, 0), k=0.4)
    cam = dict(view=(0.0, -0.55, 1.0), lens=100, margin=1.1)
    return s, stones, cam


def _rot(p, c, a):
    p = np.asarray(p, float); ca, sa = math.cos(a), math.sin(a)
    return np.stack([c[0] + p[..., 0] * ca - p[..., 1] * sa, c[1] + p[..., 0] * sa + p[..., 1] * ca, c[2] + p[..., 2]], -1)


def petal_link(s, c=(0, 0, 0), a=0.0, D=5.0, stones=None, kind="aquamarine"):
    """Signature four-petal tracery flower as a bracelet link: open petals with a heart
    notch at each tip, carved spiky leaves between them, a faceted stone in claws at the
    heart, jump-ring eyes at the two side petals."""
    c = np.asarray(c, float)
    half = [(1.9, 0.0), (2.0, 1.2), (3.4, 3.0), (5.6, 3.7), (7.6, 2.9), (8.5, 1.4), (7.9, 0.45), (7.1, 0.0)]
    pet = np.array([[x, y, 0] for x, y in half] + [[x, -y, 0] for x, y in half[::-1][1:-1]])
    for k in range(4):
        ang = a + k * math.pi / 2
        loop = catmull(pet, 8, closed=True)
        lp = _rot(loop, c, ang)
        rr = 0.74 + 0.16 * np.clip((np.linalg.norm(loop[:, :2], axis=1) - 5) / 3, 0, 1)
        blade(s, np.vstack([lp, lp[:1]]), np.append(rr, rr[0]), np.append(rr, rr[0]) / 1.15, normal=(0, 0, 1), k=0.45)
        # tiny point in the notch
        s.stroke(_rot(np.array([[7.2, 0, 0], [7.9, 0, 0.1], [8.6, 0, 0.1]]), c, ang), [0.55, 0.4, TIP], k=0.3)
        # spiky carved leaf between this petal and the next
        la = ang + math.pi / 4
        d = np.array([math.cos(la), math.sin(la), 0.08])
        s.feather(c + np.array([math.cos(la), math.sin(la), 0]) * 4.3 + [0, 0, 0.1], d, (0, 0, 1), 4.6, 1.45, T=0.42,
                  skew=1.0, pitch=0.36, depth=0.13, slope=0.9, seed=50 + k, notches=2, quill=0.05, tipT=0.7, k=0.4)
    # heart: collar + claws
    s.torus(c + [0, 0, -0.2], 2.85, 0.75, normal=(0, 0, 1), k=0.5)
    rec = claws(s, c + [0, 0, 1.1], D, normal=(0, 0, 1), spin=a + math.pi / 4, wire=0.42)
    if stones is not None: stones.append(dict(kind=kind, **rec))
    for sx in (1, -1):
        e = _rot(np.array([sx * 9.4, 0, 0]), c, a)
        s.torus(e, 0.95, 0.5, normal=(0, 0, 1), k=0.35)


def petal_bracelet():
    """Petal bracelet test: three flower links on bought jump rings (render only shows
    three; the bracelet takes five plus chain)."""
    s = Scene(); rings = Scene(); stones = []
    xs = (-21.4, 0.0, 21.4)
    for i, x in enumerate(xs):
        petal_link(s, (x, abs(x) * 0.12, 0), a=math.atan2(0.12 * np.sign(x), 1) if x else 0, stones=stones,
                   kind=("aquamarine", "garnet", "aquamarine")[i])
    for x in (-10.7, 10.7):
        rings.torus((x, abs(x) * 0.12 + 0.0, 0.05), 1.55, 0.5, normal=(0, 1, 0.0), k=0)
    cam = dict(view=(0.15, -0.75, 1.0), lens=100, margin=1.06)
    return [s, rings], stones, cam


def heart_unit(s, c, sc, stones=None, kind=None, D=None, seed=0):
    """One 'vertebra' of the heart spine: a small spikey heart (pointing down) with a pair
    of carved feather processes sweeping out and down, thorns on the lobes."""
    c = np.asarray(c, float)
    H = [(0, 2.9), (1.3, 4.6), (3.2, 5.0), (4.6, 3.6), (4.3, 1.0), (2.9, -1.6), (1.3, -3.4), (0, -4.9)]
    right = np.array([[x * sc, y * sc, 0] for x, y in H]); left = right[::-1][1:-1] * [-1, 1, 1]
    loop = catmull(np.vstack([right, left]), 8, closed=True) + c
    r = np.interp(loop[:, 1] - c[1], [-5 * sc, 0, 5 * sc], [0.62 * sc + 0.15, 0.85 * sc + 0.2, 0.9 * sc + 0.2])
    blade(s, np.vstack([loop, loop[:1]]), np.append(r, r[0]), np.append(r, r[0]) / 1.25, normal=(0, 0, 1), k=0.5)
    for sx in (1, -1):
        # feather process, out and sweeping down, tip curling
        s.feather(c + [3.6 * sc * sx, 1.6 * sc, 0.15], [0.94 * sx, 0.34, 0.0], (0, 0, 1), 10.5 * sc + 1.5, 2.3 * sc + 0.3,
                  T=0.45, skew=0.8, pitch=0.42, depth=0.16, slope=1.1, bend=-0.05 * sx / sc, seed=seed + sx * 3,
                  notches=2, quill=0.1, k=0.45)
        # thorn on the lobe and a small back-curl on the flank
        p = c + np.array([3.0 * sx, 5.0, 0]) * sc
        s.stroke(catmull([p, p + np.array([0.9 * sx, 1.4, 0.1]) * sc, p + np.array([2.2 * sx, 2.1, 0.1]) * sc], 5),
                 np.linspace(0.7 * sc + 0.1, TIP, 13), k=0.4)
        p = c + np.array([2.6 * sx, -2.2, 0]) * sc
        s.stroke(catmull([p, p + np.array([2.0 * sx, -0.6, 0.1]) * sc, p + np.array([2.6 * sx, -2.0, 0.2]) * sc], 5),
                 np.linspace(0.65 * sc + 0.1, TIP, 13), k=0.4)
    if stones is not None and kind:
        s.torus(c + [0, 0.3 * sc, -0.3], D * 0.55, 0.55, normal=(0, 0, 1), k=0.5)
        for sx in (1, -1):    # cross struts tying the collet to the heart
            s.stroke([c + [sx * D * 0.55, 0.3 * sc, -0.2], c + [sx * 3.6 * sc, 0.8 * sc, -0.1]], [0.5, 0.6], k=0.4)
        stones.append(dict(kind=kind, **claws(s, c + [0, 0.3 * sc, 0.9], D, normal=(0, 0, 1), spin=math.pi / 4, wire=0.4)))
    return c + np.array([0, -4.9 * sc, 0]), c + np.array([0, 2.9 * sc, 0])


def heart_spine():
    """Heart spine pendant: six spikey hearts stacked like vertebrae, graded down, each
    with carved feather processes; stones down the spine (aquamarine at the top, then
    garnets). A drop for a chain, made in one cast."""
    s = Scene(); stones = []
    y = 0.0; prev_tip = None
    scales = [1.25, 1.1, 0.97, 0.86, 0.76, 0.67]
    for i, sc in enumerate(scales):
        c = np.array([0, y, 0])
        if prev_tip is not None:
            c[1] = prev_tip[1] - 2.0 * sc
        kind = "aquamarine" if i == 0 else ("garnet" if i in (2, 4) else None)
        D = 6.0 if i == 0 else 3.5
        tip, cleft = heart_unit(s, c, sc, stones, kind, D, seed=60 + 7 * i)
        if prev_tip is not None:
            s.stroke([prev_tip, (prev_tip + cleft) / 2, cleft], [0.75 * sc + 0.15, 0.6 * sc + 0.15, 0.75 * sc + 0.15], k=0.45)
        prev_tip = tip; y = c[1]
    # dagger tail
    s.stroke([prev_tip, prev_tip + [0, -3.0, 0], prev_tip + [0, -6.5, 0]], [0.7, 0.5, TIP], k=0.4)
    # bail
    s.torus([0, 2.9 * scales[0] + 2.2, 0], 1.9, 0.75, normal=(1, 0, 0), k=0.45)
    cam = dict(view=(0.0, -0.45, 1.0), lens=100, margin=1.08)
    return s, stones, cam


# ---------------------------------------------------------------- fancy stones (stained glass)
CAL = {  # calibrated fancy sizes (length, width) mm
    "marquise": [(4, 2), (5, 2.5), (6, 3), (7, 3.5), (8, 4), (10, 5)],
    "pear": [(4, 3), (5, 3), (6, 4), (7, 5), (8, 5), (9, 6)],
    "round": [(2, 2), (2.5, 2.5), (3, 3), (3.5, 3.5), (4, 4), (5, 5)],
}


def fancy_caps(shape, L, W):
    """2D outline of a fancy stone as capsules [(a, b, r1, r2)] in stone-local xy
    (length along +x, centred)."""
    tip = 0.1
    if shape == "marquise":
        return [((0, 0), (L / 2 - tip, 0), W / 2, tip), ((0, 0), (-L / 2 + tip, 0), W / 2, tip)]
    if shape == "pear":
        return [((-L / 2 + W / 2, 0), (L / 2 - tip, 0), W / 2, tip)]
    return [((0, 0), (1e-3, 0), W / 2, W / 2)]


def _ucap2_np(x, y, r1, r2, h):
    px = np.abs(y); py = x
    b = (r1 - r2) / h; a = math.sqrt(max(0, 1 - b * b)); k = -b * px + a * py
    d = a * px + b * py - r1
    d = np.where(k < 0, np.sqrt(px ** 2 + py ** 2) - r1, d)
    d = np.where(k > a * h, np.sqrt(px ** 2 + (py - h) ** 2) - r2, d)
    return d


def caps_outline(caps, n=72, inset=0.0):
    """Girdle polygon of a capsule-union outline (radial bisection)."""
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    dirs = np.stack([np.cos(th), np.sin(th)], 1)
    lo = np.zeros(n); hi = np.full(n, 20.0)
    def f(r):
        p = dirs * r[:, None]; d = np.full(n, 1e9)
        for (a, b, r1, r2) in caps:
            a = np.array(a); b = np.array(b); v = b - a; h = max(np.linalg.norm(v), 1e-4); e = v / h
            q = p - a; x = q @ e; y = q @ np.array([-e[1], e[0]])
            d = np.minimum(d, _ucap2_np(x, y, r1, r2, h))
        return d + inset
    for _ in range(40):
        mid = (lo + hi) / 2; inside = f(mid) < 0
        lo = np.where(inside, mid, lo); hi = np.where(inside, hi, mid)
    return dirs * lo[:, None]


CAST = [True]      # production settings: bezel walls / bead settings (Nov 18 production plan)
BEZEL = 0.7


def set_fancy(s, c, ang, shape, L, W, kind, stones, vein=0.5, ledge=0.32, normal=(0, 0, 1), e1=None):
    """Seat a fancy stone flush in the lattice: a fused vein ring round the girdle, the
    seat cut into it, and an open light hole under it (plique-a-jour)."""
    c = np.asarray(c, float); N = nrm(normal)
    if e1 is None: e1 = np.array([math.cos(ang), math.sin(ang), 0.0])
    e1 = np.asarray(e1, float); e1 = nrm(e1 - N * np.dot(e1, N)); e2 = np.cross(N, e1)
    caps = fancy_caps(shape, L, W)
    if CAST[0] and shape == "round" and W <= 2.0:
        # bead setting for the tiniest rounds: a low seat ring and four raised beads over the girdle
        out = caps_outline(caps, 40, inset=-0.3)
        ring = np.array([c + e1 * x + e2 * y - N * 0.1 for x, y in out])
        s.stroke(np.vstack([ring, ring[:1]]), np.full(len(ring) + 1, 0.42), k=0.3)
        for t in np.arange(4) * math.pi / 2 + math.pi / 4:
            d = e1 * math.cos(t) + e2 * math.sin(t)
            s.sphere(c + d * (W / 2 + 0.12) + N * 0.32, 0.36, k=0.12)
    elif CAST[0]:
        # real bezel: a 0.7 mm wall hugging the girdle, from below the seat to enough height to push over the crown
        top = min(1.1, 0.16 * W + 0.45); bot = -0.45; H = top - bot
        out = caps_outline(caps, 72, inset=-BEZEL / 2)
        ring = np.array([c + e1 * x + e2 * y + N * (bot + top) / 2 for x, y in out])
        ring = np.vstack([ring, ring[:1]])
        tg = np.gradient(ring, axis=0); rad = np.cross(tg, N); rad /= np.maximum(np.linalg.norm(rad, axis=1), 1e-9)[:, None]
        s.stroke(ring, np.full(len(ring), H / 2), k=0.3, flat=max(1.0, H / BEZEL), normals=rad)
        if vein > BEZEL / 2:       # keep the lattice weight around the bezel foot so it still reads as leading
            foot = np.array([c + e1 * x + e2 * y + N * (bot + 0.1) for x, y in caps_outline(caps, 56, inset=-(BEZEL + vein * 0.4))])
            s.stroke(np.vstack([foot, foot[:1]]), np.full(len(foot) + 1, vein * 0.8), k=0.35)
    else:
        out = caps_outline(caps, 56, inset=-(vein * 0.75))          # vein centreline, just outside the girdle
        ring = np.array([c + e1 * x + e2 * y + N * 0.05 for x, y in out])
        s.stroke(np.vstack([ring, ring[:1]]), np.full(len(ring) + 1, vein), k=0.35)
    for (a, b, r1, r2) in caps:                                 # seat (girdle down to -0.05) and light hole
        A = c + e1 * a[0] + e2 * a[1]; B = c + e1 * b[0] + e2 * b[1]
        s.prism(A, B, r1 + 0.04, max(r2 + 0.04, 0.12), -0.05, 3.0, normal=N, op=1, k=0.05)
        s.prism(A, B, max(r1 - ledge, 0.2), max(r2 - ledge * 0.5, 0.05), -3.0, 0.2, normal=N, op=1, k=0.05)
    stones.append(dict(kind=kind, c=c.tolist(), n=N.tolist(), e1=e1.tolist(), D=W, L=L,
                       outline=caps_outline(caps, 48).tolist()))


def snap(shape, avail_w, max_l):
    best = None
    for L, W in CAL[shape]:
        if W <= avail_w and L <= max_l:
            best = (L, W)
    return best


def pack_stones(outline, root, rng, gap=0.8, res=0.08, sizes=None, tries=500, margin=1.1, flow_curl=0.0, blocked=()):
    """Greedy stained-glass packing: fill a closed 2D outline with calibrated fancy stones,
    largest first, each oriented along a vein flow radiating from `root`. Returns
    [(shape, L, W, (x, y), ang)]."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    o = np.asarray(outline)[:, :2]
    lo = o.min(0) - 2; hi = o.max(0) + 2
    n = np.ceil((hi - lo) / res).astype(int)
    def to_px(p): return [tuple(((q - lo) / res)) for q in p]
    dom = Image.new("1", tuple(n), 0); ImageDraw.Draw(dom).polygon(to_px(o), fill=1)
    dom = np.array(dom).T.astype(bool)
    dom = ndimage.binary_erosion(dom, iterations=int(margin / res))
    occ = ~dom
    if blocked:
        bl = Image.new("1", tuple(n), 0); db = ImageDraw.Draw(bl)
        for pts, wdt in blocked:
            db.line(to_px(np.asarray(pts)[:, :2]), fill=1, width=max(1, int(round((wdt + 2 * gap) / res))), joint="curve")
        occ |= np.array(bl).T.astype(bool)
    gpx = max(1, int(round(gap / res)))
    placed = []
    sizes = sizes or [("marquise", 10, 5), ("pear", 9, 6), ("marquise", 8, 4), ("pear", 8, 5), ("pear", 7, 5),
                      ("marquise", 7, 3.5), ("pear", 6, 4), ("marquise", 6, 3), ("round", 5, 5), ("pear", 5, 3),
                      ("marquise", 5, 2.5), ("round", 4, 4), ("round", 3.5, 3.5), ("marquise", 4, 2), ("round", 3, 3),
                      ("round", 2.5, 2.5), ("round", 2, 2)]
    if tries == "fit":                                   # farthest-point greedy: largest stone that fits the biggest hole
        cand = sorted(sizes, key=lambda z: -z[1] * z[2])
        polys = {z: caps_outline(fancy_caps(*z), 40) for z in cand}
        while True:
            dt = ndimage.distance_transform_edt(~occ) * res
            ij = np.unravel_index(np.argmax(dt), dt.shape); rmax = dt[ij]
            if rmax < min(z[2] for z in cand) / 2 * 0.98:
                if os.environ.get("PACKDBG"): np.save("/tmp/occ.npy", occ); print("stop rmax", rmax, len(placed))
                break
            c = lo + (np.array(ij) + 0.5) * res
            v = c - np.asarray(root); a0 = math.atan2(v[1], v[0]) + flow_curl * np.linalg.norm(v)
            done = False
            for z in cand:
                if z[2] / 2 > rmax - 0.12: continue
                for da in (0, 0.3, -0.3, 0.6, -0.6, math.pi / 2):
                    ang = a0 + da + (math.pi if z[0] == "pear" and rng.random() < 0.8 else 0)
                    ca, sa = math.cos(ang), math.sin(ang); p0 = polys[z]
                    for off in ((0, 0), (0.3, 0), (-0.3, 0)):
                        cc = c + off[0] * np.array([ca, sa])
                        poly = np.stack([cc[0] + p0[:, 0] * ca - p0[:, 1] * sa, cc[1] + p0[:, 0] * sa + p0[:, 1] * ca], 1)
                        m = Image.new("1", tuple(n), 0); ImageDraw.Draw(m).polygon(to_px(poly), fill=1)
                        m = np.array(m).T.astype(bool)
                        if not (m & occ).any():
                            occ |= ndimage.binary_dilation(m, iterations=gpx)
                            placed.append((z[0], z[1], z[2], (float(cc[0]), float(cc[1])), ang)); done = True; break
                    if done: break
                if done: break
            if not done:
                rr = max(2, int(0.25 / res))
                yy, xx = np.ogrid[-rr:rr + 1, -rr:rr + 1]
                i0, j0 = ij; sl = (slice(max(i0 - rr, 0), i0 + rr + 1), slice(max(j0 - rr, 0), j0 + rr + 1))
                disk = (yy ** 2 + xx ** 2 <= rr * rr)[(sl[0].start - (i0 - rr)):, (sl[1].start - (j0 - rr)):]
                occ[sl] |= disk[:occ[sl].shape[0], :occ[sl].shape[1]]
        return placed
    free = np.argwhere(~occ)
    for shape, L, W in sizes:
        poly0 = caps_outline(fancy_caps(shape, L, W), 40)
        for _ in range(tries):
            free = np.argwhere(~occ)
            if len(free) == 0: break
            ij = free[rng.integers(len(free))]
            c = lo + (ij + 0.5) * res
            v = c - np.asarray(root)
            ang = math.atan2(v[1], v[0]) + flow_curl * np.linalg.norm(v)
            if shape == "pear" and rng.random() < 0.8: ang += math.pi          # point back to the root
            ca, sa = math.cos(ang), math.sin(ang)
            poly = np.stack([c[0] + poly0[:, 0] * ca - poly0[:, 1] * sa, c[1] + poly0[:, 0] * sa + poly0[:, 1] * ca], 1)
            m = Image.new("1", tuple(n), 0); ImageDraw.Draw(m).polygon(to_px(poly), fill=1)
            m = np.array(m).T.astype(bool)
            if (m & occ).any(): continue
            occ |= ndimage.binary_dilation(m, iterations=gpx)
            placed.append((shape, L, W, (float(c[0]), float(c[1])), ang))
    return placed


def leading(outline, placed, res=0.08, rmin=0.38, rmax=2.0, z=0.12, step=0.45, spur=0.7):
    """Stained-glass came: the medial skeleton of the silver left between the packed stones,
    traced into strokes whose radius is the local half-gap, so every gap is filled with
    raised silver leading instead of left open."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    from skimage.morphology import skeletonize
    o = np.asarray(outline)[:, :2]
    lo = o.min(0) - 2; hi = o.max(0) + 2
    n = np.ceil((hi - lo) / res).astype(int)
    def to_px(p): return [tuple(((q - lo) / res)) for q in p]
    im = Image.new("1", tuple(n), 0); dr = ImageDraw.Draw(im); dr.polygon(to_px(o), fill=1)
    st = Image.new("1", tuple(n), 0); ds = ImageDraw.Draw(st)
    for shape, L, W, c, ang in placed:
        p0 = caps_outline(fancy_caps(shape, L, W), 40); ca, sa = math.cos(ang), math.sin(ang)
        ds.polygon(to_px(np.stack([c[0] + p0[:, 0] * ca - p0[:, 1] * sa, c[1] + p0[:, 0] * sa + p0[:, 1] * ca], 1)), fill=1)
    region = np.array(im).T.astype(bool) & ~np.array(st).T.astype(bool)
    dt = ndimage.distance_transform_edt(region) * res
    sk = skeletonize(region)
    nb = ndimage.convolve(sk.astype(int), np.ones((3, 3), int), mode="constant") - 1
    nb[~sk] = 0
    seen = np.zeros_like(sk)
    N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    def walk(a, b):
        path = [a, b]; seen[b] = True
        while nb[path[-1]] == 2:
            i, j = path[-1]; nxt = None
            for di, dj in N8:
                q = (i + di, j + dj)
                if 0 <= q[0] < sk.shape[0] and 0 <= q[1] < sk.shape[1] and sk[q] and q != path[-2] and q not in path[-3:]:
                    nxt = q; break
            if nxt is None: break
            if seen[nxt] and nb[nxt] == 2: path.append(nxt); break
            seen[nxt] = True; path.append(nxt)
        return path
    paths = []
    nodes = [tuple(p) for p in np.argwhere(sk & (nb != 2))]
    for a in nodes:
        seen[a] = True
        for di, dj in N8:
            b = (a[0] + di, a[1] + dj)
            if 0 <= b[0] < sk.shape[0] and 0 <= b[1] < sk.shape[1] and sk[b] and not (seen[b] and nb[b] == 2):
                if nb[b] != 2 and b < a: continue
                paths.append(walk(a, b))
    for p in np.argwhere(sk & ~seen):                      # closed loops
        p = tuple(p)
        if seen[p]: continue
        seen[p] = True
        for di, dj in N8:
            b = (p[0] + di, p[1] + dj)
            if sk[b]: paths.append(walk(p, b)); break
    out = []
    for path in paths:
        ij = np.array(path)
        xy = lo + (ij + 0.5) * res
        L = np.sum(np.linalg.norm(np.diff(xy, axis=0), axis=1))
        ends = [nb[path[0]] == 1, nb[path[-1]] == 1]
        if any(ends) and L < spur: continue
        r = np.clip(dt[ij[:, 0], ij[:, 1]] + 0.08, rmin, rmax)
        if len(r) > 11: r = np.convolve(np.pad(r, 5, mode="edge"), np.ones(11) / 11, mode="valid")
        k = max(2, int(L / step) + 1)
        u = np.linspace(0, len(xy) - 1, k).astype(int)
        pts = np.column_stack([xy[u], np.full(k, z)])
        out.append((pts, r[u]))
    return out


def bug_wing():
    """Stained-glass wing: a moth forewing whose veins are the lead lines of a window.
    Raised radial veins and a crossvein split the wing into panes; each pane is packed
    with calibrated fancy stones (marquise, pear, round) of one colour, flush-set and
    open-backed so light comes through, with fine silver came filling every gap. Panes run
    garnet and amethyst at the root to aquamarine and topaz at the margin. A calligraphic
    costa, a closed margin, a scroll, beads and a bail at the root."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    s = Scene(); stones = []
    rng = np.random.default_rng(11)
    ctrl = [(0, 0), (8, 3.2), (20, 6.0), (33, 8.0), (43, 8.4), (47, 5.6), (46.5, 0.5), (43, -6.5), (37, -13.5),
            (30, -16.0), (24, -14.0), (16, -9.5), (8, -5.0), (2, -2.2)]
    outline = catmull(np.array([[x, y, 0] for x, y in ctrl]), 10, closed=True)
    root = (-1.5, -0.5)
    # venation: two trunks from the root (R and Cu) that fork at a crossvein closing the
    # discal cell, M rising from the crossvein; branches bow slightly on the way to the margin
    def vein(p, q, bow=0.05):
        p = np.array(p, float); q = np.array(q, float); v = q - p; L = np.linalg.norm(v)
        m = (p + q) / 2 + bow * np.array([-v[1], v[0]])
        return catmull([[*p, 0], [*m, 0], [*q, 0]], 12)
    R0, M0, C0 = (19.0, 3.4), (23.5, -2.2), (14.0, -6.0)
    veins = [vein((1.0, -0.2), R0, 0.03), vein((1.0, -0.6), C0, -0.03),
             vein(R0, (31, 7.9)), vein(R0, (41, 8.5), 0.03), vein(R0, (46.6, 3.6), 0.0),
             vein(M0, (45.6, -3.0), 0.02), vein(M0, (40.2, -10.6), -0.02),
             vein(C0, (31.5, -16.0), -0.04), vein(C0, (19.0, -11.6), -0.03)]
    cross = catmull([[*R0, 0], [22.5, 0.8, 0], [*M0, 0], [19.5, -4.6, 0], [*C0, 0]], 10)
    vw = 0.8
    placed = pack_stones(outline, root, rng, gap=0.7, res=0.06, sizes=[
        ("marquise", 5, 2.5), ("pear", 4, 3), ("marquise", 4, 2), ("round", 3, 3), ("round", 2.5, 2.5),
        ("round", 2, 2), ("round", 1.5, 1.5)], tries="fit", margin=0.9, flow_curl=0.006,
        blocked=[(v, vw) for v in veins] + [(cross, vw)])
    # panes: label the wing cut by the veins, one colour per pane by distance from the root
    o = outline[:, :2]; res = 0.1; lo = o.min(0) - 2; n = np.ceil((o.max(0) + 2 - lo) / res).astype(int)
    px = lambda p: [tuple((q - lo) / res) for q in np.asarray(p)[:, :2]]
    im = Image.new("L", tuple(n), 0); d = ImageDraw.Draw(im); d.polygon(px(o), fill=1)
    for v in veins + [cross]: d.line(px(v), fill=0, width=3)
    lab, nl = ndimage.label(np.array(im).T > 0)
    cen = ndimage.center_of_mass(np.ones_like(lab), lab, range(1, nl + 1))
    pal = ["garnet", "amethyst", "citrine", "peridot", "aquamarine", "topaz"]
    order = {}
    keyd = sorted(range(1, nl + 1), key=lambda li: math.hypot(*(lo + np.array(cen[li - 1]) * res - root)))
    for rank, li in enumerate(keyd):                      # spread the whole palette over the panes, root to tip
        order[li] = min(len(pal) - 1, int(rank * len(pal) / nl))
    # came first so the seats cut through it, then the veins, then the stones
    for pts, r in leading(outline, placed, rmin=0.36, rmax=0.85, z=0.1):
        s.stroke(pts, r, k=0.25, flat=1.5)
    for v in veins + [cross]:
        v = resample(v, 0.6)
        s.stroke(v + [0, 0, 0.3], np.full(len(v), vw * 0.7), k=0.3, flat=1.0)
    for shape, L, W, c, ang in placed:
        ij = np.clip(((np.array(c) - lo) / res).astype(int), 0, np.array(lab.shape) - 1)
        li = lab[ij[0], ij[1]]
        kind = pal[order.get(li, 3)]
        set_fancy(s, (c[0], c[1], 0.0), ang, shape, L, W, kind, stones, vein=0.32)
    print(len(placed), "stones,", nl, "panes")
    # margin all round, heavier along the costa (leading edge)
    full = np.vstack([outline, outline[:1]])
    lead = (full[:, 1] > 0.6 * np.interp(full[:, 0], [0, 47], [0, 6])) & (full[:, 0] < 46)
    rad = np.where(lead, profile(np.clip(full[:, 0] / 46, 0, 1), [(0, 1.15), (0.5, 0.85), (1, 0.62)]), 0.6)
    rad = np.convolve(np.pad(rad, 4, mode="edge"), np.ones(9) / 9, mode="valid")
    s.stroke(full + [0, 0, 0.12], rad, k=0.45)
    # root: scroll curl, beads and a bail
    curl = catmull([[0.4, 0.3, 0.3], [-3.0, 3.0, 0.4], [-6.0, 1.6, 0.5], [-5.6, -1.4, 0.5], [-3.6, -0.8, 0.5]], 8)
    s.stroke(curl, profile(np.linspace(0, 1, len(curl)), [(0, 1.2), (1, 0.65)]), k=0.5)
    s.sphere(curl[-1], 0.95, k=0.3)
    stem_ball(s, [0.6, -1.4, 0.2], [-2.2, -5.0, 0.3], 0.42, 0.9)
    stem_ball(s, [3.0, -2.6, 0.2], [2.6, -6.4, 0.3], 0.38, 0.7)
    s.torus([-3.4, 5.0, 0.0], 1.9, 0.72, normal=(0, 1, 0), k=0.4)
    s.stroke([[-2.4, 2.4, 0.3], [-3.0, 3.6, 0.2]], [0.85, 0.75], k=0.3)
    cam = dict(view=(0.0, -0.45, 1.0), lens=100, margin=1.06)
    return s, stones, cam


PIECES = {"horn_ring": horn_ring, "wing_ring": wing_ring, "heart_pendant": heart_pendant, "petal_bracelet": petal_bracelet, "heart_spine": heart_spine, "bug_wing": bug_wing}


# ---------------------------------------------------------------- stones + render (bpy)
def stone_mesh(rec, kind):
    import bpy, bmesh
    from scipy.spatial import ConvexHull
    D, L = rec["D"], rec["L"]
    pts = []
    if rec.get("bead"):
        me = bpy.data.meshes.new("bead"); bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=D / 2)
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new("bead_" + kind, me); bpy.context.collection.objects.link(ob)
        ob.location = rec["c"]
        return ob
    if rec.get("outline"):
        o = np.array(rec["outline"]); W = D
        for sc, z in ((0.58, 0.16 * W), (0.86, 0.085 * W), (1.0, 0.012 * W), (1.0, -0.012 * W), (0.55, -0.2 * W)):
            for x, y in o[::2] if sc < 1 else o:
                pts.append((x * sc, y * sc, z))
        for t in np.linspace(-0.25, 0.25, 5):               # keel
            pts.append((t * L, 0, -0.42 * W))
        P = np.array(pts)
        return _hull_obj(P, kind, rec)
    def ring(n, r, z, off=0.0):
        for i in range(n):
            a = 2 * math.pi * (i + off) / n
            pts.append((math.cos(a) * r * L / D, math.sin(a) * r, z))
    ring(8, 0.27 * D, 0.155 * D, 0.5)          # table
    ring(8, 0.43 * D, 0.085 * D)               # crown mains / stars
    ring(16, 0.5 * D, 0.012 * D, 0.25)         # girdle top
    ring(16, 0.5 * D, -0.012 * D, 0.25)        # girdle bottom
    ring(8, 0.34 * D, -0.16 * D, 0.5)          # pavilion
    pts.append((0, 0, -0.43 * D))              # culet
    P = np.array(pts)
    return _hull_obj(P, kind, rec)


def _hull_obj(P, kind, rec):
    import bpy, bmesh
    from scipy.spatial import ConvexHull
    hull = ConvexHull(P)
    me = bpy.data.meshes.new("stone"); bm = bmesh.new()
    vs = [bm.verts.new(p) for p in P]
    for f in hull.simplices:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.002, verts=bm.verts, edges=bm.edges)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    ob = bpy.data.objects.new("stone_" + kind, me); bpy.context.collection.objects.link(ob)
    n = np.array(rec["n"]); e1 = np.array(rec["e1"]); e2 = np.cross(n, e1)
    from mathutils import Matrix
    M = Matrix(((e1[0], e2[0], n[0], rec["c"][0]), (e1[1], e2[1], n[1], rec["c"][1]),
                (e1[2], e2[2], n[2], rec["c"][2]), (0, 0, 0, 1)))
    ob.matrix_world = M
    return ob


def facet_mat(kind):
    import bpy
    import jlib
    m = jlib.stone_mat(kind)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = max(0.9, jlib.STONES[kind]["transmission"])
    b.inputs["Roughness"].default_value = 0.0
    b.inputs["Coat Weight"].default_value = 0.0
    return m


def to_blender(V, F, name):
    import bpy
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(F.size); me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set("loop_start", np.arange(0, F.size, 3))
    me.update(); me.validate()
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    ob["metal"] = True
    return ob


def realism(objs, hdri="studio.exr", hdri_strength=0.7, rot=0.6):
    """Closer-to-life look on top of studio_white: cast-and-polished sterling (slight
    micro-roughness, darker recesses where polishing wheels can't reach, faint hand-finish
    ripple), gems coloured by absorption through their depth instead of a flat tint, a
    real studio HDRI in the reflections, and AgX tone mapping for natural highlights."""
    import bpy
    s = bpy.context.scene
    s.view_settings.view_transform = 'AgX'
    s.view_settings.exposure = float(os.environ.get("EXPO", "0.0"))
    s.cycles.transmission_bounces = 16; s.cycles.glossy_bounces = 12; s.cycles.max_bounces = 24
    s.cycles.caustics_refractive = True; s.cycles.blur_glossy = 0.5
    # light tent: the piece sits in a bright white tent (a uniform white world), soft
    # softboxes give the highlight gradients, and mid-grey flags (not black) give the
    # silver its edges, the way jewelry is photographed
    w = s.world; bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = float(os.environ.get("TENT", "0.45"))
    if os.environ.get("WORLD", "grad") == "grad":
        # photo-studio falloff instead of a flat white world: bright overhead, a soft horizon,
        # dark floor and a few dark vertical gaps, so polished silver gets real gradients and
        # crisp dark edges the way it does on a white sweep under softboxes
        wn = w.node_tree.nodes; wl = w.node_tree.links
        tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ")
        wl.new(tc.outputs["Normal"], sep.inputs[0])
        rp = wn.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
        el[0].position = 0.0; el[0].color = (0.45, 0.45, 0.45, 1)
        el[1].position = 1.0; el[1].color = (1, 1, 1, 1)
        e2 = el.new(0.47); e2.color = (0.08, 0.08, 0.08, 1)
        e3 = el.new(0.6); e3.color = (0.55, 0.55, 0.55, 1)
        mr = wn.new("ShaderNodeMapRange"); mr.inputs[1].default_value = float(os.environ.get("ZSIGN", "1")); mr.inputs[2].default_value = -float(os.environ.get("ZSIGN", "1"))
        wl.new(sep.outputs["Z"], mr.inputs[0]); wl.new(mr.outputs[0], rp.inputs[0])
        # vertical dark gaps around the azimuth (between softboxes)
        az = wn.new("ShaderNodeMath"); az.operation = 'ARCTAN2'
        wl.new(sep.outputs["Y"], az.inputs[0]); wl.new(sep.outputs["X"], az.inputs[1])
        sn = wn.new("ShaderNodeMath"); sn.operation = 'SINE'
        mul = wn.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 3.0
        wl.new(az.outputs[0], mul.inputs[0]); wl.new(mul.outputs[0], sn.inputs[0])
        gp = wn.new("ShaderNodeMapRange"); gp.inputs[1].default_value = -1; gp.inputs[2].default_value = 1
        gp.inputs[3].default_value = 0.35; gp.inputs[4].default_value = 1.0
        wl.new(sn.outputs[0], gp.inputs[0])
        mx = wn.new("ShaderNodeMixRGB"); mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        wl.new(rp.outputs[0], mx.inputs[1]); wl.new(gp.outputs[0], mx.inputs[2])
        wl.new(mx.outputs[0], bg.inputs[0])
        bg.inputs[1].default_value = float(os.environ.get("TENT", "1.1"))
    for ob in s.objects:
        for ms in getattr(ob, "material_slots", []):
            mt = ms.material
            if mt and mt.name.startswith("card"):
                for nd in mt.node_tree.nodes:
                    if nd.type == "BSDF_DIFFUSE": g_ = float(os.environ.get("FLAG", "0.0")); nd.inputs[0].default_value = (g_, g_, g_, 1)
    # sterling, high polish: clean bright base, near-mirror finish with only micro variation,
    # no low-frequency bump (that read as "puddly"), reflections kept crisp
    s.cycles.blur_glossy = 0.0
    m = bpy.data.materials.new("sterling_real"); m.use_nodes = True; t = m.node_tree; N = t.nodes
    b = N["Principled BSDF"]
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Base Color"].default_value = (0.97, 0.96, 0.945, 1)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0; nz.inputs["Detail"].default_value = 2
    rr = N.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.035; rr.inputs[4].default_value = 0.075
    t.links.new(nz.outputs[0], rr.inputs[0]); t.links.new(rr.outputs[0], b.inputs["Roughness"])
    import jlib
    for ob in objs:
        if ob.get("metal"):
            ob.data.materials.clear(); ob.data.materials.append(m)
        else:
            kind = ob.get("kind")
            if kind: ob.data.materials.clear(); ob.data.materials.append(gem_real(kind))


GEM_ABS = {  # absorption colour, density per mm, ior, dispersion (Abbe-ish)
    "garnet": ((0.62, 0.03, 0.06), 1.4, 1.76, 0.03), "amethyst": ((0.55, 0.25, 0.8), 0.7, 1.55, 0.013),
    "spinel": ((0.99, 0.55, 0.68), 0.45, 1.72, 0.020), "citrine": ((1.0, 0.6, 0.12), 0.7, 1.55, 0.013), "peridot": ((0.5, 0.78, 0.1), 0.8, 1.67, 0.02),
    "aquamarine": ((0.55, 0.85, 0.95), 0.45, 1.58, 0.014), "topaz": ((0.15, 0.48, 0.92), 0.8, 1.62, 0.014),
    "moonstone": ((0.85, 0.88, 0.95), 0.2, 1.52, 0.01), "londonblue": ((0.14, 0.34, 0.62), 0.75, 1.62, 0.014), "labradorite": ((0.05, 0.06, 0.08), 3.0, 1.56, 0.01),
}


def gem_real(kind):
    import bpy
    nm = "gem_" + kind
    if nm in bpy.data.materials: return bpy.data.materials[nm]
    col, dens, ior, disp = GEM_ABS[kind]
    m = bpy.data.materials.new(nm); m.use_nodes = True; t = m.node_tree; N = t.nodes
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*[0.75 + 0.25 * c for c in col], 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.0; b.inputs["IOR"].default_value = ior
    if "Dispersion" in b.inputs: b.inputs["Dispersion"].default_value = disp
    va = N.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (*col, 1); va.inputs["Density"].default_value = dens
    t.links.new(va.outputs[0], N["Material Output"].inputs["Volume"])
    return m


def build(name, quality="preview"):
    s, stones, cam = PIECES[name]()
    scenes = s if isinstance(s, list) else [s]
    vox = {"preview": 0.06, "real": 0.035}.get(quality, 0.04)
    meshes = []
    for j, sc in enumerate(scenes):
        P = sc.array()
        print(name, j, len(P), "prims", flush=True)
        V, F = sdf.mesh(P, vox if j == 0 else 0.05)
        meshes.append(sdf.save_stl(V, F, os.path.join(OUT, name + ("" if j == 0 else f"_part{j}") + ".stl"),
                                   smooth=8 if quality == "real" else 0))
    m = meshes[0]
    info = dict(name=name, watertight=bool(m.is_watertight), volume_cm3=round(abs(m.volume) / 1000, 3),
                sterling_g=round(abs(m.volume) / 1000 * 10.36, 1), size_mm=[round(float(x), 1) for x in m.extents],
                stones=[dict(kind=r["kind"], D=r["D"], L=r["L"]) for r in stones])
    json.dump(info, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    print(info, flush=True)
    import bpy, jlib
    jlib.reset()
    objs = []
    for j, mm in enumerate(meshes):
        V2, F2 = np.asarray(mm.vertices, np.float32), np.asarray(mm.faces, np.int32)
        ob = to_blender(V2, F2, f"{name}_{j}")
        cap = 1500000 if quality == "real" else 600000
        if len(F2) > cap:
            d = ob.modifiers.new("d", 'DECIMATE'); d.ratio = cap / len(F2)
        objs.append(ob)
    for r in stones:
        st = stone_mesh(r, r["kind"]); st.data.materials.append(facet_mat(r["kind"])); st["kind"] = r["kind"]; objs.append(st)
    res, spp = {"preview": (900, 48), "real": (1800, 200)}.get(quality, (2000, 256))
    if os.environ.get("RES"): res, spp = map(int, os.environ["RES"].split(","))
    jlib.studio_white(objs, view=cam["view"], res=res, samples=spp, margin=cam.get("margin", 1.18), lens=cam.get("lens", 100))
    if quality == "real": realism(objs)
    tag = {"preview": "_preview", "real": "_real"}.get(quality, "")
    rgba = os.path.join(OUT, f"{name}_white{tag}_rgba.png")
    jlib.render(rgba)
    flat = rgba.replace("_rgba", "")
    import shutil; shutil.copy(rgba, flat); jlib.flatten_white(flat)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, name + ".blend"))
    return flat


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "preview")
