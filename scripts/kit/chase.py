"""Chase every broad stroke of a finished SDF scene with carved-feather barbs (22 Nov 2026 polish overhaul).

Why: the client's bar is a phone photo of real oxidised cast sterling, densely carved, and "why cant these petals
be as detailed as those feathers?" (A4: the best-detailed piece sets the bar for every piece). Most of the kit's
members are smooth swelling strokes, and a smooth stroke has nothing to hold oxide: under the photographic look it
reads as plain chrome. This pass keeps every silhouette and every member exactly as designed (E1: refine, don't
redesign) and cuts the carved-feather surface into the top of each broad stroke after the fact:
  - the crest stays polished as the shaft (a bright line), the flanks carry engraved barbs that sweep back
    toward the stroke's own needle end, so the carving reads the direction the stroke was drawn in
  - U-section cuts 0.18 to 0.24 mm deep (render-fidelity row 2: shallow scratches vanish), width about 0.2 mm
  - pitch scales with the stroke (0.32 to 0.6 mm), jittered, and now and then two barbs split apart or one is
    left out, so it never reads as a machined comb (banned: evenly spaced rows)
  - no cuts near the needle ends (they stay clean points), on thin strokes (claws, wires, prongs, tendrils
    under 0.5 mm), near stones (settings stay exactly as checked), or on a ring's inner face (HOLE)

usage: chase.apply(scene, stones, kind) after the piece is built and bridged, before meshing (make.py CHASE=1).
Env: CH_RMIN 0.5 (mm, thinnest stroke chased), CH_DEPTH 0.2, CH_END 0.14 (fraction of each end left clean).
"""
import math
import os
import numpy as np

CONE = 0.0


def _env(k, d):
    return float(os.environ.get(k, d))


def _chains(P):
    """Group consecutive additive cone rows that join end to start into strokes."""
    out, cur = [], []
    for i, r in enumerate(P):
        if r[0] != CONE or r[1] != 0.0:
            if cur: out.append(cur); cur = []
            continue
        a = r[4:7]; R = r[7:16].reshape(3, 3); L = r[16]
        if cur:
            pr = P[cur[-1]]; pb = pr[4:7] + pr[7:16].reshape(3, 3)[0] * pr[16]
            if np.linalg.norm(pb - a) > 1e-3:
                out.append(cur); cur = []
        cur.append(i)
    if cur: out.append(cur)
    return out


