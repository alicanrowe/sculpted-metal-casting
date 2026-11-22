"""Ray-sampled thickness on the exact layer-kit mesh (npz), and where the thin spots are.
usage: python thick.py <piece.npz> [n]"""
import bpy
import sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
z = np.load(sys.argv[1]); V, F = z["V"].astype(float), z["F"]
n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 4000
bvh = BVHTree.FromPolygons(V.tolist(), F.tolist(), all_triangles=True)
rng = np.random.default_rng(1)
A = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
fi = rng.choice(len(F), n, p=A / A.sum())
u = rng.random((n, 2)); m = u.sum(1) > 1; u[m] = 1 - u[m]
P = V[F[fi, 0]] + u[:, :1] * (V[F[fi, 1]] - V[F[fi, 0]]) + u[:, 1:] * (V[F[fi, 2]] - V[F[fi, 0]])
N = np.cross(V[F[fi, 1]] - V[F[fi, 0]], V[F[fi, 2]] - V[F[fi, 0]]); N /= np.linalg.norm(N, axis=1, keepdims=True)
# Relief on a solid body: a ray along the surface normal runs sideways through every carved ridge and reports
# the ridge's width, which is fine to cast. What matters is that nothing overhangs as a flap or floats: so cast the
# ray straight down toward the ring's axis (RADIAL=1, default) from every point that faces outward.
radial = "--normal" not in sys.argv
D = N.copy()
if radial:
    D = -np.column_stack([P[:, 0], np.zeros(n), P[:, 2]]); D /= np.linalg.norm(D, axis=1, keepdims=True)
    face_out = (N * -D).sum(1) > 0.3
else:
    D = -N; face_out = np.ones(n, bool)
d = np.full(n, np.nan)
for i in np.where(face_out)[0]:
    o = Vector(P[i] + D[i] * 1e-3); hit = bvh.ray_cast(o, Vector(D[i]), 30.0)
    if hit[0] is not None: d[i] = hit[3]
ok = ~np.isnan(d); dd = d[ok]
print("samples", ok.sum(), "p5 %.2f  min %.2f  median %.2f" % (np.percentile(dd, 5), dd.min(), np.median(dd)))
thin = ok & (d < 0.3)
Pt = P[thin]; r = np.hypot(Pt[:, 0], Pt[:, 2])
print(thin.sum(), "under 0.3 mm; their height above the finger:", np.round(np.percentile(r - 8.45, [5, 50, 95]), 2) if thin.any() else "-")
np.save(sys.argv[1][:-4] + "_thin.npy", Pt)
