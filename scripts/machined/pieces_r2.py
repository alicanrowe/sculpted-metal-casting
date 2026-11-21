"""GOVERNOR r2: the oil computer drawn in liquid silver.
Lines of liquid silver (the oil and its channels) swell and taper; the machine appears only at the nodes, as
small crisp turned and knurled parts. Black only in the recesses (antiqued), never black-painted parts.
Rings: finger axis = Y, top of the finger = +Z. Units mm."""
import math
import numpy as np
import mlib
from mlib import M, CS, Piece, cyl, lathe, knurl, union, cut, extrude, rotx, roty, rotz, place, box
import manifold3d as m3
import sdf
from oil import sdf_part, line, ring_pt, curve, prof
from pieces_r1 import gerotor2

FINGER = 19.8 / 2
PIECES = {}


def reg(name):
    def d(fn):
        PIECES[name] = fn; return fn
    return d


def to_top(s, z):
    """a part turned about Z, standing on the top of the ring at height z"""
    return s.translate((0, 0, z))


def split_shank(s, theta0, R_low, R_top, spread, r_head, r_low, k=0.5):
    """two liquid lines run up out of the head on each side, cross under the finger and pass each other: the
    shank. They start inside the head (theta0 small, R_top high) so the head swallows their ends: no nubs."""
    for side in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 19):
            th = theta0 + t * (2 * math.pi - 2 * theta0)
            ph = t * math.pi
            y = side * spread * math.cos(ph)
            near = abs(math.cos(th / 2))            # 1 at the head, 0 under the finger
            R = R_low + (R_top - R_low) * near ** 4
            pts.append(ring_pt(th, R, y * (1 - 0.5 * near ** 8)))
        line(s, pts, [(0, r_head * 0.8), (0.1, r_head), (0.3, (r_head + r_low) / 2), (0.5, r_low),
                      (0.7, (r_head + r_low) / 2), (0.9, r_head), (1, r_head * 0.8)], k=k, n=10)


# ------------------------------------------------------------------ 01 GEROTOR ring
@reg("gv_gerotor_ring")
def gerotor_ring():
    """The pump. Two lines of oil rise round the finger into a liquid cup, and on the cup sits the pump itself:
    a turned outer rotor with a knurled rim, and inside it the five-lobed inner rotor, which really turns on its
    pin. Liquid where the oil flows, machined where it is pumped."""
    pc = Piece("gv_gerotor_ring", "ring")
    ri = FINGER
    s = sdf.Scene()
    top = ri + 2.6                       # where the cup meets the turned head
    split_shank(s, math.radians(10), ri + 0.95, top - 0.2, 4.3, 1.75, 0.85)
    # the cup: a flared bowl that gathers the lines and rises in a meniscus to the rotor's rim
    s.cone((0, 0, ri + 0.6), (0, 0, top - 0.6), 2.6, 6.2, k=2.2)
    s.ellipsoid((0, 0, ri + 1.4), (5.6, 3.9, 1.5), k=1.8)
    body = sdf_part(s)
    # finger bore (comfort fit) and the flat the head is turned onto
    bore = place(lathe([(0, -9), (ri + 0.35, -9), (ri, -3.2), (ri, 3.2), (ri + 0.35, 9), (0, 9)]), rotx(-90))
    body = body - bore - box(40, 40, 20, center=False).translate((-20, -20, top))
    # turned head: the outer rotor
    N, Rp, rp, e = 6, 4.6, 0.62, 0.42
    inner2, cavity2 = gerotor2(N=N, Rp=Rp, rp=rp, e=e, steps=300)
    Ro = 6.6; H = 3.4
    outer = lathe([(0, 0), (Ro - 0.35, 0), (Ro, 0.35), (Ro, H - 0.4), (Ro - 0.4, H), (0, H)]).translate((e, 0, 0))
    outer = outer - extrude(cavity2, H, 0.9)                                       # rotor pocket
    kn = knurl(Ro + 0.01, 0.9, H - 0.8, pitch=0.62, depth=0.32).translate((e, 0, 0))
    outer = (outer - lathe([(Ro - 0.34, 0.9), (Ro + 1, 0.9), (Ro + 1, H - 0.8), (Ro - 0.34, H - 0.8)]).translate((e, 0, 0))) + \
            (kn - cyl(Ro - 0.36, H, 0).translate((e, 0, 0)))
    post = lathe([(0, 0.5), (0.48, 0.5), (0.48, H - 0.35), (0.36, H - 0.2), (0, H - 0.2)])      # the rotor turns on it
    head = to_top(outer + post, top - 0.02)
    pc.add("body", body + head, "antique")
    # the inner rotor: turns on a steel pin in the pocket
    rot = mlib.chamfered_plate(inner2.offset(-0.12, m3.JoinType.Round, 2, 48), H - 1.15, c=0.18, z0=0) - cyl(0.62, 6, -1)
    rot = rot - cyl(1.55, 1, H - 1.15 - 0.35)                                      # a turned spot face round the pin
    pc.add("inner_rotor", to_top(rot, top + 0.95), "bright")
    pc.notes["views"] = [(0.38, -1.0, 0.55), (0.0, -1.0, 0.0), (1.0, -0.15, 0.3), (0.15, -0.3, 1.0)]
    return pc


def get(name):
    return PIECES[name]()


# ------------------------------------------------------------------ shared turned parts
def ruby_cup(D=3.969, wall=0.9, base=0.0, knurled=True):
    """A turned cup that holds a precision ruby ball on a 90 deg seat behind a swaged lip (the check-ball seat).
    Built along +Z from z=base. Returns (cup solid, cavity to cut from anything the cup is fused to, ball centre z)."""
    rb = D / 2
    zc = base + 1.3 + rb * 0.72
    rc, zt = rb * math.cos(math.radians(45)), zc - rb * math.sin(math.radians(45))
    zs = lambda r: zt - (rc - r) - 0.035
    rlip = rb * 0.86
    zl = zc + math.sqrt(rb ** 2 - rlip ** 2)
    R = rb + wall
    prof = [(0, base), (R - 0.3, base), (R, base + 0.3), (R, zc - 0.1), (rlip + 0.5, zl + 0.28), (0, zl + 0.28)]
    cup = lathe(prof)
    if knurled:
        zk0, zk1 = base + 0.35, zc - 0.45
        if zk1 - zk0 > 0.7:
            kn = knurl(R + 0.01, zk0, zk1, pitch=0.55, depth=0.26, chamfer=0.15)
            cup = (cup - lathe([(R - 0.27, zk0), (R + 1, zk0), (R + 1, zk1), (R - 0.27, zk1)])) + (kn - cyl(R - 0.29, zk1 - zk0, zk0))
    cav = lathe([(0, zs(0.8) - 0.5), (0.8, zs(0.8) - 0.5), (0.8, zs(0.8)), (rb + 0.03, zs(rb + 0.03)), (rb + 0.03, zc)] +
                [(math.sqrt(max(rb ** 2 - (z - zc) ** 2, 0)) + 0.035, z) for z in np.linspace(zc + 0.1, zl - 0.01, 8)] +
                [(rlip, zl + 0.03), (rlip, zl + 1.0), (0, zl + 1.0)])
    return cup, cav, zc


