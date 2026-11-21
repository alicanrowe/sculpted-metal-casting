#!/usr/bin/env python3
"""Rest check: does the piece stand where the model puts it, on every foot, without rocking or tipping?

A physics-settle check without a simulator. A rigid piece on a flat floor rests on its lowest points; it
stands still only if its centre of mass falls inside the polygon those points make, and it rocks if a foot
the design means to stand on hangs above the floor. Run it before any render that shows the piece standing
(furniture, sawhorses, vessels, a ring or pendant laid flat) and before export.

  python check_rest.py MODEL.(glb|stl|obj) [--units mm|cm|m|in] [--up z|y] [--feet N]
                       [--tol 0.3] [--slab 3] [--margin-deg 10] [--json out.json]

--feet     how many feet the design stands on (4 for a table or sawhorse, 3 for a tripod). Each foot is a
           cluster of the model's bottom points; a foot whose lowest point is more than --tol above the
           floor is a gap and the piece rocks.
--tol      contact tolerance in mm (0.3 mm default: under that, felt pads, floor and finish take it up).
--slab     how far above the floor (mm) to look for feet; raise it for feet that are cut at an angle.
--margin-deg  WARN when the piece tips over at less than this lean (10 deg default). FAIL when the centre
           of mass sits outside the support polygon (it falls over on its own).
Exit code 1 on any FAIL. Needs: pip install trimesh numpy scipy shapely
"""
import argparse, json, math, sys
import numpy as np
import trimesh
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from shapely.geometry import MultiPoint, Point

UNIT_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}


def load(path, units, up):
    obj = trimesh.load(path, force=None)
    meshes = list(obj.dump()) if isinstance(obj, trimesh.Scene) else [obj]
    meshes = [m for m in meshes if isinstance(m, trimesh.Trimesh) and len(m.faces)]
    s = UNIT_MM[units]
    for m in meshes:
        m.apply_scale(s)
        if up == "y":  # Y-up (glTF / Blender GLB) -> Z-up
            m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    return meshes


