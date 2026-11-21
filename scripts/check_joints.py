"""Joint check: how solidly is each stone's head tied into the rest of the piece?
For every stone, take a spherical shell just outside its setting and count the separate metal links that
cross it from the setting to the main body (the biggest piece of metal outside the shell). A head carried
on one thin link reads weak and is weak (Bombyx review, 21 Nov: "this being the only connection point seems
a lil weak"). Hanging drops (claw-set pears on a stalk) are meant to hang from one link; they are reported
as 'drop' and only their link's section is checked.
usage: python check_joints.py piece.stl piece.json [--pitch 0.1] [--min-links 3] [--min-area 1.2]
exit 1 if any head stone fails.
"""
import sys, json, argparse, math
import numpy as np, trimesh
from scipy import ndimage

ap = argparse.ArgumentParser(); ap.add_argument("stl"); ap.add_argument("json")
ap.add_argument("--pitch", type=float, default=0.1); ap.add_argument("--min-links", type=int, default=3)
ap.add_argument("--min-area", type=float, default=1.2, help="mm^2, total section of the links")
ap.add_argument("--min-link-area", type=float, default=0.35, help="mm^2, a link thinner than this does not count")
a = ap.parse_args()
m = trimesh.load(a.stl); J = json.load(open(a.json)); stones = J.get("stones", [])
p = a.pitch
vg = m.voxelized(p).fill()
V = vg.matrix; T = vg.transform
idx = np.argwhere(V); org = T[:3, 3]
pts = org + idx * p
st26 = np.ones((3, 3, 3), bool)
out = []; fails = 0
def links_at(c, r_in, w):
    """separate metal links crossing the shell r_in..r_in+w from the setting to the main body: (count, areas)"""
    r_out = r_in + w
    d = np.linalg.norm(pts - c, axis=1)
    shell = (d > r_in) & (d < r_out); outside = d >= r_out
    Vs = np.zeros_like(V); Vs[tuple(idx[shell].T)] = True
    Vo = np.zeros_like(V); Vo[tuple(idx[outside].T)] = True
    lo, no = ndimage.label(Vo, st26)
    if no == 0: return None
    sizes = ndimage.sum(Vo, lo, range(1, no + 1)); main = int(np.argmax(sizes)) + 1
    grow_main = ndimage.binary_dilation(lo == main, st26)
    ls, ns = ndimage.label(Vs, st26)
    near_in = np.zeros_like(V); near_in[tuple(idx[shell & (d < r_in + 1.5 * p)].T)] = True
    rm = r_in + w / 2
    band = np.zeros_like(V); band[tuple(idx[shell & (np.abs(d - rm) < p * 0.5)].T)] = True
    areas = []
    for k in range(1, ns + 1):
        comp = ls == k
        if not (comp & near_in).any() or not (comp & grow_main).any(): continue
        ar = float((comp & band).sum()) * p * p
        if ar >= a.min_link_area: areas.append(round(ar, 2))
    return areas


for i, s in enumerate(stones):
    c = np.asarray(s["c"], float); D = float(s["D"]); L = float(s.get("L", D))
    r0 = max(D, L) / 2 + 0.9
    prof = []
    for r in np.arange(r0, r0 + 3.01, 0.5):      # the neck: the narrowest crossing in the 3 mm round the setting
        ar = links_at(c, r, 0.6)
        if ar is None: break
        prof.append((round(float(r), 1), len(ar), round(sum(ar), 2)))
    if not prof:
        out.append(dict(i=i, kind=s["kind"], D=D, L=L, role="all-inside", ok=True)); continue
    neck = min(prof, key=lambda q: q[2])
    role = "drop" if s.get("drop") else "head"
    need = max(a.min_area, 0.12 * D * D) if role == "head" else a.min_link_area
    ok = neck[2] >= need and (role == "drop" or neck[1] >= 2 or neck[2] >= 3 * need)
    if not ok: fails += 1
    out.append(dict(i=i, kind=s["kind"], D=D, L=L, role=role, neck_r=neck[0], links=neck[1], area=neck[2], need=round(need, 2), ok=bool(ok), prof=prof))
name = J.get("name", a.stl)
bad = [o for o in out if not o.get("ok", True)]
print("joints", name, "stones", len(out), "fails", fails,
      "worst:", "OK" if not bad else "; ".join(f"#{o['i']} {o['kind']} {o['D']}mm {o['role']} links {o['links']} area {o['area']}" for o in bad))
for o in out: print("  ", json.dumps(o))
sys.exit(1 if fails else 0)
