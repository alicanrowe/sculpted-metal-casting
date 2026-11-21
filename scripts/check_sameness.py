"""Sameness check: does a new collection look too much like itself, or like the collections before it?

The client's rule: every piece in a collection has its own silhouette idea, and a new collection must not read
as an earlier one in a new colour ("a bit samey", "meh samey", "ten near-identical cuffs"). This scores what a
viewer actually sees, the product squares, plus the meshes when they exist, and flags the pairs that are too
close before anyone else sees them.

    python3 -I check_sameness.py --new NAME=SQUARES_DIR [--new-stl STL_DIR] \
        --ref NAME=SQUARES_DIR [--ref NAME=SQUARES_DIR ...] [--ref-stl NAME=STL_DIR ...] \
        [--types TYPES.json] [--out REPORT_DIR]

Squares are the 1080 px four-view squares (hero view on top). Only the hero view is scored. Each image becomes
six feature groups:
  shape    silhouette of the hero view, normalised and compared by IoU (best of four flips)
  outline  how straight the silhouette contour is (turning-angle histogram): machined vs grown
  tone     luminance histogram of the piece: all-bright, two-tone, dark
  colour   share of saturated pixels and their hue histogram: stone or enamel load and colour
  edges    gradient-orientation histogram and edge density: straight ruled detail vs curling detail
  grain    fine-detail energy at three scales: knurl or engraving vs smooth polish
and, when both pieces have an STL,
  surface  dihedral-angle histogram of the mesh: crisp machined edges vs smooth cast surfaces.
Each group distance is divided by the median distance of that group across the reference collections, so 1.0
means "as different as two typical reference pieces". The pair distance D is the weighted mean.

Flags. Calibration (Nov 2026, two cast-silver collections of 72 and 64 squares): one design in four colourways
scores D 0.01 to 0.05; two rings from different motifs of one collection (same type, same organic silver, pale
stone on top) 0.29 to 0.6, median 0.62 for same-type pairs; a piece's nearest piece in the other collection
median 0.67, 5th percentile 0.44.
  SAME  D < 0.35  inside the new collection: two pieces read as one design. Fix before showing.
  NEAR  D < 0.55  inside the new collection: look at the pair; they need different silhouette ideas.
  ECHO  D < 0.50  a new piece's nearest piece in an earlier collection: it reads as that collection. Fix.
Collection level:
  RESKIN  set ratio under 1.10: mean D between the new and an earlier collection, over the mean D inside them.
          About 1.0 means the new pieces sit among the old ones: the whole set reads as the old one, recoloured.
          Calibration: a later round of the same collection 1.04; a second collection built on the first one's
          kit, types and finish 1.04 (flagged, rightly); a machined two-tone collection against both 1.25 to 1.34.
          A centroid test was tried first and rejected: the means of any two varied sets of silver on white
          converge, so it flagged everything.
  TYPES   more than half the pieces are ring / earrings / cuff / pendant, or the type mix is close to an earlier
          collection's (Jensen-Shannon under 0.15): pick piece types that come from the brief.
Exit code 1 when anything is flagged SAME, ECHO, RESKIN or TYPES.
Writes REPORT_DIR/sameness.json, sameness.txt and pairs.jpg (the closest pairs side by side).
"""
import sys, os, re, json, glob, math, argparse
import numpy as np
from PIL import Image

HERO_H = 760          # the square's hero view band
GROUPS = ["shape", "outline", "tone", "colour", "edges", "grain", "surface"]
WEIGHTS = {"shape": 1.4, "outline": 1.0, "tone": 1.0, "colour": 0.8, "edges": 1.0, "grain": 0.8, "surface": 1.2}
T_SAME, T_NEAR, T_ECHO = 0.35, 0.55, 0.50
T_RESKIN = 1.10   # set ratio under this: the new set sits among the old pieces (see calibration)
BASIC = {"ring", "ear", "earrings", "cuff", "pendant"}
TYPE_WORDS = ["ring", "ear", "pendant", "cuff", "clip", "necklace", "bangle", "bracelet", "brooch", "stud", "tiebar",
              "cufflinks", "signet", "medallion", "bolo", "stack", "buckle", "collar", "climber", "drop", "nail", "choker",
              "chain", "pin", "anklet", "grill", "cap"]


