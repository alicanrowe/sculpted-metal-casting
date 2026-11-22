"""Classify thick.py's thin samples: band/blank edge, crevice between strokes (metal again just past the gap),
or a free flap (air beyond). usage: python3 thin_class.py piece.npz"""
import bpy, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
sys.path.insert(0, __file__.rsplit("/", 1)[0]); import layer as Ly
z = np.load(sys.argv[1]); V, F = z["V"].astype(float), z["F"]
Pt = np.load(sys.argv[1][:-4] + "_thin.npy")
bvh = BVHTree.FromPolygons(V.tolist(), F.tolist(), all_triangles=True)
B = Ly.RingBlank(Ri=8.45, band_w=4.2, band_t=1.8, Rh=7.6, drum=1.2, H=3.0, rim=(0.30, 0.22), edge_lo=0.18)
th = np.arctan2(Pt[:, 0], Pt[:, 2]); s = np.clip(Pt[:, 1] / B.halfw(th), -1, 1)
rg = np.linalg.norm(B.point(th, s)[:, [0, 2]], axis=1); r = np.hypot(Pt[:, 0], Pt[:, 2])
cls = []
for i, p in enumerate(Pt):
    D = -np.array([p[0], 0, p[2]]); D /= np.linalg.norm(D)
    h1 = bvh.ray_cast(Vector(p + D * 1e-3), Vector(D), 30)           # leaves the metal
    if h1[0] is None: cls.append("none"); continue
    h2 = bvh.ray_cast(h1[0] + Vector(D * 1e-3), Vector(D), 30)       # next metal
    gap = h2[3] if h2[0] is not None else 99
    if abs(s[i]) > 0.93: cls.append("band edge")
    elif gap < 0.6: cls.append("crevice (metal %.2f mm on)" % gap if False else "crevice")
    else: cls.append("flap")
cls = np.array(cls)
for c in np.unique(cls): print(c, (cls == c).sum())
fl = cls == "flap"
if fl.any():
    print("flaps: height above ground", np.round(np.percentile(r[fl] - rg[fl], [5, 50, 95]), 2))
    print(np.round(Pt[fl][:10], 2))
