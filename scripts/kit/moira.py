"""Moira's hand (refs/research/RESEARCH.md): carved feathers that wrap the body, signature petals with spiky leaves,
thorned hearts, gatepiece scrolls, soft stars, claw-set big stones, fine chain and pear drops.
hyodomachine accents: cross fleury, graded bead rows, chrome hook with bead, needle tips.
All in world coordinates (mm), z up out of the face."""
import math
import numpy as np
import sculpt as K
from v2 import claws
from kit import heart_outline

Z = np.array([0, 0, 1.0])


def nrm(v):
    v = np.asarray(v, float); return v / max(np.linalg.norm(v), 1e-9)


def v3(p, z=0.0):
    p = np.asarray(p, float)
    return p if len(p) == 3 else np.array([p[0], p[1], z])


def rot2(d, a):
    c, s_ = math.cos(a), math.sin(a); return np.array([d[0] * c - d[1] * s_, d[0] * s_ + d[1] * c])


# ------------------------------------------------------------------ feather
def feather(s, base, d, n=Z, L=30.0, W=None, bend=0.0, wrap=0.0, seed=1.0, T=None, k=0.0, notches=3):
    """Moira's carved feather: polished shaft ridge, fine engraved barbs, a few splits, slender (L:W ~ 6)."""
    W = W or L * 0.09
    T = T or float(np.clip(0.035 * L, 0.45, 0.9))
    s.feather(v3(base), v3(d), v3(n), L, W, T=T, skew=0.78, pitch=float(np.clip(0.01 * L + 0.06, 0.28, 0.55)),
              depth=float(np.clip(0.007 * L + 0.06, 0.15, 0.32)), slope=0.95, bend=bend, wrap=wrap, seed=seed,
              shaft=float(np.clip(0.011 * L, 0.22, 0.5)), ridge=float(np.clip(0.008 * L, 0.15, 0.32)), cup=0.22,
              notches=notches, quill=0.07, tipT=0.4, k=k)


def fan(s, base, d, n=Z, L=30.0, count=3, spread=0.35, step=None, seed=1, bend=0.0, wrap=0.0, lift=0.55, shrink=0.82):
    """Individually placed feathers fanned into a wing, each overlapping the next like shingles."""
    base = v3(base); d = nrm(v3(d)); n = nrm(v3(n)); side = np.cross(n, d)
    step = L * 0.12 if step is None else step
    out = []
    for i in range(count):
        a = (i - (count - 1) * 0.15) * spread / max(1, count - 1) * 2
        di = nrm(d * math.cos(a) + side * math.sin(a))
        b = base + side * step * i * 0.5 + n * lift * i - d * step * i * 0.3
        Li = L * shrink ** i
        feather(s, b, di, n, Li, bend=bend * (1 + 0.2 * i), wrap=wrap, seed=seed + i * 1.7)
        out.append((b, di, Li))
    return out


# ------------------------------------------------------------------ stones and settings
THORNY = [True]      # claws grow on into thorns (Nov 18 check: stock prongs read catalogue)


def prong(s, st, c, D, kind, L=None, normal=Z, spin=0.0, n=None, wire=None):
    """Claw-set faceted stone, Moira's way: thin claws, big stone, sits proud."""
    L = L or D
    # snap to stock calibrated sizes (production plan): ovals 5x3..12x10, rounds 1.5..10 in half mm
    if abs(L - D) < 0.05:
        D = L = float(np.clip(math.floor(D * 2 + 1e-6) / 2, 1.5, 10.0))      # snap down: a bigger stock stone never crowds its neighbour
    else:
        ov = [(5, 3), (6, 4), (7, 5), (8, 6), (9, 7), (10, 8), (12, 10)]
        fit = [q for q in ov if q[0] <= max(L, D) + 1e-6 and q[1] <= min(L, D) + 1e-6] or ov[:1]
        q = max(fit, key=lambda q: q[0] * q[1]); L, D = (q if L >= D else q[::-1])
        L, D = float(L), float(D)
    n = n or (6 if (L / D) < 1.15 and D > 6 else 4)
    wire = wire or float(np.clip(0.07 * D + 0.12, 0.3, 0.55))
    rec = claws(s, v3(c), D, L, normal=v3(normal), spin=spin, n=n, wire=wire, k=0.3)
    st.append(dict(kind=kind, **rec))
    if THORNY[0]:
        # Moira, not catalogue: every claw grows on past the crown into an uneven thorn that flicks out to a needle
        cc = v3(c); N = v3(normal) / max(np.linalg.norm(v3(normal)), 1e-9)
        a1 = np.cross(N, [0, 1, 0]) if abs(N[1]) < .9 else np.cross(N, [1, 0, 0]); a1 = a1 / np.linalg.norm(a1); a2 = np.cross(N, a1)
        ca, sa = math.cos(spin), math.sin(spin); e1, e2 = a1 * ca + a2 * sa, -a1 * sa + a2 * ca
        rg = np.random.default_rng(int(abs(cc.sum() * 997)) % (2 ** 31))
        for t in np.arange(n) * 2 * math.pi / n + (math.pi / n if n == 4 else 0):
            d = e1 * math.cos(t) * L / 2 + e2 * math.sin(t) * D / 2; dn = d / max(np.linalg.norm(d), 1e-9)
            p0 = cc + d * 1.0 + dn * wire * 1.1 - N * D * 0.22     # rooted below the girdle, outside the stone
            ln = D * rg.uniform(0.18, 0.5); tw = np.cross(N, dn) * rg.uniform(-0.4, 0.4)
            p1 = p0 + (N * 0.55 + dn * 0.6 + tw) * ln * 0.55
            p2 = p0 + (N * 0.35 + dn * 1.0 + tw * 1.4) * ln
            pm = cc + d * 1.0 + dn * wire * 1.1 + N * D * 0.14
            s.stroke(np.array([p0, pm, p1, p2]), np.array([wire * 1.05, wire * 0.95, wire * 0.75, 0.07]), k=0.12)
    return rec


