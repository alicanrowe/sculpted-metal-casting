"""Eight versions of MB-SH-01 Rest, each weighting one influence hard (Nov 18).
  a CARVED  Moira        carved all over, stone clusters, melted drips
  b LIQUID  hyodomachine pure liquid chrome, swells to needles, curls, no carving
  c EDGE    Soderberg    knife-edge steel, leather and hardware do the talking
  d WASH    Gsongim      bone forms, washed/oxidised silver
  e STAGE   Komune       one oversized moth fills the frame
  f THREAD  Wen Jue Lu   fine wire, pale stones, quiet
  g THORN   tattoo flash barbs and thorns up every member
  h SWARM   many small moths on a liquid stretcher
python sawvar.py render <letter> [pass]   (renders through sawmoth.render with hooks)"""
import sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sawmoth as SM
from sawmoth import sdf, v2, wisp, W2, K, Mo, Flat, body, smoothstep, LX, CU_HW
from sdf import Scene

NAMES = dict(a="CARVED", b="LIQUID", c="EDGE", d="WASH", e="STAGE", f="THREAD", g="THORN", h="SWARM")
LEAD = dict(a="Moira", b="hyodomachine", c="Richard Söderberg", d="Gsongim", e="Komune", f="Wen Jue Lu", g="hyodomachine x Moira, flash",
            h="Moira x hyodomachine, multiplied")


# ------------------------------------------------------------------ parametric members
def leg(s, sx, S=0.9, w0=3.3, pinch=1.95, flare=1.3, t0=1.1, tpinch=0.35, grooves=12, gspan=(0.02, 0.2), gr=0.24,
        tendon=True, horns=True, horn_w=1.35, horn_grooves=10, horn_tip=0.42, knife=False, zt=67.5):
    x0 = sx * LX
    zs = np.linspace(2.0, zt, 40); u = (zs - zs[0]) / (zs[-1] - zs[0])
    xs = x0 - sx * S * np.sin(math.pi * u) + sx * 0.25 * S * np.sin(2 * math.pi * u)
    pts = np.column_stack([xs, np.zeros_like(zs), zs])
    if knife:
        hw = lambda t: w0 - (w0 - pinch) * t
        ht = lambda t: t0 + 0 * t
    else:
        hw = lambda t: w0 - pinch * np.sin(math.pi * np.clip(t / 0.85, 0, 1)) ** 1.1 + flare * smoothstep((t - 0.78) / 0.22)
        ht = lambda t: t0 - tpinch * np.sin(math.pi * np.clip(t / 0.85, 0, 1)) + 0.1 * smoothstep((t - 0.8) / 0.2)
    v2.blade(s, pts, hw, ht, normal=(1, 0, 0), k=0.8, grooves=grooves, both=True, gr=gr, barb=0.7, groove_span=gspan)
    if not knife:
        s.ellipsoid((x0, 0, 3.6), (1.5, 3.4, 1.6), k=1.6)
    if tendon:
        uu = u[3:-4]
        K.ribbon(s, np.column_stack([xs[3:-4] + sx * ht(uu) * 0.85, 1.1 * np.sin(2.3 * math.pi * uu + 0.6) * (0.4 + 0.6 * np.sin(math.pi * uu)), zs[3:-4]]),
                 w=0.6, thin=0.7, ends=(0.2, 0.3), wkeys=[(0, 0.6), (0.3, 1.3), (0.6, 0.8), (1, 1.1)], k=0.5)
    hps = []
    if horns:
        top = pts[-1]
        for sy in (1, -1):
            h = np.array([[0, zt - 3], [sy * 2.6, 68.6], [sy * 5.6, 71.2], [sy * 6.95, 74.2], [sy * 7.05, 77.2], [sy * 6.6, 79.0], [sy * 6.15, 79.6]])
            hp = sdf.catmull(np.column_stack([np.full(len(h), top[0]), h]), 10)
            v2.blade(s, hp, lambda t: horn_w * (1 - t) ** 0.9 + 0.12, lambda t: 0.7 * horn_w * (1 - t) ** 0.7 + 0.12, normal=(1, 0, 0), k=0.6,
                     grooves=horn_grooves, both=True, gr=0.16, barb=0.5, groove_span=(0.1, 0.6))
            if horn_tip: s.sphere(hp[-1], horn_tip, k=0.15)
            hps.append(hp)
    return pts, hw, ht, hps


