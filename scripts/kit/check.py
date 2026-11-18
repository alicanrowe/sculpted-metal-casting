"""Castability check for every STL in out/: watertight, size, volume, sterling
weight, and a ray-sampled wall/wire thickness (5th percentile and minimum).
Run with python -I check.py <out dir>; writes checks.json there."""
import sys, os, json, glob
import numpy as np
import trimesh
import bpy  # noqa: F401  (for mathutils)
from mathutils import Vector
from mathutils.bvhtree import BVHTree

STERLING = 10.36  # g/cm3
out = sys.argv[1]
res = {}
for f in sorted(glob.glob(os.path.join(out, "*.stl"))):
    m = trimesh.load(f)
    name = os.path.basename(f)[:-4]
    pts, fi = trimesh.sample.sample_surface_even(m, 2500, seed=1)
    nrm = m.face_normals[fi]
    bvh = BVHTree.FromPolygons(m.vertices.tolist(), m.faces.tolist())
    th = []
    for p_, n_ in zip(pts, nrm):
        o = Vector(p_ - n_ * 0.005)
        hit = bvh.ray_cast(o, Vector(-n_), 30.0)
        if hit[0] is not None:
            th.append((hit[0] - o).length)
    th = np.array(th); th = th[th > 0.02]
    vol = abs(m.volume) / 1000.0  # cm3
    res[name] = dict(
        watertight=bool(m.is_watertight),
        size_mm=[round(float(x), 1) for x in m.extents],
        volume_cm3=round(vol, 3),
        sterling_g=round(vol * STERLING, 1),
        sterling_dwt=round(vol * STERLING / 1.555, 1),
        thickness_p5_mm=round(float(np.percentile(th, 5)), 2),
        thickness_min_mm=round(float(th.min()), 2),
        tris=int(len(m.faces)),
    )
    print(name, res[name], flush=True)
json.dump(res, open(os.path.join(out, "checks.json"), "w"), indent=1)
