"""GOVERNOR r3: men's jewelry from the oil computer. Real chain and plain bands, hand-forged and distressed, each
broken by one machined part from the gearbox (a spool, a drilled plate, a ring gear), with one small ruby where
the steel check ball sits. Nothing melted, nothing sculpted. Units mm; the table is z = 0 for chains."""
import math
import numpy as np
import mlib
from mlib import M, CS, Piece, cyl, lathe, knurl, extrude, rotx, roty, rotz, place, box
import manifold3d as m3
from chains import oval_link, lay, place_m, frame
from pieces_r2 import spool, orient_at, ruby_cup, FINGER
from pieces_r1 import gerotor2

PIECES = {}


def reg(name):
    def d(fn):
        PIECES[name] = fn; return fn
    return d


def get(name):
    return PIECES[name]()


def flush_seat(D):
    """a ruby ball set flush in a surface (top face at z=0, normal +Z): a drilled seat with a 90 deg floor and a
    swaged lip at 0.86 of the ball's radius, so the ball shows a little under half and cannot fall out.
    Returns (cavity to cut, ball centre z)."""
    rb = D / 2
    rl = 0.86 * rb
    zc = -math.sqrt(rb * rb - rl * rl) - 0.03
    zf = zc - rb * math.sin(math.radians(45))
    zb = zc - rb - 0.035
    prof = [(0, zb - 0.4), (0.3, zb - 0.4)]
    prof += [((rb + 0.035) * math.cos(a), zc + (rb + 0.035) * math.sin(a)) for a in np.radians(np.linspace(-72, 0, 7))]
    prof += [(math.sqrt(max(rb ** 2 - (z - zc) ** 2, 0)) + 0.035, z) for z in np.linspace(zc + 0.15, -0.02, 6)]
    prof += [(rl, 0.0), (rl, 1.5), (0, 1.5)]
    return lathe(prof), zc


def ring_link(Di, d):
    """a round jump ring / eye: inner diameter Di, wire d"""
    return oval_link(Di, Di, d)


def bolt_clasp(Di=3.6, d=1.0):
    """a spring-ring clasp: a round tube ring with its gate cut and a small thumb tab"""
    r = ring_link(Di, d)
    R = Di / 2 + d / 2
    r = r - box(0.18, d * 2, d).translate((R, 0, d * 0.5 + 0.2))                             # the gate line
    return r


def chain_parts(pc, slots, placed, finish="forged"):
    for i, (sl, (R, p, s, t)) in enumerate(zip(slots, placed)):
        if sl.get("solid") is None:
            continue
        pc.add(sl.get("label", "link%02d" % i), place_m(sl["solid"], R, p), sl.get("finish", finish))


CABLE = dict(Li=4.4, Wi=2.8, d=1.0)


def cable_slot(Li=4.4, Wi=2.8, d=1.0, cut=None, flat=1.0, square=False, **kw):
    lk = oval_link(Li, Wi, d, flat=flat, cut=(0.36 * d if cut is None else cut) or None, square=square)
    return dict(Li=Li, h=Wi / 2 + d, d=d, solid=lk, **kw)


def bar_slot(bar, half_len, eye_Di, eye_d, nb_Li, slack=0.88, lean=-45.0, label="bar", finish="forged"):
    """a straight part in the chain: `bar` lies along local X from -half_len to +half_len, with a round eye at each
    end; returns a slot whose spacing puts the neighbouring links through the eyes"""
    xe = half_len + eye_Di / 2 + eye_d * 0.15
    eye = oval_link(eye_Di, eye_Di, eye_d)
    solid = bar + eye.translate((xe, 0, 0)) + eye.translate((-xe, 0, 0))
    pe = slack * (eye_Di + nb_Li) / 2
    Li = 2 * (xe + pe) / slack - nb_Li
    return dict(Li=Li, h=max(eye_Di / 2 + eye_d, 2.0), d=eye_d, solid=solid, lean=lean, label=label, finish=finish)


def up_in_slot(lean):
    """the local direction that ends up pointing straight up once a slot leans by `lean`"""
    s, c = math.sin(math.radians(lean)), math.cos(math.radians(lean))
    return np.array([0.0, s, c])


