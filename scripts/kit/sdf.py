"""v2 sculpting kit: signed-distance modelling for liquid, cast-looking silver.

Every piece is a list of primitives (tapered round-cone strokes, flattened blades, spheres,
ellipsoids, tori) combined in order with SMOOTH union / subtraction, so forms fuse like
poured metal instead of meeting as wires. Grooves (feather barbs, veins, engraving) are
thin strokes subtracted with a small blend. Meshed by narrow-band marching cubes.
Units: mm."""
import math
import numpy as np
from numba import njit, prange

# prim row layout
#  0 type (0 roundcone, 1 sphere, 2 ellipsoid, 3 torus)
#  1 op (0 union, 1 subtract, 2 intersect)
#  2 k blend
#  3 flat (z squash factor >= 1)
#  4..6 origin   7..15 R (world->local, row major)
#  16 L (roundcone length) / torus major R
#  17 r1  18 r2   (ellipsoid: 16..18 radii)
#  19..24 world AABB min/max
NF = 42
SPHERE, CONE, ELL, TORUS, FEATHER = 1, 0, 2, 3, 4
# feather params (cols 25..41): L, W, T, skew, pitch, depth, slope, ky, kz, seed, shaft, ridge,
#                                cup, nnotch, quill, tipT, bottom_depth