# ------------------------------------------------------------------ image features
def load_hero(path):
    im = Image.open(path).convert("RGB")
    if im.size[0] == im.size[1] and im.size[0] >= 1000:
        k = im.size[0] / 1080.0
        im = im.crop((0, 0, im.size[0], int(HERO_H * k)))
    return np.asarray(im, np.float32) / 255.0


def fg_mask(a):
    mn = a.min(2); mx = a.max(2)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    m = (mn < 0.93) | ((sat > 0.18) & (mx < 0.995))
    from scipy import ndimage
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_fill_holes(m)
    return m


def norm_mask(m, S=96):
    ys, xs = np.nonzero(m)
    if not len(ys): return np.zeros((S, S), bool)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    c = m[y0:y1, x0:x1]
    h, w = c.shape; k = (S - 4) / max(h, w)
    im = Image.fromarray((c * 255).astype(np.uint8)).resize((max(1, int(w * k)), max(1, int(h * k))), Image.BILINEAR)
    out = np.zeros((S, S), np.uint8)
    oy = (S - im.size[1]) // 2; ox = (S - im.size[0]) // 2
    out[oy:oy + im.size[1], ox:ox + im.size[0]] = np.asarray(im)
    return out > 127


def contour_turns(m):
    from skimage import measure
    cs = measure.find_contours(np.pad(m.astype(float), 2), 0.5)
    if not cs: return np.zeros(8)
    c = max(cs, key=len)
    # resample to even steps, then turning angles
    d = np.linalg.norm(np.diff(c, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(d)])
    n = max(32, int(s[-1] / 2.0)); u = np.linspace(0, s[-1], n)
    c = np.stack([np.interp(u, s, c[:, 0]), np.interp(u, s, c[:, 1])], 1)
    v = np.diff(c, axis=0); ang = np.arctan2(v[:, 0], v[:, 1])
    t = np.abs((np.diff(ang) + np.pi) % (2 * np.pi) - np.pi)
    # smooth over 3 steps so pixel stair-steps don't count as turns
    t = np.convolve(t, np.ones(3) / 3, "same")
    h, _ = np.histogram(np.degrees(t), bins=[0, 1, 2.5, 5, 10, 20, 40, 80, 181])
    return h / max(h.sum(), 1)