def foot(s, sx, H=3.6, curl=4.6, reach=17.4, hw0=2.1, ht0=1.35, grooves=16, gspan=(0.2, 0.8), tip=0.4, knife=False):
    x0 = sx * LX
    yz = np.array([[-reach, curl], [-reach + 0.2, 2.0], [-15.2, 0.95], [-10, H * 0.47], [-4, H * 0.89], [0, H],
                   [4, H * 0.89], [10, H * 0.47], [15.2, 0.95], [reach - 0.2, 2.0], [reach, curl]])
    pts = sdf.catmull(np.column_stack([np.full(len(yz), x0), yz]), 10)
    if knife:
        hw = lambda t: 0.6 + hw0 * np.sin(math.pi * np.clip(t, 0, 1)) ** 0.4
        ht = lambda t: ht0 + 0 * t
    else:
        hw = lambda t: 0.15 + hw0 * np.sin(math.pi * np.clip(t, 0, 1)) ** 0.75
        ht = lambda t: 0.18 + ht0 * np.sin(math.pi * np.clip(t, 0, 1)) ** 0.5
    v2.blade(s, pts, hw, ht, normal=(1, 0, 0), k=0.8, grooves=grooves, both=True, gr=0.24, barb=0.7, groove_span=gspan)
    if tip:
        for e in (pts[0], pts[-1]): s.sphere(e, tip, k=0.15)
    for sy in (1, -1):
        s.ellipsoid((x0, sy * 15.0, 0.75), (1.0, 1.9, 0.75), k=0.6)
    return pts


def rail(s, sag=0.9, hook=1.0, grooves=0, ht0=1.28, tip=0.48):
    xz = [(-38.6, 71.6 - 8.4 * hook), (-39.2, 71.6 - 5.1 * hook), (-38.3, 69.8), (-36.2, 71.5), (-30, 71.6), (0, 71.6),
          (30, 71.6), (36.2, 71.5), (38.3, 69.8), (39.2, 71.6 - 5.1 * hook), (38.6, 71.6 - 8.4 * hook)]
    pts = sdf.catmull(np.array([(x, 0, z) for x, z in xz]), 10)
    e = 0.11
    hw = lambda t: 0.15 + 2.55 * smoothstep(np.minimum(t, 1 - t) / e) + sag * np.exp(-((t - 0.5) / 0.16) ** 2)
    ht = lambda t: 0.15 + ht0 * smoothstep(np.minimum(t, 1 - t) / e)
    v2.blade(s, pts, hw, ht, normal=(0, 1, 0), k=0.8, grooves=grooves, both=True, gr=0.24, barb=0.7, groove_span=(0.05, 0.95))
    # removable seat: a flat 2.86 cm working top at 74.3 (the original rail top); the cushion's slot slides over it
    s.prism((-34.0, 0, 71.0), (34.0, 0, 71.0), 1.43, 1.43, 0.0, 3.3, normal=(0, 0, 1), k=0.4)
    if tip:
        for p in (pts[0], pts[-1]): s.sphere(p, tip, k=0.15)
    return pts


def moth(s, st, rng, pal, cz=33.0, fspan=25.0, hspan=17.5, fang=0.26, hang=-0.4, size=26.0, wmul=1.7, fst=1, hst=0,
         back=True, connect=True, x=0.0):
    m = Flat(o=(x, 0, 0), u=(1, 0, 0), v=(0, 0, 1))
    wisp.WMUL[0] = wmul
    tips = []
    for sx in (1, -1):
        f = W2.vein_wing(s, m, st, (sx * size * 0.085, cz + 1.0), fspan, ang=fang, sx=sx, rng=rng, shape="moth_f", stones=fst, pal=pal, z=0.0)
        h = W2.vein_wing(s, m, st, (sx * size * 0.085, cz - 2.0), hspan, ang=hang, sx=sx, rng=rng, shape="moth_h", stones=hst, pal=pal[::-1], z=0.0)
        tips.append((sx, f["tip"], h["tip"]))
    wisp.WMUL[0] = 1.0
    body(s, m, st, (0, cz), size, pal, kind="butterfly", rng=rng)
    if back:
        D = size * 0.13
        s.ellipsoid((x, D * 0.3, cz + 0.5), (D * 0.55, D * 0.5, D * 0.6), k=0.6)
        Mo.prong(s, st, (x, D * 0.5, cz + 0.5), D * 0.9, pal[1 % len(pal)], normal=(0, 1, 0), n=4, wire=max(0.26, D * 0.08))
    if connect:
        for sx, ft, ht in tips:
            for t, w in ((ft, 1.0), (ht, 0.85)):
                t = np.asarray(t, float) + [x, 0]
                xl = sx * (LX - 1.0)
                if abs(t[0]) > abs(xl): continue
                a = np.array([t[0], 0.0, t[1]]); b = np.array([xl + sx * 0.6, 0.0, t[1] + 0.6])
                K.ribbon(s, np.array([a, (a + b) / 2 + [0, 0, 0.8], b]), w=w, thin=0.75, ends=(0.0, 0.0),
                         wkeys=[(0, 0.7), (0.5, 0.85), (1, 1.4)], k=0.5)
    return tips


