"""Clipping check for a layer-kit piece: metal inside any stone's volume. usage: python3 clipcheck.py piece.npz"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, v2, layer as Ly, trimesh
npz = sys.argv[1]; info = json.load(open(npz[:-4] + ".json"))
d = np.load(npz); M = Ly.to_manifold(d["V"], d["F"]); bad = 0
for i, r in enumerate(info["stones"]):
    r = dict(r); r.setdefault("e1", [1, 0, 0]); ob = v2.stone_mesh(r, r["kind"])
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh(); me.calc_loop_triangles()
    V = np.array([ob.matrix_world @ v.co for v in me.vertices]); F = np.array([t.vertices[:] for t in me.loop_triangles])
    t = trimesh.Trimesh(V, F); t.merge_vertices()
    vol = (M ^ Ly.to_manifold(np.asarray(t.vertices), np.asarray(t.faces))).volume()
    ok = vol < 1e-3; bad += not ok
    print("stone %d %s %.1f mm: metal inside %.4f mm3 %s" % (i, r["kind"], r["D"], vol, "OK" if ok else "CLIPS"))
print("CLIPPING", "PASS" if not bad else "FAIL")
