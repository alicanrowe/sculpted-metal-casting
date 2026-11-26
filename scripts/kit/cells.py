"""Enamel cells (25 Nov 2026): real enamel cells, cut after meshing.

Client critique, 25 Nov 2026: the colour fields looked messy and unrealistic and the making was unclear.
The old coat() lifted a tube and cut the balloon at a grazing angle, so the colour ran out to a
feathered, uneven edge with no metal wall to hold it. No cold-enamel shop could fill that.

v3 makes every colour field a cast cell, the way a champleve enamel or a soft-enamel pin is made:
  * the cell is a pocket cast into the brass, its walls square to the surface (radial on a balloon), its floor an
    even `depth` below the outer surface, inside floor corner left by the voxel (~0.04 mm, the wax printer rounds
    it to about 0.2), rim edge sharp;
  * a land of metal >= 0.8 mm (Materialise OnSite brass minimum) surrounds every cell: to a neighbouring cell, a
    stone seat, a neck or a twist; metal under the floor to any hollow >= 0.8 mm;
  * the enamel fills the cell to FILL_BELOW (0.10 mm) under the rim, following the curve of the crown, so the
    metal edge stands as a crisp line round the colour; it is 0.03 mm clear of walls and floor (no clipping).
Cutting is a mesh boolean (manifold3d) on the finished, smoothed metal, so the rim stays sharp.

A cell is recorded on the Scene by helium.inlay() / helium.coat(); make.py calls apply(s, mesh) after meshing.
"""
import math, os, sys
import numpy as np

FILL_BELOW = 0.10     # enamel surface under the rim (mm)
GAP = 0.03            # enamel clear of the metal walls and floor (mm)
LAND = 0.8            # metal round every cell (mm)
FLOOR = 0.8           # metal under the floor to any hollow (mm)
MIN_W = 1.2           # narrowest cell a syringe can fill (mm)
SIMPLIFY = 0.003      # marching-cubes meshes thinned to within 3 microns (a long cell was 6.7M triangles)
CLIP_TOL = 0.005      # mm3 of enamel/metal overlap allowed: thinning leaves specks of ~0.001 (a 0.1 mm cube), invisible
MENISCUS = 0.05       # enamel creeps this far up the wall at the edge (mm)


def _eval(rows, pts):
    from sdf import eval_pts
    if len(rows) == 0: return np.full(len(pts), 1e3, np.float32)
    return eval_pts(np.ascontiguousarray(pts, np.float64), np.ascontiguousarray(rows, np.float64),
                    np.arange(len(rows), dtype=np.int64))


def _cull(rows, lo, hi):
    if len(rows) == 0: return rows
    k = rows[:, 2:3]
    m = np.all(rows[:, 19:22] - k <= hi, 1) & np.all(rows[:, 22:25] + k >= lo, 1)
    return rows[m]


def outer_rows(s):
    """The metal without its hollows: the cell depth is measured from the outside skin only."""
    P = s.array(); keep = np.ones(len(P), bool)
    for a, b in getattr(s, "hollow_ranges", []): keep[a:b] = False
    return P[keep]


def cavity_rows(s):
    """The hollows as solids (union), for the floor-thickness check."""
    P = s.array(); out = []
    for a, b in getattr(s, "hollow_ranges", []):
        r = P[a:b].copy(); r[:, 1] = 0; r[:, 2] = 0; out.append(r)
    return np.vstack(out) if out else np.zeros((0, P.shape[1]))


# ---------------------------------------------------------------- footprints (signed, mm, negative inside)
def _superellipse(u, v, a, b, m):
    q = (np.abs(u / a) ** m + np.abs(v / b) ** m) ** (1.0 / m)
    return (q - 1.0) * np.minimum(a, b)


def foot_spot(c, pts):
    """Oval/pill window on a lobe crown: footprint in the tangent plane, walls parallel to `up`."""
    o = np.asarray(c["c"]); xa = np.asarray(c["xa"]); ya = np.asarray(c["ya"])
    d = pts - o
    g = _superellipse(d @ xa, d @ ya, c["rx"], c["ry"], c.get("m", 2.6))
    return np.maximum(g, -(d @ np.asarray(c["up"]) + c["depth"] + 0.8))     # this side only, never the back