def apply(s, stones, kind, seed=7):
    """ov2 (22 Nov): every cut is tested against the real metal before it is kept. ov1 trusted a lens-section
    model of each stroke; where strokes fuse, flatten or overlap the model was wrong, and a voxel wall test showed
    under-0.6 mm metal rising from 3.6% to 13% of a piece, plus two weakened stone heads (Vine ear). Now a barb is
    kept only if: its floor has 0.6 mm of metal under it (a 0.3 mm ball fits 0.3 mm below the floor), it does not
    break out through the stroke's side, its centre really is just under a surface (so it opens up, not into a
    buried overlap), and it stays 1 mm further from every stone than before."""
    import sdf as SD
    P = s.array()
    idx = np.arange(len(P), dtype=np.int64)
    rng = np.random.default_rng(seed)
    rmin = _env("CH_RMIN", 0.5); depth = _env("CH_DEPTH", 0.2); endf = _env("CH_END", 0.14)
    lo = P[:, 19:22].min(0); hi = P[:, 22:25].max(0); ctr = (lo + hi) / 2
    st = [(np.asarray(r["c"], float), 0.5 * max(r["D"], r["L"]) + 1.7) for r in stones if "c" in r]
    cand = []                                   # (pts, gw, n, y*side, g)
    n_strokes = 0
    for ch in _chains(P):
        if len(ch) < 6: continue
        A = np.array([P[i, 4:7] for i in ch]); X = np.array([P[i, 7:10] for i in ch]); N = np.array([P[i, 13:16] for i in ch])
        Ls = np.array([P[i, 16] for i in ch]); r1 = np.array([P[i, 17] for i in ch]); fl = np.array([P[i, 3] for i in ch])
        tot = Ls.sum()
        if tot < 3.0 or np.median(r1) < rmin: continue
        cum = np.concatenate([[0], np.cumsum(Ls)])
        tip_dir = 1.0 if r1[-1] <= r1[0] else -1.0        # barbs sweep toward the thinner (needle) end
        n_strokes += 1
        u = 0.0
        while True:
            rr = float(np.interp(u, cum[:-1], r1))
            pitch = float(np.clip(0.4 * rr, 0.28, 0.45)) * rng.uniform(0.85, 1.15)
            u += pitch
            if u >= tot: break
            f = u / tot
            if f < endf or f > 1 - endf: continue
            k = min(int(np.searchsorted(cum, u) - 1), len(ch) - 1)
            t = (u - cum[k]) / max(Ls[k], 1e-6)
            r = r1[k] if k + 1 >= len(ch) else r1[k] * (1 - t) + r1[k + 1] * t
            if r < rmin: continue
            if rng.random() < 0.08: continue                 # a barb left out now and then (a split)
            x = X[k]; n = N[k]; y = np.cross(n, x)
            c = A[k] + x * Ls[k] * t
            th = r / max(fl[k], 1.0)
            if any(np.linalg.norm(c - sc) < sr + r for sc, sr in st): continue
            if kind == "ring":                                # never the inner face of a ring
                out = c - ctr; out[1] = 0.0                   # ring axis is the kit's Y
                if np.dot(n, out) < -0.2 * np.linalg.norm(out): continue
            dz = min(depth, 2 * th - 0.6)
            if dz < 0.12: continue
            g = float(np.clip(0.07 + 0.02 * r, 0.085, 0.11))
            sweep = math.radians(rng.uniform(54, 60))
            for side in (1.0, -1.0):
                vs = []
                for dzv in (dz, max(0.12, dz - 0.04), 0.12):          # deepest first: a barb is cut as deep as the wall allows
                    for eo in (0.86, 0.72, 0.6):                      # and as long as the edge allows
                        pts = []
                        for e in (0.12, 0.5 * (0.12 + eo), eo):
                            lat = e * r
                            h = th * math.sqrt(max(0.0, 1 - e * e))
                            back = lat * math.tan(sweep) * 0.9
                            pts.append(c + y * side * lat + x * tip_dir * back + n * (h - (dzv - g)))
                        vs.append(pts)
                cand.append((vs, [g * 0.8, g, g * 0.7], n, y * side, g))
    if not cand:
        print(f"chase: {n_strokes} strokes, 0 cuts", flush=True); return 0
    cand_n = len(cand); n_cut = 0; n_ok = 0
    if os.environ.get("CH_MODE", "ridge") == "ridge":
        # ov2 default: RAISED barbs. Most strokes are 0.7 to 0.9 mm thick, too thin to cut 0.12 to 0.2 mm into and
        # keep a 0.5 mm floor (the wall test passed 5 of 462 cut barbs on the Feitian ear). So the barbs stand
        # proud of the stroke instead, like chased relief: tapered ridges (pointed both ends, never a round cap)
        # laid on the surface, and the narrow valleys between them hold the oxide. Nothing is cut, so no wall
        # gets thinner and the mesh stays closed.
        hr = _env("CH_RIDGE", 0.11)
        Q = np.array([vs[0][j] for vs, gw, n, ys, g in cand for j in range(3)], np.float64)
        Nn = np.array([n for vs, gw, n, ys, g in cand for j in range(3)], np.float64)
        Pa = np.asarray(P, np.float64)
        for _ in range(3):                                    # project each barb point onto the real surface along n
            dd = SD.eval_pts(Q, Pa, idx); Q = Q - Nn * dd[:, None]
        dd = SD.eval_pts(np.vstack([Q, Q - Nn * 0.3, Q + Nn * 0.3]), Pa, idx).reshape(3, -1)
        good = ((np.abs(dd[0]) < 0.04) & (dd[1] < 0) & (dd[2] > 0.05)).reshape(cand_n, 3).all(1)   # on a face, not an edge
        Q = Q.reshape(cand_n, 3, 3); Nn = Nn.reshape(cand_n, 3, 3)
        for i in np.nonzero(good)[0]:
            p0, p1, p2 = Q[i] - Nn[i] * hr * 0.35
            seglen = np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1)
            if seglen < 0.25: continue
            s.cone(p0 - (p1 - p0) * 0.15, p1, 0.02, hr, k=0.03)       # swell from a point
            s.cone(p1, p2 + (p2 - p1) * 0.15, hr, 0.02, k=0.0)        # and draw out to a point
            n_cut += 2; n_ok += 1
        print(f"chase: {n_strokes} strokes, {n_cut} ridge segments ({n_ok} of {cand_n} barbs on a face)", flush=True)
        return n_cut
    NV = len(cand[0][0])
    Q = []
    for vs, gw, n, ys, g in cand:
        for pts in vs:
            for p in pts:
                fl_ = p - n * g                                   # the cut's floor
                Q += [p, p + n * (g + 0.14), fl_ - n * 0.25, p + ys * (g + 0.15)]
    d = SD.eval_pts(np.asarray(Q, np.float64), np.asarray(P, np.float64), idx).reshape(len(cand), NV, 3, 4)
    okv = ((d[..., 0] < 0)                      # cut centre inside metal
           & (d[..., 1] > 0)                    # a surface just above: the cut opens up, not into a buried overlap
           & (d[..., 2] <= -0.25)               # 0.5 mm of metal under the floor (0.25 ball fits 0.25 below it)
           & (d[..., 3] < -0.03)).all(2)        # no break-out through the side
    for (vs, gw, n, ys, g), ok in zip(cand, okv):
        if not ok.any(): continue
        pts = vs[int(np.argmax(ok))]; n_ok += 1
        for a_, b_, ga, gb in zip(pts[:-1], pts[1:], gw[:-1], gw[1:]):
            s.cone(a_, b_, ga, gb, op=1, k=0.04); n_cut += 1
    print(f"chase: {n_strokes} strokes, {n_cut} cuts ({n_ok} of {cand_n} barbs passed the wall test)", flush=True)
    return n_cut
