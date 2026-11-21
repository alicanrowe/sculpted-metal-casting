"""Casting export: the watertight STL a jeweler or casting house receives.
Decimates a voxel mesh to a sane size (quadric, shape-preserving), keeps it only if it is still watertight,
one body, and within 0.3% of the original volume, and writes it zipped (binary STL) with its stone JSON.
usage: python cast_export.py <in.stl> <stones.json> <out_dir> [--faces 400000]
"""
import sys, os, json, zipfile, argparse
import numpy as np, trimesh

ap = argparse.ArgumentParser(); ap.add_argument("stl"); ap.add_argument("js"); ap.add_argument("out")
ap.add_argument("--faces", type=int, default=400000)
a = ap.parse_args()
name = os.path.splitext(os.path.basename(a.stl))[0]
m0 = trimesh.load(a.stl, force="mesh")
v0 = abs(m0.volume) if m0.is_watertight else None
best = m0; note = "full resolution"
if len(m0.faces) > a.faces and v0:
    import fast_simplification
    for tgt in (a.faces, int(a.faces * 1.5), a.faces * 2):
        red = 1 - tgt / len(m0.faces)
        if red <= 0: break
        V, F = fast_simplification.simplify(m0.vertices.astype(np.float32), m0.faces.astype(np.int32), target_reduction=red)
        m1 = trimesh.Trimesh(V, F, process=True)
        if m1.is_watertight and len(m1.split(only_watertight=False)) == 1 and abs(abs(m1.volume) - v0) / v0 < 0.003:
            best = m1; note = f"decimated {len(m0.faces)} -> {len(m1.faces)} faces, volume within {abs(abs(m1.volume) - v0) / v0 * 100:.2f}%"
            break
os.makedirs(a.out, exist_ok=True)
zp = os.path.join(a.out, name + ".zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.writestr(name + ".stl", best.export(file_type="stl"))
    z.write(a.js, name + "_stones.json")
print(f"cast_export {name}: watertight {best.is_watertight} faces {len(best.faces)} volume {abs(best.volume):.1f} mm3 "
      f"bbox {np.round(best.extents, 1).tolist()} mm ({note}) -> {zp} {os.path.getsize(zp) / 1e6:.1f} MB")
