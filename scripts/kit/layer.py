"""Insert-and-layer relief: the way the best CAD jewellers model ornament in ZBrush, rebuilt in Python.

Their pipeline (read from a maker's process reel, 22 Nov 2026; see references/insert-layer.md):
  1. a heavy, simple BLANK (a signet or dome shank made from deformed primitives, kept clean and smooth)
  2. a small LIBRARY of ornament elements, each sculpted once at high resolution (a crescent, a lobed leaf)
  3. HAND PLACEMENT: hundreds of copies dropped onto the blank one by one, each scaled, bent and turned
     to follow one flow, stacked in three or more depths so they overlap like shingles
  4. a matte GROUND texture (stipple) in the gaps, against polished elements and plain mouldings
  5. a live UNION of everything into one solid at very high resolution (their 6 M point DynaMesh), then decimate

Here: the blank is a parametric mesh, elements are swept meshes with a cut section (crest, bevel, engraved
groove) rather than round SDF tubes, placement drapes each element over the blank through a plan mapping,
and manifold3d unions it all exactly (crisp intersections, no voxel smoothing).

Units mm. Ring axis is Y, the top of the ring is +Z.
"""
import math
import numpy as np
import trimesh
import manifold3d as mf

EDGE_DIVE = 0.15      # mm an insert's edges go under the ground (must beat the deepest stipple pit)


# ----------------------------------------------------------------------------------------------- meshes

def _grid_tris(nu, nl, closed_u=False):
    """Triangles for an nu x nl grid of loops (each loop closed, nl verts)."""
    F = []
    rng_u = nu if closed_u else nu - 1
    for i in range(rng_u):
        i2 = (i + 1) % nu
        for j in range(nl):
            j2 = (j + 1) % nl
            a, b, c, d = i * nl + j, i * nl + j2, i2 * nl + j2, i2 * nl + j
            F.append((a, b, c)); F.append((a, c, d))
    return np.array(F, np.int64)


def signed_volume(V, F):
    V = np.asarray(V, float); F = np.asarray(F)
    return float(np.einsum("ij,ij->i", V[F[:, 0]], np.cross(V[F[:, 1]], V[F[:, 2]])).sum() / 6.0)


def to_manifold(V, F):
    """Mesh -> manifold, fixing winding: mirroring an element or mapping it through a left-handed plan frame
    turns it inside out, and an inside-out part silently vanishes from the union."""
    F = np.asarray(F)
    if signed_volume(V, F) < 0:
        F = F[:, ::-1]
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(V, np.float32), tri_verts=np.asarray(F, np.uint32)))


def from_manifold(M):
    m = M.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts), process=False)


# ----------------------------------------------------------------------------------------------- blank