def foot_band(c, pts, tree=None):
    """Long pill down a balloon's crown: coordinates (arc length along the path, arc across the crown); the
    walls are radial, so they meet the surface square all the way round."""
    from scipy.spatial import cKDTree
    P = np.asarray(c["P"]); T = np.asarray(c["T"]); N = np.asarray(c["N"])
    S = S0 = np.asarray(c["S"]); R = np.asarray(c["R"])
    # the path is stored every 0.1 mm; snapping to the nearest sample made the frame jump ~0.06 mm at the crown,
    # which marched out as saw teeth along the rim. Interpolate the frame to 5 microns first.
    k = 20; u = np.arange((len(S) - 1) * k + 1) / k; i0 = np.minimum(u.astype(int), len(S) - 2); t = (u - i0)[:, None]
    lerp = lambda A: A[i0] * (1 - t) + A[i0 + 1] * t
    P = lerp(P); T = lerp(T); N = lerp(N); S = lerp(S[:, None])[:, 0]; R = lerp(R[:, None])[:, 0]
    T /= np.linalg.norm(T, axis=1)[:, None]; N -= T * np.einsum("ij,ij->i", N, T)[:, None]
    N /= np.linalg.norm(N, axis=1)[:, None]; B = np.cross(T, N)
    tree = tree or cKDTree(P)
    _, i = tree.query(pts)
    v = pts - P[i]
    s = S[i] + np.einsum("ij,ij->i", v, T[i])
    vn = np.einsum("ij,ij->i", v, N[i]); vb = np.einsum("ij,ij->i", v, B[i])
    phi = np.arctan2(vb, vn)
    a = phi * R[i]                                   # arc across the crown at the surface
    s0, s1 = c["s0"], c["s1"]; sc = (s0 + s1) / 2; Ls = (s1 - s0) / 2
    W = np.interp(s, S0, c["W"])
    g = _superellipse(s - sc, a, Ls, W, c.get("m", 3.0))
    g[np.abs(phi) > 1.4] = 10.0                      # never the far side of the tube
    return g


def footprint(c, pts, tree=None):
    return foot_spot(c, pts) if c["kind"] == "spot" else foot_band(c, pts, tree)


def cell_box(c):
    if c["kind"] == "spot":
        r = max(c["rx"], c["ry"]) + 1.2; h = c["depth"] + 2.0; o = np.asarray(c["c"])
        return o - max(r, h), o + max(r, h)
    P = np.asarray(c["P"]); S = np.asarray(c["S"])
    a, b = c.get("bs0", c["s0"] - 1.5), c.get("bs1", c["s1"] + 1.5)
    m = (S >= a) & (S <= b)
    # only round the crown, not the whole tube (a 9 mm balloon's box ran a 15 GB machine out of memory)
    R = np.asarray(c["Rraw"])[m]; N = np.asarray(c["N"])[m]; Pm = P[m]
    C = np.vstack([Pm + N * R[:, None], Pm + N * (0.45 * R[:, None])])      # crown down to a squashed balloon's top
    pad = float(np.max(np.asarray(c["W"])[m])) * 1.15 + 1.2
    return C.min(0) - pad, C.max(0) + pad


def chunks(c, L=4.0, over=0.8):
    """Long bands are meshed in overlapping lengths (memory); the pieces union into one cell."""
    if c["kind"] == "spot" or c["s1"] - c["s0"] <= L + 3: return [c]
    a0, a1 = c["s0"] - 1.5, c["s1"] + 1.5; k = int(math.ceil((a1 - a0) / L)); e = np.linspace(a0, a1, k + 1)
    return [dict(c, bs0=float(e[i] - over), bs1=float(e[i + 1] + over)) for i in range(k)]


# ---------------------------------------------------------------- meshing helpers
def _mc(field, lo, vox):
    from skimage.measure import marching_cubes
    f = field.copy(); f[0], f[-1], f[:, 0], f[:, -1], f[:, :, 0], f[:, :, -1] = 1, 1, 1, 1, 1, 1
    if f.min() >= 0: return None
    V, F, _, _ = marching_cubes(f, 0.0, spacing=(vox,) * 3, gradient_direction="ascent")
    V = V + lo
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0: F = F[:, ::-1]     # outward normals (positive volume)
    return V, np.ascontiguousarray(F)


def _man(VF, simp=False):
    import manifold3d as m3
    V, F = VF
    mesh = m3.Mesh(vert_properties=np.ascontiguousarray(V, np.float32), tri_verts=np.ascontiguousarray(F, np.uint32))
    mesh.merge()
    M = m3.Manifold(mesh)
    return M.simplify(SIMPLIFY) if simp else M


def to_man(tm):
    return _man((np.asarray(tm.vertices), np.asarray(tm.faces)))


