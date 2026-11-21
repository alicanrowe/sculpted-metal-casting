"""Member check: how the strokes of a piece end and meet, straight from the SDF scene (no mesh needed).
Catches the faults the stone, joint and clipping checks never looked at (Bombyx review 2, 21 Nov 2026):
  NUB    a stroke that ends blunt (end radius >= --min-r) with its round cap showing: in air, or half out of
         the member it butts into ("this nub in buyao is ugly", "senmurv ... got some nubs to smooth out").
         An end must draw out to a point, or be swallowed whole by the metal it joins.
  CROSS  a stroke whose centre runs through or over a carved blade (feather/leaf) away from the blade's root
         ("zhang qians vine needs fixing": stems laid across the leaf face with melted junctions).
         A stem may only meet a leaf at its root.
  BOLT   a separate point (a short cone drawn to a needle) started inside a much wider body: the body necks
         down in a step to a pinched spike instead of tapering as one curve ("feitan needs more smoothing").
  HOLE   (rings) metal inside the finger opening, below the inner face of the band
         ("this piece still has geometry issues": nubs and spikes in the finger hole).
usage: python check_members.py <piece> [<piece> ...] [--min-r 0.45] [--json out.json]   exit 1 if any fault.
       from check_members import check_scene; check_scene(scene, stones, kind)   (planted tests)
"""
import sys, os, json, math, argparse
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("pieces", nargs="*")
ap.add_argument("--min-r", type=float, default=0.45, help="mm: ends thinner than this are points, not caps")
ap.add_argument("--show", type=float, default=0.6, help="fraction of the cap that may show")
ap.add_argument("--cross", type=float, default=1.0, help="mm of a stroke allowed over a blade away from its root")
ap.add_argument("--ring-r", type=float, default=None, help="mm: finger-hole radius of the ring band (default: the kit's RING_R)")
ap.add_argument("--json")
a = ap.parse_args([] if __name__ != "__main__" else None)
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/nbcache")
import sdf
import traceback as _tb
_ORIG_ADD = sdf.Scene._add
def _traced_add(self, *aa, **kw):
    _ORIG_ADD(self, *aa, **kw)
    if not hasattr(self, "who"): self.who = []
    fr = [f"{x.name}:{x.lineno}" for x in _tb.extract_stack(limit=9)[:-1] if x.name not in ("_traced_add", "cone", "stroke", "ribbon", "mk", "check", "<module>", "_add")]
    self.who.append(" < ".join(fr[::-1][:4]))
sdf.Scene._add = _traced_add
try:
    from make import PIECES
except Exception:
    PIECES = {}

CONE, FEATHER = sdf.CONE, sdf.FEATHER


def chains(P):
    """consecutive cone rows that join end to start form one stroke"""
    out = []; cur = []
    for i in range(len(P)):
        r = P[i]
        if r[0] != CONE or r[1] != 0:
            if cur: out.append(cur); cur = []
            continue
        a_ = r[4:7]; b_ = a_ + r[7:10] * r[16]
        if cur:
            pr = P[cur[-1]]; pb = pr[4:7] + pr[7:10] * pr[16]
            if np.linalg.norm(pb - a_) < 1e-4: cur.append(i); continue
            out.append(cur)
        cur = [i]
    if cur: out.append(cur)
    return out


def hemi(n=24):
    g = (1 + 5 ** 0.5) / 2; k = np.arange(n) + 0.5
    z = k / n; r = np.sqrt(1 - z * z); t = 2 * math.pi * k / g
    return np.stack([r * np.cos(t), r * np.sin(t), z], 1)          # unit hemisphere about +z


H = hemi()


def basis(t):
    t = t / np.linalg.norm(t); u = np.cross(t, [0, 0, 1.0])
    if np.linalg.norm(u) < 1e-3: u = np.cross(t, [0, 1.0, 0])
    u /= np.linalg.norm(u); v = np.cross(t, u)
    return np.stack([u, v, t], 0)


def check(name):
    mk, kind = PIECES[name]
    s, st = mk()
    return check_scene(s, st, kind)


