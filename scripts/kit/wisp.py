"""Round 3 style layer (Nov 17): the client: "ours are still robotic while the references are sculptural and wispy".
While ORGANIC is on (see organic()), the shared stroke helpers stop drawing even-width, dead-flat, ruler-straight
lines:
  lead   -> bowed, swelling in the middle and drawing fine toward its ends
  nib    -> width breathes along the stroke (calligraphic swell / thin) and closed rims rise and fall in z
  vein_wing -> veins S-curve and taper to hairlines, fewer cross-veins, leading edge swells hard at the root,
               and one or two hyodomachine wisps (hairline curls ending in a bead) trail off the tips.
Everything is deterministic (seeded from the geometry) so a piece renders the same twice."""
import math
import contextlib
import numpy as np
import kit
import glassB
import glass64
import wings2 as W2
import sculpt as K
import moira as Mo
from kit import smooth
from sdf import resample, arclen, profile

ORGANIC = [False]
WMUL = [1.0]      # line-weight multiplier for vein wings (furniture scale / casting minimums)
_orig = dict(lead=kit.lead, nib=kit.nib, vein_wing=W2.vein_wing)


def _rng(pts, salt=0):
    a = np.asarray(pts, float).ravel()
    return np.random.default_rng(int(abs(a.sum() * 1000.0 + a[:4].prod() * 7.0 + salt)) % (2 ** 31))


def _keys(rng, n, lo, hi, closed):
    v = rng.uniform(lo, hi, n)
    if closed: v[-1] = v[0]
    return [(float(u), float(x)) for u, x in zip(np.linspace(0, 1, n), v)]


def lead(s, m, pts, r=0.42, z=0.05, closed=False, n=8, k=0.3):
    if not ORGANIC[0] or closed:
        return _orig["lead"](s, m, pts, r=r, z=z, closed=closed, n=n, k=k)
    rng = _rng(pts, 1)
    c = smooth(pts, n, False) if len(pts) > 2 else np.column_stack([np.asarray(pts, float)[:, :2], np.zeros(2)])
    c = resample(c, 0.3)
    u = arclen(c); L = max(u[-1], 1e-6); u = u / L
    if len(c) > 3:
        d = c[-1, :2] - c[0, :2]; nn = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-6)
        bow = rng.choice([-1, 1]) * rng.uniform(0.06, 0.16) * L
        c[:, :2] += np.outer(np.sin(math.pi * u) * bow, nn)
    a0_, a1_ = rng.uniform(0.35, 0.6, 2)          # uneven ends: one end fuller than the other
    R = r * (a0_ * (1 - u) + a1_ * u + 1.15 * np.sin(math.pi * u) ** 1.2)
    R = np.maximum(R, 0.4)                        # 0.8 mm casting floor
    zz = z + 0.35 * r * np.sin(math.pi * u)
    s.stroke(np.array([m.P(x, y, zv) for (x, y, _), zv in zip(c, zz)]), R, k=max(k, 0.4))
    return c[:, :2]


def nib(s, m, pts, w=1.0, pen=0.75, hair=0.2, z=0.0, thick=0.62, taper=(0.12, 0.2), tip=None, n=10,
        closed=False, k=0.35, rise=None, wkeys=None, op=0, engrave=0.0, mitre=True):
    if ORGANIC[0] and op == 0:
        rng = _rng(pts, 2)
        if wkeys is None: wkeys = _keys(rng, 9 if closed else 5, 0.42, 1.9, closed)
        # r4-fix3: no automatic rim engraving (regular notches read as bead rows)
        if closed and len(pts) >= 6:
            # hand-cut, not drawn: a slow uneven wobble along the outline so mirrored wings never match exactly
            P = np.asarray(pts, float).copy(); xy = P[:, :2]
            ext = float(np.ptp(xy, axis=0).max())
            tg = np.roll(xy, -1, 0) - np.roll(xy, 1, 0); nn = np.column_stack([-tg[:, 1], tg[:, 0]])
            nn /= np.maximum(np.linalg.norm(nn, axis=1), 1e-9)[:, None]
            ph = rng.uniform(0, 2 * math.pi, 3); tt = np.linspace(0, 2 * math.pi, len(P), endpoint=False)
            wob = sum(a_ * np.sin(f_ * tt + p_) for a_, f_, p_ in zip((0.018, 0.012, 0.006), (2, 3, 5), ph)) * ext
            P[:, :2] = xy + nn * wob[:, None]; pts = P
        if rise is None and closed: rise = _keys(rng, 6, 0.0, 0.9 * w, True)
        k = max(k, 0.45)
    return _orig["nib"](s, m, pts, w=w, pen=pen, hair=hair, z=z, thick=thick, taper=taper, tip=tip, n=n, closed=closed, k=k,
                        rise=rise, wkeys=wkeys, op=op, engrave=engrave, mitre=mitre)