def centre_of_mass(meshes):
    """Uniform density. Watertight parts use their solid volume; open shells fall back to surface area."""
    total, acc, open_parts = 0.0, np.zeros(3), 0
    for m in meshes:
        if m.is_volume:
            w, c = abs(m.volume), m.center_mass
        else:
            open_parts += 1
            w, c = m.area, m.triangles_center.T @ m.area_faces / max(m.area, 1e-12)
        total += w
        acc += w * np.asarray(c)
    return acc / total, open_parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--units", default="mm", choices=UNIT_MM)
    ap.add_argument("--up", default="z", choices=["z", "y"])
    ap.add_argument("--feet", type=int, default=0)
    ap.add_argument("--tol", type=float, default=0.3)
    ap.add_argument("--slab", type=float, default=3.0)
    ap.add_argument("--margin-deg", type=float, default=10.0)
    ap.add_argument("--json")
    a = ap.parse_args()

    meshes = load(a.model, a.units, a.up)
    V = np.vstack([m.vertices for m in meshes])
    floor = V[:, 2].min()
    com, open_parts = centre_of_mass(meshes)
    height = com[2] - floor

    # Feet: connected patches of bottom faces (within the slab), merged when closer than a few mm in plan.
    patches = []
    for m in meshes:
        z = m.vertices[:, 2]
        sel = np.where((z[m.faces] < floor + a.slab).all(1))[0]
        if not len(sel):
            continue
        keep = np.zeros(len(m.faces), bool); keep[sel] = True
        adj = m.face_adjacency[keep[m.face_adjacency].all(1)]
        idx = {f: i for i, f in enumerate(sel)}
        from scipy.sparse import coo_matrix
        n = len(sel)
        rows = [idx[f] for f in adj[:, 0]]; cols = [idx[f] for f in adj[:, 1]]
        g = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
        _, lab = connected_components(g, directed=False)
        for k in np.unique(lab):
            vi = np.unique(m.faces[sel[lab == k]])
            patches.append(m.vertices[vi])
    link = max(2.0, a.slab)
    if patches:
        trees = [cKDTree(p[:, :2]) for p in patches]
        n = len(patches); r, c = [], []
        for i in range(n):
            for j in range(i + 1, n):
                if trees[i].query(patches[j][:, :2], distance_upper_bound=link)[0].min() < link:
                    r.append(i); c.append(j)
        from scipy.sparse import coo_matrix
        _, plab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    feet = []
    for k in (np.unique(plab) if patches else []):
        p = np.vstack([patches[i] for i in np.where(plab == k)[0]])
        feet.append({"xy": p[:, :2].mean(0).round(1).tolist(), "gap_mm": round(float(p[:, 2].min() - floor), 3),
                     "points": p[p[:, 2] < floor + a.tol][:, :2]})
    feet.sort(key=lambda f: f["gap_mm"])
    touching = [f for f in feet if f["gap_mm"] <= a.tol]

    fails, warns = [], []
    if open_parts:
        warns.append(f"{open_parts} part(s) are open shells; their weight is taken from surface area, so the "
                     "centre of mass is approximate. Make them watertight for an exact answer.")

    if a.feet:
        if len(feet) < a.feet:
            warns.append(f"found {len(feet)} foot cluster(s) within {a.slab} mm of the floor, expected {a.feet}: "
                         "a foot is short by more than the slab, or feet are joined; raise --slab to see.")
        hanging = [f for f in feet[:a.feet] if f["gap_mm"] > a.tol]
        for f in hanging:
            fails.append(f"ROCKS: foot at {f['xy']} mm sits {f['gap_mm']} mm above the floor "
                         f"(tolerance {a.tol} mm). Level the feet in the model (trim the long ones or lengthen this one).")

    pts = np.vstack([f["points"] for f in touching]) if touching else np.zeros((0, 2))
    hull = MultiPoint([tuple(p) for p in pts]).convex_hull if len(pts) else None
    tip_deg = None
    if hull is None or hull.geom_type != "Polygon" or hull.area < 1.0:
        fails.append("ROLLS: the piece touches the floor on a point or a line only, so it rolls or falls over. "
                     "Give it a flat or a third contact.")
    else:
        c = Point(com[0], com[1])
        d = hull.exterior.distance(c)
        if not hull.contains(c):
            fails.append(f"TIPS OVER: centre of mass is {d:.1f} mm outside the footprint; it falls over by itself.")
            tip_deg = -math.degrees(math.atan2(d, height))
        else:
            tip_deg = math.degrees(math.atan2(d, height))
            if tip_deg < a.margin_deg:
                warns.append(f"TIPPY: falls over at a {tip_deg:.1f} deg lean (under {a.margin_deg} deg). "
                             "Widen the footprint or lower the weight.")

    rep = {"model": a.model, "floor_mm": round(float(floor), 2), "com_mm": com.round(1).tolist(),
           "com_height_mm": round(float(height), 1), "feet_found": len(feet), "feet_touching": len(touching),
           "feet": [{k: v for k, v in f.items() if k != "points"} for f in feet],
           "footprint_mm2": round(hull.area, 1) if hull is not None else 0,
           "tip_angle_deg": None if tip_deg is None else round(tip_deg, 1),
           "fails": fails, "warns": warns, "result": "FAIL" if fails else "PASS"}
    if a.json:
        json.dump(rep, open(a.json, "w"), indent=1)
    print(f"{rep['result']}: {len(touching)}/{len(feet)} feet on the floor, footprint {rep['footprint_mm2']} mm2, "
          f"centre of mass {rep['com_height_mm']} mm up, tips at {rep['tip_angle_deg']} deg")
    for f in feet:
        print(f"  foot {f['xy']}: gap {f['gap_mm']} mm")
    for m in fails:
        print("FAIL", m)
    for m in warns:
        print("WARN", m)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
