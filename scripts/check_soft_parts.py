"""Soft-part check: could a leatherworker cut, sew and fit these straps, ties and pads, and does the closure work?

    python check_soft_parts.py --rigid FRAME.stl --soft STRAPS.stl --t 0.30 [--closure TOGGLES.stl]
                               [--units cm] [--pad-min 1.5] [--allow-ring] [--json out.json]

--soft holds the strap, tie and ear meshes (one file, any number of bodies); --t is their nominal thickness in model
units (0.30 cm = 3 mm veg-tan, 0.15 cm = 1.5 mm lambskin). Bodies whose sheet thickness (2 x volume / area) is
over --pad-min (default 5t) are seat pads: listed, not thickness-checked. --closure holds toggles, buckles or studs that fasten the straps.

Per strap body it reports:
  THICKNESS  ray-sampled thickness, 10th to 75th percentile, within 0.6t to 1.6t of nominal (the
             top quarter is left out: rays from a strap's cut edges measure its width): leather is one
             thickness. A fused knot, a blob or a lump reads as thick; a sliver reads as thin.
  MESH       each body is one closed solid (an open or cracked body renders as black lines and can't be cut).
  RING       a closed loop (a torus-like body) touching the frame can't be put on or taken off: it needs a
             closure, unless it is sewn on round the frame for good (--allow-ring).
  INSIDE     strap surface inside the frame: leather can't pass through metal (more than 2% of vertices fails).
  TOUCH      the strap rests on or wraps the frame (it is within one thickness of it somewhere).
Per closure body:
  FASTENS    it touches a strap; a toggle floating clear of the strap fastens nothing.
Exit code 1 on any FAIL.

Why: on 18 Nov 2026 a seat's knot, ears and tether were fused blobs, the tether was a closed ring that could not
open, the toggle fastened nothing, and mesher cracks showed as black lines. The renders looked fine at hero distance.
Needs: pip install trimesh numpy rtree"""
import sys, json, argparse
import numpy as np


def thickness(body, n=500, seed=0):
    """Distance from a surface point straight in to the opposite surface, sampled over the body's faces."""
    rng = np.random.default_rng(seed)
    f = rng.choice(len(body.faces), n, replace=True, p=body.area_faces / body.area)   # area-weighted
    nrm = body.face_normals[f]
    eps = 0.02 * min(body.extents)
    o = body.triangles_center[f] - nrm * eps
    loc, ri, _ = body.ray.intersects_location(o, -nrm, multiple_hits=False)
    if not len(ri): return np.array([])
    return np.linalg.norm(loc - o[ri], axis=1) + eps


def inside_frac(rigid, pts):
    """Share of pts behind the rigid mesh's nearest face (signed distance by nearest-face normal)."""
    import trimesh
    if not len(pts): return 0.0
    lo, hi = pts.min(0), pts.max(0); pad = 0.05 * max(hi - lo)
    T = rigid.triangles
    f = np.nonzero(((T.min(1) <= hi + pad) & (T.max(1) >= lo - pad)).all(1))[0]
    if not len(f): return 0.0
    m = rigid.submesh([f], append=True)
    cp, d, tid = trimesh.proximity.closest_point(m, pts)
    s = np.einsum("ij,ij->i", pts - cp, m.face_normals[tid])
    return float(np.mean(s < -1e-6))