def wisp(s, m, a, d, L, w=0.4, z=0.4, curl=1.0, bead=True, rng=None):
    """hyodomachine hairline: leaves a point along d, curls (total turn ~ curl rad), draws to a needle, ends in a bead."""
    rng = rng or np.random.default_rng(0)
    a = np.asarray(a, float); d = np.asarray(d, float); d = d / max(np.linalg.norm(d), 1e-6)
    n = 14; pts = [a]; ang = math.atan2(d[1], d[0]); step = L / n
    for i in range(n):
        ang += curl / n * (1 + 1.2 * i / n)
        pts.append(pts[-1] + step * np.array([math.cos(ang), math.sin(ang)]))
    P = np.array(pts)
    # hyodomachine: no ball on the end. With bead=True the stroke swells into a drop just before the tip and
    # then draws out to a needle; without it, it simply thins to a needle.
    wk = [(0, 1.0), (0.55, 0.65), (0.82, 1.55), (1, 0.5)] if bead else [(0, 1.0), (0.6, 0.6), (1, 0.45)]
    K.ribbon(s, np.column_stack([P, z + 0.4 * np.sin(np.linspace(0, math.pi, len(P)))]), m=m, w=max(w, 0.42), thin=0.85,
             ends=(0.0, 0.14 if bead else 0.5), wkeys=wk, k=0.3)


