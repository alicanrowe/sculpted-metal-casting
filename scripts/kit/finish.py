"""Finish a layer-kit piece the way the reference maker does after placing inserts: DynaMesh (voxel remesh) the
exact union, then close each pinhole tunnel that is left (layer.close_handle) and remesh again, until the main
body has no tunnels (genus 1 for a ring) or 3 rounds have passed. Writes <out>.npz/.stl/.json.
usage: python3 finish.py <piece_L.npz> <out_prefix> [voxel_mm=0.03] [target_genus=1]"""
import sys, os, json, subprocess, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layer as Ly
from scipy.spatial import cKDTree
src, out = sys.argv[1], sys.argv[2]
vs = sys.argv[3] if len(sys.argv) > 3 else "0.03"; target = int(sys.argv[4]) if len(sys.argv) > 4 else 1
here = os.path.dirname(os.path.abspath(__file__)); t0 = time.time()


def vox(a, b):
    subprocess.run([sys.executable, os.path.join(here, "vox.py"), a, b, vs], check=True)


def save(M, ref, path):
    m = Ly.from_manifold(max(M.decompose(), key=lambda p: p.volume()))
    _, idx = cKDTree(ref["V"]).query(np.asarray(m.vertices), workers=-1)
    np.savez_compressed(path, V=np.asarray(m.vertices), F=np.asarray(m.faces), ground=ref["ground"][idx])
    return m


vox(src, out + "_r0")
cur = out + "_r0"
for rnd in range(1, 4):
    d = np.load(cur + ".npz"); M = Ly.to_manifold(d["V"], d["F"])
    print("round", rnd, "genus", M.genus(), round(time.time() - t0), "s", flush=True)
    if M.genus() <= target:
        break
    for lo, hi in Ly.find_handles(M):
        M, added = Ly.close_handle(M, lo, hi)
        print("  closed a pinhole at", np.round((lo + hi) / 2, 2), "adding %.3f mm3" % added, flush=True)
    save(M, d, out + "_c.npz")
    vox(out + "_c.npz", out + "_r%d" % rnd); cur = out + "_r%d" % rnd
d = np.load(cur + ".npz"); M = Ly.to_manifold(d["V"], d["F"])
# the remesh rounds the seat by up to a voxel, into the stone: cut every bezel seat again, exactly
for st in json.load(open(src[:-4] + ".json"))["stones"]:
    if st.get("setting") == "bezel" and np.allclose(st["n"], [0, 0, 1]):
        M = M - Ly.bezel_cut(st["c"][2], st["D"] / 2).translate([st["c"][0], st["c"][1], 0])
        print("re-cut the bezel seat", flush=True)
m = save(M, d, out + ".npz"); m.export(out + ".stl")
g = Ly.to_manifold(np.asarray(m.vertices), np.asarray(m.faces)).genus()
print("FINAL genus", g, "(PASS)" if g <= target else "(FAIL: tunnels left)", "bodies", m.body_count, "watertight",
      m.is_watertight, "sterling g", round(abs(m.volume) / 1000 * 10.36, 2), round(time.time() - t0), "s", flush=True)
info = json.load(open(src[:-4] + ".json")); info["name"] = os.path.basename(out); info["genus"] = int(g)
info["sterling_g"] = round(abs(m.volume) / 1000 * 10.36, 1); info["volume_cm3"] = round(abs(m.volume) / 1000, 3)
json.dump(info, open(out + ".json", "w"), indent=1)
for f in os.listdir(os.path.dirname(os.path.abspath(out))):
    p = os.path.join(os.path.dirname(os.path.abspath(out)), f)
    if f.startswith(os.path.basename(out) + "_r") or f.startswith(os.path.basename(out) + "_c."):
        os.remove(p)
