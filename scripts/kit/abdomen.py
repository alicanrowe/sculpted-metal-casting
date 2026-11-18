"""Insect abdomen, Nov 18. client feedback: the graded bead row read as a crude bead string. Replaced everywhere by one carved form:
a single liquid stroke, widest just below the thorax, tapering in a long S to a needle, with shallow carved plate
lines (chevrons, Moira's engraving) across its back instead of separate spheres."""
import math
import numpy as np
import sculpt as K
from kit import nib


def abdomen(s, m, top, d, L, W, z=0.6, rng=None, plates=5, bend=None):
    """top: 2D point under the thorax; d: unit 2D direction toward the tail; L length; W max half width."""
    rng = rng or np.random.default_rng(0)
    top = np.asarray(top, float); d = np.asarray(d, float); d = d / np.linalg.norm(d); nn = np.array([-d[1], d[0]])
    b = (rng.uniform(-0.07, 0.07) if bend is None else bend) * L
    t = np.linspace(0, 1, 36)
    P = top + np.outer(t * L, d) + np.outer(b * np.sin(t * math.pi * 1.1), nn)
    zz = z + W * 0.5 * np.sin(np.clip(t * 1.6, 0, 1) * math.pi * 0.5) * (1 - t)
    K.ribbon(s, np.column_stack([P, zz]), m=m, w=W, thin=0.78, ends=(0.0, 0.42),
             wkeys=[(0, 0.82), (0.16, 1.0), (0.45, 0.78), (0.75, 0.42), (1, 0.15)], k=0.6)
    # carved plate lines: shallow chevrons pointing to the tail, fading out down the body
    for i, u in enumerate(np.linspace(0.14, 0.62, plates)):
        j = int(u * (len(t) - 1)); c = P[j]
        tg = P[min(j + 1, len(P) - 1)] - P[max(j - 1, 0)]; tg /= np.linalg.norm(tg); ng = np.array([-tg[1], tg[0]])
        half = W * (1.0 - 0.75 * u) * 0.92
        pts = [c - ng * half - tg * half * 0.35, c + tg * half * 0.12, c + ng * half - tg * half * 0.35]
        nib(s, m, pts, w=max(0.24, W * 0.11), pen=0.0, hair=0.9, z=float(zz[j]) + W * 0.42 * (1 - u), taper=(0.3, 0.3), k=0.2)
    return P[-1]