# ------------------------------------------------------------------ 05 SHIFT VALVE bar bracelet
@reg("gv_shiftvalve_bracelet")
def shiftvalve_bracelet():
    """The comparator. A plain distressed cable chain broken by one bar: the shift valve's spool, an inch long,
    turned with its three lands and two grooves, and a ruby set flush in the end land where the governor's oil
    pushes."""
    pc = Piece("gv_shiftvalve_bracelet", "flat")
    r = 1.7
    sp, L = spool(r, [(5.2, 2.6), (6.4, 2.6), (5.2, 0)], stem=1.05, c=0.25)
    cap = lambda z0, sg: lathe([(0, 0), (r - 0.25, 0), (r, 0.25 * sg), (r, 0.9 * sg), (0, 0.9 * sg)] if sg > 0 else
                               [(0, 0.9 * sg), (r, 0.9 * sg), (r, 0.25 * sg), (r - 0.25, 0), (0, 0)]).translate((0, 0, z0))
    bar = sp.translate((0, 0, -L / 2))
    bar = place(bar, roty(90))
    lean = 45.0
    v = up_in_slot(lean)
    cav, zc = flush_seat(1.5)
    xr = -L / 2 + 2.6
    bar = bar - orient_at(cav, np.array([xr, 0, 0]) + r * v, v)
    links = [cable_slot(**CABLE) for _ in range(44)]
    clasp = dict(Li=3.6, h=2.3, d=1.0, solid=bolt_clasp(3.6, 1.0), label="clasp")
    slots = [bar_slot(bar, L / 2, 2.2, 0.95, CABLE["Li"], lean=lean)] + links[:22] + [clasp] + links[22:]
    loop, placed = lay(slots, e=3.4)
    chain_parts(pc, slots, placed)
    Rb, pb, _, _ = placed[0]
    pc.ball(tuple(pb + Rb @ (np.array([xr, 0, 0]) + (r + zc) * v)), 1.5, "ruby")
    pc.notes["views"] = [(0.0, -1.0, 1.1), (0.0, -0.02, 1.0), (1.0, -0.3, 0.35), (0.25, -1.0, 0.2)]
    pc.notes["length"] = "about 19 cm"
    return pc


def eye(Di, d, lean):
    """a round eye leaning `lean` degrees about the chain line (local X)"""
    return oval_link(Di, Di, d).rotate((lean, 0, 0))


def lean_of(i, lean=45.0):
    return lean if i % 2 == 0 else -lean


def sweep_convex(P, U, V, sec):
    """sweep a convex 2D section `sec` [(u, v), ...] along polyline P with frames (U, V): exact hulls per segment"""
    rings = [np.array([p + u * a + v * b for a, b in sec]) for p, u, v in zip(P, U, V)]
    hulls = [M.hull_points(np.vstack(rings[i:i + 3]).tolist()) for i in range(len(P) - 2)]
    return M.batch_boolean(hulls, m3.OpType.Add)


def rrect(w, h, r, n=6):
    """a convex rounded rectangle section, w across (u), h thick (v)"""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for a in np.radians(np.linspace(a0, a0 + 90, n)):
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ------------------------------------------------------------------ 01 GEROTOR ring
@reg("gv_gerotor_ring")
def gerotor_ring():
    """A gerotor pump's outer rotor is a ring with six soft pockets cut into it. The ring is that rotor at the size
    of a finger: a heavy forged band whose outside rises and falls in six shallow lobes, with a ruby set in one land."""
    pc = Piece("gv_gerotor_ring", "ring")
    ri = FINGER; W = 7.2; T = 2.5
    th = np.linspace(0, 2 * math.pi, 361)[:-1]
    r = ri + T - 0.95 * (0.5 + 0.5 * np.cos(6 * th)) ** 2.2
    outer = CS([[(float(a * math.cos(t)), float(a * math.sin(t))) for a, t in zip(r, th)]])
    band = extrude(outer, W, -W / 2)
    env = lathe([(0, -W / 2), (ri + T - 0.55, -W / 2), (ri + T + 0.05, -W / 2 + 0.55), (ri + T + 0.05, W / 2 - 0.55),
                 (ri + T - 0.55, W / 2), (0, W / 2)])
    band = band ^ env
    band = band - lathe([(0, -9), (ri + 0.45, -9), (ri, -W / 2 + 0.8), (ri, W / 2 - 0.8), (ri + 0.45, 9), (0, 9)])
    cav, zc = flush_seat(2.0)
    v = np.array([0, -1.0, 0])           # a land (theta = 270 deg) in the 2D outline: the top once turned
    band = band - orient_at(cav, v * (ri + T), v)
    R = rotx(-90)
    pc.add("band", place(band, R), "forged")
    up = R @ v
    pc.ball(tuple(up * (ri + T + zc)), 2.0, "ruby")
    pc.notes["views"] = [(0.55, -1.0, 0.75), (0.0, -0.12, 1.0), (1.0, 0.0, 0.18), (0.0, -1.0, 0.12)]
    return pc


