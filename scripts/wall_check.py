"""Vendor min-wall check on every face of an STL (not a sample).

    python -I wall_check.py PART.stl [MIN_MM=0.8] [MIN_GAP_MM=0.6]

For each face it fires a ray inward along the normal and reports the wall
thickness; it must print `thin 0` to pass. It also fires a ray outward and lists
gaps narrower than MIN_GAP (openings that will fill or fuse in casting).
Faces under 1e-4 mm^2 are mesh slivers and are ignored. Needs trimesh, and
embreex for speed (pip install trimesh embreex scipy).
"""
import sys
import numpy as np
import trimesh
from scipy.cluster.hierarchy import fcluster, linkage


def rays(m, sign):
    o = m.triangles_center + sign * m.face_normals * 1e-4
    t = np.full(len(o), np.inf)
    for s in range(0, len(o), 50000):
        sl = slice(s, s + 50000)
        loc, ri, _ = m.ray.intersects_location(o[sl], sign * m.face_normals[sl], multiple_hits=False)
        t[s + ri] = np.linalg.norm(loc - o[sl][ri], axis=1)
    return t


def spots(m, mask, t, label):
    c = m.triangles_center[mask][:20000]
    if len(c) < 2:
        return
    lab = fcluster(linkage(c, 'single'), 1.5, 'distance')
    for l in np.unique(lab):
        p = c[lab == l]
        print(f"  {label} at {p.mean(0).round(1).tolist()} mm, {len(p)} faces, min {t[mask][:20000][lab == l].min():.2f} mm")


def main():
    path = sys.argv[1]
    lim = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
    m = trimesh.load(path)
    real = m.area_faces > 1e-4
    t = rays(m, -1)
    g = rays(m, +1)
    thin = np.isfinite(t) & (t < lim) & real
    tight = np.isfinite(g) & (g < gap) & real
    print(f"{path}: faces {len(m.faces)}, watertight {m.is_watertight}, bodies {len(m.split(only_watertight=False))}")
    print(f"thin {int(thin.sum())} (walls under {lim} mm, {m.area_faces[thin].sum():.2f} mm2), "
          f"min wall {t[np.isfinite(t) & real].min():.3f} mm")
    spots(m, thin, t, "thin wall")
    print(f"tight {int(tight.sum())} (gaps under {gap} mm)")
    spots(m, tight, g, "tight gap")
    sys.exit(1 if thin.any() else 0)


if __name__ == "__main__":
    main()
