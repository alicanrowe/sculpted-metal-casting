"""motif library, built on sculpt.py liquid ribbons. Every motif draws in a mapper m
(Flat or Cyl) using 2D coords (x, y) plus a z lift, so it works on plates, rings and cuffs.
See AESTHETIC.md for the rules these follow."""
import math
import numpy as np
import sculpt as K
from sdf import resample, arclen, profile
from kit import bead, pane, smooth, Flat, nrm
from detail import milgrain, acanthus
from v2 import blade

TIP = K.TIP


def rot(v, a):
    c, s_ = math.cos(a), math.sin(a)
    return np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]])


def local(o, ang, pts, flip=1):
    """Points given in a local frame (x along ang, y to the left * flip) -> plane coords."""
    o = np.asarray(o, float)
    return np.array([o + rot(np.array([p[0], p[1] * flip]), ang) for p in pts])


def rib(s, m, pts2, z, **kw):
    """Ribbon through 2D points with a z profile (scalar, list per point, or keys)."""
    pts2 = np.asarray(pts2, float)
    if np.isscalar(z): zz = np.full(len(pts2), float(z))
    else: zz = np.asarray(z, float)
    return K.ribbon(s, np.column_stack([pts2, zz]), m=m, **kw)


# ------------------------------------------------------------------ strokes
def whip(s, m, pts2, w=1.4, z=0.0, rise=0.8, twist=0.9, ends=(0.22, 0.22), thin=0.35, wk=None, k=0.3):
    """Art Nouveau whiplash: needle - swell - needle, rising off the plane and twisting."""
    n = len(pts2); zz = [z + rise * math.sin(math.pi * i / (n - 1)) for i in range(n)]
    return rib(s, m, pts2, zz, w=w, thin=thin, ends=ends, k=k,
               wkeys=wk or [(0, 0.5), (0.35, 1.0), (0.7, 0.7), (1, 0.5)],
               twist=[(0, 0.0), (0.5, twist), (1, 0.15)])


def hook(s, m, st, o, ang, L, cd=1, w=None, kind="garnet", z=0.0, rise=0.9, turns=0.85, bead_d=None, k=0.3):
    """Calligraphic hook: a needle that sweeps out, swells, and rolls into a tightening spiral
    that holds a bead in its counter. o = needle tip, ang = direction of travel, cd = curl side."""
    w = w or L * 0.085
    lead = [(0, 0), (0.25 * L, -0.05 * L), (0.52 * L, -0.03 * L)]
    C = np.array([0.74 * L, 0.21 * L]); th = np.linspace(-math.pi / 2, -math.pi / 2 + turns * 2 * math.pi, 34)
    r = 0.21 * L + (0.09 * L - 0.21 * L) * np.linspace(0, 1, len(th)) ** 0.9
    sp = np.stack([C[0] + r * np.cos(th), C[1] + r * np.sin(th)], 1)
    P = local(o, ang, np.vstack([lead, sp[1:]]), cd)
    zz = list(np.linspace(z, z + rise, len(P)))
    c, W, _ = rib(s, m, P, zz, w=w, thin=0.42, ends=(0.24, 0.0), round_ends=(False, True), k=k,
                  wkeys=[(0, 0.4), (0.3, 1.0), (0.55, 0.7), (0.8, 0.95), (1, 0.75)], twist=[(0, 0.0), (0.4, 0.7), (1, 0.0)])
    s.sphere(c[-1], W[-1] * 1.02, k=0.2)
    Cw = local(o, ang, [C], cd)[0]
    if kind:
        d = bead_d or max(1.2, min(4.5, 2 * (0.15 * L - w * 0.55) + 0.5))
        bead(s, m, st, (Cw[0], Cw[1]), d, kind, z=z + rise * 0.8 + d * 0.32)
    return Cw