class RingBlank:
    """A heavy ring blank: band at the back, a round domed head on top (plan radius Rh, dome height H, drum wall).

    Outer surface is r(theta, s): theta round the finger axis (0 = top), s in [-1, 1] across the width.
    plan(a, x) gives the point and normal at arc length a (at the finger radius) and axial offset x, which is
    nearly isometric on the head, so elements placed in plan keep their size and shape."""

    def __init__(self, Ri=8.45, band_w=3.4, band_t=1.7, Rh=7.6, drum=1.5, H=2.6, rim=(0.42, 0.32), bump=None, edge_lo=0.55):
        self.edge_lo = edge_lo
        self.rim_at = 0.8
        self.Ri, self.bw, self.bt, self.Rh, self.drum, self.H, self.rim = Ri, band_w, band_t, Rh, drum, H, rim
        self.bump = bump    # optional f(a, x) -> extra outer height (mm), for mouldings

    def halfw(self, th):
        a = self.Ri * np.abs(th)
        circ = np.sqrt(np.clip(self.Rh ** 2 - a ** 2, 0, None))
        k = 2.2
        return self.bw / 2 + np.logaddexp(0, k * (circ - self.bw / 2)) / k     # smooth max(band, head circle)

    def height(self, a, x):
        """Outer height above the finger radius at plan (a, x)."""
        rho = np.sqrt(a ** 2 + x ** 2)
        u = np.clip(rho / self.Rh, 0, 1.6)
        head = np.clip(1 - u ** 2, 0, None)
        # band thickness eases up into the drum under the head; the dome sits on the drum
        th = np.abs(a) / self.Ri
        back = self.bt + (self.drum - self.bt) * np.exp(-(np.clip(np.abs(a) - self.Rh * 0.55, 0, None) / 3.2) ** 2)
        back = back + 0.25 * (1 - np.cos(np.clip(th, 0, math.pi))) * 0          # placeholder for comfort taper
        h = back + self.H * head ** 0.7
        r0, rw = self.rim                                                     # moulding round the dome's foot
        h = h + r0 * np.exp(-((rho - self.Rh * self.rim_at) / rw) ** 2) * (rho < self.Rh * 1.05)
        if self.bump is not None:
            h = h + self.bump(a, x)
        return h

    def point(self, th, s):
        w = self.halfw(th)
        x = s * w
        a = self.Ri * th
        edge = self.edge_lo + (1 - self.edge_lo) * np.clip(1 - s ** 2, 0, 1) ** 0.35              # crowned section, a wall at the edges
        h = self.height(a, x) * edge
        r = self.Ri + h
        return np.stack([r * np.sin(th), x, r * np.cos(th)], -1)

    def mesh(self, nth=1400, ns=260):
        th = np.linspace(-math.pi, math.pi, nth, endpoint=False)
        # outer: s from -1 to 1 (denser at the edges), inner: back from 1 to -1 at the finger radius (slight comfort crown)
        so = np.sin(np.linspace(-math.pi / 2, math.pi / 2, ns))
        si = so[::-1][1:-1]
        TH, SO = np.meshgrid(th, so, indexing="ij")
        outer = self.point(TH, SO)
        TH2, SI = np.meshgrid(th, si, indexing="ij")
        w2 = self.halfw(TH2)
        ri = self.Ri - 0.12 * (1 - SI ** 2)
        inner = np.stack([ri * np.sin(TH2), SI * w2, ri * np.cos(TH2)], -1)
        loops = np.concatenate([outer, inner], 1)                            # (nth, nl, 3)
        nl = loops.shape[1]
        V = loops.reshape(-1, 3)
        F = _grid_tris(nth, nl, closed_u=True)
        return V, F, (nth, ns)

    # -- plan coordinates: a = arc round the ring at the finger radius, x = ARC LENGTH across the surface from the
    # centre line (not the axial offset). Measuring x along the surface keeps an element its true width where the
    # head curves down into its flank, instead of squashing it into a tab standing on the edge.
    def _arc(self):
        if getattr(self, "_tab", None) is not None:
            return self._tab
        from scipy.interpolate import RegularGridInterpolator as RGI
        thg = np.linspace(-math.pi, math.pi, 1025)
        sg = np.linspace(-1, 1, 801)
        TH, S = np.meshgrid(thg, sg, indexing="ij")
        Pt = self.point(TH, S)
        seg = np.linalg.norm(np.diff(Pt, axis=1), axis=-1)
        Lc = np.concatenate([np.zeros((len(thg), 1)), np.cumsum(seg, 1)], 1)
        Lc -= Lc[:, [400]]                                               # 0 on the centre line
        hw = np.minimum(-Lc[:, 0], Lc[:, -1])
        ug = np.linspace(-1, 1, 801)
        Sinv = np.stack([np.interp(ug * hw[i], Lc[i], sg) for i in range(len(thg))])
        self._tab = (thg, hw, RGI((thg, ug), Sinv), RGI((thg, sg), Lc))
        return self._tab

    def arc_hw(self, th):
        thg, hw, _, _ = self._arc()
        return np.interp(np.asarray(th, float), thg, hw)

    def s_of(self, a, x):
        thg, hw, Si, _ = self._arc()
        th = np.clip(np.asarray(a, float) / self.Ri, -math.pi, math.pi)
        u = np.clip(np.asarray(x, float) / np.interp(th, thg, hw), -1, 1)
        return Si(np.stack([np.ravel(th), np.ravel(u)], -1)).reshape(np.shape(th))

    def axial(self, a, x):
        th = np.asarray(a, float) / self.Ri
        return self.s_of(a, x) * self.halfw(th)

    def arc_of(self, a, x_axial):
        """Axial x -> arc x (for masks computed from mesh vertices)."""
        _, _, _, Lt = self._arc()
        th = np.clip(np.asarray(a, float) / self.Ri, -math.pi, math.pi)
        s = np.clip(np.asarray(x_axial, float) / self.halfw(th), -1, 1)
        return Lt(np.stack([np.ravel(th), np.ravel(s)], -1)).reshape(np.shape(th))

    def plan(self, a, x, n_out=True):
        """Point and outward normal on the outer surface at plan coordinates (a, x)."""
        a = np.asarray(a, float); x = np.asarray(x, float)
        th = a / self.Ri
        s = np.clip(self.s_of(a, x), -0.999, 0.999)
        P = self.point(th, s)
        e = 1e-3
        Pa = self.point((a + e) / self.Ri, np.clip(self.s_of(a + e, x), -0.999, 0.999)) - P
        Px = self.point(th, np.clip(self.s_of(a, x + e), -0.999, 0.999)) - P
        N = np.cross(Px, Pa)
        N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-12
        return P, N, Pa / e, Px / e

    def stretch(self, a, x):
        """Plan a is measured at the finger radius; up on the head the surface is that much longer round the ring.
        Multiply an element's a-offsets by this so it keeps its true length."""
        th = a / self.Ri
        r = np.linalg.norm(self.point(np.array(th), np.array(np.clip(self.s_of(a, x), -0.999, 0.999)))[[0, 2]])
        return self.Ri / r