# ------------------------------------------------------------------ 02 PRESSURE REGULATOR necklace
@reg("gv_regulator_necklace")
def regulator_necklace():
    """The pressure regulator: a spool held between a spring and line pressure. A ball chain necklace carries it as
    a short pendant: two turned lands with the steel spring between them on the stem, a ruby flush in the end."""
    pc = Piece("gv_regulator_necklace", "flat")
    from chains import Loop
    db, pb = 3.0, 3.9
    n = int(450 / pb)
    loop = Loop(n * pb, 0.62, e=2.6)
    s0 = loop.L * 0.75
    zt = 2.65
    balls, ctr = [], []
    for i in range(n):
        s = s0 + i * pb
        ds = min(abs(i * pb), abs(n * pb - i * pb))
        p, t = loop.at(s)
        z = db / 2 + (zt - db / 2) * math.exp(-(ds / 16.0) ** 2)
        ctr.append(np.array([p[0], p[1], z]))
    for i in range(n):
        a, b = ctr[i], ctr[(i + 1) % n]
        balls.append(M.sphere(db / 2, 24).translate(tuple(a)))
        d = b - a; L = np.linalg.norm(d)
        balls.append(orient_at(cyl(0.36, L, 0, seg=12), a, d))
    chain = M.batch_boolean(balls, m3.OpType.Add)
    # the pendant: a tube bail the chain runs through, and the spool hanging from it, laid flat toward the front
    yc = ctr[0][1]
    tube = lathe([(1.75, -3.2), (2.6, -3.2), (2.6, 3.2), (1.75, 3.2)])
    pend = place(tube, roty(90), (0, yc, zt))
    r = 2.6
    sp, L = spool(r, [(6.0, 4.0), (6.0, 2.0), (4.2, 0)], stem=1.15, c=0.3)
    neck = lathe([(0, 0), (1.3, 0), (1.3, 2.4), (0, 2.4)])
    body = neck + sp.translate((0, 0, 2.1))
    cav, zc = flush_seat(2.0)
    body = body - cav.translate((0, 0, 2.1 + L))
    d = np.array([0, -1.0, 0]); p0 = np.array([0, yc - 2.05, zt])
    pend = pend + orient_at(body, p0, d)
    pc.add("chain", chain, "forged")
    pc.add("pendant", pend, "forged")
    spr = mlib.helix_spring(1.72, 0.42, 1.0, 2.1 + 6.0 + 0.12, 2.1 + 6.0 + 4.0 - 0.12)
    pc.add("spring", orient_at(spr, p0, d), "steel", bought=True)
    pc.ball(tuple(p0 + d * (2.1 + L + zc)), 2.0, "ruby")
    cy = float(yc - 2.0 - (2.1 + L) / 2 + 4.0)
    pc.notes["views"] = [(0.3, -1.0, 1.05, 0.0, cy, 2.0, 58.0), (0.0, -0.02, 1.0), (0.6, -1.0, 0.25), (-0.4, -1.0, 0.8, 0.0, cy, 2.0, 40.0)]
    pc.notes["length"] = "50 cm ball chain"
    return pc


# ------------------------------------------------------------------ 03 GOVERNOR ID bracelet
@reg("gv_governor_id")
def governor_id():
    """The governor: two weights on pivots that swing out with road speed. A flattened curb chain with a forged ID
    plate; the plate carries the two pivots as bright domed rivets, and a ruby where the oil leaves."""
    pc = Piece("gv_governor_id", "flat")
    lean = 45.0
    C = dict(Li=5.0, Wi=3.1, d=1.45, flat=1.45, cut=0.0)
    n_links = 34
    Lp, Wp, Tp = 34.0, 8.6, 1.9
    plate = mlib.chamfered_plate(mlib.rounded_rect2(Lp, Wp, 2.2), Tp, c=0.35, z0=-Tp / 2)
    for x in (-8.5, 8.5):                                    # the flyweight pivots: rivet holes, heads fitted below
        plate = plate - cyl(0.85, 4, -2).translate((x, 0, 0))
    cav, zc = flush_seat(1.5)
    xr = Lp / 2 - 4.0
    plate = plate - cav.translate((xr, 0, Tp / 2))
    Di, de = 2.8, 1.35
    xe = Lp / 2 + Di / 2 - 0.2
    solid = plate + eye(Di, de, lean_of(1, lean) * -1).translate((xe, 0, 0)) + eye(Di, de, lean_of(1, lean) * -1).translate((-xe, 0, 0))
    pe = 0.97 * (Di + C["Li"]) / 2
    plate_slot = dict(Li=0, h=0, d=de, solid=solid, lean=0.0, label="plate", pitch=xe + pe)
    links = [cable_slot(**C) for _ in range(n_links)]
    clasp = dict(Li=5.0, h=3.1, d=1.2, solid=bolt_clasp(5.0, 1.2), label="clasp")
    slots = [plate_slot] + links[:17] + [clasp] + links[17:]
    slots[-1]["pitch"] = xe + pe
    loop, placed = lay(slots, aspect=1.05, e=2.0, lean=lean, straight=2 * xe + 6)
    chain_parts(pc, slots, placed)
    Rb, pb_, _, _ = placed[0]
    for x in (-8.5, 8.5):
        riv = lathe([(0, -Tp / 2 - 0.3), (0.82, -Tp / 2 - 0.3), (0.82, Tp / 2), (1.55, Tp / 2), (1.55, Tp / 2 + 0.35)] +
                    [(1.55 * math.cos(a), Tp / 2 + 0.35 + 0.5 * math.sin(a)) for a in np.linspace(0.2, math.pi / 2, 6)])
        pc.add("rivet%d" % (0 if x < 0 else 1), place_m(riv.translate((x, 0, 0)), Rb, pb_), "forged_hi")
    pc.ball(tuple(pb_ + Rb @ np.array([xr, 0, Tp / 2 + zc])), 1.5, "ruby")
    pc.notes["views"] = [(0.0, -1.0, 1.1), (0.0, -0.02, 1.0), (1.0, -0.3, 0.35), (0.25, -1.0, 0.2)]
    return pc