def crown(s, m, o, ang, size, n=3, lean=1, z=0.0, k=0.3):
    """A crown of hooked horns all leaning one way, like a breaking wave."""
    for i in range(n):
        f = 1.0 - 0.22 * abs(i - (n - 1) / 2) - 0.06 * i
        b = np.asarray(o, float) + rot(np.array([0, i * size * 0.3 * (-lean)]), ang)
        pts = local(b, ang, [(0, 0), (0.45 * size * f, -0.05 * size), (0.85 * size * f, 0.12 * size * lean),
                             (1.0 * size * f, 0.42 * size * lean), (0.85 * size * f, 0.58 * size * lean)])
        rib(s, m, pts, list(np.linspace(z, z + 0.25 * size, 5)), w=0.13 * size + 0.12, thin=0.45, ends=(0.0, 0.32), k=k,
            wkeys=[(0, 0.9), (0.4, 1.0), (1, 0.6)], twist=[(0, 0), (1, 0.9 * lean)])


def volute(s, m, st, start, centre, r0=None, cw=1, w=1.2, z=0.0, kind="garnet", turns=1.0):
    st_ = np.asarray(start, float); C = np.asarray(centre, float); R0 = np.linalg.norm(st_ - C)
    K.scroll(s, start, centre, r0 or R0 * 0.22, turns=turns, cw=cw, w=w, z=z, rise=R0 * 0.15, m=m)
    if kind:
        d = max(1.2, min(3.4, R0 * 0.75))
        bead(s, m, st, (C[0] + (st_[0] - C[0]) * 0.08, C[1] + (st_[1] - C[1]) * 0.08), d, kind, z=z + R0 * 0.15 + d * 0.3)


# ------------------------------------------------------------------ forms
def crescent(s, m, st, c, R, ang=math.pi / 2, w=None, kinds=("londonblue", "aquamarine", "garnet"), z=0.0, span=1.62, n=3, horn_curl=0.25):
    """A liquid crescent: belly swelling, horns drawn into needles that curl inward; graduated
    stones sit along the inside of the belly."""
    w = w or R * 0.2
    a = np.linspace(ang - span / 2 * math.pi, ang + span / 2 * math.pi, 40)
    rr = R * (1 - horn_curl * np.abs(np.linspace(-1, 1, 40)) ** 3)
    pts = np.stack([c[0] + rr * np.cos(a), c[1] + rr * np.sin(a)], 1)
    zz = z + R * 0.12 * np.cos(np.linspace(-1, 1, 40) * math.pi / 2)
    cc, W, _ = rib(s, m, pts, zz, w=w, thin=0.4, ends=(0.32, 0.32), wkeys=[(0, 0.3), (0.5, 1.0), (1, 0.3)],
                   twist=[(0, -0.5), (0.5, 0.0), (1, 0.5)])
    mid = ang  # the belly
    out = []
    for i in range(n):
        f = (i - (n - 1) / 2) / max(1, (n - 1) / 2)
        d = R * (0.42 - 0.12 * abs(f)) if n > 1 else R * 0.55
        aa = mid + f * 0.3 * math.pi * (1 if n > 1 else 0)
        rad = R - w * 0.55 - d * 0.36
        p = (c[0] + rad * math.cos(aa), c[1] + rad * math.sin(aa))
        bead(s, m, st, p, d, kinds[i % len(kinds)], z=z + R * 0.1 + d * 0.3)
        out.append(p)
    return out


def loop(cx, cy, L, H, ang, n=26):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = L * (1 - np.cos(t)) / 2; y = H * np.sin(t) * (1 - np.cos(t)) / 2 * 0.9
    c, s_ = math.cos(ang), math.sin(ang)
    return np.stack([cx + c * x - s_ * y, cy + s_ * x + c * y], 1)


