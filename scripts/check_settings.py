"""Stone setting check: could a setter actually set every stone in this casting, and would it stay put?

    python check_settings.py PIECE.stl PIECE.json [--units mm|cm] [--json out.json]

PIECE.json is the file make.py writes next to the STL: {"stones": [{kind, D, L, c, n, e1, bead?, outline?}, ...]}
(c = girdle centre, n = table direction, e1 = long axis; outline = girdle outline in (e1, e2) for fancy panes).
Furniture kits write the same records from sawmoth.py; pass --units cm.

For each stone it samples the metal around the girdle and reports:
  HOLD     metal rising beside and above the girdle (claw tips, bead grains or a bezel wall that can be pushed
           over) in enough places that the stone can't lift out: 3+ separate holds with no gap of 180 deg or more,
           4+ for ovals, pears and marquises (L/D > 1.2), or a continuous bezel.
  SEAT     metal under the girdle (a bearing ledge, gallery or seat) all the way round, same spacing rule.
  CLEAR    the stone's own volume is free of metal, so it can drop into its seat: more than 10% of sample points
           inside metal fails (under 10% is mesh smoothing at the seat edge, or a pear checked as an ellipse).
  SPACING  girdles don't touch or crowd: at least 0.3 mm of metal between neighbouring stones.
A stone with no metal at its girdle at all is FLOATING. Exit code 1 if any stone fails.

Why: on 18 Nov 2026 settings and straps were modelled that could not be made (fused blobs, a toggle that fastened
nothing, stones whose claws missed the girdle). A render can hide all of that; this check can't be fooled by lighting.
Needs: pip install trimesh numpy rtree"""
import sys, json, math, argparse
import numpy as np


def frame(st):
    n = np.asarray(st["n"], float); n /= np.linalg.norm(n)
    e1 = np.asarray(st.get("e1") or np.cross(n, [0, 1, 0] if abs(n[1]) < .9 else [1, 0, 0]), float)
    e1 -= n * np.dot(e1, n); e1 /= np.linalg.norm(e1)
    return n, e1, np.cross(n, e1)