def min_dist(a, b, n=1500, seed=1):
    import trimesh
    rng = np.random.default_rng(seed)
    v = a.vertices[rng.choice(len(a.vertices), min(n, len(a.vertices)), replace=False)]
    lo, hi = v.min(0), v.max(0); pad = 0.2 * max(hi - lo) + 1e-3
    T = b.triangles
    f = np.nonzero(((T.min(1) <= hi + pad) & (T.max(1) >= lo - pad)).all(1))[0]
    if not len(f): return float("inf")
    _, d, _ = trimesh.proximity.closest_point(b.submesh([f], append=True), v)
    return float(d.min())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rigid", required=True); ap.add_argument("--soft", required=True)
    ap.add_argument("--t", type=float, required=True, help="nominal leather thickness, model units")
    ap.add_argument("--closure"); ap.add_argument("--units", default="cm")
    ap.add_argument("--pad-min", type=float, default=None, help="bodies thicker than this are pads (default 5t)")
    ap.add_argument("--min-body", type=float, default=None, help="ignore specks under this volume (default t^3)")
    ap.add_argument("--allow-ring", action="store_true"); ap.add_argument("--json")
    a = ap.parse_args()
    import trimesh
    rigid = trimesh.load(a.rigid, force="mesh")
    soft = trimesh.load(a.soft, force="mesh")
    t = a.t; pad_min = a.pad_min or 5 * t; vmin = a.min_body or t ** 3
    bodies = [b for b in soft.split(only_watertight=False) if abs(b.volume) > vmin or len(b.faces) > 200]
    res, fails, straps = [], 0, []
    for i, b in enumerate(bodies):
        if b.volume < 0: b.invert()
        th = thickness(b)
        p10, p50, p90 = (np.percentile(th, [10, 50, 75]) if len(th) else (0, 0, 0))
        r = dict(body=i, faces=len(b.faces), volume=round(abs(float(b.volume)), 3), watertight=bool(b.is_watertight),
                 euler=int(b.euler_number), t_p10=round(float(p10), 3), t_p50=round(float(p50), 3), t_p75=round(float(p90), 3))
        bad = []
        r["t_sheet"] = round(2 * abs(float(b.volume)) / max(float(b.area), 1e-9), 3)   # a thin sheet: 2V/A = its thickness
        if r["t_sheet"] >= pad_min:
            r["role"] = "pad"
        else:
            r["role"] = "strap"; straps.append(b)
            if not b.is_watertight: bad.append("MESH (open or cracked body)")
            if p90 > 1.6 * t: bad.append(f"THICKNESS (lumps to {p90:.2f}, nominal {t}: fused blob or knot)")
            if p10 < 0.6 * t: bad.append(f"THICKNESS (thins to {p10:.2f}, nominal {t})")
            d = min_dist(b, rigid)
            r["gap_to_frame"] = round(d, 3)
            ins = inside_frac(rigid, b.vertices[:: max(1, len(b.vertices) // 3000)])
            r["inside_frame"] = round(ins, 3)
            if ins > 0.02: bad.append(f"INSIDE ({ins:.0%} of the strap is inside the frame)")
            if b.is_watertight and b.euler_number == 0 and d <= t and not a.allow_ring:
                bad.append("RING (a closed loop on the frame: it can't come off without a closure)")
            r["touches_frame"] = d <= t
        r["verdict"] = "; ".join(bad) or "OK"; fails += bool(bad); res.append(r)
    if not any(r.get("touches_frame") for r in res if r["role"] == "strap"):
        res.append(dict(verdict="TOUCH (no strap rests on or wraps the frame: what holds the seat?)")); fails += 1
    if a.closure:
        cl = trimesh.load(a.closure, force="mesh")
        sm = trimesh.util.concatenate(straps) if straps else None
        for j, c in enumerate(cl.split(only_watertight=False)):
            if abs(c.volume) < vmin and len(c.faces) < 100: continue
            d = min_dist(c, sm) if sm is not None else float("inf")
            ok = d <= 0.5 * t
            res.append(dict(closure=j, gap_to_strap=round(d, 3), verdict="OK" if ok else f"FASTENS (closure sits {d:.2f} clear of every strap: it fastens nothing)"))
            fails += not ok
    for r in res:
        tag = "OK  " if r["verdict"] == "OK" else "FAIL"
        if "body" in r:
            print(f"  {tag} body {r['body']:<3d} {r['role']:5s} t {r['t_p10']:.2f}/{r['t_p50']:.2f}/{r['t_p75']:.2f}  "
                  f"euler {r['euler']:3d}  " + ("" if r["role"] == "pad" else f"gap {r['gap_to_frame']:.2f}  inside {r['inside_frame']:.2f}")
                  + ("" if tag == "OK  " else "   <- " + r["verdict"]))
        else:
            print(f"  {tag} " + (f"closure {r['closure']} gap {r['gap_to_strap']:.2f}  " if "closure" in r else "") + ("" if tag == "OK  " else "<- " + r["verdict"]))
    print(f"{fails} FAIL" if fails else "soft parts buildable")
    if a.json: json.dump(res, open(a.json, "w"), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
