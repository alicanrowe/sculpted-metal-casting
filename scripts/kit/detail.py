"""detail kit: the hand-finish layer on top of kit.py.
engraved barbs on wide strokes (nib(..., engrave=pitch)), milgrain edges, acanthus chasing,
and hyodomachine-style swelling hooks that split into needle points."""
import math
import numpy as np
from sdf import resample, arclen, tangents
from kit import nib, spike, ball, bead, smooth, TIP
from v2 import blade


def milgrain(s, m, pts, d=0.42, z=0.35, closed=False, k=0.05):
    """A row of tiny beads (milgrain) along a path, sitting on the metal."""
    c = smooth(pts, 6, closed) if len(pts) > 2 else np.column_stack([np.asarray(pts, float), np.zeros(len(pts))])
    c = resample(c, d * 1.05)
    for x, y, _ in c[:-1] if closed else c:
        s.sphere(m.P(x, y, z), d * 0.5, k=k)


def acanthus(s, m, p, ang, size=3.0, n=3, z=0.2, curl=1, k=0.25):
    """A chased acanthus spray: n engraved leaf blades fanning from p along ang, tips curling
    back (the grill reference's carved ornament, kept small and cast-friendly)."""
    p = np.asarray(p, float)
    for i in range(n):
        a = ang + (i - (n - 1) / 2) * 0.55
        L = size * (1.0 - 0.18 * abs(i - (n - 1) / 2))
        d = np.array([math.cos(a), math.sin(a)]); nn = np.array([-d[1], d[0]]) * curl * (1 if i >= (n - 1) / 2 else -1)
        pts2 = [p, p + d * L * 0.45 + nn * L * 0.12, p + d * L * 0.85 + nn * L * 0.05, p + d * L * 0.9 - nn * L * 0.22]
        c = smooth(pts2, 8)
        c = resample(c, 0.15); u = arclen(c); u = u / u[-1]
        W = TIP + (size * 0.2 - TIP) * np.sin(np.clip(u, 0, 1) * math.pi) ** 0.8 * (1 - u) ** 0.35
        P = np.array([m.P(x, y, z + 0.5 * size * 0.12 * math.sin(math.pi * uu)) for (x, y, _), uu in zip(c, u)])
        N = np.array([m.N(x, y) for x, y, _ in c])
        blade(s, P, W, np.maximum(W * 0.45, np.minimum(W, 0.3)), normal=N, k=k, grooves=max(3, int(L / 0.45)), both=True, gr=0.07, barb=0.8)
    ball(s, m, tuple(p), size * 0.14, z=z)


def hook(s, m, pts, w=1.0, pen=0.75, split=True, hair=0.18, z=0.0, rise=0.9, bead_kind=None, stones=None, engrave=0.0):
    """Hyodomachine stroke: a liquid broad-nib line that swells, rises off the surface, hooks
    at the end and throws a hairline spur off its belly into a needle point."""
    c, W = nib(s, m, pts, w=w, pen=pen, hair=hair, taper=(0.18, 0.35), z=z, thick=0.8,
               rise=[(0, 0.0), (0.45, rise), (1, 0.15)], engrave=engrave)
    if split:
        j = int(len(c) * 0.55); p = c[j]; tg = c[min(j + 3, len(c) - 1)] - c[max(j - 3, 0)]
        tg = tg / max(np.linalg.norm(tg), 1e-6); nn = np.array([-tg[1], tg[0]])
        L = w * 4.5
        spike(s, m, tuple(p), tuple(p + tg * L * 0.8 + nn * L * 0.55), r0=W[j] * 0.45, bend=0.25, z0=z + rise * 0.8, z1=z + rise * 0.3)
    if bead_kind and stones is not None:
        bead(s, m, stones, tuple(c[-1]), w * 1.5, bead_kind)
    return c, W