def spool(r, lands, z0=0.0, stem=0.55, c=0.12):
    """A valve spool: lands [(len, gap), ...] turned on a stem; crisp chamfered lands, bright."""
    prof = [(0, z0)]; z = z0
    for i, (L, gap) in enumerate(lands):
        prof += [(r - c, z), (r, z + c), (r, z + L - c), (r - c, z + L)]
        z += L
        if gap > 0:
            prof += [(stem, z), (stem, z + gap)]
            z += gap
    prof += [(0, z)]
    return lathe(prof), z


def orient_at(solid, p, d):
    """move a part built along +Z so it starts at p and points along d"""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    z = np.array([0, 0, 1.0]); v = np.cross(z, d); c = float(np.dot(z, d))
    if np.linalg.norm(v) < 1e-9:
        R = np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * (1 / (1 + c))
    return place(solid, R, tuple(p))


# ------------------------------------------------------------------ 03 GOVERNOR signet
@reg("gv_governor_signet")
def governor_signet():
    """The governor spins with the output shaft; two weights swing out as it turns faster and pull a spool. The
    signet's face is the two flyweights themselves: heavy liquid commas, turned 180 degrees from each other as
    if flung out mid-spin, with the bright spool lying in the channel between them. The band swells up into
    them; nothing is stuck on."""
    pc = Piece("gv_governor_signet", "ring")
    ri = FINGER
    s = sdf.Scene()
    top = ri + 2.7
    # the band: one stroke right round, thin under the finger, swelling up into the seat on both sides
    ths = np.linspace(math.radians(24), math.radians(336), 29)
    pts = [ring_pt(th, ri + 1.0 + 1.2 * abs(math.cos(th / 2)) ** 4, 0.0) for th in ths]
    line(s, pts, [(0, 2.5), (0.25, 1.4), (0.5, 1.05), (0.75, 1.4), (1.0, 2.5)], k=0.7, n=8, flat=1.3, normal=(0, 1, 0))
    s.ellipsoid((0, 0, ri + 1.5), (4.4, 3.2, 1.5), k=1.4)
    for sg in (1, -1):          # the two flyweights, 2-fold symmetric
        P = [(sg * x, sg * y, top + z) for x, y, z in [(1.5, -4.4, 0.2), (3.9, -3.9, 0.7), (5.7, -1.4, 1.15), (5.5, 1.9, 1.15), (3.7, 4.2, 0.8), (1.65, 4.6, 0.45)]]
        line(s, P, [(0, 0.42), (0.2, 1.45), (0.45, 2.3), (0.72, 1.5), (1.0, 0.36)], k=0.35, n=12, flat=1.25, normal=(0, 0, 1))
    body = sdf_part(s)
    bore = place(lathe([(0, -9), (ri + 0.35, -9), (ri, -3.5), (ri, 3.5), (ri + 0.35, 9), (0, 9)]), rotx(-90))
    zs = top + 0.45                                                   # spool axis
    trough = place(cyl(1.01, 9.6, -4.8), rotx(-90), (0, 0, zs)) + box(2.02, 9.6, 3.0).translate((0, 0, zs + 1.5))
    body = body - bore - trough
    pc.add("body", body, "antique")
    sp, L = spool(0.95, [(1.5, 0.7), (2.0, 0.7), (1.5, 0)])
    sp = place(sp.translate((0, 0, -L / 2)), rotx(-90), (0, 0, zs - 0.06))
    pc.add("spool", sp, "bright")
    pc.notes["views"] = [(0.45, -0.8, 1.0), (0.0, -0.05, 1.0), (1.0, -0.1, 0.25), (0.0, -1.0, 0.15)]
    return pc


# ------------------------------------------------------------------ 04 MODULATOR cufflinks
@reg("gv_modulator_cufflinks")
def modulator_cufflinks():
    """The vacuum modulator: a sealed can whose diaphragm feels engine load. Each cufflink face is the can, turned
    and domed, with its rolled seam and the adjusting screw in its centre; behind it the vacuum line runs out as a
    liquid stroke that curls into the toggle."""
    pc = Piece("gv_modulator_cufflinks", "flat")
    Rc = 7.4
    dome = [(Rc - 0.9 - t * (Rc - 3.0), 1.95 + 1.5 * math.sin(t * math.pi / 2) ** 0.8 + 0.16 * math.sin(t * math.pi * 5))
            for t in np.linspace(0, 1, 60)]                                   # the diaphragm's convolutions, turned
    can = lathe([(0, 0), (Rc - 0.8, 0), (Rc - 0.15, 0.35), (Rc, 0.9), (Rc - 0.1, 1.45), (Rc - 0.55, 1.6)] + dome +
                [(2.1, 3.45), (2.1, 3.65), (0, 3.65)])
    can = can - lathe([(Rc - 0.42, 1.18), (Rc + 1, 1.05), (Rc + 1, 1.3)])                       # the rolled seam's lap line
    can = can - lathe([(0, 2.9), (1.32, 2.9), (1.32, 4), (0, 4)])                              # screw bore
    screw = lathe([(0, 2.95), (1.25, 2.95), (1.25, 3.67), (1.45, 3.67), (1.45, 4.2), (1.3, 4.35), (0, 4.35)])
    screw = screw - box(0.35, 3.2, 0.5).translate((0, 0, 4.2))                                # screwdriver slot
    s = sdf.Scene()                                                                            # the vacuum line and toggle
    P = [(0, 0, 0.4), (0, 0, -2.0), (0.8, 0, -4.6), (3.2, 0, -6.6), (6.4, 0, -7.4), (9.0, 0, -7.0)]
    line(s, P, [(0, 1.5), (0.25, 1.05), (0.55, 1.2), (0.8, 1.55), (1.0, 0.5)], k=0.8, n=10)
    Q = [(0.8, 0, -6.9), (-1.4, 0, -7.4), (-4.4, 0, -7.1)]
    line(s, Q, [(0, 1.4), (0.5, 1.2), (1.0, 0.45)], k=0.6, n=10)
    s.cone((0, 0, -0.8), (0, 0, 0.3), 1.0, 3.2, k=0.9)
    stem = sdf_part(s, vox=0.045)
    pc.add("can", can + stem - box(30, 30, 10).translate((0, 0, 5.0 + 0.0)) + can, "antique")
    pc.add("screw", screw, "bright")
    pc.mirror_pair(24.0)
    pc.notes["views"] = [(0.35, -0.9, 1.0), (0.0, -0.02, 1.0), (1.0, -0.3, 0.2), (0.3, -1.0, -0.4)]
    return pc