def rose(s, m, st, c, R, n=6, kinds=("londonblue", "aquamarine"), centre="garnet", z=0.0, swirl=0.35, w=None):
    """Spokeless rose: pear stones each held in a liquid loop springing from a centre bead."""
    w = w or max(0.32, R * 0.075)
    for i in range(n):
        a = 2 * math.pi * i / n + math.pi / 2
        p0 = (c[0] + R * 0.18 * math.cos(a), c[1] + R * 0.18 * math.sin(a))
        o = loop(p0[0], p0[1], R * 0.85, R * 0.62, a + swirl)
        o = np.vstack([o, o[:1]])
        K.ribbon(s, np.column_stack([o, np.full(len(o), z) + 0.15 * R * np.sin(np.linspace(0, math.pi, len(o)))]), m=m,
                 w=w, thin=0.6, ends=(0, 0), k=0.25)
        cc = o[:-1].mean(0)
        L = max(1.5, round(R * 0.5 * 2) / 2); Wd = max(1.0, round(R * 0.32 * 2) / 2)
        pane(s, Flat(o=m.P(0, 0, z)) if isinstance(m, Flat) else m, st, (cc[0], cc[1]), "pear", L, Wd,
             kinds[i % len(kinds)], ang=a + swirl + math.pi, vein=max(0.2, w * 0.7))
    bead(s, m, st, tuple(c), max(1.2, R * 0.42), centre, z=z + R * 0.2)


def lancet(s, m, st, base, hw, h, kind="amethyst", z=0.0, w=None, cusps=True, grain=True, feet=True, apex_bead=None):
    """Gothic lancet: two liquid sides bow out from pinched feet, cross at the apex into needles;
    a marquise glows inside; cusps on the inner edge; milgrain along the outside."""
    w = w or max(0.35, hw * 0.13)
    bx, by = base
    for sd in (1, -1):
        pts = [(bx + sd * hw * 0.5, by), (bx + sd * hw * 0.95, by + h * 0.18), (bx + sd * hw, by + h * 0.42),
               (bx + sd * hw * 0.7, by + h * 0.72), (bx + sd * hw * 0.18, by + h * 0.94), (bx - sd * hw * 0.22, by + h * 1.06),
               (bx - sd * hw * 0.42, by + h * 1.18)]
        zz = [z, z + 0.1 * h, z + 0.12 * h, z + 0.12 * h, z + 0.1 * h + 0.03 * h * sd, z + 0.1 * h + 0.06 * h * sd, z + 0.1 * h + 0.06 * h * sd]
        c, W, _ = rib(s, m, pts, zz, w=w, thin=0.6, ends=(0.0, 0.14), wkeys=[(0, 0.8), (0.3, 1.0), (0.85, 0.8), (1, 0.6)],
                      twist=[(0, 0), (1, 0.4 * sd)])
        if feet:
            f = [(bx + sd * hw * 0.5, by), (bx + sd * hw * 0.42, by - h * 0.1), (bx + sd * hw * 0.8, by - h * 0.17), (bx + sd * hw * 1.15, by - h * 0.12)]
            rib(s, m, f, [z, z, z + 0.02 * h, z + 0.05 * h], w=w * 0.9, thin=0.6, ends=(0.0, 0.4), wkeys=[(0, 1.0), (1, 0.6)])
        if cusps:
            q = np.array([bx + sd * hw * 0.84, by + h * 0.5]); dd = np.array([-sd, -0.4]); dd /= np.linalg.norm(dd)
            rib(s, m, [q, q + dd * hw * 0.2, q + dd * hw * 0.4], z + 0.12 * h, w=w * 0.65, thin=0.7, ends=(0.0, 0.6),
                wkeys=[(0, 1.0), (1, 0.6)])
        if grain:
            c2 = resample(smooth(pts, 10), 0.18)[:, :2]; u = np.linspace(0, 1, len(c2)); keep = (u > 0.05) & (u < 0.8)
            t2 = np.gradient(c2, axis=0); t2 /= np.linalg.norm(t2, axis=1)[:, None]
            nO = np.stack([t2[:, 1], -t2[:, 0]], 1) * sd
            edge = c2[keep] + nO[keep] * (w * 0.9)
            milgrain(s, m, edge[::3], d=max(0.35, w * 0.4), z=z + 0.1 * h)
    pane(s, m, st, (bx, by + h * 0.45), "marquise", round(h * 0.42 * 2) / 2, round(hw * 0.9 * 2) / 2, kind, ang=math.pi / 2, vein=w * 0.7)
    if apex_bead:
        bead(s, m, st, (bx, by + h * 1.0), max(1.2, hw * 0.4), apex_bead, z=z + 0.12 * h + 0.6)
    return (bx, by + h * 1.18)