def buckle(s, rng, x0, a=2.3, b=1.8, r0=0.32, plain=False):
    y0 = -(CU_HW + 0.55); z0 = 75.4
    th = np.linspace(0, 2 * math.pi, 49); e = 0.25 if plain else 0.6
    ring = np.column_stack([x0 + a * np.sign(np.cos(th)) * np.abs(np.cos(th)) ** e, np.full_like(th, y0),
                            z0 + b * np.sign(np.sin(th)) * np.abs(np.sin(th)) ** e])
    r = np.full(len(th), r0) if plain else r0 + 0.5 * r0 * (0.5 + 0.5 * np.cos(2 * th + rng.uniform(0, 1)))
    s.stroke(ring, r, k=0.12, normals=np.tile([0, 1, 0], (len(th), 1)), flat=3.0 if plain else 1.4)
    sx = 1 if x0 >= 0 else -1
    if plain:
        s.cone((x0, y0, z0 - b), (x0, y0, z0 + b), r0 * 0.8, r0 * 0.8, k=0.1, flat=2.0, zhint=(0, 1, 0))
        s.cone((x0, y0 - 0.2, z0), (x0 + sx * (a + 0.2), y0 - 0.3, z0), 0.2, 0.2, k=0.1)
    else:
        tong = np.array([(x0 - sx * 0.2, y0 - 0.15, z0), (x0 + sx * 0.8, y0 - 0.35, z0 + 0.1), (x0 + sx * (a + 0.7), y0 - 0.25, z0 + 0.25)])
        K.ribbon(s, tong, w=0.28, thin=0.8, ends=(0.0, 0.6), k=0.15)
        s.sphere(tong[-1], 0.2, k=0.1)


def yz_flat(x):
    return Flat(o=(x, 0, 0), u=(0, 1, 0), v=(0, 0, 1))


def thorn(s, p, d, L, r):
    d = np.asarray(d, float); d /= np.linalg.norm(d); p = np.asarray(p, float)
    s.cone(p - d * r, p + d * L, r, 0.06, k=0.4)


# ------------------------------------------------------------------ the eight
def v_a(rng, st):   # CARVED (Moira)
    s = Scene(); pal = ["garnet", "amethyst", "citrine"]
    for sx in (1, -1):
        foot(s, sx, grooves=36, gspan=(0.06, 0.94))
        pts, hw, ht, _ = leg(s, sx, grooves=60, gspan=(0.02, 0.95), gr=0.3, horn_grooves=18)
        # a cluster of claw-set stones on the outer face of each leg head, the way Moira stacks stones
        for i, (dz, dy, D) in enumerate(((58.5, 0.0, 3.5), (55.2, 1.2, 2.5), (55.0, -1.3, 2.0), (61.6, -0.9, 2.0))):
            xo = sx * (LX + 1.2 + 0.3 * D)
            s.ellipsoid((sx * (LX + 0.8), dy, dz), (0.9, D * 0.55, D * 0.55), k=0.6)
            Mo.prong(s, st, (xo, dy, dz), D, pal[i % 3], normal=(sx, 0, 0), n=4, wire=0.3)
    rail(s, sag=1.1, grooves=70)
    # melted drips running off the underside of the rail
    for x, L in ((-22, 2.6), (-9, 1.6), (4, 3.2), (17, 2.0)):
        z = 69.6 - 1.1 * math.exp(-((x / 80 + 0.0) / 0.16) ** 2)
        s.ellipsoid((x, 0, z - L * 0.5), (0.55, 0.55, L * 0.6), k=0.9)
        s.sphere((x, 0, z - L * 1.05), 0.6, k=0.5)
    moth(s, st, rng, pal, wmul=2.1, fst=2, hst=1)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0) for sx in (1, -1)]
    return s, s2