def girdle(st, m=72):
    """Girdle points and outward unit normals in local (e1, e2) coordinates."""
    if st.get("outline"):
        o = np.asarray(st["outline"], float)
        if np.allclose(o[0], o[-1]): o = o[:-1]
        # resample to m points by arc length
        cl = np.vstack([o, o[:1]]); seg = np.linalg.norm(np.diff(cl, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
        t = np.linspace(0, s[-1], m, endpoint=False)
        P = np.column_stack([np.interp(t, s, cl[:, 0]), np.interp(t, s, cl[:, 1])])
        ctr = P.mean(0)
        tg = np.roll(P, -1, 0) - np.roll(P, 1, 0); N = np.column_stack([tg[:, 1], -tg[:, 0]])
        N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
        flip = np.sum(N * (P - ctr), 1) < 0; N[flip] *= -1
        return P, N
    a, b = float(st.get("L") or st["D"]) / 2, float(st["D"]) / 2
    th = np.linspace(0, 2 * math.pi, m, endpoint=False)
    P = np.column_stack([a * np.cos(th), b * np.sin(th)])
    N = np.column_stack([np.cos(th) / a, np.sin(th) / b]); N /= np.linalg.norm(N, axis=1)[:, None]
    return P, N


def groups(flags):
    """Runs of True around a closed ring -> list of (start, length); and the largest False gap, in samples."""
    f = np.asarray(flags, bool); m = len(f)
    if f.all(): return [(0, m)], 0
    if not f.any(): return [], m
    k = int(np.argmin(f))                     # start just after a gap so runs don't wrap
    g = np.roll(f, -k)
    runs, gaps, i = [], [], 0
    while i < m:
        j = i
        while j < m and g[j] == g[i]: j += 1
        (runs if g[i] else gaps).append((i, j - i)); i = j
    return runs, max(l for _, l in gaps)


class Local:
    """Inside/outside test near one stone: crop the casting to a ball round the stone, then call a point inside
    when it lies behind the nearest face (signed distance by nearest-face normal). Robust on the kit's smoothed,
    not-quite-watertight meshes and fast without embree."""
    def __init__(self, mesh, c, R):
        import trimesh
        T = mesh.triangles                          # faces whose bounding box meets the ball's box (big faces too)
        f = np.nonzero(((T.min(1) <= c + R) & (T.max(1) >= c - R)).all(1))[0]
        self.m = mesh.submesh([f], append=True) if len(f) else None

    def contains(self, q):
        if self.m is None: return np.zeros(len(q), bool)
        import trimesh
        cp, d, tid = trimesh.proximity.closest_point(self.m, q)
        s = np.einsum("ij,ij->i", q - cp, self.m.face_normals[tid])
        return s < 0


def check(mesh, stones, unit_mm=1.0, m=72):
    out = []
    centres = []
    for i, st in enumerate(stones):
        D = float(st["D"]); L = float(st.get("L") or D); W = min(D, L)
        c = np.asarray(st["c"], float); n, e1, e2 = frame(st)
        loc = Local(mesh, c, 0.8 * max(L, D) + 1.5 / unit_mm)
        P, N = girdle(st, m)
        to3 = lambda xy, h: c + np.outer(xy[:, 0], e1) + np.outer(xy[:, 1], e2) + h * n
        tiny = 0.12 / unit_mm                     # 0.12 mm in model units
        # HOLD: just outside the girdle, at and above girdle height
        hold = np.zeros(m, bool)
        for d in (0.02, 0.06, 0.12):
            for h in (0.02, 0.06, 0.10, 0.14):
                q = to3(P + N * (d * W + tiny), h * W)
                hold |= loc.contains(q)
        # SEAT: under the girdle, from just inside to just outside
        seat = np.zeros(m, bool)
        for d in (-0.12, -0.04, 0.04):
            for h in (-0.06, -0.14, -0.24):
                q = to3(P + N * (d * W), h * W - tiny)
                seat |= loc.contains(q)
        # CLEAR: points inside the stone (crown and pavilion, shrunk 15%) must not be metal
        inner = []
        layers = ((0.80, 0.03), (0.55, 0.10)) if st.get("bead") else ((0.80, 0.03), (0.55, 0.10), (0.75, -0.06), (0.55, -0.18), (0.30, -0.30))
        for f, h in layers:                   # a bead stone sits proud on its grains: only its top half must be clear
            inner.append(to3(P[::3] * f, h * W))
        inner.append(c[None, :] + n * 0.05 * W)
        inner = np.vstack(inner)
        buried = float(loc.contains(inner).mean())
        hr, hg = groups(hold); sr, sg = groups(seat)
        need = 4 if L / D > 1.2 or D / L > 1.2 else 3
        cont = hold.mean() > 0.9
        hold_ok = cont or (len(hr) >= need and hg < m // 2)
        seat_ok = seat.mean() > 0.9 or (len(sr) >= 3 and sg < m // 2)
        verdict = []
        if not hold.any() and not seat.any(): verdict.append("FLOATING")
        else:
            if not hold_ok: verdict.append(f"HOLD ({len(hr)} holds, widest gap {360 * hg // m} deg; needs {need})")
            if not seat_ok: verdict.append(f"SEAT ({len(sr)} supports, widest gap {360 * sg // m} deg)")
        if buried > 0.10: verdict.append(f"CLEAR ({buried:.0%} of the stone is inside metal: it can't drop in)")
        out.append(dict(i=i, kind=st.get("kind"), size=f"{L:g}x{D:g}" if abs(L - D) > 0.05 else f"{D:g}",
                        holds="bezel" if cont else len(hr), hold_gap_deg=360 * hg // m, seat_cover=round(float(seat.mean()), 2),
                        buried=round(buried, 3), verdict="OK" if not verdict else "; ".join(verdict)))
        centres.append((c, n, e1, e2, P))
    # SPACING: closest girdle-to-girdle distance between neighbours
    gap_min = 0.3 / unit_mm
    for i in range(len(centres)):
        ci, ni, a1, a2, Pi = centres[i]
        Gi = ci + np.outer(Pi[:, 0], a1) + np.outer(Pi[:, 1], a2)
        for j in range(i + 1, len(centres)):
            cj, nj, b1, b2, Pj = centres[j]
            if np.linalg.norm(ci - cj) > (np.abs(Pi).max() + np.abs(Pj).max()) * 1.5 + gap_min: continue
            Gj = cj + np.outer(Pj[:, 0], b1) + np.outer(Pj[:, 1], b2)
            d = float(np.min(np.linalg.norm(Gi[:, None] - Gj[None], axis=2)))
            if d < gap_min:
                for k in (i, j):
                    o = out[k]; msg = f"SPACING ({d * unit_mm:.2f} mm to stone {j if k == i else i})"
                    o["verdict"] = msg if o["verdict"] == "OK" else o["verdict"] + "; " + msg
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl"); ap.add_argument("stones")
    ap.add_argument("--units", default="mm", choices=["mm", "cm"])
    ap.add_argument("--json")
    a = ap.parse_args()
    import trimesh
    mesh = trimesh.load(a.stl, force="mesh")
    d = json.load(open(a.stones)); st = d["stones"] if isinstance(d, dict) else d
    st = [s for s in st if "c" in s and "n" in s]
    if not st:
        print("no stone positions in", a.stones, "(re-run make.py stl: it now writes c/n/e1)"); sys.exit(2)
    res = check(mesh, st, 10.0 if a.units == "cm" else 1.0)
    bad = 0
    for r in res:
        print(f"  {('OK' if r['verdict'] == 'OK' else 'FAIL'):4s} #{r['i']:<3d} {r['kind'] or '?':11s} {r['size']:>8s}  holds {r['holds']!s:5s} gap {r['hold_gap_deg']:3d} deg"
              f"  seat {r['seat_cover']:.2f}  buried {r['buried']:.2f}" + ("" if r["verdict"] == "OK" else "   <- " + r["verdict"]))
        bad += r["verdict"] != "OK"
    print(f"{len(res) - bad} of {len(res)} stones settable" + ("" if not bad else f"; {bad} FAIL"))
    if a.json: json.dump(res, open(a.json, "w"), indent=1)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