@njit(cache=True, fastmath=True)
def _hash(a):
    x = math.sin(a * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


@njit(cache=True, fastmath=True)
def _feather(P, i, x, y, z):
    L = P[i, 25]; W = P[i, 26]; T = P[i, 27]; skew = P[i, 28]; pitch = P[i, 29]; depth = P[i, 30]
    slope = P[i, 31]; ky = P[i, 32]; kz = P[i, 33]; seed = P[i, 34]; shaft = P[i, 35]; ridge = P[i, 36]
    cup = P[i, 37]; nn = int(P[i, 38]); quill = P[i, 39]; tipT = P[i, 40]; bdep = P[i, 41]
    # unbend: out-of-plane wrap (kz) then in-plane sweep (ky)
    if abs(kz) > 1e-6:
        sg = 1.0 if kz > 0 else -1.0
        R = 1.0 / abs(kz); zz = R - z * sg
        r = math.sqrt(x * x + zz * zz); a = math.atan2(x, zz)
        x = a * R; z = (R - r) * sg
    if abs(ky) > 1e-6:
        sg = 1.0 if ky > 0 else -1.0
        R = 1.0 / abs(ky); yy = R - y * sg
        r = math.sqrt(x * x + yy * yy); a = math.atan2(x, yy)
        x = a * R; y = (R - r) * sg
    u = x / L
    uc = min(max(u, 0.0), 1.0)
    # outline
    if uc < quill:
        w = shaft
    else:
        v = (uc - quill) / (1.0 - quill)
        w = max(shaft * (1.0 - v), W * math.pow(max(0.0, math.sin(math.pi * math.pow(v, 0.62))), 0.75))
    if y < 0:
        w = shaft + (w - shaft) * skew
    ay = abs(y)
    # barb coordinate: barbs leave the shaft angled toward the tip and curve outward
    x0 = x - ay * slope - 0.35 * slope * ay * ay / max(W, 1e-6)
    fb = x0 / pitch
    nb = math.floor(fb)
    f = fb - nb
    g = max(0.0, 1.0 - min(f, 1.0 - f) / 0.3)
    dm = 0.65 + 0.7 * _hash(nb * 1.37 + seed + (0.5 if y < 0 else 0.0))
    q = min(1.0, ay / max(w, 1e-6))
    we = w - 0.09 * min(1.0, pitch / 0.28) * g * dm * q * q * (1.0 if uc > quill else 0.0)   # serrated edge; scales down below the mm pitch floor (cm kits: 0.9 mm teeth read as leaves, 18 Nov)
    dy = ay - we
    dx = max(-x, x - L)
    dxy = max(dy * 0.85, dx)
    taper = 1.0 - (1.0 - tipT) * uc
    tv = T * taper * (0.45 + 0.55 * math.sqrt(max(0.0, 1.0 - q * q)))
    zc = cup * q * q * w
    rid = ridge * max(0.0, 1.0 - (ay / max(shaft, 1e-6)) ** 2) * taper
    ttop = tv + rid
    tbot = tv + rid * 0.6
    if ay > shaft * 0.9 and uc > quill:
        fade = min(1.0, (ay - shaft * 0.9) / 0.25)
        ttop -= depth * dm * g * fade
        tbot -= bdep * dm * g * fade
    dz = max(z - zc - ttop, zc - tbot - z)
    d = max(dxy, dz)
    # edge splits: a few barbs pull apart, cut through
    for k in range(nn):
        xn = L * (quill + 0.12 + 0.7 * _hash(seed + k * 3.1))
        side = 1.0 if _hash(seed + k * 7.7) > 0.5 else -1.0
        if side * y > 0:
            fr = 0.35 + 0.25 * _hash(seed + k * 1.3)
            sd = max(abs(x0 - xn) - 0.06 - 0.12 * (ay / max(w, 1e-6)), fr * w - ay)
            d = max(d, -sd)
    return d * 0.8



@njit(cache=True, fastmath=True)
def _ucap2(x, y, r1, r2, h):
    """2D uneven capsule along +x: circle r1 at 0, circle r2 at (h, 0)."""
    px = abs(y); py = x
    b = (r1 - r2) / h
    a = math.sqrt(max(0.0, 1.0 - b * b))
    k = -b * px + a * py
    if k < 0.0:
        return math.sqrt(px * px + py * py) - r1
    if k > a * h:
        return math.sqrt(px * px + (py - h) ** 2) - r2
    return a * px + b * py - r1


@njit(cache=True, fastmath=True)
def _prim(P, i, x, y, z):
    t = P[i, 0]
    if t == 4.0:
        ox, oy, oz = x - P[i, 4], y - P[i, 5], z - P[i, 6]
        lx = P[i, 7] * ox + P[i, 8] * oy + P[i, 9] * oz
        ly = P[i, 10] * ox + P[i, 11] * oy + P[i, 12] * oz
        lz = P[i, 13] * ox + P[i, 14] * oy + P[i, 15] * oz
        d = _feather(P, i, lx, ly, lz)
        # clip to the feather's own bounding box: far from the feather its field is not a distance, and inside
        # blocks woken by other parts it left hairline slivers (sawhorse round, Nov 18)
        bx = max(P[i, 19] - x, x - P[i, 22]); by = max(P[i, 20] - y, y - P[i, 23]); bz = max(P[i, 21] - z, z - P[i, 24])
        return max(d, max(bx, max(by, bz)))
    ox, oy, oz = x - P[i, 4], y - P[i, 5], z - P[i, 6]
    lx = P[i, 7] * ox + P[i, 8] * oy + P[i, 9] * oz
    ly = P[i, 10] * ox + P[i, 11] * oy + P[i, 12] * oz
    lz = P[i, 13] * ox + P[i, 14] * oy + P[i, 15] * oz
    f = P[i, 3]
    lz *= f
    if t == 1.0:
        d = math.sqrt(lx * lx + ly * ly + lz * lz) - P[i, 17]
    elif t == 0.0:
        L = P[i, 16]; r1 = P[i, 17]; r2 = P[i, 18]
        l2 = L * L; rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
        yv = lx * L
        zv = yv - l2
        qy = ly * l2; qz = lz * l2
        x2 = qy * qy + qz * qz
        y2 = yv * yv * l2
        z2 = zv * zv * l2
        k = (1.0 if rr > 0 else -1.0) * rr * rr * x2
        sz = 1.0 if zv > 0 else (-1.0 if zv < 0 else 0.0)
        sy = 1.0 if yv > 0 else (-1.0 if yv < 0 else 0.0)
        if sz * a2 * z2 > k:
            d = math.sqrt(x2 + z2) * il2 - r2
        elif sy * a2 * y2 < k:
            d = math.sqrt(x2 + y2) * il2 - r1
        else:
            d = (math.sqrt(x2 * a2 * il2) + yv * rr) * il2 - r1
    elif t == 2.0:
        rx = P[i, 16]; ry = P[i, 17]; rz = P[i, 18]
        k0 = math.sqrt((lx / rx) ** 2 + (ly / ry) ** 2 + (lz / rz) ** 2)
        k1 = math.sqrt((lx / rx ** 2) ** 2 + (ly / ry ** 2) ** 2 + (lz / rz ** 2) ** 2)
        d = k0 * (k0 - 1.0) / max(k1, 1e-9)
    elif t == 5.0:
        d2 = _ucap2(lx, ly, P[i, 17], P[i, 18], P[i, 16])
        z0 = P[i, 25]; z1 = P[i, 26]
        dz = max(z0 - lz, lz - z1)
        d = max(d2, dz)
    else:
        q = math.sqrt(lx * lx + ly * ly) - P[i, 16]
        d = math.sqrt(q * q + lz * lz) - P[i, 17]
    return d / f


@njit(cache=True, fastmath=True)
def _combine(d, p, op, k):
    if op == 0.0:
        if k <= 0: return min(d, p)
        h = max(k - abs(d - p), 0.0) / k
        return min(d, p) - h * h * k * 0.25
    if op == 1.0:
        p = -p
    if k <= 0: return max(d, p)
    h = max(k - abs(d - p), 0.0) / k
    return max(d, p) + h * h * k * 0.25


@njit(parallel=True, cache=True, fastmath=True)
def eval_pts(pts, P, idx):
    n = pts.shape[0]
    out = np.empty(n, np.float32)
    for j in prange(n):
        x, y, z = pts[j, 0], pts[j, 1], pts[j, 2]
        d = 1e9
        for ii in range(idx.shape[0]):
            i = idx[ii]
            p = _prim(P, i, x, y, z)
            d = _combine(d, p, P[i, 1], P[i, 2])
        out[j] = d
    return out


# ---------------------------------------------------------------- scene building
def _frame(xaxis, zhint):
    xa = np.asarray(xaxis, float); xa /= np.linalg.norm(xa)
    zh = np.asarray(zhint, float)
    za = zh - xa * np.dot(zh, xa)
    if np.linalg.norm(za) < 1e-6:
        za = np.cross(xa, [0, 1, 0]) if abs(xa[1]) < .9 else np.cross(xa, [1, 0, 0])
    za /= np.linalg.norm(za)
    ya = np.cross(za, xa)
    return np.array([xa, ya, za])          # rows = local axes -> world->local


class Scene:
    def __init__(self):
        self.rows = []

    def _add(self, typ, op, k, flat, o, R, a, b, c, lo, hi, extra=None):
        r = np.zeros(NF)
        if extra is not None: r[25:25 + len(extra)] = extra
        r[0], r[1], r[2], r[3] = typ, op, k, max(1.0, flat)
        r[4:7] = o; r[7:16] = np.asarray(R).ravel(); r[16:19] = a, b, c
        pad = k + 0.05
        r[19:22] = np.asarray(lo) - pad; r[22:25] = np.asarray(hi) + pad
        self.rows.append(r)

    def sphere(self, c, r, op=0, k=0.0):
        c = np.asarray(c, float)
        self._add(SPHERE, op, k, 1, c, np.eye(3), 0, r, 0, c - r, c + r)

    def ellipsoid(self, c, radii, xaxis=(1, 0, 0), zhint=(0, 0, 1), op=0, k=0.0):
        c = np.asarray(c, float); m = max(radii)
        self._add(ELL, op, k, 1, c, _frame(xaxis, zhint), *radii, c - m, c + m)

    def torus(self, c, R, r, normal=(0, 0, 1), op=0, k=0.0):
        c = np.asarray(c, float); n = np.asarray(normal, float); n /= np.linalg.norm(n)
        F = _frame(np.cross(n, [0, 1, 0]) if abs(n[1]) < .9 else np.cross(n, [1, 0, 0]), n)
        self._add(TORUS, op, k, 1, c, F, R, r, 0, c - R - r, c + R + r)

    def cone(self, a, b, r1, r2, op=0, k=0.0, flat=1.0, zhint=(0, 0, 1)):
        a = np.asarray(a, float); b = np.asarray(b, float)
        L = np.linalg.norm(b - a)
        if L < 1e-5:
            return self.sphere(a, max(r1, r2), op, k)
        m = max(r1, r2)
        self._add(CONE, op, k, flat, a, _frame(b - a, zhint), L, r1, r2,
                  np.minimum(a, b) - m, np.maximum(a, b) + m)

    def stroke(self, pts, radii, op=0, k=0.0, flat=1.0, normals=None, kseg=0.0):
        """A tapered stroke along a polyline. flat>1 squashes the section along `normals`
        (blades/leaves). The first segment blends into the scene with k, the rest join
        each other with kseg (0 = exact)."""
        pts = np.asarray(pts, float); radii = np.asarray(radii, float)
        if normals is None:
            normals = np.tile([0, 0, 1.0], (len(pts), 1))
        normals = np.asarray(normals, float)
        if normals.ndim == 1: normals = np.tile(normals, (len(pts), 1))
        # segments of one stroke join almost exactly: a full smooth blend at every joint bulges the stroke into
        # an even ribbed/beaded texture that reads machined (Nov 18 check). Only the first segment blends with k.
        ks = kseg if kseg else min(k, 0.03)
        for i in range(len(pts) - 1):
            self.cone(pts[i], pts[i + 1], radii[i], radii[i + 1], op, k if i == 0 or op else ks,
                      flat, (normals[i] + normals[i + 1]) / 2)

    def feather(self, base, direction, normal, L, W, T=0.55, skew=0.8, pitch=0.32, depth=0.13, slope=0.9,
                bend=0.0, wrap=0.0, seed=1.0, shaft=0.38, ridge=0.22, cup=0.12, notches=3, quill=0.08,
                tipT=0.55, bottom_depth=0.0, op=0, k=0.0):
        """A hand-carved feather: shaft ridge, engraved barbs angled to the tip, a few
        split barbs at the edge. bend = in-plane curvature (1/mm, + curls toward +y),
        wrap = out-of-plane curvature (1/mm, + curls the tip toward +normal;
        use - with the normal pointing away from a finger/wrist to wrap round it)."""
        base = np.asarray(base, float)
        F = _frame(direction, normal)
        # tight box: push a lattice of local points through the forward bend (ky) then wrap (kz)
        xs = np.linspace(-1.0, L + 1.0, 40)
        ys = np.array([-(W + 0.6), 0.0, W + 0.6]); zs = np.array([-(T + 0.6), T + cup * W + 0.8])
        X, Yv, Zv = [a.ravel() for a in np.meshgrid(xs, ys, zs, indexing="ij")]
        if abs(bend) > 1e-6:
            R = 1 / abs(bend); sg = 1.0 if bend > 0 else -1.0; a = X / R; r = R - Yv * sg
            X, Yv = r * np.sin(a), (R - r * np.cos(a)) * sg
        if abs(wrap) > 1e-6:
            R = 1 / abs(wrap); sg = 1.0 if wrap > 0 else -1.0; a = X / R; r = R - Zv * sg
            X, Zv = r * np.sin(a), (R - r * np.cos(a)) * sg
        Wp = base + np.stack([X, Yv, Zv], 1) @ F
        self._add(FEATHER, op, k, 1, base, F, 0, 0, 0, Wp.min(0) - 0.3, Wp.max(0) + 0.3,
                  extra=[L, W, T, skew, pitch, depth, slope, bend, wrap, seed, shaft, ridge, cup, notches, quill,
                         tipT, bottom_depth])

    def prism(self, a, b, r1, r2, z0, z1, normal=(0, 0, 1), op=0, k=0.0):
        """Extruded 2D teardrop/capsule (circle r1 at a, r2 at b) between z0..z1 along
        normal: stone seats and light holes for fancy shapes."""
        a = np.asarray(a, float); b = np.asarray(b, float)
        F = _frame(b - a, normal); L = max(np.linalg.norm(b - a), 1e-4)
        m = max(r1, r2) + max(abs(z0), abs(z1))
        self._add(5, op, k, 1, a, F, L, r1, r2, np.minimum(a, b) - m, np.maximum(a, b) + m, extra=[z0, z1])

    def array(self):
        return np.array(self.rows) if self.rows else np.zeros((0, NF))


# ---------------------------------------------------------------- curves & profiles
def bezier(ctrl, n=48):
    """Smooth curve through a cubic Bezier chain (ctrl = [p0, c0, c1, p1, c2, c3, p2, ...])."""
    c = np.asarray(ctrl, float); segs = (len(c) - 1) // 3
    out = []
    for s in range(segs):
        p0, p1, p2, p3 = c[3 * s:3 * s + 4]
        t = np.linspace(0, 1, n, endpoint=(s == segs - 1))[:, None]
        out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)
    return np.vstack(out)