def v_b(rng, st):   # LIQUID (hyodomachine)
    s = Scene(); pal = ["londonblue", "aquamarine"]
    for sx in (1, -1):
        fp = foot(s, sx, H=4.4, curl=8.0, reach=19.5, hw0=1.7, ht0=1.1, grooves=0, tip=0.5)
        pts, hw, ht, hps = leg(s, sx, S=2.2, w0=3.8, pinch=2.9, flare=1.9, t0=1.25, tpinch=0.6, grooves=0, tendon=False, horn_grooves=0)
        # two liquid strands spiral up each leg and leave it as hairline curls under the seat
        zs = pts[:, 2]; u = (zs - zs[0]) / (zs[-1] - zs[0])
        for ph in (0.0, math.pi):
            ang = ph + 2.4 * math.pi * u
            rr = (hw(u) * 0.55 + 0.5)
            P = np.column_stack([pts[:, 0] + sx * 0 + np.cos(ang) * (ht(u) + 0.35), np.sin(ang) * rr, zs])
            K.ribbon(s, P[2:-2], w=0.55, thin=0.8, ends=(0.25, 0.1), wkeys=[(0, 0.5), (0.4, 1.3), (0.8, 0.7), (1, 1.0)], k=0.6)
        for hp in hps:
            sy = 1 if hp[-1][1] > 0 else -1
            wisp.wisp(s, yz_flat(hp[-1][0]), hp[-1][1:], np.array([-sy * 0.6, -0.4]), 6.0, w=0.45, z=0.0, curl=sy * 3.2, rng=rng)
        for e in (fp[0], fp[-1]):
            sy = 1 if e[1] > 0 else -1
            wisp.wisp(s, yz_flat(e[0]), e[1:], np.array([-sy * 0.3, 1.0]), 7.0, w=0.45, z=0.0, curl=sy * 2.8, rng=rng)
    rp = rail(s, sag=2.0, hook=1.5)
    for e in (rp[0], rp[-1]):
        sg = 1 if e[0] > 0 else -1
        wisp.wisp(s, Flat(o=(0, 0, 0), u=(1, 0, 0), v=(0, 0, 1)), np.array([e[0], e[2]]), np.array([-sg * 0.5, -1.0]), 9.0, w=0.5, z=0.0,
                  curl=sg * 3.0, rng=rng)
    moth(s, st, rng, pal, wmul=1.3, fst=0, hst=0, back=False)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0, r0=0.42) for sx in (1, -1)]
    return s, s2


def v_c(rng, st):   # EDGE (Soderberg)
    s = Scene(); pal = ["moonstone"]
    for sx in (1, -1):
        foot(s, sx, H=2.4, curl=1.0, reach=16.5, hw0=1.3, ht0=0.55, grooves=0, tip=0, knife=True)
        leg(s, sx, S=0.0, w0=3.4, pinch=2.4, t0=0.55, grooves=0, tendon=False, horns=False, knife=True, zt=70.0)
    rail(s, sag=0.0, hook=0.35, ht0=1.0, tip=0)
    moth(s, st, rng, pal, cz=34.0, fspan=16.0, hspan=11.0, size=15.0, wmul=1.0, fst=0, hst=0, back=False)
    s2 = Scene()
    for sx in (1, -1):
        for xc in (12.0, 28.0): buckle(s2, rng, sx * xc, a=2.6, b=2.2, r0=0.3, plain=True)
    return s, s2


