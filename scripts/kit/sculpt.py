"""sculpt kit: sculptural forms instead of tubes.
ribbon  - a liquid chrome ribbon (lens section) that swells, twists in 3D and ends in needles
drop    - a liquid teardrop: heavy round head pulled into a whipped tail
scroll  - a Baroque C/S scroll: ribbon tightening into a volute, bead held in the eye
arch    - a Gothic lancet: pointed arch ribbon with cusps on the inner edge and a finial
All coordinates are in the buckle plane (x, y) with z up out of the face."""
import math
import os
import numpy as np
from sdf import resample, arclen, tangents, catmull, profile

TIP = 0.1


def _curve(pts, step=0.18, closed=False):
    p = np.asarray(pts, float)
    if p.shape[1] == 2: p = np.column_stack([p, np.zeros(len(p))])
    c = catmull(p, 14, closed) if len(p) > 2 else p
    return resample(c, step)


def ribbon(s, pts, w=2.0, wkeys=None, thin=0.32, twist=None, z=None, ends=(0.12, 0.18), k=0.3, round_ends=(False, False),
           tip=TIP, flat_max=6.0, m=None):
    """pts: 2D or 3D control points (z from the 3rd column, or from z keys [(u, z)]).
    w = max half width; wkeys = [(u, f)] width profile; thin = thickness/width ratio (lens);
    twist = [(u, radians)] rotation of the ribbon face about its own tangent (0 = face up).
    ends: fraction of length over which each end draws out into a needle."""
    c = _curve(pts)
    u = arclen(c); u = u / u[-1]
    if z is not None: c[:, 2] = profile(u, z)
    W = w * (profile(u, wkeys) if wkeys else np.ones(len(u)))
    t0, t1 = ends
    if t0 > 0 and not round_ends[0]:
        f = np.clip(u / t0, 0, 1); W = tip + (W - tip) * (1 - (1 - f) ** 2.2)
    if t1 > 0 and not round_ends[1]:
        f = np.clip((1 - u) / t1, 0, 1); W = tip + (W - tip) * (1 - (1 - f) ** 2.2)
    T = np.maximum(W * thin, np.minimum(W, float(os.environ.get("TFLOOR", 0.36))))   # TFLOOR: raise to 0.45 for small or many-piece runs (casting p5 >= 0.8 mm)
    ups = None
    if m is not None:
        ups = np.array([m.N(x, y) for x, y, _ in c])
        c = np.array([m.P(x, y, zz) for x, y, zz in c])
    tg = tangents(c)
    tw = profile(u, twist) if twist else np.zeros(len(u))
    N = []
    for i, (t, a) in enumerate(zip(tg, tw)):
        up = ups[i] if ups is not None else np.array([0, 0, 1.0])
        n0 = up - t * (up @ t); n0 /= max(np.linalg.norm(n0), 1e-6)
        b = np.cross(t, n0)
        N.append(n0 * math.cos(a) + b * math.sin(a))
    N = np.array(N)
    for i in range(len(c) - 1):
        r1, r2 = W[i], W[i + 1]
        fl = min(flat_max, max(1.0, 0.5 * (r1 / T[i] + r2 / T[i + 1])))
        s.cone(c[i], c[i + 1], r1, r2, k=(k if i == 0 else 0.0), flat=fl, zhint=(N[i] + N[i + 1]) / 2)
    return c, W, N


def drop(s, head, direction, r, L, curl=0.6, z=0.0, k=0.9, tail_w=None, m=None):
    """Liquid teardrop: sphere head, tail whipping off along direction and curling to a point."""
    d = np.asarray(direction, float); d /= np.linalg.norm(d); n = np.array([-d[1], d[0]])
    h = np.asarray(head, float)
    pts = [h, h + d * L * 0.35 + n * curl * L * 0.05, h + d * L * 0.7 + n * curl * L * 0.18, h + d * L + n * curl * L * 0.45]
    P = np.column_stack([np.array(pts), np.full(4, z)])
    c = _curve(P, 0.15); u = arclen(c); u = u / u[-1]
    W = TIP + (r * 0.92 - TIP) * (1 - u) ** 1.7
    if m is not None: c = np.array([m.P(x, y, zz) for x, y, zz in c])
    for i in range(len(c) - 1):
        s.cone(c[i], c[i + 1], W[i], W[i + 1], k=0.0)
    s.sphere(np.array([h[0], h[1], z]) if m is None else m.P(h[0], h[1], z), r, k=k)
    return c


def scroll(s, start, centre, r0, turns=1.1, cw=1, w=1.2, z=0.0, rise=0.8, wk_end=0.55, k=0.3, eye=True, m=None):
    """Baroque volute: from start, spiral into centre tightening to r0 at the eye."""
    st = np.asarray(start, float); C = np.asarray(centre, float)
    a0 = math.atan2(st[1] - C[1], st[0] - C[0]); R0 = np.linalg.norm(st - C)
    th = np.linspace(0, 1, 60)
    a = a0 + cw * turns * 2 * math.pi * th
    rr = R0 + (r0 - R0) * th ** 0.75
    pts = np.stack([C[0] + rr * np.cos(a), C[1] + rr * np.sin(a), z + rise * np.sin(math.pi * th * 0.8)], 1)
    c, W, N = ribbon(s, pts, w=w, wkeys=[(0, 1.0), (0.5, 0.85), (1, wk_end)], thin=0.45, ends=(0.0, 0.0), k=k, m=m)
    if eye:
        s.sphere(c[-1], W[-1] * 1.05, k=0.2)
    return c, W


def lancet_arch(cx, base_y, half_w, h, n=60):
    """Pointed (Gothic) arch outline: two arcs meeting at the apex, plus the jambs down to base."""
    R = (half_w ** 2 + (h * 0.55) ** 2) / (2 * half_w) * 1.0
    spring = base_y + h * 0.45
    apex = np.array([cx, base_y + h])
    # right arc centred at (cx + half_w - R, spring)
    cr = np.array([cx + half_w - R, spring])
    a_top = math.atan2(apex[1] - cr[1], apex[0] - cr[0])
    ar = np.linspace(0, a_top, n // 2)
    right = np.stack([cr[0] + R * np.cos(ar), cr[1] + R * np.sin(ar)], 1)
    cl = np.array([cx - half_w + R, spring])
    al = np.linspace(math.pi - a_top, math.pi, n // 2)
    left = np.stack([cl[0] + R * np.cos(al), cl[1] + R * np.sin(al)], 1)
    jr = np.array([[cx + half_w, base_y + (spring - base_y) * f] for f in np.linspace(0, 1, 6)[:-1]])
    jl = np.array([[cx - half_w, spring - (spring - base_y) * f] for f in np.linspace(0, 1, 6)[1:]])
    return np.vstack([jr, right, left[1:], jl]), apex, (cr, cl, R, spring)


def cusp(s, p, d, L, w=0.5, z=0.0):
    """A Gothic cusp: a small horn growing off the arch's inner edge into a point."""
    p = np.asarray(p, float); d = np.asarray(d, float); d /= np.linalg.norm(d)
    q = np.array([p, p + d * L * 0.5, p + d * L])
    P = np.column_stack([q, np.full(3, z)])
    for i in range(2):
        s.cone(P[i], P[i + 1], [w, w * 0.55, TIP][i], [w, w * 0.55, TIP][i + 1], k=0.25 if i == 0 else 0.0)