def pear(s, st, top, D, L, kind, down=(0, -1, 0), normal=Z, wire=None):
    """A pear stone hanging point-up from a little ring: the classic Moira dangle."""
    down = nrm(v3(down)); top = v3(top)
    c = top + down * (L * 0.62)
    spin = math.atan2(down[1], down[0])
    prong(s, st, c, D, kind, L=L, normal=normal, spin=spin, n=3, wire=wire)
    s.torus(top + down * 0.3, 0.9, 0.3, normal=np.cross(down, v3(normal)), k=0.2)
    s.cone(top + down * 0.5, c - down * L * 0.38, 0.32, 0.28, k=0.2)


def drop(s, top, r=1.0, down=(0, -1, 0)):
    """Small solid silver drop on the end of a chain."""
    down = nrm(v3(down)); top = v3(top)
    s.cone(top, top + down * r * 2.6, 0.22, r * 0.85, k=0.4)
    s.sphere(top + down * r * 3.0, r, k=0.6)


def chain(s, pts, link=1.5, wire=0.26, n=None):
    """Fine cable chain along a polyline: alternating links."""
    P = K._curve(np.asarray([v3(p) for p in pts]), 0.1)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cs = np.concatenate([[0], np.cumsum(seg)])
    step = link * 1.15; m = max(1, int(cs[-1] / step))
    for i in range(m):
        u = (i + 0.5) * step
        j = min(int(np.searchsorted(cs, u)), len(P) - 1)
        c = P[j]; t = nrm(P[min(j + 1, len(P) - 1)] - P[max(j - 1, 0)])
        side = nrm(np.cross(t, Z)) if abs(t[2]) < 0.9 else np.array([1, 0, 0.0])
        nrmv = side if i % 2 else nrm(np.cross(t, side))
        tt = np.linspace(0, 2 * math.pi, 17)
        loop = [c + t * math.cos(a) * link * 0.6 + nrm(np.cross(nrmv, t)) * math.sin(a) * link * 0.3 for a in tt]
        s.stroke(np.array(loop), np.full(17, wire), k=0.0)


# ------------------------------------------------------------------ stars
def star(s, c, R, normal=Z, rot=0.0, puff=0.3, points=5):
    """Moira's star: soft sculpted points, a little domed."""
    c = v3(c); n = nrm(v3(normal))
    e1 = nrm(np.cross(n, [0, 1, 0]) if abs(n[1]) < 0.9 else np.cross(n, [1, 0, 0])); e2 = np.cross(n, e1)
    for i in range(points):
        a = rot + i * 2 * math.pi / points + math.pi / 2
        d = e1 * math.cos(a) + e2 * math.sin(a)
        s.cone(c + n * R * 0.04, c + d * R, R * 0.42, R * 0.07, k=0.15, flat=2.6, zhint=n)
    s.ellipsoid(c + n * R * 0.04, (R * 0.34, R * 0.34, R * 0.2), zhint=n, k=0.2)