# ----------------------------------------------------------------------------------------------- elements

def _section(eta, crest, groove, gw, rnd=1.7):
    """Height profile across an element (eta in [-1, 1]): a carved, off-centre crest with convex flanks, and an
    optional engraved V groove beside the crest. Returns 0 at the edges, 1 at the crest."""
    d = eta - crest
    half = np.where(d >= 0, 1 - crest, 1 + crest)
    f = np.clip(1 - (np.abs(d) / half) ** 2, 0, 1) ** rnd    # rnd 1.3: a bell, round on top and flaring into the ground with no step (the fused, polished look); 0.5 reads as a slab
    if groove > 0:
        g = groove * np.clip(1 - np.abs(eta - crest * 0.2) / gw, 0, 1) ** 1.2
        f = np.maximum(f - g, 0.08 * f)
    return f


def crescent(L, W, H, bend=0.6, curl=0.0, crest=0.35, groove=0.0, gw=0.18, peak=0.38, lift=0.0, tip_lift=0.0,
             sink=0.35, nu=90, nv=21, tip=0.09, rnd=1.3, fillet=0.0, conform=True):
    """One ornament element: a pointed crescent / flame / acanthus lobe, built as a swept cut section.

    Local frame: x along the element's chord (0..L), y across, z up off the surface. bend is the total turn of
    the spine (radians) with curl adding a tighter hook at the far end (tight at the head, long sweep at the tail),
    W the maximum full width (at `peak` along the length), H the crest height. Both ends draw out to a point
    (half-width `tip`). The section is sunk `sink` below the surface so it fuses when unioned.
    lift raises the whole element (layering over a neighbour), tip_lift raises the far tip off the surface (an
    undercut curl). Returns (verts in local frame, faces, spine)."""
    u = np.linspace(0, 1, nu)
    turn = bend * u + curl * u ** 3
    ds = L / (nu - 1)
    ang = np.concatenate([[0], np.cumsum((turn[1:] + turn[:-1]) / 2 * 0 + np.diff(turn) * 0)])  # keep shape
    k = np.gradient(turn) / ds                                              # curvature along the spine
    phi = np.cumsum(k) * ds
    phi -= phi[0]
    sp = np.zeros((nu, 2))
    sp[1:, 0] = np.cumsum(np.cos(phi[:-1]) * ds)
    sp[1:, 1] = np.cumsum(np.sin(phi[:-1]) * ds)
    tg = np.stack([np.cos(phi), np.sin(phi)], 1)
    nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
    a, b = peak / (1 - peak) * 1.0, 1.0
    prof = (u ** a) * ((1 - u) ** b)
    prof /= prof.max()
    hw = np.maximum(W / 2 * prof ** 0.85, tip)
    hh = H * np.maximum(prof ** 0.6, 0.05) + lift + tip_lift * u ** 2.5
    base = lift * 0.0 + tip_lift * u ** 2.5                                 # a lifted tip lifts its underside too
    # the section: a round core (|eta| <= 1) standing on a concave fillet skirt out to 1 + fillet, so every
    # stroke grows out of the ground the way a DynaMeshed and polished insert does, never a cookie-cutter wall
    core = -np.cos(np.linspace(0, math.pi, nv))
    ns_ = max(3, nv // 4)
    sk = np.linspace(0, 1, ns_ + 1)[1:]
    eta = np.concatenate([-(1 + fillet * sk[::-1]), core, 1 + fillet * sk]) if fillet > 0 else core
    c0 = 0.28 if fillet > 0 else 0.0
    loops = []
    for i in range(nu):
        c = sp[i]; n = nr[i]
        side = np.sign(bend + curl) if (bend + curl) != 0 else 1.0
        e_in = np.clip(eta, -1, 1)
        f = _section(e_in, crest * side, groove, gw, rnd)
        # the edges dive EDGE_DIVE under the ground, deeper than the stipple pits: an edge lying on the blank leaves coincident skins, and one passing over a pit leaves a pinhole tunnel under it (genus 259 on the first dome ring); both
        # mesh as zero-thickness flaps (they read as 0.0 mm walls in the thickness check)
        z = base[i] - EDGE_DIVE + (c0 + (1 - c0) * f) * (hh[i] - base[i] + EDGE_DIVE)
        out = np.abs(eta) > 1
        if fillet > 0:
            t = (np.abs(eta[out]) - 1) / fillet
            z[out] = (base[i] + c0 * (hh[i] - base[i])) * (1 - t) ** 2 - 0.03 * t
        top = np.stack([c[0] + n[0] * eta * hw[i], c[1] + n[1] * eta * hw[i], z], 1)
        bot_z = -sink + base[i] * 0.85
        e_max = eta[-1]
        if conform:     # underside follows the ground across the whole width (a 2-point chord left air pockets
            eb = eta[::-1] * e_max / max(abs(eta[-1]), 1e-9)       # under wide strokes on the shank: genus 11 after remesh)
            bot = np.stack([c[0] + n[0] * eb * hw[i], c[1] + n[1] * eb * hw[i], np.full(len(eb), bot_z)], 1)
        else:
            bot = np.array([[c[0] + n[0] * hw[i] * e_max, c[1] + n[1] * hw[i] * e_max, bot_z],
                            [c[0] - n[0] * hw[i] * e_max, c[1] - n[1] * hw[i] * e_max, bot_z]])
        loops.append(np.concatenate([top, bot]))
    loops = np.array(loops)
    nl = loops.shape[1]
    V = loops.reshape(-1, 3)
    F = list(_grid_tris(nu, nl))
    # caps: fan each end loop to its centroid (the loop is already tiny, so the end reads as a point)
    for i, flip in ((0, True), (nu - 1, False)):
        cidx = len(V)
        V = np.vstack([V, loops[i].mean(0)])
        for j in range(nl):
            t = (i * nl + j, i * nl + (j + 1) % nl, cidx)
            F.append(t[::-1] if flip else t)
    F = np.array(F, np.int64)
    m = trimesh.Trimesh(V, F, process=False)
    if m.volume < 0:
        F = F[:, ::-1]
    return V, F, np.column_stack([sp, hh, hw])        # spine: x, y, crest height, true half-width


_DEEP = np.random.default_rng(7)


def place(blank, V, a0, x0, rot, mirror=False, scale=1.0, drop=0.0, k=None, deep=None):
    """Drape an element onto the blank: its local origin goes to plan (a0, x0), x axis turned `rot` radians
    from the +a direction (round the ring), local z along the surface normal. Every vertex is mapped through
    the plan, so a long element bends over the dome and down the shoulder instead of sticking out flat."""
    V = np.asarray(V, float) * scale
    y = -V[:, 1] if mirror else V[:, 1]
    ca, sa = math.cos(rot), math.sin(rot)
    k = blank.stretch(a0, x0) if k is None else k
    a = a0 + (ca * V[:, 0] - sa * y) * k
    x = x0 + sa * V[:, 0] + ca * y
    P, N, _, _ = blank.plan(a, x)
    # every element's buried part (edges and underside) goes a slightly different depth: with all of them at exactly
    # -EDGE_DIVE and -sink, overlapping elements share coincident faces under the ground, and the exact union turns
    # those into zero-volume slivers and pinhole tunnels (71 slivers, genus 96 on the dome ring)
    deep = _DEEP.uniform(0.0, 0.06) if deep is None else deep
    Z = V[:, 2] - drop
    Z = np.where(V[:, 2] < 0, Z - deep, Z)
    return P + N * Z[:, None]


# ----------------------------------------------------------------------------------------------- ground

def stipple(blank, V, mask_fn, pitch=0.2, depth=0.07, rad=0.11, seed=0):
    """Matte ground: scatter pits (a jittered grid, never a row) over the outer surface and press them in along
    the normal where mask_fn(a, x) > 0. Returns displaced verts. V must come from blank.mesh()."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    r = np.linalg.norm(V[:, [0, 2]], axis=1)
    th = np.arctan2(V[:, 0], V[:, 2])
    a = blank.Ri * th; x = blank.arc_of(a, V[:, 1])
    outer = r > blank.Ri + 0.05
    A0, A1 = a.min(), a.max(); X0, X1 = x.min(), x.max()
    ga, gx = np.meshgrid(np.arange(A0, A1, pitch), np.arange(X0, X1, pitch), indexing="ij")
    pts = np.column_stack([ga.ravel(), gx.ravel()]) + rng.uniform(-0.45, 0.45, (ga.size, 2)) * pitch
    dep = depth * rng.uniform(0.6, 1.25, len(pts))
    rr = rad * rng.uniform(0.75, 1.2, len(pts))
    tree = cKDTree(pts)
    q = np.column_stack([a[outer], x[outer]])
    d, idx = tree.query(q, k=4, distance_upper_bound=rad * 2.2)
    dd = np.zeros(len(q))
    for k in range(4):
        ok = np.isfinite(d[:, k])
        ii = idx[ok, k]
        dd[ok] = np.maximum(dd[ok], dep[ii] * np.clip(1 - (d[ok, k] / rr[ii]) ** 2, 0, None) ** 1.5)
    w = np.clip(mask_fn(q[:, 0], q[:, 1]), 0, 1)
    n = np.zeros((len(V), 3))
    n[:, 0] = np.sin(th); n[:, 2] = np.cos(th)
    V2 = V.copy()
    V2[outer] -= n[outer] * (dd * w)[:, None]
    return V2


# ----------------------------------------------------------------------------------------------- union + checks

def union(parts):
    """Live union of the blank and every insert (manifold3d, exact). parts: list of (V, F)."""
    ms = [to_manifold(V, F) for V, F in parts]
    return mf.Manifold.batch_boolean(ms, mf.OpType.Add)


def float_check(blank, inserts, min_buried=0.6):
    """Every insert must be rooted in the blank: at least min_buried of its spine must sit with its underside
    below the surface (a dropped IMM part that hovers is a floater, and the union would keep it as a 2nd body)."""
    bad = []
    for name, spine_world_under in inserts:
        if spine_world_under < min_buried:
            bad.append((name, round(spine_world_under, 2)))
    return bad


def spine_plan(spine, a0, x0, rot, mirror=False, k=1.0):
    """The element's spine in plan coordinates (for spacing and footprint checks)."""
    y = -spine[:, 1] if mirror else spine[:, 1]
    ca, sa = math.cos(rot), math.sin(rot)
    return np.column_stack([a0 + (ca * spine[:, 0] - sa * y) * k, x0 + sa * spine[:, 0] + ca * y])


class Packer:
    """Hand placement, automated the way the maker does it by eye: each new element follows the flow, keeps
    its own channel (it may overlap a neighbour's edge, never sit on its spine), and stays on the field."""

    def __init__(self, inside):
        self.inside = inside           # f(a, x) -> bool array: the field the element may sit on
        self.pts = np.zeros((0, 2)); self.w = np.zeros(0); self.h = np.zeros(0); self.id = np.zeros(0, int)
        self.rw = np.zeros(0)
        self.under = 0.0; self.n = 0
        self.fuse, self.clear = 0.12, 0.10     # mm: overlap at least this much, or stay at least this far apart

    def fits(self, sp, hw, overlap=0.5, rw=None, field=True):
        if field and not np.all(self.inside(sp[:, 0], sp[:, 1])):
            return False
        if len(self.pts) == 0:
            return True
        d = np.sqrt(((sp[:, None, :] - self.pts[None, :, :]) ** 2).sum(-1))
        need = (hw + self.w[None, :]) * (1 - overlap)
        if np.any(d < need):
            return False
        # no near-misses: two inserts either fuse well into each other or keep a clear gap. Edges (or a tip and a
        # flank) that only just touch leave a hairline crevice that the union closes into a pinhole tunnel, and the
        # wax gets an undrainable slot. rw = true half-width at each spine sample, so tips count as thin.
        if rw is not None:
            gap = d - rw[:, None] - self.rw[None, :]
            gm = np.full(self.n, np.inf); np.minimum.at(gm, self.id, gap.min(0))
            if np.any((gm > -self.fuse) & (gm < self.clear)):
                return False
        touch = d < (hw + self.w[None, :])
        self.under = float(self.h[touch.any(0)].max()) if touch.any() else 0.0   # height of what it crosses
        return True

    def add(self, sp, hw, h=0.0, rw=None):
        self.pts = np.vstack([self.pts, sp]); self.w = np.concatenate([self.w, np.full(len(sp), hw)])
        self.h = np.concatenate([self.h, np.full(len(sp), h)]); self.id = np.concatenate([self.id, np.full(len(sp), self.n)])
        self.rw = np.concatenate([self.rw, rw if rw is not None else np.full(len(sp), hw * 1.5)])
        self.n += 1


# ----------------------------------------------------------------------------------------------- 3D gate

class Gate:
    """Exact check of each new element against the blank and every element it overlaps, before it is kept.
    The plan-view near-miss rule in Packer misses contacts made above the ground (two strokes leaning together
    over a curved surface, a stroke that touches a neighbour at two places), and each of those is a tunnel in the
    union. The gate refuses an element when, clipped to a box round the pair, blank + this + that has a handle,
    when it barely touches a neighbour (overlap under `touch` mm3), or when it doesn't reach the blank at all."""

    def __init__(self, blank_V, blank_F, touch=0.02, pairs=False):
        self.B = to_manifold(blank_V, blank_F)
        self.items = []                       # (lo, hi, manifold)
        self.touch = touch
        self.pairs = pairs        # default for ok(); hand-placed lead strokes pass pairs=False (checking them too
                                  # threw out the lead sweeps: 309 -> 254 inserts, a sparse dome)
        self.refused = 0

    @staticmethod
    def _box(lo, hi, pad=0.3):
        lo = np.asarray(lo) - pad; hi = np.asarray(hi) + pad
        return mf.Manifold.cube((hi - lo).tolist()).translate(lo.tolist())

    @staticmethod
    def _handles(M):
        return sum(max(0, c.genus()) for c in M.decompose())

    def ok(self, V, F, extra=(), pairs=None):
        p = to_manifold(V, F); lo, hi = V.min(0), V.max(0)
        box = self._box(lo, hi); Bx = self.B ^ box
        if (p ^ self.B).volume() < 1e-3 or self._handles((Bx + p) ^ box):
            self.refused += 1; return None
        pairs = self.pairs if pairs is None else pairs
        for (lo2, hi2, q) in (list(self.items) + list(extra) if pairs else []):
            if np.any(lo > hi2 + 0.05) or np.any(lo2 > hi + 0.05):
                continue
            I = p ^ q
            if I.is_empty():
                continue
            if I.volume() < self.touch:
                self.refused += 1; return None
            bx = self._box(np.minimum(lo, lo2), np.maximum(hi, hi2))
            if self._handles(((self.B ^ bx) + p + q) ^ bx):
                self.refused += 1; return None
        return (lo, hi, p)

    def add(self, item):
        self.items.append(item)


# ----------------------------------------------------------------------------------------------- seal

def find_handles(M, leaf=1.2):
    """Locate the handles (tunnels) of a closed mesh: split its box in halves recursively, keeping the halves whose
    clipped pieces still have genus above 0. Returns small boxes [(lo, hi)], one per tunnel. The ring's own loop
    is cut by the first split and is not reported."""
    def g(lo, hi):
        I = M ^ mf.Manifold.cube((hi - lo).tolist()).translate(lo.tolist())
        return sum(max(0, p.genus()) for p in I.decompose())
    bb = M.bounding_box(); out = []
    def rec(lo, hi, gg):
        if gg <= 0:
            return
        if (hi - lo).max() < leaf:
            out.append((lo, hi)); return
        ax = int(np.argmax(hi - lo)); m = (lo[ax] + hi[ax]) / 2
        h1 = hi.copy(); h1[ax] = m; l2 = lo.copy(); l2[ax] = m
        a, b = g(lo, h1), g(l2, hi)
        if a + b < gg and (hi - lo).max() < 3 * leaf:     # a tunnel lies across this cut: the box itself is the spot
            out.append((lo, hi))
        rec(lo, h1, a); rec(l2, hi, b)
    lo = np.array(bb[:3]) - 0.01; hi = np.array(bb[3:]) + 0.01
    rec(lo, hi, g(lo, hi))
    return out


def seal(M, blank, rise=0.06, verbose=True):
    """Close the last pinhole tunnels at the ground: inside each located box, raise the blank's outer surface by
    `rise` mm and union it in. A 0.06 mm rise over a 1 mm patch of stippled ground can't be seen and fills the
    crevice where two strokes meet the ground. Returns the sealed manifold."""
    import trimesh as _tm
    V, F, _ = blank.mesh(nth=900, ns=160)
    t = _tm.Trimesh(V, F, process=False)
    if t.volume < 0:
        t.invert()
    outer = np.hypot(V[:, 0], V[:, 2]) > blank.Ri + 0.05
    Bd = to_manifold(V + t.vertex_normals * rise * outer[:, None], np.asarray(t.faces))
    boxes = find_handles(M)
    for lo, hi in boxes:
        c = (lo + hi) / 2; s = np.maximum(hi - lo, 1.0) + 0.4
        M = M + (Bd ^ mf.Manifold.cube(s.tolist()).translate((c - s / 2).tolist()))
        if verbose:
            print("  sealed a pinhole at", np.round(c, 2), flush=True)
    return M



def _raster(M, lo, hi, vx):
    """Solid occupancy of M on a grid (slices filled even-odd)."""
    from PIL import Image, ImageDraw
    n = np.ceil((hi - lo) / vx).astype(int) + 1
    occ = np.zeros(n, bool)
    for k in range(n[2]):
        acc = np.zeros((n[1], n[0]), bool)
        for c in M.slice(lo[2] + k * vx).to_polygons():
            c = (np.array(c) - lo[:2]) / vx
            im = Image.new("1", (int(n[0]), int(n[1])), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in c], fill=1)
            acc ^= np.array(im)
        occ[:, :, k] = acc.T
    return occ


