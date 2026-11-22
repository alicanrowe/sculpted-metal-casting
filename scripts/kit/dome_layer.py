"""bx_dome_ring rebuilt with the insert-and-layer pipeline (layer.py).

Same idea as the Bombyx dome ring (Hagia Sophia: a dome of turning ribs rising to a crown stone), rebuilt the
way the reel's maker works: a heavy domed blank, one carved element (the crescent) placed a few hundred times
in three depths, a stippled ground between, one polished moulding, one exact union.
The ribs become seven wind gusts (the carved capitals inside Hagia Sophia are wind-blown acanthus, drilled so
the ground reads black), all turning the same way round the stone; the shoulders carry the wind on down the band.

usage: python dome_layer.py <outdir>     -> <outdir>/bx_dome_ring_L.stl + .json + .npz (exact union, ~6 min)
then:  python finish.py <outdir>/bx_dome_ring_L.npz <outdir>/bx_dome_ring   (remesh and close pinholes, ~10 min)
check: python clipcheck.py <outdir>/bx_dome_ring.npz; python thick.py ...npz; python thin_class.py ...npz;
       ../check_settings.py <outdir>/bx_dome_ring.stl <outdir>/bx_dome_ring.json
render: SHARP=180 FSTOP=0.25 PRES=1200 PSPP=64 python render_mesh.py <outdir>/bx_dome_ring.stl <outdir>/bx_dome_ring.json <prefix> 01
"""
import math, os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layer as Ly
import manifold3d as mf

NAME = "bx_dome_ring_L"
D_STONE = 5.5
GUSTS = 7