# ------------------------------------------------------------------ 04 VACUUM MODULATOR cufflinks
@reg("gv_modulator_cufflinks")
def modulator_cufflinks():
    """The vacuum modulator is a sealed can whose diaphragm feels engine load. Each cufflink face is the can, turned
    with its rolled seam, the diaphragm's rings and the slotted adjusting screw; behind it a short chain runs to a
    toggle bar, as on a pair of old chain cufflinks."""
    pc = Piece("gv_modulator_cufflinks", "flat")
    Rc, H = 7.0, 3.4
    can = lathe([(0, 0), (Rc - 0.6, 0), (Rc, 0.6), (Rc, 1.4), (Rc - 0.25, 1.7), (Rc - 0.25, 2.1),
                 (Rc - 0.9, H - 0.35), (2.0, H), (0, H)])
    can = can - lathe([(Rc - 0.12, 1.45), (Rc + 1, 1.3), (Rc + 1, 1.6)])                 # the rolled seam's lap line
    for rr in (3.0, 4.1, 5.2):                                                           # the diaphragm's rings
        z = H - (rr - 2.0) / (Rc - 2.9) * 0.9
        can = can - lathe([(rr - 0.22, z + 0.5), (rr, z - 0.22), (rr + 0.22, z + 0.5)])
    can = can - lathe([(0, H - 1.0), (1.3, H - 1.0), (1.3, H + 1), (0, H + 1)])
    screw = lathe([(0, H - 0.95), (1.22, H - 0.95), (1.22, H + 0.35), (1.05, H + 0.55), (0, H + 0.55)])
    screw = screw - box(0.32, 3.0, 0.5).translate((0, 0, H + 0.45))
    # back: a post with an eye, two links, the toggle bar
    post = lathe([(0, 0.1), (0.9, 0.1), (0.9, -1.6), (0, -1.6)][::-1])
    Di, d = 2.0, 0.9
    eyeA = oval_link(Di, Di, d).rotate((0, 90, 0))                         # ring standing in the YZ plane
    zA = -1.6 - Di / 2 - d / 2 + 0.25
    can_part = can + post + eyeA.translate((0, 0, zA))
    Li, Wi, dl = 3.4, 2.1, 0.85
    lk = oval_link(Li, Wi, dl, cut=0.3)
    vert = lambda s, quarter: s.rotate((0, 90, 0)).rotate((0, 0, 90 if quarter else 0))   # long axis along Z
    p1 = 0.86 * (Di + Li) / 2
    z1 = zA - p1
    z2 = z1 - 0.86 * Li
    tb = lathe([(0, -7.0), (1.2, -7.0), (1.45, -6.75), (1.45, 6.75), (1.2, 7.0), (0, 7.0)])
    tb = (tb - lathe([(1.25, -5.8), (2, -5.8), (2, -3.6), (1.25, -3.6)]) - lathe([(1.25, 3.6), (2, 3.6), (2, 5.8), (1.25, 5.8)])) + \
         (knurl(1.46, -5.8, -3.6, pitch=0.45, depth=0.2, chamfer=0.1) - cyl(1.24, 2.2, -5.8)) + \
         (knurl(1.46, 3.6, 5.8, pitch=0.45, depth=0.2, chamfer=0.1) - cyl(1.24, 2.2, 3.6))
    tb = place(tb, roty(90))
    eyeB = vert(oval_link(Di, Di, d), True)                                 # XZ, in the bar's plane
    zB = z2 - 0.86 * (Li + Di) / 2
    tog = tb.translate((0, 0, zB - Di / 2 - d / 2 - 1.2)) + eyeB.translate((0, 0, zB)) + \
        lathe([(0, 0), (0.6, 0), (0.6, 1.0), (0, 1.0)]).translate((0, 0, zB - Di / 2 - d / 2 - 0.9))
    pc.add("can", can_part, "forged")
    pc.add("screw", screw, "forged_hi")
    pc.add("link1", vert(lk, True).translate((0, 0, z1)), "forged")
    pc.add("link2", vert(lk, False).translate((0, 0, z2)), "forged")   # XZ, then YZ
    pc.add("toggle", tog, "forged")
    pc.mirror_pair(22.0)
    pc.notes["views"] = [(0.35, -0.9, 0.9), (0.0, -0.02, 1.0), (1.0, -0.3, 0.2), (0.3, -1.0, -0.3)]
    return pc


# ------------------------------------------------------------------ 06 CHECK BALL huggie hoops
@reg("gv_check_ear")
def check_ear():
    """A check ball lets oil pass one way and shuts the other. Each earring is a small heavy hoop of forged tube,
    with a ruby ball swaged flush into its lowest point, where a check ball sits in its pocket."""
    pc = Piece("gv_check_ear", "flat")
    R, rt = 6.4, 1.2
    hoop = M.revolve(CS.circle(rt, 32).translate((R, 0)), 72, 360.0)       # torus about Z (in the XY plane)
    hoop = hoop.rotate((90, 0, 0))                                         # stand it up facing -Y
    hoop = hoop - box(0.22, 4, 4).translate((0, 0, R + rt))                # the hinge line where it opens
    cav, zc = flush_seat(2.0)
    v = np.array([0, -0.6, -0.8]); v /= np.linalg.norm(v)
    c0 = np.array([0, 0, -R])
    hoop = hoop - orient_at(cav, c0 + v * rt, v)
    pc.add("hoop", hoop, "forged")
    pc.ball(tuple(c0 + v * (rt + zc)), 2.0, "ruby")
    pc.mirror_pair(18.0)
    pc.notes["views"] = [(0.35, -1.0, 0.25), (0.0, -1.0, 0.02), (1.0, -0.2, 0.1), (0.3, -0.6, 1.0)]
    return pc