def vein_wing(s, m, st, root, span, ang=0.0, sx=1, z=0.0, rng=None, beads=True, kind="moonstone", shape="fore", stones=0,
              pal=("aquamarine", "moonstone")):
    if not ORGANIC[0]:
        return _orig["vein_wing"](s, m, st, root, span, ang=ang, sx=sx, z=z, rng=rng, beads=beads, kind=kind, shape=shape,
                                  stones=stones, pal=pal)
    rng = rng or np.random.default_rng(0)
    place, _poly_at = W2.place, W2._poly_at
    ext = np.asarray(W2._shape(shape), float); sc = span / np.linalg.norm(ext, axis=1).max()
    o = resample(smooth(ext * sc, 10, closed=True), 0.2)[:, :2]
    tip_i = int(np.argmax(np.linalg.norm(o, axis=1)))
    w = max(0.55, span * 0.03) * WMUL[0]      # floors: every vein casts at 0.8 mm or more
    wf = lambda x: max(x, 0.5)
    lead_ = o[:tip_i + 1]; Lp = place(lead_, root, ang, sx)
    # leading edge: a swelling, twisting liquid stroke, fat at the root, hairline at the tip
    K.ribbon(s, np.column_stack([Lp, z + 0.5 + 1.1 * np.sin(np.linspace(0, math.pi, len(Lp))) ** 1.5]), m=m, w=w * 1.5, thin=0.55,
             ends=(0.0, 0.18), wkeys=[(0, 1.4), (0.25, 1.05), (0.6, 0.7), (1, 0.4)], twist=[(0, 0), (0.45, 0.7 * sx), (1, 0.1 * sx)], k=0.45)
    # Moira: the costa is carved, not a plain wire: engraved barbs cut along the swelling leading edge
    # the blade rides proud of the liquid stroke along its whole length, so the barbs read as a carved feathered spar
    # (when it sat inside the stroke only a short row of pits showed at the root and read as pave)
    zz = z + 0.6 + 1.0 * np.sin(np.linspace(0, math.pi, len(Lp))) ** 1.5
    Pc = np.array([m.P(x, y, zv) for (x, y), zv in zip(Lp, zz)]); Nc = np.array([m.N(x, y) for x, y in Lp])
    if len(Pc) > 4:
        import v2 as _v2
        # r4-fix3: no engraved barbs (evenly spaced cuts read as ladder ticks / bead rows). The spar is a proud, smooth
        # sculpted blade whose width breathes unevenly along its length and draws to a needle.
        ph_ = rng.uniform(0, 6.28)
        _v2.blade(s, Pc, lambda t_: w * (1.9 - 1.5 * t_) * (1 + 0.22 * np.sin(7.0 * t_ + ph_) * np.sin(3.1 * t_)) + 0.1,
                  lambda t_: w * (0.8 - 0.5 * t_) + 0.08, normal=Nc, k=0.45, grooves=0)
    trail = np.vstack([o[tip_i:], o[:1]]); Tp = place(trail, root, ang, sx)
    K.ribbon(s, np.column_stack([Tp, z + 0.25 + 0.35 * np.sin(np.linspace(0, 3 * math.pi, len(Tp))) ** 2]), m=m, w=wf(w * 0.5), thin=0.8,
             ends=(0.0, 0.0), wkeys=_keys(rng, 7, 0.55, 1.1, False), k=0.3)
    nv = int(rng.integers(3, 5)) if shape != "dragon" else int(rng.integers(2, 4))
    veins = [lead_]; tips = []
    for j, f in enumerate(np.linspace(0.14, 0.8, nv)[::-1]):
        e = _poly_at(trail, f)
        a0 = _poly_at(lead_, 0.06 + 0.1 * (nv - 1 - j) / max(1, nv - 1)) * 0.55
        dd = e - a0; nn = np.array([-dd[1], dd[0]]) / max(np.linalg.norm(dd), 1e-6)
        wob = rng.uniform(0.04, 0.08) * span * rng.choice([-1, 1])
        m1 = a0 + dd * 0.33 + nn * wob; m2 = a0 + dd * 0.68 - nn * wob * 0.6
        veins.append(np.array([a0, m1, m2, e]))
    veins.append(trail[::-1])
    for j, v in enumerate(veins[1:-1]):
        e = v[-1]; dd = (e - v[-2]) / np.linalg.norm(e - v[-2])
        vv = np.asarray(v, float)          # veins stop at the trailing edge: no loose wire ends past the outline
        P = place(vv, root, ang, sx)
        K.ribbon(s, np.column_stack([P, z + 0.3 + 0.4 * np.sin(np.linspace(0, math.pi, len(P)))]), m=m, w=wf(w * 0.6), thin=0.6,
                 ends=(0.0, 0.0), wkeys=[(0, 1.6), (0.3, 1.0), (0.65, 0.7), (1, 0.55)], twist=[(0, 0), (0.5, 0.5 * sx), (1, 0.0)], k=0.35)
        tips.append((P[-1], P[-1] - P[-2]))
        if beads and j % 2 == 0:      # vein roots melt into the costa (a molten swelling, not a ball)
            q = place(v[0], root, ang, sx); s.ellipsoid(m.P(q[0], q[1], z + 0.4), (w * 1.1, w * 1.1, w * 0.55), k=0.6)
    cells = []
    for a, b in zip(veins[:-1], veins[1:]):
        A = resample(smooth(a, 8), 0.2)[:, :2] if len(a) > 2 else a
        B = resample(smooth(b, 8), 0.2)[:, :2] if len(b) > 2 else b
        prev = 0.25
        for f in np.sort(rng.uniform(0.35, 0.85, int(rng.integers(1, 3)))):
            p, q = _poly_at(A, f), _poly_at(B, f * rng.uniform(0.92, 1.08))
            if np.linalg.norm(p - q) < span * 0.05: continue
            dd = q - p; nn = np.array([-dd[1], dd[0]])
            mid = (p + q) / 2 + nn * rng.uniform(0.12, 0.25) * rng.choice([-1, 1])
            P = place(np.array([p, mid, q]), root, ang, sx)
            K.ribbon(s, np.column_stack([P, np.full(3, z + 0.3)]), m=m, w=wf(w * 0.32), thin=0.85, ends=(0.0, 0.0),
                     wkeys=[(0, 1.2), (0.5, 0.7), (1, 1.2)], k=0.3)
            cells.append(((_poly_at(A, (prev + f) / 2) + _poly_at(B, (prev + f) / 2)) / 2, np.linalg.norm(p - q), f - prev))
            prev = f
    nw = 0 if span < 20 else min(len(tips), 1 if rng.random() < 0.7 else 2)     # small wings: no hairline curls (fragile, scratchy)
    for t, d in [tips[i] for i in rng.choice(len(tips), size=nw, replace=False)]:
        wisp(s, m, t, d, span * rng.uniform(0.22, 0.4), w=max(0.42, w * 0.45), z=z + 0.3, curl=sx * rng.uniform(1.2, 2.4), rng=rng)
    if stones:
        cells.sort(key=lambda c: -c[1])
        done_ = []
        for i, (cc, gap, df) in enumerate(cells[:stones * 3]):
            if len(done_) >= stones: break
            D = float(np.clip(gap * 0.55, 1.5, 5.0)); P = place(cc, root, ang, sx)
            if any(np.linalg.norm(np.asarray(P) - q) < (D + d_) / 2 + 1.2 for q, d_ in done_): continue   # never jam two stones
            done_.append((np.asarray(P), D))
            Mo.prong(s, st, m.P(P[0], P[1], z + D * 0.45 + 0.2), D, pal[i % len(pal)], normal=m.N(P[0], P[1]), n=4, wire=max(0.26, D * 0.08))
    return dict(root=place(o[0], root, ang, sx), tip=place(o[tip_i], root, ang, sx))


for _mod in (kit, glassB, glass64):
    _mod.lead = lead; _mod.nib = nib
W2.vein_wing = vein_wing


@contextlib.contextmanager
def organic():
    ORGANIC[0] = True
    try: yield
    finally: ORGANIC[0] = False