def comet(s, head, d, L, R, count=4, normal=Z, seed=0):
    """A trail of little stars falling away from a head star, joined by tapering silver tails."""
    rng = np.random.default_rng(seed)
    head = v3(head); d = nrm(v3(d)); n = nrm(v3(normal)); side = np.cross(n, d)
    star(s, head, R, n, rot=rng.uniform(0, 1))
    for i in range(1, count):
        f = i / count
        p = head + d * L * f + side * L * 0.16 * math.sin(f * 2.4 + seed)
        star(s, p, R * (1 - 0.55 * f), n, rot=rng.uniform(0, 1))
        s.cone(head, p, R * 0.18, R * 0.08, k=0.3, flat=1.8, zhint=n)


# ------------------------------------------------------------------ signature petal
def petal(s, st, c, R, kind="garnet", n_petals=5, normal=Z, rot=0.0, leaves=True, D=None):
    """Signature petal: rounded cupped petals round a claw-set stone, spiky leaves between."""
    c = v3(c); n = nrm(v3(normal))
    e1 = nrm(np.cross(n, [0, 1, 0]) if abs(n[1]) < 0.9 else np.cross(n, [1, 0, 0])); e2 = np.cross(n, e1)
    for i in range(n_petals):
        a = rot + i * 2 * math.pi / n_petals
        d = e1 * math.cos(a) + e2 * math.sin(a)
        zh = nrm(n * 0.9 - d * 0.42)
        pc = c + d * R * 0.56 + n * R * 0.12
        s.ellipsoid(pc, (R * 0.48, R * 0.36, R * 0.11), xaxis=d, zhint=zh, k=0.35)
        # the petal is a cup: hollow its upper face
        s.ellipsoid(pc + zh * R * 0.12 + d * R * 0.04, (R * 0.4, R * 0.29, R * 0.1), xaxis=d, zhint=zh, op=1, k=0.12)
        if leaves:
            a2 = a + math.pi / n_petals; d2 = e1 * math.cos(a2) + e2 * math.sin(a2)
            s.cone(c + d2 * R * 0.6, c + d2 * R * 1.32 - n * R * 0.08, R * 0.2, 0.08, k=0.25, flat=2.4, zhint=n)
    s.sphere(c, R * 0.42, k=0.3)
    D = D or R * 0.82
    prong(s, st, c + n * (R * 0.32 + D * 0.45), D, kind, normal=n, spin=rot)