def check_scene(s, st, kind, band_rows=60):
    P = s.array().astype(np.float64)
    n = len(P); allidx = np.arange(n, dtype=np.int64)
    stones = [(np.asarray(q["c"], float), max(float(q["D"]), float(q.get("L", q["D"])))) for q in st]
    faults = []

    def near_stone(p, pad=1.2):
        return any(np.linalg.norm(p - c) < D / 2 + pad for c, D in stones)

    def rest(ch):
        m = np.ones(n, bool); m[ch] = False
        return allidx[m]

    ch_all = chains(P)
    for ch in ch_all:
        if hasattr(s, 'who') and 'prong' in s.who[ch[0]]: continue
        r0 = P[ch[0]]; r1 = P[ch[-1]]
        ends = [(r0[4:7], -r0[7:10], r0[17]), (r1[4:7] + r1[7:10] * r1[16], r1[7:10], r1[18])]
        L = sum(P[i][16] for i in ch)
        idx = None
        closed = np.linalg.norm(ends[0][0] - ends[1][0]) < 1e-3          # a closed loop has no ends
        src = s.who[ch[0]] if hasattr(s, "who") else ""
        finding = any(f in src for f in ("ear_wire", "stud_post", "pin:", "prong"))  # claws are the setter's, checked by check_settings  # bought-in findings' own ends are functional
        for e, (p, t, r) in enumerate(ends):
            if closed or finding or r < a.min_r or near_stone(p): continue
            if idx is None: idx = rest(ch)
            q = p + (H * r * 0.92) @ basis(t)
            d = sdf.eval_pts(q.astype(np.float32), P, idx)
            show = float((d > 0.0).mean())
            if show > a.show:
                faults.append(dict(kind="NUB", at=np.round(p, 2).tolist(), r=round(float(r), 2), showing=round(show, 2), stroke_mm=round(float(L), 1), src=s.who[ch[0]] if hasattr(s, "who") else ""))
        # BOLT: a short stroke drawn to a needle whose start sits inside a much wider body
        if len(ch) <= 3 and ends[1][2] < 0.25 and ends[0][2] < 0.9 and L < 6:
            if idx is None: idx = rest(ch)
            p0 = ends[0][0]; d0 = float(sdf.eval_pts(p0[None].astype(np.float32), P, idx)[0])
            # walk out along the stroke to where it leaves the body, and compare its radius with the body's width there
            t = -ends[0][1] / np.linalg.norm(ends[0][1]); B = basis(t)
            for f in np.linspace(0, 1, 11):
                pt = p0 + t * L * f
                if sdf.eval_pts(pt[None].astype(np.float32), P, idx)[0] > 0: break
            rr = ends[0][2] + (ends[1][2] - ends[0][2]) * f
            back = pt - t * 0.6
            side = np.array([back + B[0] * w for w in np.linspace(-4, 4, 33)])
            ds = sdf.eval_pts(side.astype(np.float32), P, idx)
            width = float((ds < 0).sum()) * 0.25 / 2         # half width of the body just behind the exit
            if width > max(1.0, 2.5 * rr) and not near_stone(p0, 1.2):
                faults.append(dict(kind="BOLT", at=np.round(pt, 2).tolist(), point_r=round(float(rr), 2), body_half_width=round(width, 2), src=s.who[ch[0]] if hasattr(s, "who") else ""))
    # CROSS: strokes over carved blades away from their root
    blades = [i for i in range(n) if P[i][0] == FEATHER and P[i][1] == 0]
    for b in blades:
        base = P[b][4:7]; Lb = P[b][25]
        bi = np.array([b], np.int64)
        for ch in ch_all:
            if hasattr(s, 'who') and any(w_ in s.who[ch[0]] for w_ in ('prong', 'ring_base', 'cuff_rails')): continue   # the shank/rails carry the motif from below
            pts = []; rad = []
            for i in ch:
                r = P[i]; a_ = r[4:7]; d_ = r[7:10] * r[16]
                for f in np.linspace(0, 1, max(2, int(r[16] / 0.25) + 1)):
                    pts.append(a_ + d_ * f); rad.append(r[17] + (r[18] - r[17]) * f)
            pts = np.array(pts); rad = np.array(rad)
            far = np.linalg.norm(pts - base, axis=1) > max(1.6, 0.18 * Lb)
            if not far.any(): continue
            d = sdf.eval_pts(pts.astype(np.float32), P, bi)
            hit = far & (d < rad * 0.6) & (rad > 0.25)
            if hit.sum() == 0: continue
            seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
            mm = float((seg * hit[1:]).sum())
            if mm > a.cross:
                faults.append(dict(kind="CROSS", at=np.round(pts[hit][0], 2).tolist(), mm_over_blade=round(mm, 1), blade_root=np.round(base, 2).tolist(), src=s.who[ch[0]] if hasattr(s, "who") else ""))
    # HOLE: rings only, metal inside the finger opening
    if kind == "ring":
        RING_R = a.ring_r
        if RING_R is None:
            from bombyx import RING_R
        band = np.arange(min(n, band_rows), dtype=np.int64)               # ring_base draws the band first (stroke + torus)
        th = np.linspace(-math.pi, math.pi, 180, endpoint=False); ys = np.linspace(-8, 8, 33)
        T, Y = np.meshgrid(th, ys, indexing="ij")
        def inner(idx):
            rs = np.linspace(RING_R - 3.0, RING_R + 0.5, 71)
            q = np.stack([np.sin(T)[..., None] * rs, np.broadcast_to(Y[..., None], T.shape + rs.shape), np.cos(T)[..., None] * rs], -1)
            d = sdf.eval_pts(q.reshape(-1, 3).astype(np.float32), P, idx).reshape(q.shape[:-1])
            hit = d < 0; first = np.where(hit.any(-1), hit.argmax(-1), len(rs) - 1)
            return rs[first]
        rin = inner(allidx); rb = inner(band)
        ref = rb[:, 16].min()                                        # the band's inner face at mid-width
        bad = rin < ref - 0.15
        if bad.any():
            k = np.argwhere(bad)
            worst = k[np.argmin(rin[bad])]
            faults.append(dict(kind="HOLE", cells=int(bad.sum()), deepest_mm=round(float(ref - rin[bad].min()), 2),
                               at_deg=round(float(np.degrees(th[worst[0]])), 0), at_y=round(float(ys[worst[1]]), 1)))
    return faults


if __name__ != "__main__": a.pieces = []
allf = {}; nbad = 0
for name in a.pieces:
    f = check(name); allf[name] = f
    kinds = {}
    for x in f: kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    print("members", name, "faults", len(f), " ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "OK")
    for x in f: print("   ", json.dumps(x))
    nbad += bool(f)
if __name__ == "__main__":
    if a.json: json.dump(allf, open(a.json, "w"), indent=1)
    sys.exit(1 if nbad else 0)