def feather(s, m, root, ang, L, wmax, z=0.0, bend=0.12, rise=0.6, k=0.3):
    """moiraxmel feather: lens blade, fine barbs angled off a raised polished spine."""
    d = np.array([math.cos(ang), math.sin(ang)]); n = np.array([-d[1], d[0]])
    r = np.asarray(root, float)
    c = smooth([r, r + d * L * 0.35 + n * L * bend * 0.6, r + d * L * 0.7 + n * L * bend, r + d * L + n * L * bend * 0.6], 12)
    c = resample(c, 0.15); u = arclen(c); u = u / u[-1]
    W = TIP + (wmax - TIP) * np.sin(np.clip(u, 0, 1) * math.pi) ** 0.6 * (1 - 0.35 * u)
    zz = z + rise * np.sin(math.pi * u * 0.8)
    P = np.array([m.P(x, y, zv) for (x, y, _), zv in zip(c, zz)]); N = np.array([m.N(x, y) for x, y, _ in c])
    T = np.maximum(W * 0.22, np.minimum(W, 0.34))
    blade(s, P, W, T, normal=N, k=k, grooves=max(6, int(L / 0.32)), both=True, gr=min(0.065, wmax * 0.03 + 0.02), barb=0.9, groove_span=(0.04, 0.96))
    q = np.array([m.P(x, y, zv) + m.N(x, y) * (Tv * 0.75) for (x, y, _), zv, Tv in zip(c, zz, T)])
    s.stroke(q[2:-3], np.linspace(max(0.08, wmax * 0.07), 0.05, len(q) - 5), k=0.1)
    return c[:, :2]


def split_wing(s, m, st, root, ang, L, z=0.0, kind="garnet", gap=0.35):
    """Two feathers split from one root, a bead holding the split."""
    feather(s, m, root, ang + gap, L, L * 0.13, z=z + 0.4, bend=0.1)
    feather(s, m, root, ang - gap * 0.7, L * 0.78, L * 0.11, z=z, bend=-0.08)
    bead(s, m, st, tuple(root), max(1.2, L * 0.13), kind, z=z + L * 0.08)


def drop(s, m, st, head, direction, r, L, kind="garnet", z=0.0, curl=0.7):
    """Liquid teardrop with a stone set in its head."""
    K.drop(s, head, direction, r, L, curl=curl, z=z, m=m)
    if kind:
        bead(s, m, st, tuple(head), r * 1.25, kind, z=z + r * 0.78)


def cage(s, m, st, c, R, H, kind="garnet", n=5, w=None, z=0.0, needle=True):
    """A cage of bowed liquid ribbons around a round stone; knot at the top, needle below."""
    w = w or max(0.28, R * 0.16)
    c = np.asarray(c, float)
    zc = z + R
    for i in range(n):
        a = math.pi * (0.1 + 0.8 * i / max(1, n - 1))
        t = np.linspace(0, 1, 9)
        x = c[0] + np.sin(math.pi * t) * R * 1.05 * math.cos(a)
        y = c[1] + H / 2 - H * t
        zz = zc - R * 0.2 + np.sin(math.pi * t) * R * 1.05 * math.sin(a)
        K.ribbon(s, np.column_stack([x, y, zz]), m=m, w=w, thin=0.55, ends=(0.0, 0.0), k=0.2,
                 wkeys=[(0, 0.7), (0.5, 1.0), (1, 0.7)], twist=[(0, 0), (1, 0)])
    s.sphere(m.P(c[0], c[1] + H / 2, zc - R * 0.2), w * 1.8, k=0.3)
    if needle:
        rib(s, m, [(c[0], c[1] - H / 2), (c[0] + R * 0.2, c[1] - H / 2 - R * 0.8), (c[0] - R * 0.1, c[1] - H / 2 - R * 1.7)],
            [zc - R * 0.2, zc - R * 0.3, zc - R * 0.4], w=w * 1.5, thin=0.6, ends=(0.0, 0.7), wkeys=[(0, 1.0), (1, 0.5)])
    st_kind = kind
    bead(s, m, st, tuple(c), R * 1.7, st_kind, z=zc)
    return (c[0], c[1] + H / 2)