def image_features(path):
    a = load_hero(path)
    m = fg_mask(a)
    nm = norm_mask(m)
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    fl = lum[m] if m.any() else np.array([1.0])
    tone, _ = np.histogram(fl, bins=10, range=(0, 1)); tone = tone / max(tone.sum(), 1)
    mx = a.max(2); mn = a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-3)
    colmask = m & (sat > 0.28) & (mx > 0.15)
    frac = colmask.sum() / max(m.sum(), 1)
    import colorsys
    if colmask.any():
        rgb = a[colmask][::max(1, colmask.sum() // 4000)]
        hues = np.array([colorsys.rgb_to_hsv(*p)[0] for p in rgb])
        hh, _ = np.histogram(hues, bins=12, range=(0, 1)); hh = hh / max(hh.sum(), 1)
    else:
        hh = np.zeros(12)
    colour = np.concatenate([[min(1.0, frac * 6)], hh * min(1.0, frac * 6)])
    # edges: gradient orientation histogram (magnitude weighted), inside the piece
    gy, gx = np.gradient(lum)
    mag = np.hypot(gx, gy); ori = (np.arctan2(gy, gx) % np.pi)
    w = mag * m
    eh, _ = np.histogram(ori[m], bins=12, range=(0, np.pi), weights=w[m]); eh = eh / max(eh.sum(), 1e-9)
    eh = np.roll(eh, -int(np.argmax(eh)))                     # rotation-invariant: dominant direction first
    dens = float((mag[m] > 0.08).mean()) if m.any() else 0.0
    peak = float(eh.max())
    edges = np.concatenate([eh, [dens, peak]])
    # grain: band-pass energy at three scales inside the piece, relative to its overall contrast
    from scipy import ndimage
    g1 = ndimage.gaussian_filter(lum, 0.8); g2 = ndimage.gaussian_filter(lum, 2.0); g3 = ndimage.gaussian_filter(lum, 5.0)
    b1 = np.abs(lum - g1)[m].mean() if m.any() else 0; b2 = np.abs(g1 - g2)[m].mean() if m.any() else 0
    b3 = np.abs(g2 - g3)[m].mean() if m.any() else 0
    tot = b1 + b2 + b3 + 1e-6
    grain = np.array([b1 / tot, b2 / tot, b3 / tot, min(1.0, tot * 8)])
    return dict(shape=nm, outline=contour_turns(nm), tone=tone, colour=colour, edges=edges, grain=grain,
                fill=float(nm.mean()), aspect=float(_aspect(m)))


def _aspect(m):
    ys, xs = np.nonzero(m)
    if not len(ys): return 1.0
    return (xs.max() - xs.min() + 1) / (ys.max() - ys.min() + 1)


# ------------------------------------------------------------------ mesh feature
def mesh_features(path, max_faces=60000):
    import trimesh
    m = trimesh.load(path, force="mesh")
    if len(m.faces) > max_faces:
        try:
            import fast_simplification
            V, F = fast_simplification.simplify(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.int32),
                                                target_reduction=1 - max_faces / len(m.faces))
            m = trimesh.Trimesh(V, F, process=True)
        except Exception:
            pass
    ang = m.face_adjacency_angles
    L = m.edges_unique_length[m.face_adjacency_edges_tree.query(m.face_adjacency_edges)[1]] if False else None
    w = np.linalg.norm(m.vertices[m.face_adjacency_edges[:, 0]] - m.vertices[m.face_adjacency_edges[:, 1]], axis=1)
    h, _ = np.histogram(np.degrees(ang), bins=[0, 2, 5, 10, 20, 35, 60, 90, 181], weights=w)
    return h / max(h.sum(), 1e-9)


# ------------------------------------------------------------------ distances
def group_dist(a, b, g):
    if g == "shape":
        A = a["shape"]; best = 0.0
        for B in (b["shape"], b["shape"][:, ::-1], b["shape"][::-1, :], b["shape"][::-1, ::-1]):
            inter = (A & B).sum(); uni = (A | B).sum()
            best = max(best, inter / max(uni, 1))
        return 1.0 - best + 0.5 * abs(math.log(max(a["aspect"], 1e-3) / max(b["aspect"], 1e-3))) * 0.3
    if g == "surface":
        if a.get("surface") is None or b.get("surface") is None: return None
    x, y = np.asarray(a[g], float), np.asarray(b[g], float)
    if g in ("tone", "outline", "surface"):          # histograms: Hellinger
        return float(np.sqrt(0.5 * ((np.sqrt(x) - np.sqrt(y)) ** 2).sum()))
    return float(np.linalg.norm(x - y))


def pair_D(a, b, scale):
    num = den = 0.0; parts = {}
    for g in GROUPS:
        d = group_dist(a, b, g)
        if d is None: continue
        dn = d / max(scale.get(g, 1.0), 1e-6)
        parts[g] = round(float(dn), 3); num += WEIGHTS[g] * dn; den += WEIGHTS[g]
    return num / max(den, 1e-9), parts


def ptype(name, types):
    if name in types: return types[name]
    toks = re.split(r"[_\-]", name.lower())
    for t in reversed(toks):
        for w in TYPE_WORDS:
            if t.startswith(w): return {"earrings": "ear", "stud": "ear"}.get(w, w)
    return toks[-1]


def js(p, q):
    keys = sorted(set(p) | set(q)); P = np.array([p.get(k, 0) for k in keys], float); Q = np.array([q.get(k, 0) for k in keys], float)
    P /= max(P.sum(), 1e-9); Q /= max(Q.sum(), 1e-9); Mx = (P + Q) / 2
    kl = lambda a, b: float(np.sum(np.where(a > 0, a * np.log2(np.maximum(a, 1e-12) / np.maximum(b, 1e-12)), 0)))
    return 0.5 * kl(P, Mx) + 0.5 * kl(Q, Mx)


def load_set(name, sq_dir, stl_dir=None, skip=("_",)):
    out = {}
    for f in sorted(glob.glob(os.path.join(sq_dir, "*.jpg")) + glob.glob(os.path.join(sq_dir, "*.png"))):
        n = os.path.splitext(os.path.basename(f))[0]
        if n.startswith(skip) or "." in n: continue          # stale copies like x.r1-stale
        ft = image_features(f); ft["file"] = f; ft["set"] = name; ft["name"] = n
        if stl_dir:
            s = os.path.join(stl_dir, n + ".stl")
            if os.path.exists(s):
                try: ft["surface"] = mesh_features(s)
                except Exception as e: print("mesh", n, e, file=sys.stderr)
        out[n] = ft
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True); ap.add_argument("--new-stl")
    ap.add_argument("--ref", action="append", default=[]); ap.add_argument("--ref-stl", action="append", default=[])
    ap.add_argument("--types"); ap.add_argument("--out", default="sameness_report")
    ap.add_argument("--max-ref", type=int, default=120, help="cap per reference set (evenly sampled)")
    a = ap.parse_args()
    types = json.load(open(a.types)) if a.types else {}
    nn, nd = a.new.split("=", 1)
    new = load_set(nn, nd, a.new_stl)
    rstl = dict(x.split("=", 1) for x in a.ref_stl)
    refs = {}
    for r in a.ref:
        rn, rd = r.split("=", 1)
        s = load_set(rn, rd, rstl.get(rn))
        if len(s) > a.max_ref:
            ks = sorted(s); idx = np.linspace(0, len(ks) - 1, a.max_ref).astype(int); s = {ks[i]: s[ks[i]] for i in idx}
        refs[rn] = s
    pool = [f for s in refs.values() for f in s.values()]
    if len(pool) < 4: pool = pool + list(new.values())
    # scale: median per-group distance across the reference pool (typical difference = 1.0)
    rng = np.random.default_rng(0); scale = {}
    pairs = [(pool[i], pool[j]) for i in range(len(pool)) for j in range(i + 1, len(pool))]
    if len(pairs) > 3000: pairs = [pairs[k] for k in rng.choice(len(pairs), 3000, replace=False)]
    for g in GROUPS:
        ds = [group_dist(x, y, g) for x, y in pairs]; ds = [d for d in ds if d is not None]
        scale[g] = float(np.median(ds)) if ds else 1.0
    flags = []; rep = dict(new=nn, n_new=len(new), refs={k: len(v) for k, v in refs.items()}, scale=scale, within=[], echo=[], collection={})
    names = sorted(new)
    # within the new collection
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            D, parts = pair_D(new[names[i]], new[names[j]], scale)
            row = dict(a=names[i], b=names[j], D=round(D, 3), parts=parts)
            if D < T_SAME: row["flag"] = "SAME"; flags.append(row)
            elif D < T_NEAR: row["flag"] = "NEAR"
            rep["within"].append(row)
    rep["within"].sort(key=lambda r: r["D"])
    # against every earlier collection
    for n in names:
        best = None
        for rn, s in refs.items():
            for m, f in s.items():
                D, parts = pair_D(new[n], f, scale)
                if best is None or D < best["D"]: best = dict(piece=n, nearest=f"{rn}/{m}", D=round(D, 3), parts=parts)
        if best:
            if best["D"] < T_ECHO: best["flag"] = "ECHO"; flags.append(best)
            rep["echo"].append(best)
    rep["echo"].sort(key=lambda r: r["D"])
    # collection level: does the set as a whole read as a new collection, or as an old one recoloured?
    # Energy-distance ratio: R = mean cross-collection D / mean of the two within-collection Ds. A reskin of an
    # old collection gives R about 1 (its pieces sit among the old ones); a set with its own look gives R well
    # above 1. Also reported: how many new pieces have their nearest neighbour in their own collection.
    for rn, s in refs.items():
        if not s: continue
        R_ = list(s.values()); N_ = [new[n] for n in names]
        cross = [pair_D(x, y, scale)[0] for x in N_ for y in R_]
        win_n = [pair_D(N_[i_], N_[j_], scale)[0] for i_ in range(len(N_)) for j_ in range(i_ + 1, len(N_))]
        rr = [(R_[i_], R_[j_]) for i_ in range(len(R_)) for j_ in range(i_ + 1, len(R_))]
        if len(rr) > 1500: rr = [rr[k] for k in rng.choice(len(rr), 1500, replace=False)]
        win_r = [pair_D(x, y, scale)[0] for x, y in rr]
        ratio = float(np.mean(cross) / max(0.5 * (np.mean(win_n) + np.mean(win_r)), 1e-9)) if win_n else 0.0
        own = 0
        for i_, x in enumerate(N_):
            dn = min([pair_D(x, y, scale)[0] for j_, y in enumerate(N_) if j_ != i_] or [9])
            dr = min(cross[i_ * len(R_):(i_ + 1) * len(R_)])
            own += dn < dr
        r = dict(ref=rn, set_ratio=round(ratio, 3), own_nearest=f"{own}/{len(N_)}")
        if ratio < T_RESKIN: r["flag"] = "RESKIN"; flags.append(dict(collection=rn, **r))
        rep["collection"][rn] = r
    tn = {}; [tn.__setitem__(ptype(n, types), tn.get(ptype(n, types), 0) + 1) for n in names]
    rep["types"] = tn
    basic = sum(v for k, v in tn.items() if k in BASIC) / max(len(names), 1)
    rep["basic_share"] = round(basic, 2)
    if basic > 0.5: flags.append(dict(flag="TYPES", why=f"{basic:.0%} of pieces are ring/ear/cuff/pendant"))
    for rn, s in refs.items():
        tr = {}; [tr.__setitem__(ptype(m, types), tr.get(ptype(m, types), 0) + 1) for m in s]
        j = js(tn, tr); rep["collection"].setdefault(rn, {})["type_js"] = round(j, 3)
        if j < 0.15: flags.append(dict(flag="TYPES", why=f"type mix close to {rn} (JS {j:.2f})"))
    rep["flags"] = flags
    os.makedirs(a.out, exist_ok=True)
    json.dump(rep, open(os.path.join(a.out, "sameness.json"), "w"), indent=1, default=str)
    lines = [f"Sameness check: {nn} ({len(new)} pieces) against " + ", ".join(f"{k} ({v})" for k, v in rep["refs"].items()),
             f"types: {tn}  basic share {basic:.0%}"]
    for rn, r in rep["collection"].items():
        lines.append(f"vs {rn}: set ratio {r.get('set_ratio')} (1.0 = reads as the same collection), nearest neighbour in own set {r.get('own_nearest')}, type JS {r.get('type_js')} {r.get('flag', '')}")
    lines.append("closest pairs inside the collection (D, 1.0 = typical difference):")
    for r in rep["within"][:8]: lines.append(f"  {r['D']:.2f} {r.get('flag', ''):4s} {r['a']} ~ {r['b']}  {r['parts']}")
    lines.append("nearest earlier piece for each new piece:")
    for r in rep["echo"]: lines.append(f"  {r['D']:.2f} {r.get('flag', ''):4s} {r['piece']} ~ {r['nearest']}")
    bad = [f for f in flags if f.get("flag") in ("SAME", "ECHO", "RESKIN", "TYPES")]
    lines.append("RESULT: " + ("PASS" if not bad else f"FAIL ({len(bad)} flags)"))
    txt = "\n".join(lines); open(os.path.join(a.out, "sameness.txt"), "w").write(txt + "\n"); print(txt)
    # contact sheet of the closest pairs
    try:
        rows = [(r["a"], new[r["a"]]["file"], r["b"], new[r["b"]]["file"], r["D"]) for r in rep["within"][:4]]
        allref = {f"{f['set']}/{m}": f for s in refs.values() for m, f in s.items()}
        rows += [(r["piece"], new[r["piece"]]["file"], r["nearest"], allref[r["nearest"]]["file"], r["D"]) for r in rep["echo"][:4]]
        S = 300; cv = Image.new("RGB", (S * 2 + 20, S * len(rows)), "white")
        for k, (_, fa, _, fb, D) in enumerate(rows):
            for c, f in enumerate((fa, fb)):
                im = Image.open(f).convert("RGB"); im.thumbnail((S, S)); cv.paste(im, (c * (S + 20), k * S))
        cv.save(os.path.join(a.out, "pairs.jpg"), quality=85)
    except Exception as e:
        print("pairs sheet:", e, file=sys.stderr)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