# ------------------------------------------------------------------ 07 SEPARATOR PLATE money clip
@reg("gv_separator_clip")
def separator_clip():
    """The separator plate times every shift with drilled holes. The clip is a forged sterling strap folded back on
    itself, its top drilled with three orifices of different sizes, and a ruby where the plate's check ball sits."""
    pc = Piece("gv_separator_clip", "flat")
    t, w, ri = 1.5, 10.5, 0.9
    Lt, Lb = 50.0, 40.0
    xb = Lt / 2 - 0.5
    def leaf(x0, x1, w0, w1, z0, crown):
        """a strap leaf with a crowned face, tapering from w1 at the bend (x1) to w0 at its rounded tip (x0)"""
        xs = np.linspace(x0, x1, 6); hulls = []
        for i in range(5):
            pts = []
            for x in (xs[i], xs[i + 1]):
                wd = w0 + (w1 - w0) * (x - x0) / (x1 - x0)
                for a in np.linspace(0, math.pi, 13):
                    pts.append((x, wd / 2 * math.cos(a), z0 + t + crown * math.sin(a)))
                    pts.append((x, wd / 2 * math.cos(a), z0))
            hulls.append(M.hull_points(pts))
        lf = M.batch_boolean(hulls, m3.OpType.Add)
        rc = 2.4
        plan = CS.batch_hull([mlib.circle2(rc, (x0 + rc, w0 / 2 - rc)), mlib.circle2(rc, (x0 + rc, -w0 / 2 + rc)),
                              mlib.rect2(0.2, w1, (x1 + 0.5, 0))])
        return lf ^ extrude(plan, 10, z0 - 2)
    top = leaf(-Lt / 2, xb + 0.01, 9.0, w, ri, 0.55)
    bot = mlib.chamfered_plate(mlib.rounded_rect2(Lb + 4, w, 2.4).translate((xb - Lb / 2 - 2, 0)), t, c=0.3, z0=-ri - t) - box(10, 20, 20).translate((xb + 5, 0, 0))
    bend = M.revolve(mlib.rounded_rect2(t, w, 0.3).translate((ri + t / 2, 0)), 48, 180.0)   # in XZ about Y? (built XY)
    bend = bend.rotate((90, 0, 0)).rotate((0, 90, 0))
    bb = bend.bounding_box()
    clip = top + bot
    clip = clip + bend.translate((xb, 0, 0))
    for x, h in ((-13.0, 0.6), (-4.0, 1.0), (5.0, 0.8)):
        clip = clip - cyl(h, 6, -3).translate((x, 0, ri)) - lathe([(0, ri + t - h * 0.5 - 0.3), (h, ri + t - h * 0.5 - 0.3), (h + 0.45, ri + t + 0.01), (0, ri + t + 0.01)]).translate((x, 0, 0))
    cav, zc = flush_seat(1.5)
    xr = -Lt / 2 + 1.5
    clip = clip - cav.translate((xr, 0, ri + t))
    clip = clip.translate((0, 0, ri + t))
    pc.add("clip", clip, "forged")
    pc.ball((xr, 0, 2 * (ri + t) + zc), 1.5, "ruby")
    pc.notes["views"] = [(0.25, -1.0, 0.75), (0.0, -0.02, 1.0), (0.2, -1.0, 0.15), (-1.0, -0.5, 0.5)]
    return pc


