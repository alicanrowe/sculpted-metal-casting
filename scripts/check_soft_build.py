"""Soft-part build check: is every non-rigid part (leather, laces, straps, cushions, foam, boards inside them) a real
part that someone could buy or cut, fix on, tension and replace, and does the model agree with what the spec says?

    python check_soft_build.py --frame FRAME.stl --spec SPEC.json [--units cm] [--json out.json]

SPEC.json lists every soft part (meshes are paths relative to the spec file):
  {"seat": {"z_min": 76.5},                 # optional: the sitting surface starts here (model units)
   "envelope": "envelope.stl",              # optional: the outside of the covered cushion
   "parts": [{"name", "kind", "mesh", "material", "thickness_mm" (or "diameter_mm" for laces and cords), "cut",
              "attach": {"method", "to": [part names or "frame"], "fasteners", "through": [parts a staple
                         or rivet passes through on the way, e.g. the cover between a flap and the board]},
              "tension"  (laces, cords, straps, drawstrings, covers: how it is pulled tight),
              "closure": {"type", "release"}  (laces, cords, straps, drawstrings: how it opens),
              "load", "replace", "inside" (optional: "envelope")}],
   "load_paths": [{"name", "chain": ["cover", "foam", ..., "frame"], "travel_ok_cm": 0.6}]}
kinds: cover, sheet, flap, strap, lace, cord, drawstring, foam, board, cushion, hardware.

FAILs (exit 1):
  SPEC      a field is missing or a placeholder: material, thickness, how it is cut, how it attaches (method, to,
            fasteners for staples/rivets/screws/stitching/nails), how it is tensioned (laces, cords, straps, covers),
            how it opens (laces, cords, straps), what load it takes, how it is replaced. No spec at all fails.
  MESH      the part's mesh is missing, empty or not one closed solid.
  THICKNESS sheet leather (cover, sheet, flap, strap) measures its stated thickness (2 x volume / area within 0.7 to
            1.4 x); laces and cords measure their diameter (4 x volume / area within 0.65 to 1.35 x). A solid blob
            called "leather" fails here.
  ATTACH    the part does not touch what it says it is fixed to (staples need contact; a lace needs to pass through
            the holes in the parts it laces).
  CLIP      a soft part passes more than 0.1 mm into the frame, or into another soft part (crimped tips excepted) (a lace through a flap with no hole there,
            a flap buried inside a cushion).
  SEAT      a lace, cord, strap, drawstring or hardware runs over the sitting surface (above seat.z_min inside the
            cushion's footprint): you would sit on the knot.
  NEST      a part said to be inside the cover (board, foam) sticks out of the envelope.
  LOAD      a load path is broken: consecutive parts in the chain are not joined (touching, or fixed through the
            parts named in attach.through, or a lace in its holes); the last link to "frame" may have a gap up to
            travel_ok_cm (the uplift travel before a lace catches). A seat load path ending at "frame" is
            required.

Why: on 20 Nov 2026 the client could not see how Thread's leather saddle would work. Its drawstrings ran over the
seat as closed rings with fused knots, its flaps were buried in a solid cushion with nothing holding them, and no
part had a material, thickness or fixing. check_soft_parts.py passed it: it checks shapes, not construction.
Needs: pip install trimesh numpy manifold3d rtree"""
import sys, os, json, argparse
import numpy as np

SHEET = {"cover", "sheet", "flap", "strap"}
LINE = {"lace", "cord", "drawstring"}
TENSIONED = LINE | {"strap", "cover"}
CLOSED = LINE | {"strap"}
OVER_SEAT_BANNED = LINE | {"strap", "hardware"}
KINDS = SHEET | LINE | {"foam", "board", "cushion", "hardware"}
FASTENED = ("staple", "rivet", "screw", "stitch", "sew", "nail", "tack", "bolt")
PLACEHOLDER = {"", "tbd", "todo", "?", "n/a", "na", "none?", "unknown", "-", "..."}


def blank(v):
    if v is None: return True
    if isinstance(v, (int, float)): return v <= 0
    if isinstance(v, (list, tuple)): return not v
    if isinstance(v, dict): return not v
    return str(v).strip().lower() in PLACEHOLDER


def spec_errors(p):
    e = []
    k = p.get("kind")
    if k not in KINDS: e.append(f"kind '{k}' (one of {sorted(KINDS)})")
    for f in ("name", "mesh", "material", "cut", "load", "replace"):
        if blank(p.get(f)): e.append(f)
    if k in LINE:
        if blank(p.get("diameter_mm")) and blank(p.get("thickness_mm")): e.append("diameter_mm")
    elif k != "hardware" and blank(p.get("thickness_mm")): e.append("thickness_mm")
    a = p.get("attach") or {}
    if blank(a.get("method")): e.append("attach.method")
    if blank(a.get("to")): e.append("attach.to")
    m = str(a.get("method", "")).lower()
    if any(w in m for w in FASTENED) and blank(a.get("fasteners")): e.append("attach.fasteners")
    if k in TENSIONED and blank(p.get("tension")): e.append("tension")
    if k in CLOSED:
        c = p.get("closure") or {}
        if blank(c.get("type")): e.append("closure.type")
        if blank(c.get("release")): e.append("closure.release")
    return e