def v_d(rng, st):   # WASH (Gsongim): bone
    s = Scene(); pal = ["labradorite", "moonstone"]
    for sx in (1, -1):
        fp = foot(s, sx, H=4.0, curl=2.2, reach=16.8, hw0=2.4, ht0=1.7, grooves=0, tip=0)
        for e in (fp[0], fp[-1]):
            for dz in (-0.6, 0.6): s.sphere(e + [0, 0, dz], 1.25, k=0.8)          # condyles
        pts, hw, ht, _ = leg(s, sx, S=0.5, w0=2.4, pinch=0.9, flare=0.6, t0=1.6, tpinch=0.4, grooves=0, tendon=False, horns=False, zt=68.5)
        for zz, rr in ((5.5, 2.3), (66.0, 2.2)):
            for dy in (-1.4, 1.4): s.sphere((pts[0][0] if zz < 10 else pts[-1][0], dy, zz), rr, k=1.2)
        # a rib cage of three short bones cradling the leather instead of horns
        for sy in (1, -1):
            for i, zz in enumerate((70.5, 73.5, 76.5)):
                P = sdf.catmull(np.array([[pts[-1][0] + sx * 0.0, sy * (2 + i * 0.5), zz - 3.5], [pts[-1][0], sy * 6.6, zz],
                                           [pts[-1][0], sy * 6.3, zz + 2.6]]), 8)
                s.stroke(P, np.linspace(0.85, 0.55, len(P)), k=0.6)
                s.sphere(P[-1], 0.75, k=0.4)
    rp = rail(s, sag=0.6, hook=0.6, tip=0)
    for e in (rp[0], rp[-1]): s.sphere(e, 1.3, k=0.8)
    moth(s, st, rng, pal, wmul=2.6, fst=0, hst=0)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0, r0=0.4) for sx in (1, -1)]
    return s, s2


def v_e(rng, st):   # STAGE (Komune): the moth is the whole frame
    s = Scene(); pal = ["moonstone", "aquamarine", "amethyst"]
    for sx in (1, -1):
        foot(s, sx, grooves=0)
        leg(s, sx, S=0.6, grooves=0, tendon=False, horn_grooves=0)
    rail(s, sag=1.2)
    moth(s, st, rng, pal, cz=40.0, fspan=36.0, hspan=31.0, fang=0.55, hang=-0.75, size=40.0, wmul=2.3, fst=2, hst=1)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0) for sx in (1, -1)]
    return s, s2


def v_f(rng, st):   # THREAD (Wen Jue Lu): fine wire
    s = Scene(); pal = ["moonstone", "aquamarine"]
    for sx in (1, -1):
        fp = foot(s, sx, H=3.0, curl=3.6, hw0=0.9, ht0=0.6, grooves=0, tip=0.3)
        x0 = sx * LX
        zs = np.linspace(2.5, 70.5, 60); u = (zs - zs[0]) / (zs[-1] - zs[0])
        for ph in (0.0, math.pi):     # two fine wires twisting round each other
            ang = ph + 3.0 * math.pi * u
            P = np.column_stack([x0 + 0.9 * np.cos(ang), 1.1 * np.sin(ang) + 0 * u, zs])
            s.stroke(P, np.full(len(P), 0.55), k=0.3)
        for zz in (20.0, 45.0): s.sphere((x0, 0, zz), 1.0, k=0.4)       # small knots
        for sy in (1, -1):
            h = np.array([[x0, 0, 69.5], [x0, sy * 4.0, 71.0], [x0, sy * 6.5, 73.5], [x0, sy * 6.8, 77.0], [x0, sy * 6.2, 79.2]])
            P = sdf.catmull(h, 10); s.stroke(P, np.linspace(0.5, 0.22, len(P)), k=0.3); s.sphere(P[-1], 0.3, k=0.1)
    rail(s, sag=0.0, hook=0.8, ht0=0.9, tip=0.3)
    moth(s, st, rng, pal, cz=34.0, fspan=17.0, hspan=12.0, size=16.0, wmul=0.9, fst=1, hst=0, back=False)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0, a=1.6, b=1.3, r0=0.22) for sx in (1, -1)]
    return s, s2