def vertebrae(s, m, st, pts2, n, size, kinds=("londonblue", "aquamarine"), z=0.0, w=None):
    """A hyodomachine spine: a liquid stem with paired hooked wings at each vertebra and a bead
    on every joint."""
    c = smooth(pts2, 10); c = resample(c, 0.2); u = arclen(c); u /= u[-1]
    w = w or size * 0.12
    rib(s, m, c[:, :2], z, w=w, thin=0.6, ends=(0.08, 0.15), wkeys=[(0, 0.8), (1, 0.6)])
    for i in range(n):
        f = (i + 0.5) / n; j = int(f * (len(c) - 1)); p = c[j, :2]
        t = c[min(j + 2, len(c) - 1), :2] - c[max(j - 2, 0), :2]; t /= np.linalg.norm(t); nn = np.array([-t[1], t[0]])
        g = 1.0 - 0.3 * f
        for sd in (1, -1):
            q = [p, p + nn * sd * size * 0.45 * g - t * size * 0.05, p + nn * sd * size * 0.8 * g + t * size * 0.25 * g,
                 p + nn * sd * size * 0.7 * g + t * size * 0.55 * g]
            rib(s, m, q, [z, z + 0.15 * size, z + 0.25 * size, z + 0.3 * size], w=w * 1.3 * g, thin=0.45, ends=(0.0, 0.45),
                wkeys=[(0, 0.9), (0.4, 1.0), (1, 0.6)], twist=[(0, 0), (1, 0.8 * sd)])
        bead(s, m, st, tuple(p), size * 0.42 * g, kinds[i % len(kinds)], z=z + size * 0.2)


def moth(s, m, st, c, size, ang=math.pi / 2, z=0.0, kind="moonstone"):
    """A small moth: engraved feather wings, a liquid body, hooked antennae."""
    c = np.asarray(c, float); d = np.array([math.cos(ang), math.sin(ang)]); nn = np.array([-d[1], d[0]])
    for sd in (1, -1):
        a = ang + sd * (math.pi / 2 - 0.35)
        feather(s, m, c + d * size * 0.12, a, size * 0.95, size * 0.2, z=z + 0.3, bend=0.18 * -sd, rise=0.3)
        a2 = ang + sd * (math.pi / 2 + 0.55)
        feather(s, m, c - d * size * 0.08, a2, size * 0.62, size * 0.15, z=z + 0.1, bend=0.12 * -sd, rise=0.2)
        ant = [c + d * size * 0.32, c + d * size * 0.62 + nn * sd * size * 0.12, c + d * size * 0.78 + nn * sd * size * 0.32,
               c + d * size * 0.7 + nn * sd * size * 0.42]
        rib(s, m, ant, z + size * 0.12, w=size * 0.04 + 0.1, thin=0.7, ends=(0.0, 0.0), wkeys=[(0, 1.0), (1, 0.8)])
        s.sphere(m.P(*ant[-1], z + size * 0.12), size * 0.05 + 0.15, k=0.2)
    body = [c + d * size * 0.34, c, c - d * size * 0.45]
    rib(s, m, body, [z + size * 0.15, z + size * 0.2, z + size * 0.1], w=size * 0.1, thin=0.9, ends=(0.0, 0.5), wkeys=[(0, 0.8), (0.3, 1.0), (1, 0.7)])
    bead(s, m, st, tuple(c + d * size * 0.34), size * 0.2, kind, z=z + size * 0.22)


def beadcurl(s, m, st, c, R, kind="garnet", ang=0.0, cd=1, z=0.0):
    """A small curl of liquid metal with a bead in its counter (c09)."""
    o = np.asarray(c, float) - rot(np.array([0.74 * R * 2.2, 0.0]), ang)
    return hook(s, m, st, o, ang, R * 2.2, cd=cd, kind=kind, z=z, rise=R * 0.25)