def build(seed=241):
    rng = np.random.default_rng(seed)
    B = Ly.RingBlank(Ri=8.45, band_w=4.2, band_t=1.8, Rh=7.6, drum=1.2, H=3.0, rim=(0.30, 0.22), edge_lo=0.18)
    t0 = time.time()
    V, F, _ = B.mesh(nth=1600, ns=260)
    rim_r = B.Rh * 0.8
    R = D_STONE / 2
    rb = R + 0.7                                                      # bezel outer radius

    def field(a, x):
        a = np.asarray(a, float); x = np.asarray(x, float)
        hw = B.arc_hw(a / B.Ri)
        rho = np.sqrt(a ** 2 + B.axial(a, x) ** 2)
        keep_rim = np.abs(rho - rim_r) > 0.38                         # the moulding stays clear and polished
        return (np.abs(x) < hw * 0.87) & keep_rim & (rho > rb - 0.15) & (np.abs(a) < math.pi * B.Ri - 0.4)

    def edges_ok(spp, W):
        """The whole footprint (both edges, not just the spine) must sit on the field, or the part of it that
        hangs past the head's edge gets squashed onto the edge and stands up as a tab."""
        t = np.gradient(spp, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
        n = np.column_stack([-t[:, 1], t[:, 0]]) * W * 0.7
        for e in (spp + n, spp - n):
            if not np.all(field(e[:, 0], e[:, 1])):
                return False
        return True

    def gmask(a, x):
        rho = np.sqrt(a ** 2 + B.axial(a, x) ** 2)
        return np.clip((np.abs(rho - rim_r) - 0.4) / 0.15, 0, 1) * np.clip((rho - rb) / 0.2, 0, 1)
    V = Ly.stipple(B, V, gmask, pitch=0.13, depth=0.05, rad=0.075, seed=seed)
    parts = [(V, F)]
    P = Ly.Packer(field)
    Vg, Fg, _ = B.mesh(nth=700, ns=140); G = Ly.Gate(Vg, Fg)     # exact contact check (see Ly.Gate)
    n_in = [0]

    def put(L, a0, x0, rot, mirror=False, force=False, H=None, W=None, **kw):
        W = W or L * 0.23
        H = H or W * 0.8
        kw.setdefault("crest", 0.08); kw.setdefault("peak", 0.3); kw.setdefault("sink", 0.3)
        v, f, sp = Ly.crescent(L, W, H, **kw)
        k = float(B.stretch(a0, x0))
        spp = Ly.spine_plan(sp, a0, x0, rot, mirror, k)
        if not force and not edges_ok(spp, W):
            return False
        if force:   # designed placements skip the field and spacing rules, but never make a near-miss
            if not P.fits(spp[::2], W * 0.33, overlap=1.0, rw=sp[::2, 3], field=False):
                return False
        elif not P.fits(spp[::2], W * 0.33, rw=sp[::2, 3]):
            return False
        if not force and P.under > 0:          # it crosses an earlier stroke: ride over it, the layering the reel has
            kw["lift"] = 0.55 * P.under; kw["sink"] = kw["sink"] + 0.2
            v, f, sp = Ly.crescent(L, W, H, **kw)
        Vp = Ly.place(B, v, a0, x0, rot, mirror=mirror, k=k)
        it = G.ok(Vp, f)                          # must reach the blank and make no tunnel with it (pairs: finish.py)
        if it is None:
            return False
        G.add(it)
        P.add(spp[::2], W * 0.33, H + kw.get("lift", 0.0), rw=sp[::2, 3])
        parts.append((Vp, f))
        n_in[0] += 1
        return True

    q0 = rng.uniform(0, 2 * math.pi)

    # ---- focal: a corolla of rays round the bezel foot, all leaning with the wind
    for i in range(24):
        q = q0 + i * 2 * math.pi / 24
        r = rb - 0.5
        L = 2.4 if i % 2 == 0 else 1.7
        Wc = L * 0.3
        for dq in (0, 0.06, -0.06, 0.12, -0.12):
          if put(L, r * math.sin(q), r * math.cos(q), math.atan2(math.cos(q), math.sin(q)) + 0.4 + dq, force=True,
            bend=0.8, curl=0.3, W=Wc, H=0.8 if i % 2 == 0 else 0.62, tip_lift=0.0):
            break

    # ---- tier 1: seven gusts (the dome's ribs): each one long sweeping crescent that runs round the stone and
    # hooks inward at its tail, with a shorter one riding in its curve. They set the turn every other stroke follows.
    for i in range(GUSTS):
        q = q0 + 0.15 + i * 2 * math.pi / GUSTS
        for (r, L, W, H) in ((rb + 0.95, 6.0, 1.25, 1.05), (rb + 0.3, 3.0, 0.85, 0.75)):
            a0, x0 = r * math.sin(q), r * math.cos(q)
            hd = math.atan2(math.cos(q), math.sin(q)) + math.pi / 2 - 0.3
            put(L, a0, x0, hd, W=W, H=H, force=True, bend=L / r * 1.0, curl=0.7, groove=0.0, tip_lift=0.0, peak=0.25, nu=200, nv=31)

    # ---- tiers 2 and 3: fill along the wind. In the dome the flow swirls out round the stone; on the band it
    # runs away from the head with a slow meander, mirrored across the band's centre line and front to back.
    def flow(a, x):
        rho = math.hypot(a, float(B.axial(a, x)))
        if rho < rim_r:
            q = math.atan2(a, x)
            return math.atan2(math.cos(q), math.sin(q)) + 0.95
        if rho < B.Rh + 1.2:                 # round the head's flank: along the rim
            q = math.atan2(a, x)
            return math.atan2(math.cos(q), math.sin(q)) - math.pi / 2 + 0.25
        sgn = 1 if a > 0 else -1
        return (0.0 if sgn > 0 else math.pi) + sgn * 0.5 * math.sin(a * 0.45) * (1 if x >= 0 else -1)

    def size(a, x):
        rho = math.hypot(a, float(B.axial(a, x)))
        if rho < rim_r:
            return 2.9
        return max(1.5, 3.8 * math.exp(-(rho - rim_r) / 14.0))

    for scale, n in ((0.7, 3000), (0.45, 3000)):      # big swirls, then smaller fill, then tiny
      for _ in range(n):
        r = rng.uniform(rb + 0.05, rim_r - 0.45); q = rng.uniform(0, 2 * math.pi)
        a, x = r * math.sin(q), r * math.cos(q)
        L = size(a, x) * scale * rng.uniform(0.8, 1.15)
        put(L, a, x, flow(a, x) + rng.uniform(-0.15, 0.15), bend=1.9, curl=1.3, groove=0.0,
            gw=0.16, tip_lift=0.0)
    nf = [0]
    # the head's flank, between the rim moulding and the head's edge: small strokes running round the rim
    for _ in range(3000):
        q = rng.uniform(0, 2 * math.pi)
        a = (rim_r + 0.6) * math.sin(q)
        x0 = float(B.arc_of(a, (rim_r + 0.45) * math.cos(q))); x1 = float(B.arc_hw(a / B.Ri)) * 0.86 * np.sign(math.cos(q))
        x = rng.uniform(min(x0, x1), max(x0, x1))            # anywhere from the moulding down to the head's edge, in arc
        nf[0] += put(rng.uniform(0.9, 2.4), a, x, math.atan2(math.cos(q), math.sin(q)) + math.pi / 2 + rng.uniform(-0.5, 0.6), bend=1.6, curl=1.0,
            tip_lift=0.0)
    print('flank strokes', nf[0], flush=True)

    # ---- shank tier 1: big S-sweeps down each shoulder (a long crescent with a reversed hook), mirrored four ways
    big = []
    for (a, xf, L, rot) in ((rim_r + 2.2, 0.45, 6.5, 0.35), (rim_r + 7.2, 0.35, 5.4, -0.3), (rim_r + 11.8, 0.2, 4.2, 0.25)):
        hw = float(B.arc_hw(a / B.Ri)); x = xf * hw
        big.append((a, x, L, rot))
    for (a, x, L, rot) in big:
        W = L * 0.21
        kk = float(B.stretch(a, x))
        v, f, sp = Ly.crescent(L, W, W * 0.85, bend=1.5, curl=-1.6, groove=0.0, nu=200, nv=31, tip_lift=0.0, peak=0.3,
                               crest=0.08, sink=0.3)
        for dq in (0.0, 0.05, -0.05, 0.1, -0.1, 0.15, -0.15):     # nudge the whole mirrored set until the gate passes
            set_ = []
            for sa in (1, -1):
                for sx in (1, -1):
                    ang = rot + dq if sa > 0 else math.pi - rot - dq
                    ang = ang if sx > 0 else -ang
                    mir = (sa * sx) < 0
                    spp = Ly.spine_plan(sp, sa * a, sx * x, ang, mir, kk)
                    Vp = Ly.place(B, v, sa * a, sx * x, ang, mirror=mir, k=kk)
                    it = G.ok(Vp, f, extra=[s_[2] for s_ in set_], pairs=False)
                    if it is None:
                        set_ = None; break
                    set_.append((spp, Vp, it))
                if set_ is None:
                    break
            if set_:
                break
        else:
            print("  big sweep at a=%.1f refused by the gate at every nudge" % a, flush=True); continue
        if not set_:
            print("  big sweep at a=%.1f refused by the gate at every nudge" % a, flush=True); continue
        for spp, Vp, it in set_:
            G.add(it); P.add(spp[::2], W * 0.42, W, rw=sp[::2, 3])
            parts.append((Vp, f)); n_in[0] += 1
    for it in range(12000):
        scale = 1.0 if it < 4000 else (0.7 if it < 8000 else 0.5)
        a = rng.uniform(0.0, math.pi * B.Ri - 0.6)
        hw = float(B.arc_hw(a / B.Ri))
        x = rng.uniform(0.15, hw * 0.88)
        if math.hypot(a, float(B.axial(a, x))) < rim_r + 0.45:
            continue
        L = size(a, x) * scale * rng.uniform(0.8, 1.1)
        rot = flow(a, x) + rng.uniform(-0.12, 0.12)
        W = L * 0.23
        v, f, sp = Ly.crescent(L, W, W * 0.8, bend=1.8, curl=1.2, groove=0.0, gw=0.16,
                               tip_lift=0.0, crest=0.08, peak=0.3, sink=0.3)
        kk = float(B.stretch(a, x))
        cands = []
        for sa in (1, -1):              # mirror front/back and across the centre line; each mirror flips the curl
            for sx in (1, -1):
                ang = rot if sa > 0 else math.pi - rot
                ang = ang if sx > 0 else -ang
                mir = (sa * sx) < 0
                spp = Ly.spine_plan(sp, sa * a, sx * x, ang, mir, kk)
                if not edges_ok(spp, W) or not P.fits(spp[::2], W * 0.33, rw=sp[::2, 3]):
                    cands = None; break
                cands.append((sa * a, sx * x, ang, mir, spp))
            if cands is None:
                break
        if not cands:
            continue
        # the four mirror images must not near-miss each other either (a stroke near the centre line and its own
        # mirror image were the commonest pinhole)
        rw = sp[::2, 3]; bad = False
        for i in range(4):
            for j in range(i + 1, 4):
                g = (np.sqrt(((cands[i][4][::2, None, :] - cands[j][4][None, ::2, :]) ** 2).sum(-1)) - rw[:, None] - rw[None, :]).min()
                if -P.fuse < g < P.clear:
                    bad = True
        if bad:
            continue
        placed = []
        for (aa, xx, ang, mir, spp) in cands:
            Vp = Ly.place(B, v, aa, xx, ang, mirror=mir, k=kk)
            it = G.ok(Vp, f, extra=[p_[1] for p_ in placed])
            if it is None:
                placed = None; break
            placed.append((Vp, it, spp))
        if not placed:
            continue
        for Vp, it, spp in placed:
            G.add(it); P.add(spp[::2], W * 0.33, W * 0.8, rw=sp[::2, 3])
            parts.append((Vp, f)); n_in[0] += 1

    print("gate refused", G.refused, flush=True)
    print("inserts", n_in[0], "build", round(time.time() - t0, 1), "s", flush=True)
    M = Ly.union(parts)
    print("union", round(time.time() - t0, 1), "s, genus", M.genus(), flush=True)

    # ---- setting: a bezel (a signet takes a bezel): a 0.7 mm wall round the girdle with a ledge under it, the
    # lip leaning in over the crown, and a clear cone under the pavilion
    ztop = B.Ri + float(B.height(np.array(0.0), np.array(0.0)))
    zg = ztop - 0.15
    seg = 360
    M = M + mf.Manifold.cylinder(2.2, R + 0.85, R + 0.7, seg).translate([0, 0, zg - 1.65])
    print("with bezel wall, genus", M.genus(), flush=True)
    cut = Ly.bezel_cut(zg, R, seg)
    M = M - cut
    st = [dict(kind="whitetopaz", D=D_STONE, L=D_STONE, c=[0.0, 0.0, zg], n=[0.0, 0.0, 1.0], e1=[1.0, 0.0, 0.0],
               setting="bezel")]
    bodies = sorted(M.decompose(), key=lambda p: -p.volume())
    real = [p for p in bodies if abs(p.volume()) > 0.01]
    if len(real) < len(bodies):
        print("dropped", len(bodies) - len(real), "zero-volume slivers")
    M = mf.Manifold.batch_boolean(real, mf.OpType.Add) if len(real) > 1 else real[0]
    for p in real[1:]:
        b = p.bounding_box()
        print("  extra body", round(p.volume(), 4), "mm3 at", np.round((np.array(b[:3]) + np.array(b[3:])) / 2, 2))
    print("genus", M.genus(), "(a ring must be 1: more means pinhole tunnels under inserts)", flush=True)
    if M.genus() > 1:
        print("next: python3 finish.py <out>/bx_dome_ring_L.npz <out>/bx_dome_ring (voxel remesh, then seal)", flush=True)
    m = Ly.from_manifold(M)
    print("final", round(time.time() - t0, 1), "s", len(m.faces), "tris", flush=True)
    # ground mask for the renderer: vertices still on the stippled blank surface (not under an insert)
    Vm = np.asarray(m.vertices)
    th = np.arctan2(Vm[:, 0], Vm[:, 2]); rv = np.hypot(Vm[:, 0], Vm[:, 2])
    a = B.Ri * th; x = Vm[:, 1]
    s = np.clip(x / B.halfw(th), -1, 1)
    rb_ = np.linalg.norm(B.point(th, s)[:, [0, 2]], axis=1)
    g = (np.abs(rv - rb_) < 0.1) & (rv > B.Ri + 0.2)
    m.ground = (g * gmask(a, B.arc_of(a, x))).astype(np.float32)
    return m, st


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    m, st = build()
    parts = m.split(only_watertight=False)
    info = dict(name=NAME, watertight=bool(m.is_watertight), volume_cm3=round(abs(m.volume) / 1000, 3),
                sterling_g=round(abs(m.volume) / 1000 * 10.36, 1), size_mm=[round(float(x), 1) for x in m.extents],
                bodies=len(parts), stones=st)
    json.dump(info, open(os.path.join(out, NAME + ".json"), "w"), indent=1)
    m.export(os.path.join(out, NAME + ".stl"))
    np.savez_compressed(os.path.join(out, NAME + ".npz"), V=np.asarray(m.vertices, np.float32), F=np.asarray(m.faces, np.int32), ground=m.ground)
    print(info["sterling_g"], "g", info["size_mm"], "bodies", info["bodies"], "watertight", info["watertight"])
