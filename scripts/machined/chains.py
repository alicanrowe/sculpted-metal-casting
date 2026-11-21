"""Governor r3: real chain, laid on the table as it is photographed, with one machined part breaking it.

A chain is a list of slots round a closed loop (an ellipse on the table). Each slot holds one link, or the eye of
the bar that disrupts the chain, or the clasp ring. Neighbouring slots turn 90 degrees to each other about the
chain's line, each leaning 45 degrees, the way a cable chain settles when laid down. All links are exact CSG
(revolved wire), reused by transform, so a 60-link chain is cheap. Units mm; the table is z = 0."""
import math
import numpy as np
import manifold3d as m3
from mlib import M, CS, lathe, cyl, box

SEG = 40


def oval_link(Li, Wi, d, flat=1.0, cut=None, seg=SEG, square=False):
    """a closed wire link in the XY plane, long axis X: inner length Li, inner width Wi, wire diameter d.
    flat > 1 squashes the wire (z), as a hammered or curb link; cut trims flats top and bottom (diamond cut);
    square uses a rounded-square wire (box and rectangle links)."""
    R = Wi / 2 + d / 2
    if square:
        sec = CS.square((d, d), True).offset(-0.18 * d, m3.JoinType.Round, 2, 16).offset(0.18 * d, m3.JoinType.Round, 2, 16)
    else:
        sec = CS.circle(d / 2, 24)
    half = M.revolve(sec.translate((R, 0)), seg, 180.0)           # half torus in XZ revolved about Z: spans +y side
    st = max(Li - Wi, 0.0)
    parts = [half.rotate((0, 0, -90)).translate((st / 2, 0, 0)), half.rotate((0, 0, 90)).translate((-st / 2, 0, 0))]
    if st > 1e-6:
        bar = M.extrude(sec, st).rotate((0, 90, 0)).translate((-st / 2, 0, 0))
        parts += [bar.translate((0, R, 0)), bar.translate((0, -R, 0))]
    lk = M.batch_boolean(parts, m3.OpType.Add)
    if flat != 1.0:
        lk = lk.scale((1, 1, 1 / flat))
    if cut:
        lk = lk - box(200, 200, 10).translate((0, 0, 5 + cut)) - box(200, 200, 10).translate((0, 0, -5 - cut))
    return lk


def ellipse_pts(a, b, n=2000, e=2.0, straight=0.0):
    """a superellipse: e = 2 is an ellipse; larger e flattens the front so a straight bar can lie in it"""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    ee = np.where(s < 0, e, 2.0)                    # only the front (-Y) half is flattened
    x = a * np.sign(c) * np.abs(c) ** (2 / ee) + np.sign(c) * straight / 2
    return np.stack([x, b * np.sign(s) * np.abs(s) ** (2 / ee)], 1)


class Loop:
    """a closed loop on the table, parametrised by arc length; scaled so its perimeter matches the chain"""

    def __init__(self, perimeter, aspect=0.8, n=4000, e=2.0, straight=0.0):
        # straight: mm of straight run inserted at the front and back (for a bar or plate); solve the scale
        k = 1.0
        for _ in range(30):
            P = ellipse_pts(1.0, aspect, n, e, straight / k)
            seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
            k = perimeter / seg.sum()
        self.P = P * k
        self.s = np.concatenate([[0], np.cumsum(seg * k)])
        self.L = self.s[-1]

    def at(self, s):
        s = s % self.L
        i = int(np.searchsorted(self.s, s, side="right") - 1); i = min(i, len(self.P) - 1)
        a, b = self.P[i], self.P[(i + 1) % len(self.P)]
        f = (s - self.s[i]) / max(self.s[i + 1] - self.s[i], 1e-9)
        p = a + (b - a) * f
        t = (b - a) / np.linalg.norm(b - a)
        return p, t


def frame(t, lean):
    """rotation taking link-local X (long axis) to the tangent t (2D), turned about it by `lean` degrees
    (0 = lying flat in the table plane)"""
    x = np.array([t[0], t[1], 0.0]); z = np.array([0, 0, 1.0]); y = np.cross(z, x)
    c, s = math.cos(math.radians(lean)), math.sin(math.radians(lean))
    y2 = c * y + s * z; z2 = -s * y + c * z
    return np.stack([x, y2, z2], 1)            # columns: images of local x, y, z


def place_m(solid, R, p):
    T = np.zeros((3, 4)); T[:, :3] = R; T[:, 3] = p
    return solid.transform(T)


def lay(slots, aspect=0.8, slack=0.88, lean=45.0, front=None, e=2.0, straight=0.0):
    """slots: list of dicts with 'Li' (inner length, for spacing), 'h' (half the link's outer width: how far it
    reaches from the chain's line when leaning) and 'solid' (or None for a gap the caller fills).
    Returns the loop and, for each slot, (rotation, position). The chain's line sits at the height that puts the
    lowest leaning link on the table. front: arc position to centre slot 0 on (default: the front, -Y)."""
    pitches = [slots[i].get("pitch", slack * (slots[i]["Li"] + slots[(i + 1) % len(slots)]["Li"]) / 2) for i in range(len(slots))]
    loop = Loop(sum(pitches), aspect, e=e, straight=straight)
    s0 = loop.L * 0.75 if front is None else front        # ellipse param starts at +X, runs CCW; -Y is 3/4 round
    zc = max(sl["h"] * math.sin(math.radians(abs(sl.get("lean", lean)))) +
             sl.get("d", 1.0) / 2 * math.cos(math.radians(abs(sl.get("lean", lean)))) for sl in slots)
    out = []
    s = s0
    for i, sl in enumerate(slots):
        p, t = loop.at(s)
        ln = sl.get("lean", lean if i % 2 == 0 else -lean)
        R = frame(t, ln)
        out.append((R, np.array([p[0], p[1], zc]), s, t))
        s += pitches[i]
    return loop, out