def v_g(rng, st):   # THORN
    s = Scene(); pal = ["garnet", "garnet", "amethyst"]
    for sx in (1, -1):
        fp = foot(s, sx, grooves=10)
        pts, hw, ht, hps = leg(s, sx, grooves=14, horn_grooves=8)
        zs = pts[:, 2]; u = (zs - zs[0]) / (zs[-1] - zs[0])
        for i in range(4, len(pts) - 3, 3):        # barbs off both edges, raking upward, alternating
            for sy in (1, -1):
                if (i // 3 + (sy > 0)) % 2: continue
                p = pts[i] + [0, sy * hw(u[i]) * 0.85, 0]
                thorn(s, p, (sx * 0.15, sy * 1.0, 0.9), 2.4 + rng.uniform(0, 1.6), 0.45)
        for j in range(8, len(fp) - 8, 9):
            thorn(s, fp[j], (0, 0.3 * (1 if fp[j][1] > 0 else -1), 1.0), 2.0, 0.42)
    rp = rail(s, sag=0.9, grooves=20)
    # barbed wire: a coil round the exposed rail with a barb at every turn
    xs = np.linspace(-33, 33, 600); ang = xs / 66 * 2 * math.pi * 11
    P = np.column_stack([xs, 1.95 * np.cos(ang), 69.6 + 1.6 * np.sin(ang)])
    keep = P[:, 2] < 71.6
    s.stroke(P[keep][::2], np.full(int(keep.sum() + 1) // 2, 0.32), k=0.2)
    for x in np.linspace(-31, 31, 12):
        thorn(s, (x, -2.1, 68.6), (0.3, -0.6, -1.0), 1.4, 0.3)
    moth(s, st, rng, pal, wmul=1.8, fst=1, hst=1)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0) for sx in (1, -1)]
    return s, s2


def v_h(rng, st):   # SWARM
    s = Scene(); pal = ["amethyst", "londonblue", "citrine", "aquamarine"]
    for sx in (1, -1):
        foot(s, sx)
        leg(s, sx)
    rail(s)
    # a liquid stretcher: one swelling stroke from leg to leg with a slow wave
    xs = np.linspace(-LX + 0.5, LX - 0.5, 50)
    P = np.column_stack([xs, np.zeros_like(xs), 30 + 2.2 * np.sin(xs / LX * math.pi * 1.5)])
    K.ribbon(s, P, w=1.1, thin=0.7, ends=(0, 0), wkeys=[(0, 1.6), (0.25, 0.7), (0.5, 1.1), (0.75, 0.7), (1, 1.6)], k=0.7)
    for i, (x, dz, sz, ang) in enumerate(((-17, 4, 11, 0.2), (-4, -3.5, 9, -0.3), (9, 3.0, 12, 0.15), (21, -2.5, 8, -0.1))):
        z = 30 + 2.2 * math.sin(x / LX * math.pi * 1.5) + dz
        moth(s, st, rng, pal[i:] + pal[:i], cz=z, fspan=sz, hspan=sz * 0.7, fang=0.26 + ang, size=sz * 0.9, wmul=1.0,
             fst=1 if sz > 10 else 0, back=False, connect=False, x=x)
        zz = 30 + 2.2 * math.sin(x / LX * math.pi * 1.5)
        K.ribbon(s, np.array([[x, 0, zz], [x, 0, z - sz * 0.3]]), w=0.45, thin=0.8, ends=(0, 0), k=0.5)
    # two more climbing the legs
    for sx, z in ((1, 50.0), (-1, 14.0)):
        m = Flat(o=(sx * (LX + 1.6), 0, 0), u=(0, 1, 0), v=(0, 0, 1))
        wisp.WMUL[0] = 1.0
        for sy in (1, -1):
            W2.vein_wing(s, m, st, (sy * 0.8, z), 8.0, ang=0.5, sx=sy, rng=rng, shape="moth_f", stones=0, pal=pal, z=0.0)
            W2.vein_wing(s, m, st, (sy * 0.8, z - 1.2), 6.0, ang=-0.3, sx=sy, rng=rng, shape="moth_h", stones=0, pal=pal, z=0.0)
        body(s, m, st, (0, z), 8.0, pal, kind="butterfly", rng=rng)
    s2 = Scene(); [buckle(s2, rng, sx * 20.0) for sx in (1, -1)]
    return s, s2


VARS = dict(a=v_a, b=v_b, c=v_c, d=v_d, e=v_e, f=v_f, g=v_g, h=v_h)
LEATHER = dict(c=dict(straps=((12.0, 3.6), (28.0, 3.6)), strap_sc=1.04), f=dict(straps=((20.0, 1.2),), strap_sc=1.02))
FINISH = dict(c="steel", d="oxidised")


def setup(letter, seed=11):
    def metal(ver):
        rng = np.random.default_rng(seed); st = []
        with wisp.organic():
            s, s2 = VARS[letter](rng, st)
        return s, st, s2
    SM.HOOK.update(metal=metal, leather=lambda: SM.build_leather(**LEATHER.get(letter, {})), finish=FINISH.get(letter, "polished"))


if __name__ == "__main__":
    L = sys.argv[2]; tag = sys.argv[3] if len(sys.argv) > 3 else "p1"
    setup(L)
    if sys.argv[1] == "mesh":
        s, st, s2 = SM.HOOK["metal"]("x"); print(L, len(s.array()), "prims", len(st), "stones")
    else:
        SM.render(f"{L}_{tag}")
