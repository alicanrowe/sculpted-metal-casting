"""Developed pieces: the client's favourites taken to finished-jewel detail.
Engraved barbs on every wide stroke, milgrain edges, acanthus chasing at joints and finials,
hyodomachine hooks that swell, lift and split into needle points; true points throughout."""
import math
import numpy as np
from sdf import Scene
from kit import *   # noqa
from detail import milgrain, acanthus, hook
from glass64 import F, mirror

PIECES = {}


def piece(kind):
    def deco(fn):
        PIECES[fn.__name__] = (fn, kind); return fn
    return deco


def loop(cx, cy, L, H, ang, n=26):
    """Teardrop loop starting at (cx, cy), pointing along ang."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = L * (1 - np.cos(t)) / 2; y = H * np.sin(t) * (1 - np.cos(t)) / 2 * 0.9
    c, s_ = math.cos(ang), math.sin(ang)
    return np.stack([cx + c * x - s_ * y, cy + s_ * x + c * y], 1)


def rosette(s, m, st, cx, cy, R, n=7, kinds=("londonblue", "aquamarine"), w=0.55, centre="londonblue", z=0.0, swirl=0.35):
    """A rose window with no rim and no spokes: pear petals each held in its own curved loop,
    the loops springing from the centre stone and leaning with a slight swirl, open between."""
    mm = Flat(o=m.P(0, 0, z) if hasattr(m, "P") else (0, 0, z))
    thorns(s, mm, st, (cx, cy), R * 0.36, centre, n=4, reach=(0.6, 0.9), wire=0.32, seed=3)
    for i in range(n):
        a = 2 * math.pi * i / n + math.pi / 2
        p0 = (cx + R * 0.2 * math.cos(a), cy + R * 0.2 * math.sin(a))
        o = loop(p0[0], p0[1], R * 0.85, R * 0.62, a + swirl)
        nib(s, mm, o, w=w, closed=True, pen=a, hair=0.35, taper=(0, 0), mitre=False)
        c = o.mean(0)
        pane(s, mm, st, (c[0], c[1]), "pear", round(R * 0.5 * 2) / 2, round(R * 0.32 * 2) / 2, kinds[i % len(kinds)], ang=a + swirl + math.pi, vein=0.3)


def _x_b14_rose_lancet_v1():
    """Rose Lancet, developed. Two calligraphic strokes rise from hooked feet, bow outward and
    cross at the top into a pair of needle points; between them a spokeless rose floats on
    hairline tendrils, two pear drops hanging from it. Lots of air; light even engraving."""
    from sdf import profile
    s = Scene(); st = []
    y0, H = -24, 46
    RISE = [(0, 0.0), (0.35, 1.6), (0.8, 3.2), (1, 3.4)]
    arch = {}
    for sx in (1, -1):
        pts = [(sx * 24.5, y0 - 2.5), (sx * 26.5, y0 - 8.5), (sx * 21.0, y0 - 11.0), (sx * 15.5, y0 - 5.0),
               (sx * 15.8, y0 + 8), (sx * 15.0, y0 + 20), (sx * 10.5, y0 + 32), (sx * 3.5, y0 + 41),
               (-sx * 1.2, y0 + H), (-sx * 2.6, y0 + H + 7.5)]
        c, W = nib(s, F, pts, w=1.6, pen=0.35 * sx, hair=0.25, thick=0.8, taper=(0.12, 0.16), engrave=1.05, mitre=False,
                   rise=RISE)
        u = np.linspace(0, 1, len(c)); arch[sx] = (c, profile(u, RISE))
        bz = 1.45; s.cone(F.P(sx * 21.4, y0 - 6.2, bz - 1.9), F.P(sx * 21.4, y0 - 6.2, bz - 0.55), 0.55, 1.3, k=0.3)  # cup body under the bead
        bead(s, F, st, (sx * 21.4, y0 - 6.2), 3.0, "garnet", z=bz)
        nib(s, F, [(sx * 21.4, y0 - 6.2), (sx * 20.6, y0 - 8.4), (sx * 21.0, y0 - 10.6)], w=0.7, hair=0.6, taper=(0, 0), z=-0.6, mitre=False)
        # one wisp grows tangentially off each leg and curls back on itself into a needle
        j = int(0.40 * len(c)); p = c[j]; zp = arch[sx][1][j]
        t = c[j + 3] - c[j - 3]; t = t / np.linalg.norm(t); n = np.array([sx * 1.0, 0.0])
        n = n - t * (n @ t); n = n / np.linalg.norm(n)
        wp = [p + n * 0.4, p + n * 2.2 + t * 2.5, p + n * 5.2 + t * 6.5, p + n * 5.6 + t * 10.5,
              p + n * 3.6 + t * 12.6, p + n * 2.2 + t * 11.4]
        nib(s, F, [tuple(q) for q in wp], w=0.7, pen=0.6 * sx, hair=0.35, taper=(0.15, 0.7), z=zp,
            rise=[(0, 0.0), (0.6, 1.4), (1, 1.6)], mitre=False)
    # the rose floats in the head, raised to the arch's height there
    rc = (0, 5.5); rz = 2.6
    rosette(s, F, st, rc[0], rc[1], 8.0, n=7, kinds=("londonblue", "aquamarine", "topaz"), w=0.72, z=rz)
    # hairline tendrils tie the rose to the arch: from the rose's edge to the nearest arch point
    for sx in (1, -1):
        c, zz = arch[sx]
        for ang, bend in ((0.35, 1.0), (-0.45, -1.0)):
            a0 = (0 if sx > 0 else math.pi) + ang * sx
            p0 = np.array([rc[0] + 8.3 * math.cos(a0), rc[1] + 8.3 * math.sin(a0)])
            j = int(np.argmin(np.linalg.norm(c - p0, axis=1))); p1 = c[j]
            mid = (p0 + p1) / 2 + np.array([0, 2.2 * bend])
            nib(s, F, [tuple(p0), tuple(mid), tuple(p1)], w=0.5, pen=1.57, hair=0.5, taper=(0, 0), z=rz,
                rise=[(0, 0.0), (1, zz[j] - rz)], mitre=False)
        # a pear drop hangs from the rose on a curved stem
        top = np.array([sx * 2.5, rc[1] - 8.0])
        stem = [tuple(top), (sx * 4.5, top[1] - 3.5), (sx * 4.0, top[1] - 6.5)]
        nib(s, F, stem, w=0.5, pen=0.0, hair=0.6, taper=(0, 0), z=rz, rise=[(0, 0.0), (1, -1.0)], mitre=False)
        drop = loop(sx * 4.0, top[1] - 6.5, 9.5, 6.0, -math.pi / 2 + sx * 0.1)
        nib(s, F, drop, w=0.48, closed=True, pen=0.0, hair=0.45, taper=(0, 0), z=rz - 1.0, mitre=False)
        cc = drop.mean(0)
        pane(s, Flat(o=(0, 0, rz - 1.0)), st, (cc[0], cc[1]), "pear", 6, 4, ["garnet", "amethyst"][sx > 0], ang=math.pi / 2 - sx * 0.1, vein=0.3)
    # belt hardware hidden behind the legs, not floating in the openings
    N = np.array([0, 0, 1.0])
    p = F.P(-15.6, -10, -0.6); s.cone(p, p - N * 4.0, 1.1, 0.9, k=0.6); s.sphere(p - N * 4.2, 1.4, k=0.4)
    for yy in (-16, -3):
        q = F.P(15.6, yy, -0.5); s.cone(q, q - N * 3.5, 1.0, 0.9, k=0.5)
    s.cone(F.P(15.6, -16, -4.0), F.P(15.6, -3, -4.0), 0.9, 0.9, k=0.5)
    return s, st



def feather(s, m, root, ang, L, wmax, z=0.0, bend=0.12, rise=0.6, barbs=None, k=0.3):
    """A moiraxmel feather blade: lens-shaped, flat, finely engraved barbs angled off a raised
    polished spine, tip drawn out to a point."""
    from sdf import resample, arclen
    from v2 import blade
    d = np.array([math.cos(ang), math.sin(ang)]); n = np.array([-d[1], d[0]])
    r = np.asarray(root, float)
    c = smooth([r, r + d * L * 0.35 + n * L * bend * 0.6, r + d * L * 0.7 + n * L * bend, r + d * L + n * L * bend * 0.6], 12)
    c = resample(c, 0.15); u = arclen(c); u = u / u[-1]
    W = TIP + (wmax - TIP) * np.sin(np.clip(u, 0, 1) * math.pi) ** 0.6 * (1 - 0.35 * u)
    zz = z + rise * np.sin(math.pi * u * 0.8)
    P = np.array([m.P(x, y, zv) for (x, y, _), zv in zip(c, zz)]); N = np.array([m.N(x, y) for x, y, _ in c])
    T = np.maximum(W * 0.22, np.minimum(W, 0.34))
    ng = barbs or int(L / 0.32)
    blade(s, P, W, T, normal=N, k=k, grooves=ng, both=True, gr=0.065, barb=0.9, groove_span=(0.04, 0.96))
    # the polished quill, standing proud of the barbs
    q = np.array([m.P(x, y, zv) + m.N(x, y) * (Tv * 0.75) for (x, y, _), zv, Tv in zip(c, zz, T)])
    s.stroke(q[2:-3], np.linspace(0.16, 0.06, len(q) - 5), k=0.1)
    return c[:, :2]


def _x_b14_rose_lancet_v3():
    """Rose Lancet. Two liquid chrome strokes rise from spiral hooks (a garnet held in each hook's
    counter), each throwing a spur off its belly, and cross at the top, one over the other, under a
    garnet knot and a chased acanthus. The rose sits where the strokes converge; two engraved
    feathers hang from it, one over the other. Strokes plain polished, ornament in clusters."""
    from sdf import profile
    s = Scene(); st = []
    RISE = [(0, 0.0), (0.3, 0.9), (0.62, 2.4), (0.84, 3.2), (1, 3.3)]
    WK = [(0, 0.7), (0.1, 0.9), (0.2, 0.6), (0.38, 1.05), (0.56, 0.9), (0.8, 0.45), (0.9, 0.42), (1, 0.55)]
    legs = {}
    for sx in (1, -1):
        C = np.array([sx * 20.6, -30.0])
        th = np.linspace(math.pi, 2 * math.pi + 0.75, 46)
        r = 5.2 - 2.1 * ((th - math.pi) / (math.pi + 0.75)) ** 1.6   # tightening spiral: tight head, long tail
        hk = np.stack([C[0] + sx * (-1) * r * np.cos(th) * -1 if False else C[0] + r * np.cos(th) * (1 if sx > 0 else -1) * 1.0,
                       C[1] + r * np.sin(th)], 1)
        hk[:, 0] = C[0] + sx * r * np.cos(th)
        up = [(sx * 15.45, -24.0), (sx * 15.8, -16.0), (sx * 15.2, -5.0), (sx * 11.6, 6.5), (sx * 5.5, 16.5),
              (sx * 0.0, 21.5), (-sx * 3.0, 25.0), (-sx * 4.6, 31.5)]
        pts = np.vstack([hk[::-1], np.array(up)])
        over = 0.9 if sx > 0 else -0.6
        rise = RISE + [(0.9, 3.25 + over), (0.95, 3.3 + over * 0.6)]
        rise = sorted(rise)
        c, W = nib(s, F, [tuple(p) for p in pts], w=1.9, pen=0.35 * sx, hair=0.42, thick=0.85, taper=(0.07, 0.12),
                   wkeys=WK, mitre=False, rise=rise)
        u = np.linspace(0, 1, len(c)); zc = profile(u, rise); legs[sx] = (c, W, zc)
        # garnet held in the hook's counter, seated against the stroke
        j = int(np.argmin(c[: len(c) // 3, 1])); nrm = C - c[j]; nrm /= np.linalg.norm(nrm)
        bc = c[j] + nrm * (W[j] + 1.45); bz = zc[j] + 1.1
        s.cone(F.P(bc[0], bc[1], bz - 1.7), F.P((bc[0] + c[j][0]) / 2, (bc[1] + c[j][1]) / 2, bz - 1.4), 0.9, 0.9, k=0.5)
        s.cone(F.P(bc[0], bc[1], bz - 1.9), F.P(bc[0], bc[1], bz - 0.5), 0.6, 1.3, k=0.3)
        bead(s, F, st, tuple(bc), 3.2, "garnet", z=bz)
        # a spur peels off the belly and flicks outward into a needle
        j = int(0.40 * len(c)); p = c[j]; t = c[j + 4] - c[j - 4]; t /= np.linalg.norm(t)
        n = np.array([sx, 0.0]); n = n - t * (n @ t); n /= np.linalg.norm(n)
        sp = [p - t * 2.0, p + t * 1.2 + n * 0.6, p + t * 4.0 + n * 2.4, p + t * 6.0 + n * 5.0, p + t * 6.0 + n * 7.6]
        nib(s, F, [tuple(q) for q in sp], w=1.55, pen=0.35 * sx, hair=0.5, thick=0.8, taper=(0.0, 0.6),
            wkeys=[(0, 0.9), (0.3, 0.85), (1, 0.6)], z=zc[j], rise=[(0, 0.0), (1, 1.2)], mitre=False)
    # the crossing: garnet knot on the join, acanthus chased below it
    X = np.array([0.0, 21.4]); xz = 3.3 + 0.9
    bead(s, F, st, tuple(X), 2.8, "garnet", z=xz + 1.0)
    s.cone(F.P(X[0], X[1], xz - 0.6), F.P(X[0], X[1], xz + 0.4), 1.0, 1.3, k=0.4)
    acanthus(s, F, (0.0, 20.2), -math.pi / 2, size=5.0, n=3, z=4.0)
    # the rose sits where the strokes converge
    rc = (0.0, 8.4); rz = 2.9
    rosette(s, F, st, rc[0], rc[1], 7.7, n=7, kinds=("londonblue", "aquamarine", "topaz"), w=0.75, z=rz, swirl=0.3)
    # two engraved feathers hang from the rose, the longer one laid over the shorter
    feather(s, F, (0.6, 1.8), -math.pi / 2 - 0.30, 15.0, 2.0, z=rz - 0.5, bend=-0.10, rise=0.3)
    feather(s, F, (-0.6, 1.6), -math.pi / 2 + 0.16, 19.0, 2.3, z=rz + 0.1, bend=0.08, rise=0.5)
    # belt hardware hidden behind the legs
    N = np.array([0, 0, 1.0])
    p = F.P(-15.7, -14, -0.6); s.cone(p, p - N * 4.0, 1.0, 0.85, k=0.6); s.sphere(p - N * 4.2, 1.3, k=0.4)
    for yy in (-20, -8):
        q = F.P(15.7, yy, -0.5); s.cone(q, q - N * 3.5, 0.95, 0.85, k=0.5)
    s.cone(F.P(15.7, -20, -4.0), F.P(15.7, -8, -4.0), 0.85, 0.85, k=0.5)
    return s, st



@piece("flat")
def x_b14_rose_lancet():
    """Rose Lancet. A Gothic lancet window, off centre, holds a spokeless rose with a liquid garnet
    drop hanging inside it. An Art Nouveau whiplash ribbon wraps the window, swelling and twisting
    as it climbs from a needle at the lower left, over a crown of hooks at the apex, to a Baroque
    volute on the right. The right jamb rolls into its own volute under a chased acanthus; an
    engraved feather lies under the ribbon on the left."""
    import sculpt as K
    s = Scene(); st = []
    cx, by, hw, H = 4.0, -12.0, 9.0, 30.0
    out, apex, (cr, cl, R, spring) = K.lancet_arch(cx, by, hw, H)
    # the window: each side rises from a pinched foot, bows out, and crosses the other at the apex
    sides = {}
    for sd in (1, -1):
        cc = cr if sd > 0 else cl
        a_top = math.atan2(apex[1] - cc[1], (apex[0] - cc[0]))
        a = np.linspace(0 if sd > 0 else math.pi, a_top, 24)
        arc = np.stack([cc[0] + R * np.cos(a), cc[1] + R * np.sin(a)], 1)
        jamb = np.array([[cx + sd * 4.8, by], [cx + sd * 8.4, by + 3.2], [cx + sd * 9.8, by + 7.5], [cx + sd * 9.4, by + 11.2]])
        tang = arc[-1] - arc[-2]; tang /= np.linalg.norm(tang)
        over = [arc[-1] + tang * 2.2, arc[-1] + tang * 4.0 + np.array([sd * 0.6, 0.8])]
        pts = np.vstack([jamb, arc[1:], over])
        zz = np.full(len(pts), 2.0); zz[-2:] += 0.6 * sd
        c, W, N = K.ribbon(s, np.column_stack([pts, zz]), w=1.3, thin=0.6, wkeys=[(0, 0.8), (0.25, 1.0), (0.85, 0.75), (1, 0.6)],
                           ends=(0.0, 0.12), twist=[(0, 0.0), (1, 0.4 * sd)])
        sides[sd] = (c, W)
        # milgrain border along the outer edge (the grill's chased frames)
        u = np.linspace(0, 1, len(c)); keep = (u > 0.04) & (u < 0.86)
        t2 = np.gradient(c[:, :2], axis=0); t2 /= np.linalg.norm(t2, axis=1)[:, None]
        nO = np.stack([t2[:, 1], -t2[:, 0]], 1) * sd
        edge = c[keep, :2] + nO[keep] * (W[keep, None] + 0.12)
        milgrain(s, F, edge[::3], d=0.5, z=2.15)
        # Gothic cusps on the inner edge at the springing and halfway up the arch
        p = np.array([cx + sd * (hw - 0.9), spring + 0.6])
        K.cusp(s, p, (-sd * 1.0, -0.4), 3.0, w=0.75, z=2.0)
        j = int(0.62 * len(c)); q = c[j, :2] - nO[j] * (W[j] * 0.6)
        K.cusp(s, q, -nO[j] + np.array([0, -0.5]), 2.2, w=0.6, z=2.0)
    s.sphere(np.array([apex[0], apex[1] + 0.3, 2.6]), 1.05, k=0.4)
    # the rose in the window, and a liquid garnet drop hanging under it
    rc = (cx, 3.2); rz = 2.2
    rosette(s, F, st, rc[0], rc[1], 6.2, n=7, kinds=("londonblue", "aquamarine", "topaz"), w=0.65, z=rz, swirl=0.35)
    K.drop(s, (cx + 1.0, -8.0), (-0.12, 1.0), 2.3, 6.6, curl=-0.9, z=2.0)
    bead(s, F, st, (cx + 1.0, -8.0), 2.6, "garnet", z=2.0 + 1.75)
    # a crown of two hooks on the apex, the big one breaking right, the small one curling back left
    for pts, w_, zz in (([apex + (0, 2.0), apex + (-1.0, 5.5), apex + (0.8, 9.0), apex + (4.2, 9.8), apex + (5.8, 7.6)], 1.25, (2.8, 3.8)),
                        ([apex + (0.4, 2.6), apex + (1.2, 5.2), apex + (0.2, 7.0), apex + (-2.2, 7.4), apex + (-3.2, 6.0)], 0.8, (2.8, 3.2))):
        K.ribbon(s, np.column_stack([np.array(pts), np.linspace(zz[0], zz[1], 5)]), w=w_, thin=0.45,
                 wkeys=[(0, 0.8), (0.4, 1.0), (1, 0.55)], ends=(0.0, 0.32), twist=[(0, 0.0), (1, 0.9)])
    # the whiplash: needle at lower left, swelling and twisting up and over the window
    wl = [(-26, -29, 0.4), (-22.5, -18, 1.4), (-17.5, -4, 2.6), (-13.5, 9, 3.4), (-7.5, 22, 3.8), (2, 33.5, 4.0),
          (13, 32.5, 3.6), (20.0, 22, 3.2), (19.6, 10.5, 2.8)]
    K.ribbon(s, wl, w=2.7, thin=0.3, wkeys=[(0, 0.35), (0.22, 1.0), (0.42, 0.7), (0.6, 0.4), (0.78, 0.55), (1, 0.7)],
             twist=[(0, 0.1), (0.25, 0.0), (0.45, 1.0), (0.6, 1.45), (0.75, 0.6), (1, 0.0)], ends=(0.2, 0.0), round_ends=(False, True))
    K.scroll(s, (19.6, 10.5), (15.9, 5.6), 1.0, turns=1.05, cw=1, w=1.9, z=2.8, rise=0.6)
    bead(s, F, st, (16.1, 5.8), 2.6, "garnet", z=4.6)
    # right foot rolls out into a volute, acanthus chased at the turn
    K.scroll(s, (cx + 5.6, by), (cx + 9.6, by - 3.4), 0.9, turns=1.0, cw=1, w=1.45, z=2.0, rise=0.5)
    acanthus(s, F, (cx + 6.4, by + 2.2), -0.2, size=4.6, n=3, z=2.7)
    # left jamb pours out into a short whipped tail
    K.ribbon(s, [(cx - 5.6, by + 0.4, 2.0), (cx - 5.4, by - 4.0, 1.6), (cx - 8.5, by - 8.0, 1.0), (cx - 13.0, by - 7.4, 0.8)],
             w=1.25, thin=0.6, wkeys=[(0, 1.0), (0.4, 1.1), (1, 0.7)], ends=(0.0, 0.35))
    # an engraved feather lies under the whiplash, root at the left jamb
    feather(s, F, (cx - 8.6, by + 6.0), math.pi - 0.55, 23.0, 2.7, z=3.4, bend=-0.10, rise=0.6)
    feather(s, F, (cx - 8.4, by + 4.2), math.pi - 0.85, 16.0, 2.2, z=2.7, bend=-0.12, rise=0.4)
    # a hairline peels off the whiplash belly and runs a row of graduated garnets into a curl
    hl = [(-21.6, -15.5, 1.6), (-17.5, -21.5, 1.4), (-10.5, -25.0, 1.3), (-3.5, -25.2, 1.4), (1.2, -22.6, 1.6), (0.6, -19.6, 1.8)]
    c, W, _ = K.ribbon(s, hl, w=0.9, thin=0.45, ends=(0.0, 0.0), wkeys=[(0, 1.3), (0.3, 0.75), (0.7, 0.95), (1, 0.8)],
                       twist=[(0, 0.0), (0.5, 0.9), (1, 0.2)])
    K.drop(s, (1.6, -17.8), (-0.35, -1.0), 1.7, 3.0, curl=0.6, z=1.9)
    u = np.linspace(0, 1, len(c))
    for f, d in ((0.3, 1.5), (0.45, 1.8), (0.6, 2.1), (0.75, 2.4)):
        j = int(f * len(c)); bead(s, F, st, (c[j, 0], c[j, 1]), d, "garnet", z=c[j, 2] + d * 0.45)
    # belt hardware behind the whiplash belly and the right volute
    Nz = np.array([0, 0, 1.0])
    p = np.array([-19.5, -11.0, 1.0]); s.cone(p, p - Nz * 5.0, 1.0, 0.85, k=0.6); s.sphere(p - Nz * 5.2, 1.3, k=0.4)
    for yy in (1.5, 7.5):
        q = np.array([17.2, yy, 2.0]); s.cone(q, q - Nz * 5.0, 0.95, 0.85, k=0.5)
    s.cone(np.array([17.2, 1.5, -3.0]), np.array([17.2, 7.5, -3.0]), 0.85, 0.85, k=0.5)
    return s, st