# ------------------------------------------------------------------ 05 SHIFT VALVE pendant
@reg("gv_shiftvalve_pendant")
def shiftvalve_pendant():
    """The comparator. A bright turned spool hangs in a cage of three liquid lines that wind round it like the
    bore's oil feeds; the lines gather at the top into the bail and at the bottom into a turned seat that holds
    a ruby check ball. Speed pressure from below, spring and throttle from above."""
    pc = Piece("gv_shiftvalve_pendant", "hang")
    s = sdf.Scene()
    zb, zt = 0.0, 30.0
    for k in range(3):
        a0 = 2 * math.pi * k / 3
        P = []
        for t in np.linspace(0, 1, 11):
            z = zb + 2.2 + t * (zt - zb - 2.6)
            R = 1.2 + 3.1 * math.sin(math.pi * t) ** 0.8
            a = a0 + 1.35 * t
            P.append((R * math.cos(a), R * math.sin(a), z))
        line(s, P, [(0, 0.95), (0.3, 0.75), (0.5, 0.62), (0.7, 0.75), (1.0, 0.95)], k=0.7, n=8)
    s.cone((0, 0, zt - 1.2), (0, 0, zt + 0.6), 1.8, 1.25, k=0.8)                              # neck
    P = [(0, 0, zt + 0.2), (0, 0, zt + 1.9)] + [(2.3 * math.sin(a), 0, zt + 4.4 - 2.3 * math.cos(a)) for a in np.linspace(0.5, 2 * math.pi - 0.5, 9)] + [(0, 0, zt + 1.9)]
    line(s, P, [(0, 1.0), (0.3, 0.85), (0.6, 0.75), (1.0, 0.95)], k=0.5, n=12, closed=False)    # bail loop
    s.cone((0, 0, zb + 1.0), (0, 0, zb + 3.2), 2.2, 1.4, k=0.8)                                 # gathers into the seat
    cage = sdf_part(s, vox=0.045)
    cup, cav, zc = ruby_cup(3.969, wall=0.85, base=0.0)
    cup = place(cup, rotx(180))                                                                 # the seat faces down
    cav = place(cav, rotx(180))
    body = (cage + cup.translate((0, 0, 1.6))) - cav.translate((0, 0, 1.6))
    # bore guides for the spool, top and bottom (turned collars inside the cage)
    for zg in (5.0, 26.0):
        body = body + (lathe([(1.25, zg - 0.8), (2.0, zg - 0.8), (2.0, zg + 0.8), (1.25, zg + 0.8)]) +
                       knurl(2.0, zg - 0.8, zg + 0.8, pitch=0.5, depth=0.22, chamfer=0.12)) - cyl(1.25, 1.7, zg - 0.85)
        for k in range(3):                                                                     # three webs to the lines
            a = 2 * math.pi * k / 3 + (0.0 if zg < 10 else 1.35 * 0.88)
            R = 1.2 + 3.1 * math.sin(math.pi * ((zg - 2.2) / (zt - 2.6))) ** 0.8
            web = orient_at(cyl(0.5, max(R - 1.6, 0.4), 0), (1.7 * math.cos(a), 1.7 * math.sin(a), zg), (math.cos(a), math.sin(a), 0))
            body = body + web
    pc.add("body", body, "antique")
    sp, L = spool(1.15, [(2.6, 1.6), (3.6, 1.6), (3.6, 1.6), (2.6, 0)], z0=0, stem=0.62)
    stems = lathe([(0, -2.4), (0.9, -2.4), (0.9, 0.05), (0, 0.05)]) + lathe([(0, L - 0.05), (0.9, L - 0.05), (0.9, L + 2.4), (0, L + 2.4)])
    sp = (sp + stems).translate((0, 0, 15.5 - L / 2))
    pc.add("spool", sp, "bright")
    pc.ball((0, 0, 1.6 - zc), 3.969, "ruby")
    pc.notes["views"] = [(0.45, -1.0, 0.35), (0.0, -1.0, 0.0), (1.0, 0.0, 0.1), (-0.5, 1.0, 0.3)]
    pc.notes["chain"] = "2 mm round belcher chain, 60 cm"
    return pc


# ------------------------------------------------------------------ 06 CHECK BALL drop earrings
@reg("gv_check_ear")
def check_ear():
    """A check ball lets oil pass one way and shuts the other. Each earring is the seat: a small turned and
    knurled cup holding a ruby ball, and below it the drop of oil it let through, a short heavy liquid drip
    cast in one with the cup."""
    pc = Piece("gv_check_ear", "flat")
    cup, cav, zc = ruby_cup(3.969, wall=0.95, base=0.0)
    # the cup faces forward (-Y); the drip hangs from its rim
    s = sdf.Scene()
    P = [(0, 0.4, -1.2), (0.45, 0.7, -4.2), (-0.35, 0.9, -8.0), (0.3, 0.8, -12.2), (0.05, 0.5, -16.0)]
    line(s, P, [(0, 1.55), (0.15, 1.25), (0.4, 1.0), (0.62, 0.85), (0.85, 0.5), (1.0, 0.2)], k=0.8, n=24, kseg=0.08)
    s.cone((0, 0.6, 0.6), (0, 0.6, -1.6), 2.3, 1.2, k=0.8)
    drip = sdf_part(s, vox=0.04)
    R = rotx(90)                                   # cup axis +Z -> -Y (facing the viewer)
    cupw = place(cup, R, (0, 0, 0)); cavw = place(cav, R, (0, 0, 0))
    post = place(lathe([(0, 0), (0.42, 0), (0.42, 10.3), (0, 10.3)]) - lathe([(0.3, 8.6), (0.5, 8.6), (0.5, 9.0), (0.3, 9.0)]), rotx(-90), (0, 0.2, 0))
    body = (cupw + drip + post) - cavw
    pc.add("seat", body, "antique")
    pc.ball((0, -zc, 0), 3.969, "ruby")
    pc.mirror_pair(16.0)
    pc.notes["views"] = [(0.45, -1.0, 0.35), (0.0, -1.0, 0.02), (1.0, -0.2, 0.1), (0.3, -0.6, 1.0)]
    return pc