def close_handle(M, lo, hi, vx=0.01, r=0.12):
    """Fill one pinhole tunnel: voxelize the box round it at 10 microns, close (dilate then erode) with a 0.12 mm
    ball, and union back only the metal the closing adds (grown 2 voxels into the existing metal). Fills crevices
    narrower than about 0.24 mm inside a 1 mm box and nothing else. Follow it with a voxel remesh (finish.py)."""
    from scipy import ndimage
    from skimage.measure import marching_cubes
    pad = r + 3 * vx; lo = np.asarray(lo) - pad; hi = np.asarray(hi) + pad
    occ = _raster(M, lo, hi, vx)
    rr = int(round(r / vx)); g = np.mgrid[-rr:rr + 1, -rr:rr + 1, -rr:rr + 1]; ball = (g ** 2).sum(0) <= rr * rr
    cl = ndimage.binary_closing(np.pad(occ, rr + 1), structure=ball)[rr + 1:-rr - 1, rr + 1:-rr - 1, rr + 1:-rr - 1]
    add = cl & ~occ
    m = int(np.ceil(pad / vx)); inner = np.zeros_like(add); inner[m:-m, m:-m, m:-m] = True
    add &= inner
    if not add.any():
        return M, 0.0
    fill = np.pad(ndimage.binary_dilation(add, iterations=2) & (cl | occ), 1)
    v, f, _, _ = marching_cubes(fill.astype(np.float32), 0.5)
    return M + to_manifold((v - 1) * vx + lo, f[:, ::-1]), float(add.sum() * vx ** 3)