def catmull(pts, n=16, closed=False):
    p = np.asarray(pts, float)
    if closed: p = np.vstack([p[-1], p, p[0], p[1]])
    else: p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1:i + 3]
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed: out.append(p[-2][None])
    return np.vstack(out)


def resample(pts, step=0.25):
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(s[-1] / step) + 1); u = np.linspace(0, s[-1], n)
    return np.stack([np.interp(u, s, pts[:, i]) for i in range(3)], 1)


def arclen(pts):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); return s / max(s[-1], 1e-9)


def profile(u, keys):
    """Radius profile: keys = [(u, r), ...] smoothstep-interpolated."""
    keys = sorted(keys); us = np.array([k[0] for k in keys]); rs = np.array([k[1] for k in keys])
    i = np.clip(np.searchsorted(us, u) - 1, 0, len(us) - 2)
    t = np.clip((u - us[i]) / (us[i + 1] - us[i]), 0, 1); t = t * t * (3 - 2 * t)
    return rs[i] * (1 - t) + rs[i + 1] * t


def tangents(pts):
    t = np.gradient(pts, axis=0); return t / np.linalg.norm(t, axis=1)[:, None]


# ---------------------------------------------------------------- meshing
def mesh(P, vox=0.05, block=40, verbose=True, _try=0):
    """Narrow-band marching cubes in blocks, with a seam guard (Nov 18). At some voxel sizes a block's prim
    culling disagrees with its neighbour, a whole block row goes missing and the casting splits exactly on a block
    seam (a sawhorse lost both legs at VOX 0.09, clean at 0.11). After meshing, open edges lying on a seam plane mean
    that happened: retry on a grid shifted by a fraction of a voxel, and raise if three shifts all fail."""
    V, F, seam_open, lo = _mesh_once(P, vox, block, verbose, shift=(0.0, 0.37, 0.61, 0.19)[_try])
    if seam_open:
        msg = f"mesher dropped a block: {seam_open} piece(s) cut off on a block seam at vox {vox} (grid shift try {_try})"
        if _try < 3:
            if verbose: print("  " + msg + "; retrying on a shifted grid", flush=True)
            return mesh(P, vox, block, verbose, _try + 1)
        raise RuntimeError(msg + "; try another VOX")
    return V, F