def to_m3(t):
    import manifold3d as m3
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def min_dist(a, b, search=5.0):
    """Smallest surface-to-surface distance (exact, manifold3d min_gap); b is cropped to a's neighbourhood first."""
    import manifold3d as m3
    bx = a.bounding_box(); lo, hi = np.array(bx[:3]), np.array(bx[3:])
    box = m3.Manifold.cube(list(hi - lo + 2 * search)).translate(list(lo - search))
    bb = b ^ box
    if bb.is_empty(): return float("inf")
    return float(a.min_gap(bb, search))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", required=True); ap.add_argument("--spec", required=True)
    ap.add_argument("--units", default="cm"); ap.add_argument("--json")
    a = ap.parse_args()
    import trimesh, manifold3d as m3
    mm = {"cm": 0.1, "mm": 1.0, "m": 0.001, "in": 1 / 25.4}[a.units]
    tol = 0.5 * mm                                                     # 0.5 mm: touching
    spec = json.load(open(a.spec)); base = os.path.dirname(os.path.abspath(a.spec))
    parts = spec.get("parts") or []
    res, fails = [], 0

    def fail(where, what):
        nonlocal fails; fails += 1; res.append(dict(part=where, verdict=what))

    if not parts:
        fail("-", "SPEC (no soft parts listed: every leather, lace, strap, cushion and board needs an entry)")
    frame = trimesh.load(a.frame, force="mesh")
    fm = to_m3(frame)
    meshes, mans = {}, {}
    for p in parts:
        nm = p.get("name", "?")
        e = spec_errors(p)
        if e: fail(nm, "SPEC (missing: " + ", ".join(e) + ")")
        path = os.path.join(base, p.get("mesh", "")) if p.get("mesh") else ""
        if not path or not os.path.exists(path):
            fail(nm, "MESH (no mesh file)"); continue
        t = trimesh.load(path, force="mesh")
        t.update_faces(t.nondegenerate_faces(height=1e-7)); t.remove_unreferenced_vertices()   # STL rounding slivers
        if len(t.faces) == 0 or not t.is_watertight or len(t.split(only_watertight=False)) == 0:
            fail(nm, "MESH (empty, open or cracked)"); continue
        meshes[nm] = t; mans[nm] = to_m3(t)
        k = p.get("kind")
        r = dict(part=nm, kind=k, volume=round(float(t.volume), 3))
        if k in SHEET and p.get("thickness_mm"):
            ts = 2 * t.volume / t.area; want = p["thickness_mm"] * mm; r["t_measured_mm"] = round(ts / mm, 2)
            if not 0.7 * want <= ts <= 1.4 * want:
                fail(nm, f"THICKNESS (measures {ts / mm:.1f} mm, spec says {p['thickness_mm']} mm: not one sheet of that leather)")
        if k in LINE:
            want = (p.get("diameter_mm") or p.get("thickness_mm") or 0) * mm
            ds = 4 * t.volume / t.area; r["d_measured_mm"] = round(ds / mm, 2)
            if want and not 0.65 * want <= ds <= 1.35 * want:
                fail(nm, f"THICKNESS (measures {ds / mm:.1f} mm across, spec says {want / mm:.1f} mm: fused knot or blob)")
        res.append(r)
    # clipping: soft vs frame, soft vs soft
    vt = (1.0 * mm) ** 3 * 2                                          # 2 mm3
    def clash(x, y):
        """Overlap volume, counting only pieces thicker than 0.1 mm (touching faces leave micron films)."""
        if min_dist(x, y, 0.5) > 1e-6: return 0.0
        v = 0.0
        for c in (x ^ y).decompose():
            cv = c.volume()
            if cv > 0 and 2 * cv / max(c.surface_area(), 1e-12) > 0.1 * mm: v += cv
        return v
    for nm, m in mans.items():
        v = clash(m, fm)
        if v > vt: fail(nm, f"CLIP (passes {v / mm ** 3:.0f} mm3 into the frame)")
    names = list(mans)
    method = {(p.get("name"), t): str((p.get("attach") or {}).get("method", "")).lower() for p in parts for t in ((p.get("attach") or {}).get("to") or [])}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            x, y = names[i], names[j]
            if any(w in method.get(k, "") for k in ((x, y), (y, x)) for w in ("crimp", "sleeve", "moulded")): continue  # a crimped tip wraps its lace
            v = clash(mans[x], mans[y])
            if v > vt: fail(f"{x} / {y}", f"CLIP ({v / mm ** 3:.0f} mm3 of one inside the other: a lace through leather with no hole, or a part buried in another)")
    # attachment
    byname = {p.get("name"): p for p in parts}
    def thick(n):
        q = byname.get(n) or {}
        return (q.get("thickness_mm") or q.get("diameter_mm") or 0) * mm
    def limit(x, y):
        """How far apart x and y may be and still be joined: touching, or the stack a staple goes through, or the
        clearance of a lace in its hole."""
        lim = tol
        for u, v in ((x, y), (y, x)):
            q = byname.get(u) or {}
            at = q.get("attach") or {}
            if v in (at.get("to") or []):
                lim = max(lim, tol + sum(thick(t) for t in (at.get("through") or [])))
            if q.get("kind") in LINE:
                lim = max(lim, 0.5 * thick(u) + tol)
        return lim
    for p in parts:
        nm = p.get("name")
        if nm not in mans: continue
        for to in (p.get("attach") or {}).get("to") or []:
            if to != "frame" and to not in mans:
                fail(nm, f"ATTACH (fixed to '{to}', which is not a listed part or has no good mesh)"); continue
            d = min_dist(mans[nm], fm if to == "frame" else mans[to])
            if d > limit(nm, to): fail(nm, f"ATTACH (fixed to {to} but sits {d / mm:.1f} mm clear of it)")
    # nothing on the sitting surface
    seat = spec.get("seat") or {}
    env = None
    if spec.get("envelope") and os.path.exists(os.path.join(base, spec["envelope"])):
        env = trimesh.load(os.path.join(base, spec["envelope"]), force="mesh")
    if "z_min" in seat:
        lo, hi = (env.bounds if env is not None else
                  np.array([[-np.inf] * 3, [np.inf] * 3]))
        for p in parts:
            nm = p.get("name")
            if p.get("kind") in OVER_SEAT_BANNED and nm in meshes:
                V = meshes[nm].vertices
                over = V[(V[:, 2] > seat["z_min"]) & (V[:, 0] >= lo[0]) & (V[:, 0] <= hi[0]) & (V[:, 1] >= lo[1]) & (V[:, 1] <= hi[1])]
                if len(over): fail(nm, f"SEAT (runs over the sitting surface, up to {V[:, 2].max():.1f}: you would sit on it)")
    else:
        if any(p.get("kind") in {"foam", "cushion", "cover"} for p in parts):
            fail("-", "SPEC (seat.z_min missing: say where the sitting surface starts)")
    # nesting
    if env is not None:
        em = to_m3(env)
        for p in parts:
            if p.get("inside") == "envelope" and p.get("name") in mans:
                out = (mans[p["name"]] - em).volume()
                if out > vt: fail(p["name"], f"NEST ({out / mm ** 3:.0f} mm3 sticks out of the cover)")
    # load paths
    lps = spec.get("load_paths") or []
    if not any((lp.get("chain") or [None])[-1] == "frame" for lp in lps):
        fail("-", "LOAD (no load path from the sitter to the frame)")
    for lp in lps:
        ch = lp.get("chain") or []
        travel = (lp.get("travel_ok_cm") or 0) * (10 * mm)
        for x, y in zip(ch, ch[1:]):
            if x == "frame": x, y = y, x
            A = fm if x == "frame" else mans.get(x); B = fm if y == "frame" else mans.get(y)
            if A is None or B is None: fail(lp.get("name", "?"), f"LOAD ({x} -> {y}: not a listed part)"); continue
            d = min_dist(A, B)
            lim = max(limit(x, y), travel if y == "frame" else 0)
            res.append(dict(part=f"{lp.get('name')}: {x} -> {y}", gap_mm=round(d / mm, 1)))
            if d > lim: fail(lp.get("name", "?"), f"LOAD ({x} -> {y} are {d / mm:.1f} mm apart: the load can't pass)")
    for r in res:
        if "verdict" in r: print(f"  FAIL {r['part']}: {r['verdict']}")
        elif "gap_mm" in r: print(f"  ok   {r['part']}  gap {r['gap_mm']} mm")
        else:
            extra = "".join(f"  {k} {r[k]}" for k in ("t_measured_mm", "d_measured_mm") if k in r)
            print(f"  ok   {r['part']:<12s} {r['kind']:<9s}{extra}")
    print(f"{fails} FAIL" if fails else "soft build: every part specified, fixed, tensioned and clear")
    if a.json: json.dump(res, open(a.json, "w"), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
