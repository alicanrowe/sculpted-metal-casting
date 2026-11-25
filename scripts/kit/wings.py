"""Gem wing: a bug wing whose cells are packed with stones, drawn with hyodomachine flare.
The leading edge is a liquid chrome ribbon that rolls past the root into a hook holding a bead;
hairline veins split the membrane and run out past the margin as needles; stones fill the cells."""
import math
import numpy as np
import sculpt as K
from kit import glaze, bead, smooth, Flat
from sdf import resample, arclen

FORE = [(0, 0), (7, 3.2), (16, 6.2), (25, 8.8), (33, 10.6), (39, 11.4), (42.5, 10.2), (40.5, 6.0), (36, 0.8),
        (30, -3.6), (23, -6.4), (15.5, -7.2), (8.5, -5.6), (3, -2.6)]
HIND = [(0, 0), (8, 1.0), (17, 0.0), (24, -3.4), (27, -8.6), (24, -14.0), (17, -16.4), (9.5, -13.6), (3.5, -7.4)]


def _xf(p, scale, ang, t, flip):
    p = np.asarray(p, float) * scale
    if flip: p = p * [1, -1]
    c, s_ = math.cos(ang), math.sin(ang)
    return p @ np.array([[c, s_], [-s_, c]]) + np.asarray(t, float)


def gem_wing(s, m, st, t=(0, 0), ang=0.0, scale=1.0, flip=False, outline=FORE, pal=("londonblue", "aquamarine", "moonstone"),
             costa_w=1.5, z=0.0, hook=True, bead_kind="garnet", n_veins=4, seed=3, needles=True, sizes=None):
    """Draws one wing; root at t, pointing along ang. Returns (outline poly, root, tip)."""
    o = smooth(_xf(outline, scale, ang, t, flip), 10, closed=True)[:, :2]
    o = resample(np.column_stack([o, np.zeros(len(o))]), 0.25)[:, :2]
    root = np.asarray(t, float)
    tip_i = int(np.argmax(np.linalg.norm(o - root, axis=1)))
    sc = scale
    # leading edge: liquid ribbon from the root to the tip, swelling then drawing out
    lead = o[: tip_i + 1]
    zz = z + 0.9 * sc * np.sin(np.linspace(0, math.pi, len(lead)))
    K.ribbon(s, np.column_stack([lead, zz]), m=m, w=costa_w * sc, thin=0.45, ends=(0.0, 0.12),
             wkeys=[(0, 1.0), (0.3, 0.95), (0.7, 0.6), (1, 0.5)], twist=[(0, 0.0), (0.5, 0.6 if not flip else -0.6), (1, 0.2)])
    # the tip flares past the margin into a needle that curls back
    d = lead[-1] - lead[-4]; d /= np.linalg.norm(d); nn = np.array([-d[1], d[0]]) * (-1 if flip else 1)
    fl = [lead[-3], lead[-1] + d * 2.5 * sc, lead[-1] + d * 4.5 * sc - nn * 1.2 * sc, lead[-1] + d * 5.2 * sc - nn * 3.0 * sc]
    K.ribbon(s, np.column_stack([np.array(fl), np.full(4, z + 0.2)]), m=m, w=costa_w * sc * 0.55, thin=0.5, ends=(0.0, 0.45),
             wkeys=[(0, 1.0), (1, 0.6)])
    # trailing edge: a fine liquid rim
    trail = np.vstack([o[tip_i:], o[:1]])
    K.ribbon(s, np.column_stack([trail, np.full(len(trail), z)]), m=m, w=max(0.36, 0.42 * sc), thin=0.7, ends=(0.0, 0.0), k=0.2)
    # veins from the root out to the margin, each breaking through as a needle
    blocked = []
    rim = o[tip_i + 3: len(o) - 6]
    picks = [rim[int(f * (len(rim) - 1))] for f in np.linspace(0.08, 0.78, n_veins)]
    for j, e in enumerate(picks):
        a = root + (lead[int(len(lead) * (0.18 + 0.1 * j))] - root) * 0.6
        bend = nn * 1.3 * sc * (1 if j % 2 else -1)
        v = np.array([a, a * 0.7 + e * 0.3 + bend, a * 0.35 + e * 0.65 + bend * 0.6, e])
        mid = v[2]
        c, W, _ = K.ribbon(s, np.column_stack([v, np.full(4, z + 0.05)]), m=m, w=max(0.3, 0.34 * sc), thin=0.8, ends=(0.0, 0.0), k=0.15)
        vv = resample(smooth(v, 8), 0.25)[:, :2]
        blocked.append((vv, max(0.3, 0.34 * sc) * 1.8))
        if needles:
            dd = e - mid; dd /= np.linalg.norm(dd)
            sd_ = (1 if j % 2 else -1)
            nd = [e - dd * 0.6, e + dd * 2.2 * sc, e + dd * 4.0 * sc + np.array([-dd[1], dd[0]]) * 1.0 * sc * sd_,
                  e + dd * 4.6 * sc + np.array([-dd[1], dd[0]]) * 2.4 * sc * sd_]
            K.ribbon(s, np.column_stack([np.array(nd), np.full(4, z)]), m=m, w=max(0.34, 0.4 * sc), thin=0.6, ends=(0.0, 0.6),
                     wkeys=[(0, 1.0), (1, 0.6)])
    # root rolls into a hook that holds a bead
    if hook:
        b = -d * 0 + (root - lead[6]); b /= np.linalg.norm(b)
        bn = np.array([-b[1], b[0]]) * (-1 if flip else 1)
        C = root + b * 2.6 * sc + bn * 1.4 * sc
        th0 = math.atan2(root[1] - C[1], root[0] - C[0]); sgn = 1 if np.cross(np.append(b, 0), np.append(bn, 0))[2] > 0 else -1
        th = th0 + sgn * np.linspace(0, 1.55 * math.pi, 22)
        rr = np.linalg.norm(root - C) * (1 - 0.35 * np.linspace(0, 1, 22))
        hk = np.stack([C[0] + rr * np.cos(th), C[1] + rr * np.sin(th)], 1)
        c, W, _ = K.ribbon(s, np.column_stack([hk, np.linspace(z, z + 0.8 * sc, 22)]), m=m, w=costa_w * sc * 0.95, thin=0.45,
                           ends=(0.0, 0.0), wkeys=[(0, 1.0), (1, 0.7)])
        s.sphere(c[-1], W[-1], k=0.2)
        if bead_kind:
            bead(s, m, st, (C[0], C[1]), max(1.6, 2.2 * sc + 0.4), bead_kind, z=z + 0.8 * sc + 1.0)
    dmax = np.linalg.norm(o - root, axis=1).max()
    kindf = lambda x, y: pal[min(len(pal) - 1, int(np.hypot(x - root[0], y - root[1]) / dmax * len(pal)))]
    glaze(s, m, st, o, kindf, sizes=sizes, seed=seed, root=root, blocked=blocked,
          margin=float(np.clip(0.75 * sc, 0.3, 0.8)), gap=float(np.clip(0.5 * sc ** 0.5, 0.32, 0.5)), vein=max(0.25, 0.3 * sc))
    return o, root, lead[-1]