def _mesh_once(P, vox, block, verbose, shift=0.0):
    from skimage.measure import marching_cubes
    P = np.array(P, np.float64)
    kmax = P[:, 2].max() if len(P) else 0          # a prim influences smooth blends up to kmax away
    P[:, 19:22] -= kmax; P[:, 22:25] += kmax
    U = P[:, 1] == 0
    lo = P[U, 19:22].min(0) - (3 + shift) * vox; hi = P[U, 22:25].max(0) + 3 * vox
    n = np.ceil((hi - lo) / vox).astype(int) + 1
    nb = np.ceil(n / block).astype(int)
    verts, faces, nv = [], [], 0
    half = 0.5 * block * vox * math.sqrt(3) + 2 * vox
    cnt = 0
    from collections import deque
    done = set(); queue = deque()
    def idx_for(b0, b1):
        m = np.all(P[:, 19:22] <= b1, 1) & np.all(P[:, 22:25] >= b0, 1)
        return np.nonzero(m)[0].astype(np.int64)
    for bi in range(nb[0]):
        for bj in range(nb[1]):
            for bk in range(nb[2]):
                i0 = np.array([bi, bj, bk]) * block
                b0 = lo + i0 * vox; b1 = b0 + block * vox
                idx = idx_for(b0, b1)
                if not np.any(P[idx, 1] == 0):
                    continue
                dc = eval_pts(((b0 + b1) / 2)[None].astype(np.float64), P, idx)[0]
                if abs(dc) <= half:
                    queue.append((bi, bj, bk))
    while queue:
        key3 = queue.popleft()
        if key3 in done: continue
        done.add(key3)
        i0 = np.array(key3) * block
        b0 = lo + i0 * vox; b1 = b0 + block * vox
        idx = idx_for(b0, b1)
        if not np.any(P[idx, 1] == 0):
            continue
        g = [lo[a] + (i0[a] + np.arange(block + 1)) * vox for a in range(3)]
        X, Y, Z = np.meshgrid(*g, indexing="ij")
        pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
        d = eval_pts(pts, P, idx).reshape(X.shape)
        if d.min() > 0 or d.max() < 0:
            continue
        # any face that the surface crosses pulls in that neighbour (no seam holes)
        for ax in range(3):
            for side, sl in ((-1, 0), (1, -1)):
                face = np.take(d, sl, axis=ax)
                if face.min() <= 0 <= face.max():
                    nk = list(key3); nk[ax] += side
                    if 0 <= nk[ax] < nb[ax] and tuple(nk) not in done:
                        queue.append(tuple(nk))
        v, f, _, _ = marching_cubes(d, 0.0, spacing=(vox, vox, vox))
        verts.append(np.asarray(v, np.float64) / vox + i0); faces.append(f + nv); nv += len(v); cnt += 1   # lattice units: seams weld exactly
    V = np.vstack(verts); F = np.vstack(faces)
    # weld block seams: identical lattice-edge vertices
    key = np.round(V * 64).astype(np.int64)          # 1/64 voxel: shared seam vertices always land on the same key
    uk, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    V = lo + V[first] * vox; F = inv.ravel()[F]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    if verbose:
        print(f"  mesh: {cnt} blocks, {len(V)} verts, {len(F)} tris", flush=True)
    # seam guard: a lost block cuts the casting on a seam plane, leaving a big separate piece whose bounding box
    # ends exactly on that plane. Small seam slivers are normal (repair them later) and are ignored here.
    seam_open = 0
    try:
        import trimesh
        parts = trimesh.Trimesh(V, F, process=False).split(only_watertight=False)
        if len(parts) > 1:
            areas = np.array([p.area for p in parts]); main = areas.max()
            for p, ar in zip(parts, areas):
                if ar == main or ar < 25 * vox * vox: continue
                g = (p.bounds - lo) / (block * vox)
                if np.any(np.abs(g - np.round(g)) < 1e-3):
                    seam_open += 1
                    if verbose: print("   cut piece", round(float(ar), 2), p.bounds.round(2).tolist(), flush=True)
    except ImportError:
        pass
    return V.astype(np.float32), F.astype(np.int32), seam_open, lo


def save_stl(V, F, path, smooth=0):
    """smooth>0: Taubin passes that take out the voxel ripple without shrinking the piece."""
    import trimesh
    m = trimesh.Trimesh(V, F, process=False)
    if smooth:
        V0 = np.array(m.vertices)
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=smooth)
        # Taubin flings the odd non-manifold vertex (where engraved barbs touch) centimetres away, which rendered
        # as straight hairlines. Anything that moved more than a voxel's worth goes back where marching cubes put it.
        e = np.linalg.norm(V0[F[:, 0]] - V0[F[:, 1]], axis=1); vox = float(np.median(e)) * 1.6
        Vs = np.array(m.vertices); bad = np.linalg.norm(Vs - V0, axis=1) > vox
        Vs[bad] = V0[bad]; m.vertices = Vs
    m.fix_normals()
    m.export(path)
    return m