# ------------------------------------------------------------------ 08 WORM TRACKS triple wrap
@reg("gv_wormtrail_wrap")
def wormtrail_wrap():
    """The worm tracks: the channels cast into a valve body, each carrying one signal. Three chains wound round the
    wrist as one bracelet, a fine cable, a square-wire rectangle link and a ball chain, one for each signal; the
    middle one passes through a short knurled bore with a ruby in it."""
    pc = Piece("gv_wormtrail_wrap", "flat")
    # inner: fine cable
    A = dict(Li=3.0, Wi=1.9, d=0.7)
    n = 61
    slots = [cable_slot(**A) for _ in range(n)] + [dict(Li=3.4, h=2.1, d=0.9, solid=bolt_clasp(3.4, 0.9), label="clasp_a")]
    for sl in slots[:-1]:
        sl["label"] = None
    loop, placed = lay(slots, aspect=0.8, e=2.4)
    for i, (sl, (R, p, s, t)) in enumerate(zip(slots, placed)):
        pc.add(sl.get("label") or "a%02d" % i, place_m(sl["solid"], R, p), "forged")
    # middle: square-wire rectangle links, broken by the knurled bore
    B = dict(Li=6.0, Wi=2.7, d=1.05, square=True, cut=0.0)
    r = 2.0
    bore = lathe([(0, -4.5), (r - 0.25, -4.5), (r, -4.25), (r, 4.25), (r - 0.25, 4.5), (0, 4.5)])
    bore = (bore - lathe([(r - 0.26, -3.2), (r + 1, -3.2), (r + 1, -1.2), (r - 0.26, -1.2)]) - lathe([(r - 0.26, 1.2), (r + 1, 1.2), (r + 1, 3.2), (r - 0.26, 3.2)])) + \
           (knurl(r, -3.2, -1.2, pitch=0.45, depth=0.2, chamfer=0.08) - cyl(r - 0.27, 2.0, -3.2)) + \
           (knurl(r, 1.2, 3.2, pitch=0.45, depth=0.2, chamfer=0.08) - cyl(r - 0.27, 2.0, 1.2))
    bore = place(bore, roty(90))
    lean = 45.0
    v = up_in_slot(lean)
    cav, zc = flush_seat(1.5)
    bore = bore - orient_at(cav, r * v, v)
    nb = 34
    sl2 = [bar_slot(bore, 4.5, 2.2, 0.95, B["Li"], lean=lean, label="bore")] + [cable_slot(**B) for _ in range(nb)]
    sl2.insert(18, dict(Li=4.0, h=2.4, d=1.0, solid=bolt_clasp(4.0, 1.0), label="clasp_b"))
    for k, sl in enumerate(sl2):
        sl.setdefault("label", None)
    loop2, placed2 = lay(sl2, aspect=0.8, e=3.0)
    for i, (sl, (R, p, s, t)) in enumerate(zip(sl2, placed2)):
        pc.add(sl.get("label") or "b%02d" % i, place_m(sl["solid"], R, p), "forged")
    Rb, pb_, _, _ = placed2[0]
    pc.ball(tuple(pb_ + Rb @ ((r + zc) * v)), 1.5, "ruby")
    # outer: ball chain, one fused strand closed by its own connector
    from chains import Loop
    db, pp = 2.2, 2.9
    m = int(round((loop2.L + 2 * math.pi * 7.5) / pp))
    L3 = Loop(m * pp, 0.8, e=2.0)
    ctr = []
    for i in range(m):
        p, t = L3.at(L3.L * 0.25 + i * pp)
        ctr.append(np.array([p[0], p[1], db / 2]))
    parts = []
    for i in range(m):
        a, b = ctr[i], ctr[(i + 1) % m]
        parts.append(M.sphere(db / 2, 20).translate(tuple(a)))
        parts.append(orient_at(cyl(0.3, np.linalg.norm(b - a), 0, seg=12), a, b - a))
    pc.add("ballchain", M.batch_boolean(parts, m3.OpType.Add), "forged")
    pc.notes["views"] = [(0.0, -1.0, 1.1), (0.0, -0.02, 1.0), (1.0, -0.3, 0.35), (0.25, -1.0, 0.2)]
    return pc


# ------------------------------------------------------------------ 09 MANUAL VALVE toggle bracelet
@reg("gv_detent_toggle")
def detent_toggle():
    """The shift lever slides the manual valve; a spring roller drops into a notch of the detent lever to hold it in
    P, R, N, D, 2 or 1. A heavy forged cable chain that closes on a toggle: the ring is the detent lever bent round,
    its six notches inside; the bar is the manual valve's spool."""
    pc = Piece("gv_detent_toggle", "flat")
    C = dict(Li=6.2, Wi=3.9, d=1.6)
    n = 22
    lean = 45.0
    # ring: lies flat, its eye leaning to meet the next link
    Rr, rw = 7.2, 1.6
    ring = M.revolve(CS.circle(rw, 32).translate((Rr, 0)), 96, 360.0)
    ring = ring.scale((1, 1, 0.85))
    for k in range(6):
        a = math.radians(150 + 12 * k)
        ring = ring - M.sphere(0.85, 32).scale((1, 1, 2.2)).translate(((Rr - rw) * math.cos(a), (Rr - rw) * math.sin(a), 0))
    cav, zc = flush_seat(1.5)
    ring = ring - cav.translate((-Rr, 0, rw * 0.85))
    De, de = 2.6, 1.4
    xe = Rr + rw + De / 2 - 0.3
    ring_s = ring + eye(De, de, -lean).translate((xe, 0, 0))       # next link (index 1) leans -lean? set below
    # toggle bar: the spool, across the chain, its eye pointing back to the previous link
    sp, L = spool(1.8, [(3.0, 1.6), (4.4, 1.6), (4.4, 1.6), (3.0, 0)], stem=1.05, c=0.28)
    sp = sp.translate((0, 0, -L / 2))
    bar = place(sp, rotx(90))                                         # along local Y
    xb = 1.8 + De / 2 + de / 2 - 0.2
    bar_s = bar + eye(De, de, lean).translate((-xb, 0, 0)) + lathe([(0, 0), (0.9, 0), (0.9, 1.0), (0, 1.0)]).rotate((0, -90, 0)).translate((-0.8, 0, 0))
    links = [cable_slot(**C) for _ in range(n)]
    pe = 0.97 * (De + C["Li"]) / 2
    slots = [dict(Li=0, h=0, d=de, solid=ring_s, lean=0.0, label="detent_ring", pitch=xe + pe)] + links + \
            [dict(Li=0, h=0, d=de, solid=bar_s, lean=0.0, label="toggle", pitch=1.8 + 2.2 + Rr + rw)]
    links[-1]["pitch"] = xb + pe - 0.4
    # leans: slot 1 leans +lean by the even/odd rule? index 1 is odd: -lean. The ring's eye must be +lean.
    slots[0]["solid"] = ring + eye(De, de, lean).translate((xe, 0, 0))
    last = len(slots) - 2                                              # the last link's index
    lb = lean_of(last, lean)
    slots[-1]["solid"] = bar + eye(De, de, -lb).translate((-xb, 0, 0)) + \
        lathe([(0, 0), (0.9, 0), (0.9, xb - De / 2 - de + 0.6), (0, xb - De / 2 - de + 0.6)]).rotate((0, -90, 0))
    loop, placed = lay(slots, aspect=1.0, e=2.0, lean=lean, straight=2 * xe + 16)
    chain_parts(pc, slots, placed)
    R0, p0, _, _ = placed[0]
    pc.ball(tuple(p0 + R0 @ np.array([-Rr, 0, rw * 0.85 + zc])), 1.5, "ruby")
    pc.notes["views"] = [(0.0, -1.0, 1.1), (0.0, -0.02, 1.0), (1.0, -0.3, 0.35), (0.25, -1.0, 0.2)]
    return pc