def bezel_cut(zg, R, seg=360):
    """The seat of a bezel for a round stone of radius R with its girdle at height zg (axis z): a clear cone under
    the pavilion, the bearing (the pavilion's own profile, 1.5% oversize, so no metal sits
    inside the stone: a flat ledge put 0.66 mm3 of metal in it), the girdle seat, and the opening over the crown
    with the lip leaning in. Subtract it after the bezel wall is added, and again after any remesh (finish.py)."""
    cut = mf.Manifold.cylinder(3.2, 0.4, R - 0.35, seg).translate([0, 0, zg - 3.45])
    cut = cut + mf.Manifold.cylinder(0.3, R - 0.35, R - 0.35, seg).translate([0, 0, zg - 0.3])
    cut = cut + mf.Manifold.cylinder(0.35, R + 0.04, R + 0.04, seg).translate([0, 0, zg - 0.1])
    cut = cut + mf.Manifold.cylinder(0.4, R + 0.04, R - 0.16, seg).translate([0, 0, zg + 0.24])
    cut = cut + mf.Manifold.cylinder(3.0, R - 0.16, R - 0.16, seg).translate([0, 0, zg + 0.62])
    D = 2 * R; k = 1.015
    prof = [(1.0, 0.0), (1.0, 0.01), (0.9865, 0.02), (0.9468, 0.04), (0.9073, 0.05), (0.8678, 0.07), (0.7891, 0.11),
            (0.711, 0.15), (0.6251, 0.18), (0.4877, 0.24), (0.3503, 0.29), (0.1671, 0.36), (0.0298, 0.42), (0.0, 0.43)]
    pts = [(0.0, 0.0)] + [(r * R * k, -d * D * k) for r, d in prof]          # (radius/R, depth/D) of the kit's brilliant
    pts = [(0.0, 0.0)] + [p for p in pts[1:]] + [(0.0, -0.43 * D * k)]
    poly = [(x, y) for x, y in pts][::-1]
    bearing = mf.Manifold.revolve(mf.CrossSection([poly]), seg)
    if bearing.volume() <= 0 or bearing.is_empty():
        bearing = mf.Manifold.revolve(mf.CrossSection([poly[::-1]]), seg)
    return cut + bearing.translate([0, 0, zg])