def from_man(M):
    """Manifold -> trimesh. A boolean can leave two distinct vertices at one position (a pinch); an STL welds
    them and the edge then has four faces. Pull each such vertex 0.004 mm toward its own faces' centroid."""
    import trimesh
    mm = M.to_mesh()
    V = np.asarray(mm.vert_properties)[:, :3].astype(np.float64); F = np.asarray(mm.tri_verts).astype(np.int64)
    key = np.round(V.astype(np.float32), 5)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    dup = np.nonzero(cnt[inv.ravel()] > 1)[0]
    if len(dup):
        cen = np.zeros_like(V); w = np.zeros(len(V))
        fc = V[F].mean(1)
        for k in range(3):
            np.add.at(cen, F[:, k], fc); np.add.at(w, F[:, k], 1)
        dvec = cen[dup] / np.maximum(w[dup], 1)[:, None] - V[dup]
        V[dup] += dvec / np.maximum(np.linalg.norm(dvec, axis=1, keepdims=True), 1e-12) * 0.004
    return trimesh.Trimesh(V, F, process=False)


def clean_enamel(et):
    """Drop the specks a chunked band can leave (Talon 3.1: 72 under 0.0001 mm3, plus three pinched edges where
    two chunks touch), and close any pinch left with pymeshfix, so the enamel STL stays one watertight body."""
    import trimesh
    et = trimesh.Trimesh(np.asarray(et.vertices), np.asarray(et.faces), process=True)   # weld as the STL will (Helium: 2-face flaps)
    parts = et.split(only_watertight=False)
    if len(parts) > 1:
        keep = [p for p in parts if abs(p.volume) > 0.01] or [max(parts, key=lambda p: abs(p.volume))]
        et = trimesh.util.concatenate(keep)
    if not et.is_watertight:
        import pymeshfix
        out = []
        for p in et.split(only_watertight=False):
            v, f = pymeshfix.clean_from_arrays(np.asarray(p.vertices), np.asarray(p.faces))
            out.append(trimesh.Trimesh(v, f, process=False))
        et = trimesh.util.concatenate(out)
        print("cells: enamel repaired, watertight", et.is_watertight, flush=True)
    return et