# ------------------------------------------------------------------ 07 SEPARATOR money clip
@reg("gv_separator_clip")
def separator_clip():
    """The separator plate times every shift with drilled holes. The clip is one liquid line bent back on itself
    like hard brake line: on top it spreads into a wide flat lozenge of silver with three turned orifices set
    flush into it, each drilled a different size, as the plate's holes are; under the bend it narrows into the
    spring leaf that holds the notes."""
    pc = Piece("gv_separator_clip", "flat")
    L = 52.0
    x0, x1 = -L / 2 + 1.0, L / 2 - 4.0
    zt = 4.7
    top = [(x0, 0, zt - 0.3), (-L / 4, 0, zt - 0.05), (0, 0, zt), (L / 4, 0, zt - 0.05), (x1, 0, zt - 0.3)]
    tk = [(0, 2.1), (0.12, 3.9), (0.45, 4.4), (0.8, 4.1), (1.0, 2.6)]
    FT = 3.0
    s = sdf.Scene()
    line(s, top, tk, k=0.5, n=8, flat=FT, normal=(0, 0, 1))
    cz = (zt - 0.3 + 0.35) / 2; rb = (zt - 0.3 - 0.35) / 2
    bend = [(x1 - 1.2 + (rb + 1.2) * math.sin(a), 0, cz + rb * math.cos(a)) for a in np.linspace(0.0, math.pi, 9)]
    bot = [(x1 - 1.2, 0, 0.35), (L / 4, 0, 0.45), (0, 0, 0.6), (-L / 4 + 2, 0, 0.95), (-L / 2 + 9, 0, 1.6)]
    P = bend + bot[1:]
    Pc = curve(P, 8)
    T = np.gradient(Pc, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.cross(T, [0, 1.0, 0]); N /= np.linalg.norm(N, axis=1)[:, None]
    line(s, P, [(0, 2.5), (0.3, 2.3), (0.55, 2.0), (0.85, 1.7), (1.0, 0.95)], k=0.6, n=8, flat=1.7, normal=N)
    clip = sdf_part(s, vox=0.045)
    for x, hole in ((-12.5, 0.6), (-3.0, 1.0), (6.5, 0.8)):
        u = (x - x0) / (x1 - x0)
        r = float(prof(201, tk)[int(round(u * 200))]); zf = zt + r / FT - 0.08       # the lozenge's top face here
        seat = lathe([(0, -0.5), (2.85, -0.5), (2.85, 2), (0, 2)])
        bez = lathe([(0, -0.95), (2.55, -0.95), (2.55, -0.05), (2.35, 0.15), (hole + 0.75, 0.15), (hole + 0.75, 0.0),
                     (hole + 0.3, -0.35), (0, -0.35)])
        clip = (clip - seat.translate((x, 0, zf))) + bez.translate((x, 0, zf))
        clip = clip - cyl(hole, 8, zf - 6)
    pc.add("clip", clip, "antique")
    pc.notes["views"] = [(0.25, -1.0, 0.75), (0.0, -0.02, 1.0), (0.2, -1.0, 0.15), (-1.0, -0.5, 0.5)]
    return pc


# ------------------------------------------------------------------ 08 WORM TRACKS cuff
WR = (29.5, 24.0)          # wrist, inside the cuff: half width (Y) and half depth (Z); wrist axis X


def wrist_pt(phi, x, lift=0.0):
    """point on the wrist oval at angle phi (0 = top, +Z), offset outward by lift"""
    y, z = WR[0] * math.sin(phi), WR[1] * math.cos(phi)
    n = np.array([math.sin(phi) / WR[0], math.cos(phi) / WR[1]]); n /= np.linalg.norm(n)
    return (x, y + lift * n[0], z + lift * n[1])


@reg("gv_wormtrail_cuff")
def wormtrail_cuff():
    """The worm tracks: the channels cast into a valve body, each carrying one signal from valve to valve. The cuff
    is five of them, running round the wrist and gathering three times: at two turned spool bores, and on top at
    a ruby check ball, the focal point. Between the nodes they spread and the wrist shows through."""
    pc = Piece("gv_wormtrail_cuff", "cuff")
    s = sdf.Scene()
    cs = [-1.0, -0.5, 0.0, 0.5, 1.0]
    ph0 = math.radians(148)
    for i, c in enumerate(cs):
        P = []
        for t in np.linspace(-1, 1, 41):
            ph = t * ph0
            g = 0.18 + 0.82 * math.sin(1.5 * ph) ** 2
            e = 1 - abs(t) ** 8                     # the five lines gather into one tip at each end
            x = (c * 10.5 * g + 0.9 * math.sin(3 * ph + i)) * e
            lift = 1.25 + 0.5 * (1 - abs(c)) * (1 - g)
            P.append(wrist_pt(ph, x, lift))
        r_mid = 1.05 + 0.25 * (1 - abs(c))
        line(s, P, [(0, 0.5), (0.08, 0.9), (0.3, r_mid), (0.5, r_mid + 0.2), (0.7, r_mid), (0.92, 0.9), (1.0, 0.5)],
             k=0.55, n=4)
    lines = sdf_part(s, vox=0.05)
    body = lines
    for ph in (-math.radians(60), math.radians(60)):              # turned spool bores across the bundle
        a = np.array(wrist_pt(ph, 0, 2.3)); n = np.array(wrist_pt(ph, 0, 3.3)) - a
        bar = lathe([(0, -5.2), (2.0, -5.2), (2.4, -4.8), (2.4, 4.8), (2.0, 5.2), (0, 5.2)])
        bar = bar - lathe([(0, -6), (1.05, -6), (1.05, 6), (0, 6)])
        for z0 in (-4.6, 3.3):
            bar = (bar - lathe([(2.15, z0), (3, z0), (3, z0 + 1.3), (2.15, z0 + 1.3)])) + (knurl(2.4, z0, z0 + 1.3, pitch=0.55, depth=0.26, chamfer=0.12) - cyl(2.14, 1.3, z0))
        R = roty(90)
        body = body + place(bar, R, tuple(a)) - place(lathe([(0, -6), (1.05, -6), (1.05, 6), (0, 6)]), R, tuple(a))
        sp, L = spool(1.0, [(1.8, 0.9), (2.4, 0.9), (1.8, 0)], stem=0.55)
        sp = place(sp.translate((0, 0, -L / 2)), R, tuple(a))
        pc.add("spool%d" % (0 if ph < 0 else 1), sp, "bright")
    cup, cav, zc = ruby_cup(3.969, wall=1.0, base=0.0)
    top = np.array(wrist_pt(0.0, 0, 1.6))
    body = (body + cup.translate(tuple(top))) - cav.translate(tuple(top))
    pc.parts.insert(0, dict(label="body", solid=body, finish="antique", fixed=True, probe=None, bought=False, layer=False))
    pc.ball((top[0], top[1], top[2] + zc), 3.969, "ruby")
    pc.notes["views"] = [(0.3, -0.25, 1.0), (0.0, -0.02, 1.0), (1.0, -0.2, 0.3), (0.0, -1.0, 0.3)]
    return pc


# ------------------------------------------------------------------ 10 BAND AND SERVO bangle
@reg("gv_servo_bangle")
def servo_bangle():
    """A band wraps a drum; a servo piston pulls one end, an adjusting screw anchors the other. The bangle is one
    liquid band wound one and a quarter times round the wrist, swelling where it would grip, its two ends passing
    side by side: one ends in the knurled adjuster, the other in the servo's turned cap with a ruby."""
    pc = Piece("gv_servo_bangle", "cuff")
    s = sdf.Scene()
    Rb = 32.6; turns = 1.28
    n = 64
    P = []
    for t in np.linspace(0, 1, n):
        ph = -math.pi * turns + 2 * math.pi * turns * t
        x = -3.6 + 7.2 * t
        P.append((x, Rb * math.sin(ph), Rb * math.cos(ph)))
    rk = [(0, 1.25), (0.08, 1.6), (0.3, 2.2), (0.5, 2.85), (0.7, 2.2), (0.92, 1.6), (1.0, 1.25)]
    line(s, P, rk, k=0.5, n=3, flat=1.5, normal=None if False else np.array([[1, 0, 0]] * len(curve(P, 3))))
    band = sdf_part(s, vox=0.055)
    Pc = curve(P, 3)
    def end_frame(i0, i1):
        a = np.array(Pc[i0]); d = np.array(Pc[i0]) - np.array(Pc[i1]); return a, d / np.linalg.norm(d)
    a, d = end_frame(0, 3)
    nut = mlib.hex_nut(5.0, 3.4, 0.0) + lathe([(0, 2.8), (1.8, 2.8), (1.8, 6.4), (1.5, 6.7), (0, 6.7)])
    nut = nut + (knurl(1.82, 3.6, 6.2, pitch=0.5, depth=0.24, chamfer=0.12) - cyl(1.58, 2.6, 3.6))
    body = band + orient_at(nut, a - 1.0 * d, d)
    a, d = end_frame(len(Pc) - 1, len(Pc) - 4)
    cup, cav, zc = ruby_cup(3.175, wall=1.0, base=0.0)
    cap = lathe([(0, -1.6), (2.6, -1.6), (2.9, -1.3), (2.9, 0.1), (0, 0.1)])
    for z0 in (-1.2, -0.55):
        cap = cap - lathe([(2.7, z0), (3, z0), (3, z0 + 0.25), (2.7, z0 + 0.25)])
    body = (body + orient_at(cap + cup, a + 0.6 * d, d)) - orient_at(cav, a + 0.6 * d, d)
    pc.add("band", body, "antique")
    c = a + 0.6 * d + zc * d
    pc.ball(tuple(c), 3.175, "ruby")
    pc.notes["views"] = [(0.35, -0.55, 1.0), (0.0, -0.02, 1.0), (1.0, -0.2, 0.3), (0.0, -1.0, 0.25)]
    return pc


# ------------------------------------------------------------------ 09 MANUAL VALVE link bracelet
def link_scene(A, B, r_end, r_side, r_tail=None):
    """an oval link; r_tail: the -x end's radius (a drop-shaped link, heavy at +x, lighter at -x)"""
    s = sdf.Scene()
    rt = r_end if r_tail is None else r_tail
    P = [(A * math.cos(a), B * math.sin(a), 0.0) for a in np.linspace(0, 2 * math.pi, 25)[:-1]]
    Pc = curve(P + [P[0]], 4)
    def rr(p):
        c = math.cos(math.atan2(p[1] / B, p[0] / A))
        return r_side + ((r_end if c > 0 else rt) - r_side) * abs(c) ** 2
    r = np.array([rr(p) for p in Pc])
    s.stroke(Pc, r, k=0.0, kseg=0.02)
    return s


@reg("gv_detent_bracelet")
def detent_bracelet():
    """The shift lever's only job in the gearbox is to slide the manual valve, held in each position by a spring
    roller dropping into a notch of the detent lever. The bracelet is a graduated chain of heavy liquid links,
    swelling toward the top of the wrist like a line under pressure, each wearing a crimped turned ferrule like a hose fitting; it closes on a turned toggle: the bar is the manual valve's spool, the ring is the
    detent lever bent round, its six notches for P, R, N, D, 2 and 1 inside."""
    pc = Piece("gv_detent_bracelet", "flat")
    A, B, r_end, r_side = 6.6, 3.7, 1.55, 1.1
    p = 9.1
    lk = sdf_part(link_scene(A, B, r_end, r_side, r_tail=1.25), vox=0.045)
    # each link wears a turned ferrule on one side, crimped on like a hydraulic hose fitting: three pressed grooves
    fl = 3.4
    fer = lathe([(0, -fl / 2), (1.45, -fl / 2), (1.75, -fl / 2 + 0.3), (1.75, fl / 2 - 0.3), (1.45, fl / 2), (0, fl / 2)])
    for zc in (-0.85, 0.0, 0.85):
        fer = fer - lathe([(1.5, zc - 0.18), (2.2, zc - 0.18), (2.2, zc + 0.18), (1.5, zc + 0.18)])
    lk = lk + place(fer, roty(90), (0, B, 0))
    n = 15
    Rarc = 60.0
    # the chain is graduated like a line of oil under pressure: the links swell toward the top of the wrist and
    # taper toward the clasp
    sc = [0.8 + 0.4 * math.sin(math.pi * i / (n - 1)) ** 1.3 for i in range(n)]
    X = [0.0]
    for i in range(n - 1):
        X.append(X[-1] + p / (2 * A) * A * (sc[i] + sc[i + 1]))
    X = [x - (X[0] + X[-1]) / 2 for x in X]
    def T(i, solid):          # lay the chain on a gentle curve, as it lies on a table
        a = X[i] / Rarc
        return solid.rotate((0, 0, math.degrees(a))).translate((Rarc * math.sin(a), Rarc * (1 - math.cos(a)), 0))
    for i in range(n):
        L = lk.scale(sc[i])
        L = L if i % 2 == 0 else L.rotate((90, 0, 0))
        L = L if i % 4 < 2 else L.rotate((0, 0, 180))           # alternate the heavy end
        pc.add("link%02d" % i, T(i, L), "antique")
    # the detent ring (toggle ring): an eye through the first link, a short stalk, the ring with six notches inside
    ae, be, re_ = 3.3, 3.5, 1.15
    eye = sdf_part(link_scene(ae, be, re_, 1.0), vox=0.045).rotate((90, 0, 0))
    xe = -A * sc[0] + (r_end * sc[0] + re_ + 0.6) - ae
    Rr, rw = 8.2, 1.7
    s = sdf.Scene()
    P = [(Rr * math.cos(a), Rr * math.sin(a), 0.0) for a in np.linspace(0, 2 * math.pi, 49)[:-1]]
    Pc = curve(P + [P[0]], 4)
    s.stroke(Pc, np.full(len(Pc), rw), k=0.0, kseg=0.02)
    s.cone((Rr + 0.6, 0, 0), (Rr + 3.6, 0, 0), 1.9, 1.3, k=0.6)              # the stalk toward the eye
    ring = sdf_part(s, vox=0.045)
    for k in range(6):                                                       # six notches inside: P R N D 2 1
        a = math.radians(180 - 50 + 20 * k)
        ring = ring - M.sphere(0.95, 48).scale((1, 1, 2.2)).translate(((Rr - rw) * math.cos(a), (Rr - rw) * math.sin(a), 0))
    xr = xe - ae - (Rr + 3.6)
    pc.add("detent_ring", T(0, eye.translate((xe, 0, 0)) + ring.translate((xr, 0, 0))), "antique")
    # toggle bar: the spool, on an eye through the last link
    sp, L = spool(1.55, [(2.4, 1.2), (3.2, 1.2), (3.2, 1.2), (2.4, 0)], stem=0.95)
    sp = sp.translate((0, 0, -L / 2))
    sp = sp + (knurl(1.56, -L / 2 + 0.2, -L / 2 + 2.2, pitch=0.5, depth=0.22, chamfer=0.12) - cyl(1.3, 2.0, -L / 2 + 0.2)) + \
         (knurl(1.56, L / 2 - 2.2, L / 2 - 0.2, pitch=0.5, depth=0.22, chamfer=0.12) - cyl(1.3, 2.0, L / 2 - 2.2))
    xl = 0.0
    eye2 = sdf_part(link_scene(ae, be, re_, 1.0), vox=0.045)
    eye2 = eye2.rotate((90, 0, 0)) if (n - 1) % 2 == 0 else eye2
    xe2 = xl + A * sc[-1] - (r_end * sc[-1] + re_ + 0.6) + ae
    s = sdf.Scene()
    s.cone((xe2 + ae, 0, 0), (xe2 + ae + 3.6, 0, 0), 1.3, 1.6, k=0.6)
    stalk = sdf_part(s, vox=0.045)
    bar = place(sp, rotx(90), (xe2 + ae + 3.6 + 1.2, 0, 0))
    pc.add("toggle", T(n - 1, eye2.translate((xe2, 0, 0)) + stalk + bar), "antique")
    pc.notes["views"] = [(0.2, -0.6, 1.0), (0.0, -0.02, 1.0), (0.2, -1.0, 0.25), (-1.0, -0.4, 0.6)]
    pc.notes["length"] = "about 19 cm closed"
    return pc


# ------------------------------------------------------------------ 11 CLUTCH PACK stacking rings
@reg("gv_clutch_stack")
def clutch_stack():
    """A clutch pack: steel plates lugged on the outside, friction plates splined on the inside, squeezed together
    by oil. Three rings worn as one stack: a liquid steel band with its six lugs milled in as scallops, a crisp
    turned friction ring with a knurled face, and a crowned ring drilled with twelve countersunk orifices."""
    pc = Piece("gv_clutch_stack", "ring")
    ri = FINGER
    def band(y0, keyfn, rfn, flatn=1.0, nseg=72):
        s = sdf.Scene()
        P, r = [], []
        for a in np.linspace(0, 2 * math.pi, nseg + 1):
            R, y = keyfn(a)
            P.append((R * math.sin(a), y0 + y, R * math.cos(a))); r.append(rfn(a))
        s.stroke(np.array(P), np.array(r), k=0.0, kseg=0.03, flat=flatn, normals=np.tile([0, 1.0, 0], (len(P), 1)))
        return sdf_part(s, vox=0.04)
    bore = lambda y0, w: place(lathe([(0, -w), (ri + 0.25, -w), (ri, -w + 0.6), (ri, w - 0.6), (ri + 0.25, w), (0, w)]), rotx(-90), (0, y0, 0))
    # steel: an even liquid band, its six lugs milled into it as clean scallops
    st = band(-3.3, lambda a: (ri + 1.05, 0.0), lambda a: 1.05, flatn=1.15)
    for k in range(6):
        a = 2 * math.pi * k / 6
        sc = place(cyl(0.62, 6, -3), rotx(-90), (0, 0, 0)).translate(((ri + 2.1 + 0.2) * math.sin(a), -3.3, (ri + 2.1 + 0.2) * math.cos(a)))
        st = st - sc
    pc.add("steel", st - bore(-3.3, 3), "antique")
    # friction: turned, knurled face band between two bright lands
    w = 2.6; y0 = 0.15
    fr = lathe([(ri, -w / 2), (ri + 1.3, -w / 2), (ri + 1.55, -w / 2 + 0.25), (ri + 1.55, w / 2 - 0.25), (ri + 1.3, w / 2), (ri, w / 2)])
    fr = (fr - lathe([(ri + 1.3, -0.75), (ri + 2, -0.75), (ri + 2, 0.75), (ri + 1.3, 0.75)])) + \
         (knurl(ri + 1.56, -0.75, 0.75, pitch=0.6, depth=0.26, chamfer=0.1) - cyl(ri + 1.28, 1.5, -0.75))
    fr = fr - cyl(ri, 4, -2)
    pc.add("friction", place(fr, rotx(-90), (0, y0, 0)), "antique")
    # orifice ring: a turned crowned band drilled with twelve countersunk orifices, the separator plate's holes
    hw = 1.1
    prof_ = [(ri, -hw), (ri + 0.9, -hw)] + [(ri + 0.9 + 0.6 * math.cos(t), hw * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 17)[1:-1]] + [(ri + 0.9, hw), (ri, hw)]
    orr = lathe(prof_)
    tool = lathe([(0, -0.75), (0.4, -0.75), (0.4, -0.35), (0.92, 0.17), (0.92, 1.0), (0, 1.0)])
    tool = place(tool, roty(90), (ri + 1.5, 0, 0))
    for k in range(12):
        orr = orr - tool.rotate((0, 0, 30 * k + 15))
    orr = orr - cyl(ri, 4, -2)
    pc.add("orifice", place(orr, rotx(-90), (0, 3.25, 0)), "antique")
    pc.notes["views"] = [(0.6, -1.0, 0.75), (0.0, -1.0, 0.05), (1.0, 0.0, 0.18), (0.3, -0.4, 1.0)]
    pc.notes["set"] = "three rings worn as one stack"
    return pc


# ------------------------------------------------------------------ 12 PLANETARY belt buckle
@reg("gv_planetary_buckle")
def planetary_buckle():
    """A planetary gearset: sun, three planets on a carrier, a ring gear toothed inside. Every clutch and band in the
    gearbox exists to hold one of these still. The buckle is a working set: the ring gear is the frame, knurled
    outside; the carrier is a dished plate behind; the sun and planets, crossed out like watch wheels, really turn
    on its posts."""
    pc = Piece("gv_planetary_buckle", "flat")
    m_, zs_, zp_ = 0.8, 15, 15
    zr_ = zs_ + 2 * zp_
    rp_r = zr_ * m_ / 2; T = 4.4
    Ro = rp_r + 4.6
    ringg = lathe([(rp_r - 0.6, 0), (Ro - 0.45, 0), (Ro, 0.45), (Ro, T - 0.45), (Ro - 0.45, T), (rp_r - 0.6, T)])
    pa = [2 * math.pi * k / 3 + math.pi / 2 for k in range(3)]
    a_c = (zs_ + zp_) * m_ / 2
    pos = [(a_c * math.cos(a), a_c * math.sin(a)) for a in pa]
    sun2 = mlib.involute_gear2(zs_, m_); pl2 = mlib.involute_gear2(zp_, m_)
    phases = [min(((sun2 ^ pl2.rotate(t).translate(xy)).area(), t) for t in np.linspace(0, 360.0 / zp_, 121)[:-1])[1] for xy in pos]
    # the ring's teeth are generated, as a gear shaper cuts them: sweep planet 0 round its orbit, spinning as it
    # would in mesh, and cut everything it passes through (plus 0.06 mm running clearance)
    th0 = math.degrees(pa[0]); sweep = []
    for th in np.linspace(0, 360, 721)[:-1]:
        spin = phases[0] + (th - th0) * (1 - zr_ / zp_)
        sweep.append(pl2.rotate(spin).translate((a_c * math.cos(math.radians(th)), a_c * math.sin(math.radians(th)))))
    sp2 = CS.batch_boolean(sweep, m3.OpType.Add).offset(0.06, m3.JoinType.Round, 2, 24)
    ringg = ringg - extrude(sp2, T + 0.2, -0.1)
    kn = knurl(Ro + 0.01, 0.75, T - 0.75, pitch=0.7, depth=0.32)
    ringg = ringg - lathe([(rp_r + 2.0, T - 0.35), (rp_r + 2.55, T - 0.35), (rp_r + 2.75, T + 0.1), (rp_r + 1.8, T + 0.1)])   # a turned groove on the face
    ringg = (ringg - lathe([(Ro - 0.33, 0.75), (Ro + 1, 0.75), (Ro + 1, T - 0.75), (Ro - 0.33, T - 0.75)])) + (kn - cyl(Ro - 0.35, T - 1.5, 0.75))
    # the carrier: a dished plate behind the gears, closing the frame, so the wheels sit on a quiet dark ground;
    # its back swells into a shallow dome toward the belt
    bk = [(0, -3.4)] + [(rr, -2.3 - 1.1 * (1 - (rr / (rp_r + 1.8)) ** 2)) for rr in np.linspace(0.5, rp_r + 1.8, 12)][1:] + [(rp_r + 1.8, 0.4), (rp_r + 1.1, 0.4)] + \
         [(rr, -1.2 - (0.17 if i % 2 else 0.0)) for i, rr in enumerate(np.arange(rp_r + 1.1, 0.3, -0.24))] + [(0, -1.2)]
    # its face is turned in fine V-grooves, which the antique fills, so the polished wheels stand on a grey field
    carrier = lathe(bk)
    frame = ringg + carrier
    # posts for the planets and the sun, on the carrier
    for (x, y) in pos + [(0, 0)]:
        post = lathe([(0, -1.6), (0.9, -1.6), (0.9, T - 0.4), (1.25, T - 0.4), (1.25, T + 0.25), (1.0, T + 0.5), (0, T + 0.5)])
        frame = frame + post.translate((x, y, 0))
    # belt bar and hook behind
    s = sdf.Scene()
    line(s, [(-Ro + 3.5, -10, -0.5), (-Ro + 3.0, -10, -4.6), (0, -10.6, -5.6), (Ro - 3.0, -10, -4.6), (Ro - 3.5, -10, -0.5)],
         [(0, 1.6), (0.2, 1.25), (0.5, 1.15), (0.8, 1.25), (1, 1.6)], k=0.6, n=8)
    line(s, [(0, Ro - 1.3, 0.3), (0, Ro - 1.6, -3.0), (0, Ro - 3.8, -5.0), (0, Ro - 6.4, -4.4)], [(0, 1.9), (0.6, 1.4), (1.0, 0.7)], k=0.6, n=8)
    back = sdf_part(s, vox=0.05) - box(80, 80, 20).translate((0, 0, 10 + 0.4))
    frame = frame + back
    pc.add("frame", frame, "antique")
    # gears: bright, turned and cut, free on the posts
    # each wheel is crossed out like a watch train's: five curved spokes between a turned hub and the rim,
    # so the dark carrier shows through and the gears read light
    def windows(z):
        r_root = z * m_ / 2 - 1.25 * m_
        r_in, r_out = 2.05, r_root - 0.85
        ann = mlib.circle2(r_out) - mlib.circle2(r_in)
        sp = []
        for k in range(5):
            pts = []
            for t in np.linspace(0, 1, 9):
                r = r_in - 0.3 + (r_out - r_in + 0.6) * t
                th = math.radians(72 * k) + 0.55 * t * t
                pts.append((r * math.cos(th), r * math.sin(th)))
            sp.append(mlib.path2(pts, 0.36 + 0.12 * (1 - t)))
        w = ann - CS.batch_boolean(sp, m3.OpType.Add)
        return w.offset(-0.3, m3.JoinType.Round, 2, 24).offset(0.3, m3.JoinType.Round, 2, 24)
    def gear(z, bore_r, phase):
        g = extrude(mlib.involute_gear2(z, m_), T - 0.6, 0.1) - cyl(bore_r, T + 1, -0.5)
        g = g - extrude(windows(z), T + 1, -0.5)
        for zz in (0.1, T - 0.5):
            g = g - (lathe([(bore_r, zz - 0.01), (bore_r + 0.9, zz - 0.01), (bore_r + 0.9, zz + 0.12), (bore_r, zz + 0.12)]) if zz > 0.2 else box(0.01, 0.01, 0.01).translate((50, 0, 0)))
        return g.rotate((0, 0, phase))
    pc.add("sun", gear(zs_, 1.05, 0.0), "bright")
    for i, ((x, y), ph) in enumerate(zip(pos, phases)):
        pc.add("planet%d" % i, gear(zp_, 1.05, 0.0).rotate((0, 0, ph)).translate((x, y, 0)), "bright")

    pc.notes["views"] = [(0.25, -0.5, 1.0), (0.0, -0.02, 1.0), (1.0, -0.3, 0.3), (0.0, 1.0, -0.6)]
    pc.notes["belt"] = "takes a 38 mm (1.5 in) belt"
    return pc


# ------------------------------------------------------------------ 02 PRESSURE REGULATOR collar
@reg("gv_regulator_collar")
def regulator_collar():
    """The pressure regulator: a spool pushed one way by a spring and the other by line pressure, bleeding off the
    excess so the whole gearbox runs at one pressure. The collar is one heavy liquid band round the neck, widest at
    the front, with a thin feedback line looping back from each end, and it ends in two turned bores that face each other across the opening: one holds the bright spool, the
    other the spring that balances it. Put it on through the gap, like a torc."""
    pc = Piece("gv_regulator_collar", "flat")
    a, b = 66.0, 58.0                        # neck, centreline half-axes (X across, Y front-back); front = -Y
    gap = math.radians(19)
    s = sdf.Scene()
    P = []
    for t in np.linspace(0, 1, 41):
        ph = gap + t * (2 * math.pi - 2 * gap)             # 0 = front (-Y)
        P.append((a * math.sin(ph), -b * math.cos(ph), 2.2 * math.sin(ph * 2) * 0.0))
    line(s, P, [(0, 3.55), (0.12, 3.25), (0.3, 2.6), (0.5, 2.35), (0.7, 2.6), (0.88, 3.25), (1.0, 3.55)], k=0.5, n=3,
         flat=1.55, normal=(0, 0, 1))
    # the feedback lines: the regulator senses its own output. From each bore a thin line leaves along the inside
    # of the collar and runs back into it a hand's width round, like the signal line fed back to the spool's end
    for sg in (1, -1):
        Q = []
        for t in np.linspace(0, 1, 15):
            ph = gap + 0.02 + t * 0.78
            ph = ph if sg > 0 else 2 * math.pi - ph
            d = 2.6 + 3.2 * math.sin(math.pi * t) ** 0.8
            x, y = a * math.sin(ph), -b * math.cos(ph)
            nx, ny = math.sin(ph) / a, -math.cos(ph) / b; nn = math.hypot(nx, ny)
            Q.append((x - d * nx / nn, y - d * ny / nn, 0.35 * math.sin(math.pi * t)))
        line(s, Q, [(0, 1.15), (0.3, 1.0), (0.7, 0.85), (1.0, 0.8)], k=0.6, n=4)
    neck = sdf_part(s, vox=0.06)
    Pc = curve(P, 3)
    body = neck
    housings = []
    for end, (i0, i1) in enumerate(((0, 3), (len(Pc) - 1, len(Pc) - 4))):
        p0 = np.array(Pc[i0]); d = p0 - np.array(Pc[i1]); d /= np.linalg.norm(d)
        H = lathe([(2.0, -1.0), (3.4, -1.0), (3.8, -0.6), (3.8, 7.4), (3.4, 7.8), (2.0, 7.8)])
        H = (H - lathe([(3.5, 1.6), (4, 1.6), (4, 5.2), (3.5, 5.2)])) + (knurl(3.81, 1.6, 5.2, pitch=0.6, depth=0.28) - cyl(3.48, 3.6, 1.6))
        H = H + lathe([(0, -1.0), (2.05, -1.0), (2.05, 0.4), (0, 0.4)])          # the bore's floor
        body = body + orient_at(H, p0 - 0.6 * d, d) - orient_at(cyl(2.0, 8.0, 0.4), p0 - 0.6 * d, d)
        housings.append((p0 - 0.6 * d, d))
    pc.add("collar", body, "antique")
    (pA, dA), (pB, dB) = housings
    sp, L = spool(1.95, [(2.4, 1.3), (3.0, 1.3), (2.4, 0)], stem=1.05)
    pc.add("spool", orient_at(sp, pA + 0.45 * dA, dA), "bright")
    spr = mlib.helix_spring(1.45, 0.45, 1.25, 0.45, 9.6)
    cap = lathe([(0, 9.2), (1.95, 9.2), (1.95, 10.6), (1.7, 10.9), (0, 10.9)])
    pc.add("spring", orient_at(spr + cap, pB + 0.45 * dB, dB), "steel", bought=True)
    pc.notes["views"] = [(0.2, -1.0, 0.8), (0.0, -0.02, 1.0), (1.0, -0.4, 0.3), (0.0, -1.0, 0.15)]
    pc.notes["fit"] = "inside 128 x 112 mm; opens 40 mm at the front"
    return pc