# ------------------------------------------------------------------ thorned heart
def thorn_heart(s, st, c, w, kind="amethyst", normal_z=0.0, horns=True, thorns=7, seed=0, tail=0.35, D=None):
    """A heart drawn as two strokes that cross at the point and run on as a needle; thorns on the outside,
    the top lobes curl into horns; a stone claw-set in the middle."""
    rng = np.random.default_rng(seed)
    c = v3(c)
    o = heart_outline(w, w * 0.95, 120)            # starts at top dip, goes clockwise round
    o = o - o.mean(0)
    i_bot = int(np.argmin(o[:, 1]))
    rightside = o[: i_bot + 1]
    leftside = np.vstack([o[i_bot:], o[:1]])[::-1]
    for side, half in ((1, rightside), (-1, leftside)):
        h = half[::6]
        bot = h[-1]; dn = nrm(h[-1] - h[-3])
        pts = np.vstack([h, bot + dn * w * tail * 0.6 + np.array([-side * w * 0.05, 0])])
        K.ribbon(s, np.column_stack([pts + c[:2], np.full(len(pts), c[2] + 0.3)]), w=w * 0.055, thin=0.6,
                 wkeys=[(0, 0.7), (0.3, 1.15), (0.75, 0.9), (1, 0.4)], ends=(0.05, 0.22), twist=[(0, 0), (0.5, 0.4 * side), (1, 0)])
        # thorns
        for j in range(thorns // 2 + 1):
            f = 0.18 + 0.6 * j / max(1, thorns // 2)
            q = half[int(f * (len(half) - 1))]
            tq = nrm(half[min(int(f * (len(half) - 1)) + 2, len(half) - 1)] - q)
            out = np.array([tq[1], -tq[0]]) * side
            if np.dot(out, q) < 0: out = -out
            L = w * rng.uniform(0.08, 0.14)
            K.cusp(s, q + c[:2] + out * w * 0.03, out * 0.8 + tq * 0.35 * side, L, w=w * 0.035, z=c[2] + 0.3)
        if horns:
            tp = half[int(len(half) * 0.12)]
            ctr = tp + np.array([side * w * 0.1, w * 0.2])
            K.scroll(s, tp + c[:2], ctr + c[:2], w * 0.03, turns=0.75, cw=-side, w=w * 0.05, z=c[2] + 0.3, rise=0.6, wk_end=0.4)
    D = D or w * 0.34
    prong(s, st, c + Z * (D * 0.5 + 0.2) + np.array([0, -w * 0.06, 0]), D, kind, L=D * 1.3, spin=math.pi / 2)


# ------------------------------------------------------------------ gatepiece
def gate_scroll(s, c, h, mirror=False, z=0.0, w=None):
    """Ornamental-fence S scroll: a stroke that curls at both ends in opposite directions."""
    c = v3(c, z); sg = -1 if mirror else 1; w = w or h * 0.045
    pts = []
    for t in np.linspace(0, 1, 50):
        a = (t - 0.5) * 2
        pts.append([sg * h * 0.22 * math.sin(a * math.pi * 1.05) * (1 - 0.3 * abs(a)), h * 0.5 * a])
    pts = np.array(pts)
    K.ribbon(s, np.column_stack([pts + c[:2], np.full(len(pts), c[2])]), w=w, thin=0.75, ends=(0.0, 0.0), k=0.25)
    for e, cw in ((pts[0], 1), (pts[-1], -1)):
        K.scroll(s, e + c[:2], e + c[:2] + np.array([sg * cw * h * 0.09, cw * h * 0.04]), w * 0.6, turns=0.8, cw=sg * cw,
                 w=w, z=c[2], rise=0.4, wk_end=0.6)


# ------------------------------------------------------------------ hyodomachine accents
def cross_fleury(s, st, c, size, normal_rot=0.0, z=0.0, kind=None, long_foot=1.6, w=None):
    """Gothic cross, hyodomachine chrome: thin arms that flare into sharp lancet tips; just behind each tip
    two hooked barbs sweep back to needle points. A bead at the crossing."""
    c = v3(c, z); w = w or size * 0.055
    for i, ln in enumerate((1.0, 1.0, long_foot, 0.85)):     # right, left, down, up
        d = rot2(np.array([1.0, 0.0]), normal_rot + [0, math.pi, -math.pi / 2, math.pi / 2][i])
        L = size * 0.5 * ln; nn = np.array([-d[1], d[0]])
        p = [c[:2] + d * w * 1.2, c[:2] + d * L * 0.45, c[:2] + d * L * 0.8, c[:2] + d * L]
        K.ribbon(s, np.column_stack([np.array(p), np.full(4, z + 0.4)]), w=w, thin=0.42,
                 wkeys=[(0, 1.0), (0.4, 0.62), (0.72, 0.75), (0.84, 1.55), (1, 0.2)], ends=(0.0, 0.12),
                 twist=[(0, 0), (0.6, 0.35), (1, 0)], k=0.25)
        q = c[:2] + d * L * 0.8
        for sd in (1, -1):
            a_ = q + nn * sd * w * 0.5
            b_ = q + nn * sd * L * 0.17 + d * L * 0.02
            e_ = q + nn * sd * L * 0.2 - d * L * 0.16
            f_ = q + nn * sd * L * 0.13 - d * L * 0.24
            K.ribbon(s, np.column_stack([np.array([a_, b_, e_, f_]), np.full(4, z + 0.3)]), w=w * 0.75, thin=0.45,
                     wkeys=[(0, 0.9), (0.35, 1.0), (1, 0.4)], ends=(0.0, 0.5), k=0.2)
    s.sphere(c + Z * 0.5, w * 1.9, k=0.4)
    if kind:
        prong(s, st, c + Z * (w * 2.4), w * 3.4, kind)


def bead_row(s, pts, r0=1.2, r1=0.6, n=5, z=0.0, wire=0.3, k=0.3):
    """Graded silver beads strung along a curve (hyodomachine dot row)."""
    P = K._curve(np.asarray([v3(p, z) for p in pts]), 0.1)
    # Nov 18: no more strung beads anywhere (they read as a crude bead string). The same call now draws one liquid stroke
    # that is fat at the start, pinches once, swells again and draws out to a needle (hyodomachine).
    K.ribbon(s, P, w=max(r0, 0.5), thin=0.75, ends=(0.0, 0.3),
             wkeys=[(0, 1.0), (0.35, 0.55), (0.6, max(0.5, r1 / r0) * 1.1), (1, 0.35)], k=max(k, 0.4))


def needle(s, a, d, L, w=0.5, z=0.0, curl=0.0):
    """A liquid stroke drawing out to a needle point, with an optional late curl."""
    a = np.asarray(a, float)[:2]; d = nrm(np.asarray(d, float)[:2]); nn = np.array([-d[1], d[0]])
    p = [a, a + d * L * 0.4, a + d * L * 0.8 + nn * curl * L * 0.08, a + d * L + nn * curl * L * 0.25]
    K.ribbon(s, np.column_stack([np.array(p), np.full(4, z)]), w=w, thin=0.6, wkeys=[(0, 1.0), (0.3, 1.1), (1, 0.5)],
             ends=(0.0, 0.55), k=0.3)