# ------------------------------------------------------------------ 10 BAND AND SERVO cuff
@reg("gv_servo_cuff")
def servo_cuff():
    """A band clamps a drum to hold a gear; a servo piston pulls one end and an adjusting screw anchors the other.
    The cuff is that band: a heavy forged strap round the wrist, its two ends facing across the opening, one finished
    with the adjuster's hex nut, the other with the servo's turned cap and a ruby."""
    pc = Piece("gv_servo_cuff", "cuff")
    from pieces_r2 import wrist_pt
    gap = 0.46
    phis = np.linspace(-math.pi + gap, math.pi - gap, 121)
    h = 2.6
    P = [np.array(wrist_pt(ph, 0, h / 2)) for ph in phis]
    V = []
    for ph in phis:
        n = np.array([0, math.sin(ph) / 29.5, math.cos(ph) / 24.0]); V.append(n / np.linalg.norm(n))
    U = [np.array([1.0, 0, 0])] * len(P)
    sec = [(7.0 / 2 * math.cos(a), -h / 2 + 0.25 + (h - 0.25) * max(math.sin(a), 0) ** 0.6 if a < math.pi else -h / 2) for a in np.linspace(0, math.pi, 15)]
    sec = [(u, v) for u, v in sec] + [(-3.3, -h / 2), (3.3, -h / 2)]
    band = sweep_convex(P, U, V, sec)
    T0 = P[0] - P[1]; T0 /= np.linalg.norm(T0)
    T1 = P[-1] - P[-2]; T1 /= np.linalg.norm(T1)
    nut = lathe([(0, -1.0), (1.7, -1.0), (1.7, 1.2), (0, 1.2)]) + mlib.hex_nut(6.2, 3.4, 0.0, z0=1.0)
    band = band + orient_at(nut, P[0] - 0.6 * T0, T0)
    cap = lathe([(0, -1.0), (3.3, -1.0), (3.6, -0.7), (3.6, 2.9), (3.3, 3.2), (0, 3.2)])
    for z0 in (0.3, 1.1):
        cap = cap - lathe([(3.35, z0), (3.8, z0), (3.8, z0 + 0.35), (3.35, z0 + 0.35)])
    cav, zc = flush_seat(2.0)
    cap = cap - cav.translate((0, 0, 3.2))
    band = band + orient_at(cap, P[-1] - 0.6 * T1, T1)
    pc.add("band", band, "forged")
    pc.ball(tuple(P[-1] - 0.6 * T1 + (3.2 + zc) * T1), 2.0, "ruby")
    pc.notes["views"] = [(0.35, -0.55, 1.0), (0.0, -0.02, 1.0), (1.0, -0.2, 0.3), (0.0, -1.0, -0.6)]
    return pc


