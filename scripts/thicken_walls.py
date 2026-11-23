"""Thicken every wall under MIN mm on an STL, smoothly, for a vendor's min-wall rule.

    python -I thicken_walls.py IN.stl OUT.stl [MIN_MM=0.8]

Each face whose inward ray thickness is under MIN gets an outward surface offset
of half its shortfall (target MIN+0.16), spread evenly over the thin patch and
faded out over ~0.8 mm, then smooth-unioned with the part (manifold3d). The patch
is sunk 0.05 mm wherever no offset is wanted so the union leaves no films.
Gaps narrower than ~0.6 mm near a thin wall fuse (they can't be cast or
polished); wider ones are kept at least 0.4 mm open. Runs up to 3 passes until no face is thin. Check with wall_check.py and a
before/after render. Needs trimesh embreex manifold3d scikit-image scipy.
"""
import sys, numpy as np, trimesh, manifold3d as mf
from scipy import ndimage
from scipy.cluster.hierarchy import fcluster, linkage
from skimage import measure


def thicken(src, MIN):
    R = MIN/2 + 0.08      # 0.96 mm across after: margin for cleanup and polish
    P = 0.025             # voxel pitch, mm
    K = 0.15              # smooth-union blend radius, mm
    m = trimesh.load(src) if isinstance(src, str) else src

    def face_thickness(mesh):
        o = mesh.triangles_center - mesh.face_normals*1e-4
        t = np.full(len(o), np.inf)
        for s in range(0, len(o), 50000):
            sl = slice(s, s+50000)
            loc, ri, _ = mesh.ray.intersects_location(o[sl], -mesh.face_normals[sl], multiple_hits=False)
            t[s+ri] = np.linalg.norm(loc - o[sl][ri], axis=1)
        return t

    t = face_thickness(m)
    sel = np.isfinite(t) & (t < MIN) & (t > 0.005) & (m.area_faces > 1e-5)
    thinpts = m.triangles_center[sel]; thint = t[sel]
    print(f"{src}: {len(thinpts)} thin faces")
    if len(thinpts) == 0:
        return m, 0
    lab = fcluster(linkage(thinpts, 'single'), 2.0, 'distance') if len(thinpts) > 1 else np.array([1])
    # keep each patch box small (memory): split big clusters into 6 mm cells
    cell = np.floor(thinpts / 6.0).astype(np.int64)
    key = np.stack([lab, cell[:, 0], cell[:, 1], cell[:, 2]], 1)
    _, lab = np.unique(key, axis=0, return_inverse=True)
    lab = lab.ravel()

    def smax(a, b, k):
        h = np.clip(0.5 + 0.5*(a - b)/k, 0, 1)
        return a*h + b*(1-h) + k*h*(1-h)

    adds = []
    for l in np.unique(lab):
        c = thinpts[lab == l]; ct = thint[lab == l]
        lo = c.min(0) - 1.6; hi = c.max(0) + 1.6
        shape = np.ceil((hi - lo)/P).astype(int) + 1
        ax = [lo[i] + P*np.arange(shape[i]) for i in range(3)]
        g = np.stack(np.meshgrid(*ax, indexing='ij'), -1).reshape(-1, 3)
        inside = m.contains(g).reshape(shape)
        din = ndimage.distance_transform_edt(inside)*P
        dout = ndimage.distance_transform_edt(~inside)*P
        f_orig = din - dout                       # >0 inside
        # offset field: each surface near a thin face moves out by half the
        # shortfall of that face's measured wall, so both sides together bring
        # the wall to TARGET; the offset fades out smoothly over ~0.8 mm.
        TARGET = MIN + 0.16
        seed = np.zeros(shape, np.float32); has = np.zeros(shape, bool)
        idx = np.clip(np.round((c - lo)/P).astype(int), 0, shape - 1)
        order = np.argsort(-ct)              # smallest t written last, wins
        seed[tuple(idx[order].T)] = ((TARGET - ct[order])/2).clip(0, TARGET/2)
        has[tuple(idx.T)] = True
        dist, ind = ndimage.distance_transform_edt(~has, return_indices=True)
        dist *= P
        need = seed[tuple(ind)]
        need = ndimage.maximum_filter(need, size=int(0.5/P) | 1)   # cover the whole thin patch evenly
        w = np.clip((0.9 - dist)/0.5, 0, 1)
        D = ndimage.gaussian_filter(need*w, 9)
        bb = int(np.ceil(0.4/P)); D[:bb] = D[-bb:] = 0; D[:, :bb] = D[:, -bb:] = 0; D[:, :, :bb] = D[:, :, -bb:] = 0
        D = ndimage.gaussian_filter(D, 2)
        # never narrow an opening (slits, pin holes) below 0.4 mm: cap the offset
        # by the local half-width of the air around each voxel
        Hair = ndimage.maximum_filter(dout.astype(np.float32), size=int(0.7/P) | 1)
        # gaps under ~0.6 mm can't be cast cleanly (investment breaks, can't polish): let those fuse
        cap = np.where(Hair < 0.3, 9.0, np.clip(Hair - 0.2, 0, None))
        D = np.minimum(D, ndimage.gaussian_filter(cap, 2))
        # sink the patch 0.05 mm under the original wherever no offset is wanted,
        # so the union never leaves paper-thin films where the two surfaces nearly meet
        f = f_orig + np.where(D > 0.005, D + 0.03, -0.05)
        f = ndimage.gaussian_filter(f, 1.0)
        f[[0, -1], :, :] = f[:, [0, -1], :] = f[:, :, [0, -1]] = -1
        v, fa, _, _ = measure.marching_cubes(f, 0.0, spacing=(P, P, P))
        piece = trimesh.Trimesh(v + lo, fa[:, ::-1], process=True)
        if piece.volume < 0: piece.invert()
        adds.append(mf.Manifold(mf.Mesh(np.asarray(piece.vertices, np.float32), np.asarray(piece.faces, np.uint32))))
        print(f"  cluster {l}: {len(c)} faces, box {np.round(hi-lo,1)} mm, max offset {D.max():.2f} mm")

    base = mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
    out = base
    for a in adds:
        out = out + a
    mm = out.to_mesh()
    res = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=True)
    res = max(res.split(only_watertight=False), key=lambda x: len(x.faces))
    print(f"added {res.volume - m.volume:.2f} mm3 ({100*(res.volume/m.volume-1):.2f}%), watertight {res.is_watertight}, euler {m.euler_number}->{res.euler_number}")
    print("bounds change mm:", np.round(res.bounds - m.bounds, 3).tolist())
    return res, len(thinpts)

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    m = src
    for k in range(3):
        m, n = thicken(m, MIN)
        if n == 0:
            break
    m.export(dst)
