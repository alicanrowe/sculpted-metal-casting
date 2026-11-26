"""Inlay v3.1: the vendor 0.8 mm wall check (rays along each face normal, like wall_check.py), split into faces at
an enamel cell and faces elsewhere. A pocket wall is square to a curved crown, so a ray fired level into the brass
from just under the rim leaves through the skin within a few tenths of a mm: that is the rim edge, not a thin wall.
The cell land (>= 0.8 mm of brass round and under every pocket) is checked by cells.py with the field instead.
    python3 wall_split.py <piece> <piece>.stl [MIN_MM=0.8]   (needs embreex for speed)"""
import sys, numpy as np, trimesh
import helium, cells
name, stl = sys.argv[1], sys.argv[2]; lim = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
s, _ = helium.PIECES[name][0]()
m = trimesh.load(stl); real = m.area_faces > 1e-4
o = m.triangles_center - m.face_normals * 1e-4; t = np.full(len(o), np.inf)
for a in range(0, len(o), 200000):
    sl = slice(a, a + 200000); loc, ri, _ = m.ray.intersects_location(o[sl], -m.face_normals[sl], multiple_hits=False)
    t[a + ri] = np.linalg.norm(loc - o[sl][ri], axis=1)
C = m.triangles_center; g = np.full(len(C), 9.0)
for c in getattr(s, "cells", []): g = np.minimum(g, cells.footprint(c, C))
thin = np.isfinite(t) & (t < lim) & real; near = g < 1.0
print(f"wall {name}: faces {len(C)}, under {lim} mm at cells (rim edge) {m.area_faces[thin & near].sum():.2f} mm2; "
      f"elsewhere {m.area_faces[thin & ~near].sum():.2f} mm2, min {t[thin & ~near].min() if (thin & ~near).any() else 9:.2f} mm")
if (thin & ~near).any():
    from scipy.cluster.hierarchy import fcluster, linkage
    ix = np.nonzero(thin & ~near)[0]; ix = np.random.default_rng(0).choice(ix, min(len(ix), 12000), replace=False)
    P = C[ix]; tt = t[ix]; lab = fcluster(linkage(P, "single"), 1.5, "distance")
    for l in np.unique(lab):
        print(f"  thin (not a cell) at {P[lab == l].mean(0).round(1).tolist()} mm, ~{m.area_faces[ix][lab == l].sum() * len(np.nonzero(thin & ~near)[0]) / len(ix):.1f} mm2, min {tt[lab == l].min():.2f} mm")