# ------------------------------------------------------------------ 11 CLUTCH PACK stacking rings
@reg("gv_clutch_stack")
def clutch_stack():
    """A clutch pack: steel plates lugged outside, friction plates grooved, fed by drilled holes, squeezed together by
    oil. Three plain forged rings worn as one stack: a steel band with six lugs milled in, a knurled friction ring,
    and a crowned ring drilled with twelve countersunk orifices."""
    pc = Piece("gv_clutch_stack", "ring")
    ri = FINGER
    w = 2.6
    st = lathe([(ri, -w / 2), (ri + 1.5, -w / 2), (ri + 1.9, -w / 2 + 0.4), (ri + 1.9, w / 2 - 0.4), (ri + 1.5, w / 2), (ri, w / 2)])
    for k in range(6):
        a = 2 * math.pi * k / 6
        st = st - cyl(0.62, 6, -3).translate(((ri + 2.15) * math.cos(a), (ri + 2.15) * math.sin(a), 0))
    st = st - lathe([(0, -3), (ri + 0.3, -3), (ri, -w / 2 + 0.5), (ri, w / 2 - 0.5), (ri + 0.3, 3), (0, 3)])
    pc.add("steel", place(st, rotx(-90), (0, -3.0, 0)), "forged")
    fr = lathe([(ri, -w / 2), (ri + 1.3, -w / 2), (ri + 1.55, -w / 2 + 0.25), (ri + 1.55, w / 2 - 0.25), (ri + 1.3, w / 2), (ri, w / 2)])
    fr = (fr - lathe([(ri + 1.3, -0.75), (ri + 2, -0.75), (ri + 2, 0.75), (ri + 1.3, 0.75)])) + \
         (knurl(ri + 1.56, -0.75, 0.75, pitch=0.6, depth=0.26, chamfer=0.1) - cyl(ri + 1.28, 1.5, -0.75))
    fr = fr - cyl(ri, 4, -2)
    pc.add("friction", place(fr, rotx(-90), (0, 0.0, 0)), "forged")
    hw = 1.25
    prof_ = [(ri, -hw), (ri + 0.9, -hw)] + [(ri + 0.9 + 0.7 * math.cos(t), hw * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 17)[1:-1]] + [(ri + 0.9, hw), (ri, hw)]
    orr = lathe(prof_)
    tool = lathe([(0, -0.75), (0.4, -0.75), (0.4, -0.35), (0.92, 0.17), (0.92, 1.0), (0, 1.0)])
    tool = place(tool, roty(90), (ri + 1.6, 0, 0))
    for k in range(12):
        orr = orr - tool.rotate((0, 0, 30 * k + 15))
    orr = orr - cyl(ri, 4, -2)
    pc.add("orifice", place(orr, rotx(-90), (0, 3.0, 0)), "forged")
    pc.notes["views"] = [(0.6, -1.0, 0.75), (0.0, -1.0, 0.05), (1.0, 0.0, 0.18), (0.3, -0.4, 1.0)]
    pc.notes["set"] = "three rings worn as one stack"
    return pc


# ------------------------------------------------------------------ 12 PLANETARY key ring
@reg("gv_planetary_keyring")
def planetary_keyring():
    """Every clutch and band in the gearbox exists to hold one part of a planetary gearset still. The ring gear, the
    one toothed on the inside, is the key ring here: forged, knurled round its rim, on a short heavy chain to a
    snap clasp for the belt loop."""
    pc = Piece("gv_planetary_keyring", "flat")
    m_, z_ = 0.9, 30
    T = 4.2
    Ro = z_ * m_ / 2 + 4.0
    rg = extrude(mlib.circle2(Ro, seg=160), T) - extrude(mlib.involute_gear2(z_, m_, internal=True), T + 2, -1)
    rg = rg ^ lathe([(0, 0), (Ro - 0.5, 0), (Ro, 0.5), (Ro, T - 0.5), (Ro - 0.5, T), (0, T)])
    kn = knurl(Ro + 0.01, 0.9, T - 0.9, pitch=0.7, depth=0.3)
    rg = (rg - lathe([(Ro - 0.33, 0.9), (Ro + 1, 0.9), (Ro + 1, T - 0.9), (Ro - 0.33, T - 0.9)])) + (kn - cyl(Ro - 0.35, T - 1.8, 0.9))
    cav, zc = flush_seat(2.0)
    xr = -(Ro - 1.9)
    rg = rg - cav.translate((xr, 0, T))
    C = dict(Li=6.2, Wi=3.9, d=1.6)
    lean = 45.0
    h = C["Wi"] / 2 + C["d"]
    zc_ = h * math.sin(math.radians(lean)) + C["d"] / 2 * math.cos(math.radians(lean))
    De, de = 3.0, 1.8
    xe = Ro + De / 2 - 0.2
    rg = rg + eye(De, de, lean).translate((xe, 0, zc_))
    pc.add("ring_gear", rg, "forged")
    pc.ball((xr, 0, T + zc), 2.0, "ruby")
    x = xe + 0.9 * (De + C["Li"]) / 2
    lk = cable_slot(**C)["solid"]
    for k in range(4):
        ln = -lean if k % 2 == 0 else lean
        pc.add("link%d" % k, lk.rotate((ln, 0, 0)).translate((x, 0, zc_)), "forged")
        x += 0.9 * C["Li"] if k < 3 else 0
    Dc, dc = 6.0, 1.7
    x += 0.9 * (C["Li"] + Dc) / 2
    pc.add("clasp", bolt_clasp(Dc, dc).rotate((-lean, 0, 0)).translate((x + 0.0, 0, zc_)), "forged")
    pc.notes["views"] = [(0.2, -1.0, 1.2), (0.0, -0.02, 1.0), (1.0, -0.3, 0.3), (0.3, -1.0, 0.3)]
    return pc