def _rss():
    import os
    return int(open("/proc/self/statm").read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 1e9


def _coords(lo, n, vox, idx):
    i, j, k = np.unravel_index(idx, n)
    return np.stack([lo[0] + i * vox, lo[1] + j * vox, lo[2] + k * vox], 1)


def grids(c, outer, vox):
    """Sample the outer skin and the footprint on the cell's box (no full coordinate array: memory)."""
    lo, hi = cell_box(c); lo = np.floor((lo - 2 * vox) / vox) * vox; hi = hi + 2 * vox   # one global lattice: chunk overlaps mesh identically (no seams)
    n = np.ceil((hi - lo) / vox).astype(int) + 1
    rows = _cull(outer, lo, hi)
    dep = c["depth"]
    # two levels: a coarse pass everywhere, the full-resolution SDF only in the shell the cell lives in
    k = 4; nc = (n - 1) // k + 2
    axc = [lo[i] + np.arange(nc[i]) * vox * k for i in range(3)]
    Gc = np.stack(np.meshgrid(*axc, indexing="ij"), -1).reshape(-1, 3)
    dc = _eval(rows, Gc).reshape(nc)
    from scipy.ndimage import map_coordinates
    I = np.indices(n, dtype=np.float32).reshape(3, -1) / k
    d = map_coordinates(dc, I, order=1, mode="nearest").astype(np.float32); del I
    need = np.nonzero(np.abs(d + dep / 2) < dep / 2 + 1.1 + 2.5 * vox * k)[0]
    for q in np.array_split(need, max(1, len(need) // 4000000)):
        d[q] = _eval(rows, _coords(lo, n, vox, q))
    band = np.abs(d + dep / 2) - (dep / 2 + 0.9)       # a shell from 0.9 above the skin to 0.9 under the floor
    g = np.full(len(d), 5.0, np.float32)
    m = np.nonzero(band < 0.2)[0]
    for q in np.array_split(m, max(1, len(m) // 4000000)):
        if len(q): g[q] = footprint(c, _coords(lo, n, vox, q))
    return lo, n, d.reshape(n), g.reshape(n), band.reshape(n)


def build_cell(c, outer, vox):
    """Returns (cutter Manifold, enamel Manifold, samples for the checks), meshing long bands in pieces."""
    cut = en = None; edge = []; flo = []
    for cc in chunks(c):
        lo, n, d, g, band = grids(cc, outer, vox)
        import resource
        print(f"  chunk {cc.get('bs0', 0):.1f}-{cc.get('bs1', 0):.1f} grid {tuple(n)} = {np.prod(n) / 1e6:.0f}M  rss now {_rss():.1f} GB", flush=True)
        dep = cc["depth"]
        prism = _mc(np.maximum(g, band), lo, vox)                     # the cell's footprint through the skin
        far = g > 0.3                                                  # mesh the levels only round the footprint (memory)
        def lim(f): f = f.copy(); f[far] = 1.0; return f
        deep = _mc(lim(d + dep), lo, vox)                              # metal deeper than the floor
        if prism is None or deep is None: continue
        cu = _man(prism, True) - _man(deep, True); del prism
        prism_in = _mc(np.maximum(g + GAP, band), lo, vox)
        # the fill line, FILL_BELOW under the skin, with the small meniscus cured enamel keeps where it wets the wall
        top = _mc(lim(d + FILL_BELOW - MENISCUS * np.clip(1 + g / 0.22, 0, 1) ** 2), lo, vox)
        floor = _mc(lim(d + dep - GAP), lo, vox)
        e = (_man(prism_in, True) ^ _man(top)) - _man(floor, True)
        cut = cu if cut is None else cut + cu
        en = e if en is None else en + e
        cut.num_tri(); en.num_tri()                                    # evaluate now: a lazy CSG tree keeps every chunk alive
        edge.append(_coords(lo, n, vox, np.nonzero(((np.abs(d) < vox * 0.8) & (np.abs(g) < vox * 0.8)).ravel())[0]))
        flo.append(_coords(lo, n, vox, np.nonzero(((np.abs(d + dep) < vox * 0.8) & (g < -0.15)).ravel())[0]))
        del d, g, band
    if cut is None: return None
    return cut, en, dict(edge=np.vstack(edge), floor=np.vstack(flo))


def _build_arrays(c, outer, vox):
    r = build_cell(c, outer, vox)
    if r is None: return None
    a, b = r[0].to_mesh(), r[1].to_mesh()
    return ((np.asarray(a.vert_properties)[:, :3].copy(), np.asarray(a.tri_verts).copy()),
            (np.asarray(b.vert_properties)[:, :3].copy(), np.asarray(b.tri_verts).copy()), r[2])


def apply(s, metal, vox, stones=()):
    """Cut every cell from the finished metal mesh and make its enamel. Returns (metal, enamels, report)."""
    cells = getattr(s, "cells", [])
    if not cells: return metal, [], dict(cells=[])
    import trimesh
    outer = outer_rows(s); cav = cavity_rows(s)
    if not metal.is_watertight:          # a pre-existing pinhole would make the boolean fail: close it first
        import subprocess, tempfile, os
        td = tempfile.mkdtemp(); a, b = os.path.join(td, "in.stl"), os.path.join(td, "out.stl"); metal.export(a)
        r = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "repair_stl.py"), a, b],
                           capture_output=True, text=True)
        print("pre-cut repair:", r.stdout.strip().splitlines()[-1:] if r.stdout else r.stderr[-300:], flush=True)
        if os.path.exists(b): metal = trimesh.load(b)
    M = to_man(metal); built = []
    print("metal manifold", M.status(), round(M.volume(), 1), flush=True)
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    for j, c in enumerate(cells):
        # each cell is built in its own short-lived process: the allocator never handed chunk memory back, and a
        # long band on a big balloon (Knot, the Helium collar) grew 0.3 GB a chunk until a 15 GB machine killed it
        with ctx.Pool(1) as pool:
            r = pool.apply(_build_arrays, (c, outer, vox))
        if r is None: print(f"cell {j} {c['colour']}: empty", flush=True); continue
        cut, en, smp = _man(r[0]), _man(r[1]), r[2]
        print(f"cell {j} built: cutter {len(r[0][1])} tris, enamel {len(r[1][1])} tris, parent rss {_rss():.1f} GB", flush=True)
        built.append((j, c, cut, en, smp))
    for j, c, cut, en, smp in built:
        M = M - cut; M.num_tri()
    rep = []; enm = []
    for j, c, cut, en, smp in built:
        e = en ^ M                                   # must be empty (no clipping)
        clip = float(e.volume()) if not e.is_empty() else 0.0
        et = clean_enamel(from_man(en)); vol = float(en.volume())
        # land: from each edge point step LAND along the surface, away from the cell, and look for trouble
        edge = smp["edge"]; bad_land = 0; worst = 9.0
        if len(edge):
            ed = edge[:: max(1, len(edge) // 600)]
            eps = 0.02
            gx = np.stack([footprint(c, ed + np.eye(3)[k] * eps) - footprint(c, ed - np.eye(3)[k] * eps) for k in range(3)], 1)
            dx = np.stack([_eval(outer, ed + np.eye(3)[k] * eps) - _eval(outer, ed - np.eye(3)[k] * eps) for k in range(3)], 1)
            nrm = dx / np.maximum(np.linalg.norm(dx, axis=1, keepdims=True), 1e-9)
            t = gx - nrm * np.einsum("ij,ij->i", gx, nrm)[:, None]
            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
            for step in (0.4, LAND):
                q = ed + t * step
                for _ in range(3):                       # walk back onto the skin
                    dq = _eval(outer, q)
                    gq = np.stack([_eval(outer, q + np.eye(3)[k] * eps) - _eval(outer, q - np.eye(3)[k] * eps) for k in range(3)], 1)
                    gq /= np.maximum(np.linalg.norm(gq, axis=1, keepdims=True), 1e-9)
                    q = q - gq * dq[:, None]
                dq = _eval(outer, q)
                lost = np.abs(dq) > 0.25                  # the surface fell away: the land ran off an edge
                in_other = np.zeros(len(q), bool)
                for k_, c2 in enumerate(cells):
                    if c2 is c: continue
                    in_other |= footprint(c2, q) < 0
                in_stone = np.zeros(len(q), bool)
                for st in stones:
                    cc = np.asarray(st["c"]); nn = np.asarray(st["n"])
                    w = q - cc; rad = np.linalg.norm(w - np.outer(w @ nn, nn), axis=1)
                    in_stone |= (rad < st["D"] / 2 + 0.3) & (np.abs(w @ nn) < st["D"])
                b = lost | in_other | in_stone
                if step == LAND: bad_land = float(b.mean())
                if b.any(): worst = min(worst, step)
        # floor: metal under the cell to any hollow
        fl = smp["floor"]; thin = 0.0; fmin = 9.0
        if len(fl) and len(cav):
            dc = _eval(cav, fl[:: max(1, len(fl) // 2000)])
            fmin = float(dc.min()); thin = float((dc < FLOOR).mean())
        # width: narrowest part of the field
        if c["kind"] == "band":
            S_ = np.asarray(c["S"]); W_ = np.asarray(c["W"]); L_ = c["s1"] - c["s0"]
            mid = (S_ >= c["s0"] + 0.2 * L_) & (S_ <= c["s1"] - 0.2 * L_)
            wmin = 2 * float(W_[mid].min())
        else:
            wmin = 2 * min(c["rx"], c["ry"])
        ok = clip < CLIP_TOL and bad_land < 0.01 and thin < 0.005 and wmin >= MIN_W
        rep.append(dict(cell=j, colour=c["colour"], kind=c["kind"], depth=c["depth"], fill_below=FILL_BELOW,
                        enamel_mm3=round(vol, 2), clip_mm3=round(clip, 4), land_fail=round(bad_land, 3),
                        land_first_fail_mm=None if worst > 8 else worst, floor_min_mm=round(fmin, 2),
                        floor_thin=round(thin, 3), min_width_mm=round(wmin, 2), ok=bool(ok)))
        print("cell", rep[-1], flush=True)
        enm.append((np.asarray(et.vertices), np.asarray(et.faces), c["colour"]))
    out = from_man(M)
    parts = out.split(only_watertight=False)
    if len(parts) > 1:                   # specks a cut can leave at a vent or seat edge (Knot: 74 under 0.0001 mm3)
        keep = [p for p in parts if abs(p.volume) > 0.01]
        print("cells: dropped", len(parts) - len(keep), "specks", flush=True)
        out = trimesh.util.concatenate(keep)
    # enamel vs stones
    for i, (V, F, col) in enumerate(enm):
        et = trimesh.Trimesh(V, F, process=False)
        for st in stones:
            dist = np.linalg.norm(V - np.asarray(st["c"]), axis=1).min() - st["D"] / 2
            if dist < 0.5: rep[i]["ok"] = False; rep[i]["stone_gap"] = round(float(dist), 2)
    allok = all(r["ok"] for r in rep)
    print("cells", "PASS" if allok else "FAIL", flush=True)
    return out, enm, dict(cells=rep, ok=allok)
