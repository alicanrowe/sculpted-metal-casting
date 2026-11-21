"""GOVERNOR: twelve pieces, one per working part of an automatic transmission's hydraulic computer.
Each builder returns an mlib.Piece. Units mm. Rings: finger axis = Y, top of the finger = +Z.
Finishes: bright (polished sterling), black (oxidised sterling), satin (brushed), steel."""
import math
import numpy as np
import mlib
from mlib import M, CS, Piece, cyl, lathe, knurl, tube, union, cut, extrude, rotx, roty, rotz, place, orient, box
import manifold3d as m3

FINGER = 19.8 / 2          # US 10 men's ring, 19.8 mm inside diameter
PIECES = {}


def reg(name):
    def d(fn):
        PIECES[name] = fn; return fn
    return d


def ring_axis(s):
    """Parts are built with Z as the finger axis; turn them so the finger runs along Y."""
    return place(s, rotx(-90))


# ------------------------------------------------------------------ 01 GEROTOR ring
def gerotor2(N=7, Rp=13.2, rp=1.5, e=0.6, steps=420):
    """Outer rotor (N inward lobes) and the conjugate inner rotor (N-1 lobes) in 2D. The outer rotor is
    centred at (e, 0), the inner at the origin. Inner rotor = the disc minus every place the outer lobes
    sweep through as the pair turns (exact conjugate envelope)."""
    pins = [(Rp * math.cos(2 * math.pi * k / N), Rp * math.sin(2 * math.pi * k / N)) for k in range(N)]
    sweep = []
    for i in range(steps):
        th = 2 * math.pi * i / steps
        phi = th * (N - 1) / N
        for px, py in pins:
            x = e + px * math.cos(phi) - py * math.sin(phi); y = px * math.sin(phi) + py * math.cos(phi)
            c, s = math.cos(-th), math.sin(-th)
            sweep.append(mlib.circle2(rp, (x * c - y * s, x * s + y * c), 40))
    sw = CS.batch_boolean(sweep, m3.OpType.Add)
    inner = mlib.circle2(Rp + rp + e, (0, 0), 240) - sw
    inner = max(inner.decompose(), key=lambda c: c.area() if (c ^ mlib.circle2(0.5)).area() > 0 else 0)   # the rotor, not the leftover ring
    # outer rotor inside outline: lobes are the pins, the spaces between them a clearance arc at Rp + 0.15
    outer_in = mlib.circle2(Rp + 0.15, (0, 0), 240) - CS.batch_boolean([mlib.circle2(rp, p, 64) for p in pins], m3.OpType.Add)
    return inner, outer_in.translate((e, 0))


@reg("gv_gerotor_ring")
def gerotor_ring():
    """The pump. A gerotor: an inner rotor with five lobes turns inside an outer rotor with six, offset by
    the eccentricity e; the crescent between them opens on one side (suction) and closes on the other
    (pressure). Cut from one sterling bar by wire EDM, left joined where the lobes mesh (palm side); the
    inner rotor is oxidised black, the outer rotor bright with a diamond-knurled rim."""
    pc = Piece("gv_gerotor_ring", "ring")
    W = 7.4
    N, Rp, rp, e = 6, 13.35, 1.5, 0.85
    inner2, cavity2 = gerotor2(N=N, Rp=Rp, rp=rp, e=e)
    Ro = 14.9
    outer2 = mlib.circle2(Ro, (e, 0), 360) - cavity2
    inner2 = inner2.offset(-0.3, m3.JoinType.Round, 2, 48) - mlib.circle2(FINGER, (0, 0), 240)   # 0.3 mm EDM kerf
    # the mesh point (where the lobes touch, opposite the crescent) is left uncut: a short web joins the rotors
    bridge = (mlib.poly([(0, 0)] + [(20 * math.cos(math.radians(a)), 20 * math.sin(math.radians(a))) for a in np.linspace(172, 188, 5)])
              ^ mlib.circle2(Rp + 0.1, (0, 0), 240)) - mlib.circle2(FINGER + 0.4, (0, 0), 240) - outer2
    in_slab = mlib.chamfered_plate(inner2 + bridge, W - 0.4, c=0.25, z0=-(W - 0.4) / 2)
    out_slab = mlib.chamfered_plate(outer2, W, c=0.3, z0=-W / 2)
    kn = knurl(Ro + 0.02, -1.9, 1.9, pitch=0.75, depth=0.42).translate((e, 0, 0))
    groove = lathe([(Ro - 0.5, -1.95), (Ro + 1, -1.95), (Ro + 1, 1.95), (Ro - 0.5, 1.95)]).translate((e, 0, 0))
    out_slab = (out_slab - groove) + (kn - cyl(Ro - 0.6, 4.2, -2.1).translate((e, 0, 0)))
    for z in (-2.9, 2.9):
        out_slab = out_slab - lathe([(Ro - 0.18, z), (Ro + 1, z - 0.3), (Ro + 1, z + 0.3)]).translate((e, 0, 0))
    in_slab = in_slab - lathe([(0, -W / 2 - 1), (FINGER + 0.9, -W / 2 - 1), (FINGER, -W / 2 + 0.5), (FINGER, W / 2 - 0.5),
                               (FINGER + 0.9, W / 2 + 1), (0, W / 2 + 1)])
    # the crescent (widest gap) sits at +x before the turn; rotate it to the top of the finger, mesh web to the palm
    R = rotx(-90) @ rotz(90)
    pc.add("outer_rotor", place(out_slab, R), "bright")
    pc.add("inner_rotor", place(in_slab, R), "black")
    pc.notes["one_body"] = "one sterling body cut by wire EDM; the inner rotor is selectively oxidised"
    pc.notes["views"] = [(0.38, -1.0, 0.42), (0.0, -1.0, 0.0), (1.0, -0.15, 0.3), (0.4, -0.5, 1.0)]
    return pc


# ------------------------------------------------------------------ 06 CHECK BALL ear studs
@reg("gv_check_ear")
def check_ear():
    """A check ball: a ball on a seat lets fluid pass one way and shuts the other. Each stud is a small
    hex-bodied check valve fitting: a 5/32 in synthetic ruby ball stands proud on a 90 deg seat, held by a
    swaged lip like a roller-ball tip, with a cross-drilled vent port in the hex. Post and butterfly behind."""
    pc = Piece("gv_check_ear", "flat")
    D = 3.969; rb = D / 2
    AF, Hh = 6.4, 2.6                               # hex body: 6.4 mm across flats
    zc = Hh + 1.75                                  # ball centre, above the hex in the turned nose
    rc, zt = rb * math.cos(math.radians(45)), zc - rb * math.sin(math.radians(45))
    zs = lambda r: zt - (rc - r) - 0.035           # 90 deg seat, 0.035 below tangent so the faceted cone clears the ball
    rlip = rb * 0.86                                # swaged lip: smaller than the ball, so it cannot leave
    zl = zc + math.sqrt(rb ** 2 - rlip ** 2)        # the lip touches the ball here
    # build the nose as solid minus a cavity, so the lip profile follows the ball exactly
    nose = lathe([(0, Hh - 0.05), (rb + 0.95, Hh - 0.05), (rb + 0.95, zc - 0.25), (rlip + 0.45, zl + 0.3), (0, zl + 0.3)])
    cav = lathe([(0, zs(0.9) - 0.6), (0.9, zs(0.9) - 0.6), (0.9, zs(0.9)), (rb + 0.03, zs(rb + 0.03)),
                 (rb + 0.03, zc), (math.sqrt(max(rb ** 2 - 0.0, 0)) , zc + 0.0)] +
                [(math.sqrt(rb ** 2 - (z - zc) ** 2) + 0.035, z) for z in np.linspace(zc + 0.1, zl - 0.01, 8)] +
                [(rlip, zl + 0.03), (rlip, zl + 1.0), (0, zl + 1.0)])
    hexb = mlib.hex_nut(AF, Hh, 0.0)
    vent = mlib.drill_x(0.5, -4, 4, 0, Hh * 0.5)
    tail = lathe([(0, -0.6), (1.6, -0.6), (1.9, -0.3), (1.9, 0.05), (0, 0.05)])
    post = lathe([(0, -10.8), (0.42, -10.8), (0.42, -0.5), (0, -0.5)])
    post = post - lathe([(0.3, -9.4), (0.5, -9.4), (0.5, -9.0), (0.3, -9.0)])     # butterfly notch
    body = union([hexb, nose, tail, post]) - cav - vent - cyl(0.5, Hh + 0.3, 0.5)    # vent reaches the seat
    pc.add("fitting", body, "bright")
    pc.ball((0, 0, zc), D, "ruby")
    pc.mirror_pair(13.0)
    pc.notes["views"] = [(0.5, -1.0, 0.7), (0.0, -0.02, 1.0), (1.0, -0.3, 0.15), (0.2, -1.0, -0.3)]
    return pc


# ------------------------------------------------------------------ 02 REGULATOR tie bar
@reg("gv_regulator_tiebar")
def regulator_tiebar():
    """The pressure regulator: a spool held against line pressure by a coil spring; when pressure beats the
    spring the spool slides and opens the exhaust, so line pressure stays where the spring sets it.
    Tie bar: a milled bar with the bore, the spool and the spring showing through a window; plug and roll
    pin at the end; the clip leaf behind is folded from the same bar."""
    pc = Piece("gv_regulator_tiebar", "flat")
    Lx, Dy, Hz = 52.0, 5.0, 6.4
    zc = Hz / 2; rb = 1.85
    body, edges = mlib.edge_split(mlib.rounded_rect2(Lx, Dy, 0.7), Hz, c=0.4)
    bore = mlib.drill_x(rb, -21.0, 27.0, 0, zc)
    window = extrude(mlib.slot2((-16.5, 0), (15.5, 0), 1.2), 10, 0).transform(np.hstack([rotx(90), [[0], [0], [0]]]).tolist())
    window = window.translate((0, -0.0, zc))              # milled through the front face to the bore
    window = window ^ box(60, 3.0, 10).translate((0, -2.5, zc))
    ports = [cyl(0.6, 4, zc).translate((x, 0, 0)) for x in (-12.0, -4.5, 7.0)]           # exhaust ports drilled from the top
    pinhole = cyl(0.42, Hz + 2, -1).translate((23.6, 0, 0))
    body = cut(body, [bore, window, pinhole] + ports); edges = cut(edges, [bore, window, pinhole] + ports)
    # clip leaf folded back from the left end
    leaf = mlib.chamfered_plate(mlib.rounded_rect2(44.0, 0.9, 0.3), 4.8, c=0.15).translate((-4.0, 3.65, 0.8))
    fold = mlib.chamfered_plate(mlib.rounded_rect2(2.4, 2.6, 0.6), 4.8, c=0.2).translate((-24.8, 3.0, 0.8))
    body = union([body, leaf, fold]) - edges
    pc.add("bar", body, "black")
    pc.add("bar_edges", edges, "bright", layer=True)
    # spool: three lands, two grooves, a stem to the spring
    prof = [(0, -20.0), (1.6, -20.0), (1.8, -19.8), (1.8, -16.2), (1.6, -16.0), (1.05, -16.0), (1.05, -9.0), (1.6, -9.0),
            (1.8, -8.8), (1.8, -3.2), (1.6, -3.0), (1.05, -3.0), (1.05, 2.0), (1.6, 2.0), (1.8, 2.2), (1.8, 6.8), (1.6, 7.0),
            (0.8, 7.0), (0.8, 10.0), (0, 10.0)]
    spool = place(lathe(prof), roty(90)).translate((0, 0, zc))
    pc.add("spool", spool, "bright")
    spring = place(mlib.helix_spring(1.2, 0.32, 0.95, 7.05, 21.9), roty(90)).translate((0, 0, zc))
    pc.add("spring", spring, "steel", bought=True)
    plug = place(lathe([(0, 22.0), (1.8, 22.0), (1.8, 26.0), (2.1, 26.0), (2.3, 26.2), (2.3, 26.9), (2.1, 27.1), (0, 27.1)]), roty(90)).translate((0, 0, zc))
    plug = plug - cyl(0.42, Hz + 2, -1).translate((23.6, 0, 0))
    pc.add("plug", plug, "bright")
    pc.add("roll_pin", cyl(0.4, Hz - 0.2, 0.1).translate((23.6, 0, 0)), "steel")
    pc.notes["views"] = [(0.25, -1.0, 0.45), (0.0, -1.0, 0.02), (0.6, -0.5, 1.0), (1.0, 0.6, 0.3)]
    return pc


# ------------------------------------------------------------------ 03 GOVERNOR signet
@reg("gv_governor_signet")
def governor_signet():
    """The governor: spun by the output shaft, two flyweights swing out with road speed and push a small
    spool, so the faster the car the higher the governor pressure. Signet: the head is the governor's
    driven gear; in its milled pocket two oxidised flyweights pivot on steel pins either side of the spool."""
    pc = Piece("gv_governor_signet", "ring")
    band = place(lathe([(FINGER, -6), (FINGER + 2.0, -6), (FINGER + 2.0, 6), (FINGER, 6)]), rotx(-90))   # finger along Y
    zs = np.linspace(-14, 14, 40)
    w = lambda z: 2.2 + 3.4 * (1 / (1 + math.exp(-(z - 4.0) / 2.4)))       # half width: narrow at the palm
    side = mlib.poly([(w(z), z) for z in zs] + [(-w(z), z) for z in zs[::-1]])
    sideS = mlib.place(extrude(side, 40, -20), np.array([[0, 0, 1.0], [1, 0, 0], [0, 1, 0]]))
    shank = band ^ sideS
    z0 = FINGER + 1.3
    saddle = M.batch_hull([cyl(6.8, 0.4, z0), box(17.0, 5.6, 0.4).translate((0, 0, FINGER * 0.62))])
    saddle = saddle ^ sideS.scale((1, 1.0, 1))
    shank = union([shank, saddle]) - place(cyl(FINGER, 20, -10), rotx(-90))
    # head: turned collar + gear teeth (the governor's driven gear) + pocket
    collar = lathe([(0, z0), (7.6, z0), (7.9, z0 + 0.3), (7.9, z0 + 1.6), (0, z0 + 1.6)])
    kn = knurl(7.9, z0 + 0.25, z0 + 1.6, pitch=0.6, depth=0.3)
    gear = extrude(mlib.involute_gear2(30, 0.55), 1.7, z0 + 1.6)
    gear = gear ^ lathe([(0, z0 + 1.6), (8.85, z0 + 1.6), (8.85, z0 + 3.0), (8.55, z0 + 3.3), (0, z0 + 3.3)])
    head = union([collar - cyl(8, 2, z0 + 0.3).translate((0, 0, 0)) + kn ^ cyl(7.9, 1.4, z0 + 0.2), collar ^ cyl(7.6, 0.3, z0),
                  gear])
    head = union([head, cyl(7.0, 1.4, z0 + 0.2)])
    ztop = z0 + 3.3
    pocket = cyl(6.2, 1.25, ztop - 1.2)
    trough = mlib.drill_x(0.92, -5.6, 5.6, 0, ztop - 1.2)                                         # the spool's bore, half exposed
    ring = union([shank, head])
    ring = cut(ring, [pocket, trough])
    ring = ring - place(cyl(FINGER, 20, -10), rotx(-90))
    # flyweights: C-shaped weights hugging the pocket wall, pivot boss at one end, oxidised
    floor = ztop - 1.2
    fw = []
    pins = []
    for sgn in (1, -1):
        wedge = mlib.poly([(0, 0)] + [(9 * math.cos(math.radians(a)), 9 * math.sin(math.radians(a))) for a in np.linspace(22, 158, 12)])
        if sgn < 0: wedge = wedge.mirror((0, 1))
        arc = (mlib.circle2(6.0) - mlib.circle2(4.5)) ^ wedge
        pv = (4.95 * math.cos(math.radians(30)), 4.95 * math.sin(math.radians(30)) * sgn)
        boss = mlib.circle2(1.0, pv, 48)
        toe = mlib.slot2((4.2 * math.cos(math.radians(150)), 4.2 * math.sin(math.radians(150)) * sgn), (-1.6, 1.75 * sgn), 0.55)
        shape = (arc + boss + toe).offset(0, m3.JoinType.Round) - mlib.circle2(0.45, pv, 32)
        shape = shape - mlib.rect2(14, 2.0, (0, 0))          # clear of the spool trough
        shape = max(shape.decompose(), key=lambda c: c.area())
        fw.append(mlib.chamfered_plate(shape, 0.95, c=0.12, z0=floor + 0.06))
        pins.append(cyl(0.4, 1.9, floor - 0.8).translate((pv[0], pv[1], 0)))
        ring = ring - cyl(0.42, 1.0, floor - 0.85).translate((pv[0], pv[1], 0))
    for i, f in enumerate(fw): pc.add(f"flyweight{i}", f, "black")
    for i, p in enumerate(pins): pc.add(f"pin{i}", p, "steel")
    sp = [(0, -5.4), (0.75, -5.4), (0.85, -5.3), (0.85, -3.6), (0.5, -3.6), (0.5, -1.2), (0.85, -1.2), (0.85, 1.2), (0.5, 1.2),
          (0.5, 3.6), (0.85, 3.6), (0.85, 5.3), (0.75, 5.4), (0, 5.4)]
    pc.add("spool", place(lathe(sp, 96), roty(90)).translate((0, 0, floor)), "bright")
    pc.add("head", ring, "bright")
    pc.notes["views"] = [(0.45, -0.8, 1.0), (0.0, -0.05, 1.0), (1.0, -0.1, 0.25), (0.0, -1.0, 0.15)]
    return pc


# ------------------------------------------------------------------ 04 MODULATOR cufflinks
@reg("gv_modulator_cufflinks")
def modulator_cufflinks():
    """The vacuum modulator: a sealed can split by a diaphragm, engine vacuum on one side, a spring on the
    other. It tells the valve body how hard the engine is working. Cufflinks: the can, two pressed halves
    joined by a rolled crimp seam, the diaphragm's convolutions turned into the dome, the hose nipple out
    the side, the threaded stem through the cuff and a knurled T-bar behind."""
    pc = Piece("gv_modulator_cufflinks", "flat")
    can = lathe([(0, 0.0), (1.9, 0.0), (2.2, 0.35), (5.6, 0.45), (6.7, 0.75), (7.15, 1.2), (7.2, 1.55),
                 (7.75, 1.55), (8.2, 1.7), (8.38, 2.0), (8.2, 2.3), (7.75, 2.45),        # the rolled seam
                 (7.2, 2.45), (7.1, 2.85), (6.6, 3.25), (5.4, 3.65), (3.6, 3.95), (1.8, 4.1), (0, 4.15)])
    # diaphragm convolutions turned into the dome (unequal: the real diaphragm's two rolls and a bead)
    def zdome(r):
        rs = [0, 1.8, 3.6, 5.4, 6.6, 7.1]; zs_ = [4.15, 4.1, 3.95, 3.65, 3.25, 2.85]
        return float(np.interp(r, rs, zs_))
    for r0, w, dp in ((4.6, 1.15, 0.42), (6.15, 0.3, 0.2)):     # one broad diaphragm roll and a fine bead line
        can = can - lathe([(r0 - w, zdome(r0 - w) + 0.6), (r0 - w, zdome(r0 - w) + 0.02), (r0, zdome(r0) - dp),
                           (r0 + w, zdome(r0 + w) + 0.02), (r0 + w, zdome(r0 + w) + 0.6)])
    # centre: the calibration screw in a counterbore (slotted, steel)
    can = can - cyl(1.25, 1.0, 3.45)
    screw0 = lathe([(0, 3.47), (1.18, 3.47), (1.18, 3.92), (1.05, 4.0), (0, 4.0)], 96)
    screw = screw0 - box(0.35, 3, 1).translate((0, 0, 4.1))
    # side hose nipple, drilled through, with a barb
    nip = place(lathe([(0.55, 0.0), (1.05, 0.0), (1.05, 1.6), (1.3, 1.9), (1.0, 3.2), (0.55, 3.2)], 96), roty(90)).translate((6.9, 0, 1.9))
    can = union([can, nip]) - mlib.drill_x(0.5, 5.5, 11, 0, 1.9)
    # stem: threaded post and a knurled T-bar, fixed (whale-back style)
    stem = union([mlib.thread(1.3, 1.08, 0.5, -8.6, 0.02), cyl(1.08, 8.7, -8.6)])
    bar = place(lathe([(0, -8.0), (1.05, -8.0), (1.25, -7.8), (1.25, 7.8), (1.05, 8.0), (0, 8.0)], 96), roty(90)).translate((0, 0, -9.7))
    bar_kn = place(knurl(1.26, -3.0, 3.0, pitch=0.55, depth=0.28), roty(90)).translate((0, 0, -9.7))
    bar = (bar - place(cyl(1.4, 6.0, -3.0), roty(90)).translate((0, 0, -9.7))) + bar_kn
    post = union([stem, bar, cyl(1.5, 0.6, -9.0)])
    body = union([can, post])
    pc.add("can", body, "bright", probe=union([can, cyl(1.1, 9, -9)]))
    pc.add("screw", screw, "steel", probe=screw0)
    pc.mirror_pair(22.0)
    pc.notes["views"] = [(0.35, -0.9, 1.0), (0.0, -0.02, 1.0), (1.0, -0.3, 0.2), (0.3, -1.0, -0.4)]
    return pc


# ------------------------------------------------------------------ 05 SHIFT VALVE bar pendant
@reg("gv_shiftvalve_pendant")
def shiftvalve_pendant():
    """The shift valve, where the computing happens: governor pressure pushes one end of the spool, throttle
    pressure and a spring push the other; when speed wins, the spool snaps across and its lands open the
    oil route to the next clutch. Pendant: an oxidised square bar bored through, the bright spool showing in
    milled ports front and back, a spring under it, a plug and eye bolt on top for the chain."""
    pc = Piece("gv_shiftvalve_pendant", "hang")
    S, L = 7.0, 40.0
    rb = 2.0
    c = 0.75                                  # long corners chamfered 45 deg after oxidising: four bright lines
    h = S / 2; oct_ = mlib.poly([(-h + c, -h), (h - c, -h), (h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c)])
    cross = mlib.rect2(S, S - 2 * c) + mlib.rect2(S - 2 * c, S)
    bar = extrude(oct_ ^ cross, L, -L / 2); edges = extrude(oct_ - cross, L, -L / 2)
    bore = cyl(rb, 38.5, -17.5)
    ports_f = [extrude(mlib.slot2((0, z0), (0, z1), 1.25), 10, 0) for z0, z1 in ((8.4, 12.6), (-2.4, 3.2), (-12.6, -8.8))]
    ports_b = [extrude(mlib.slot2((0, z0), (0, z1), 1.25), 10, 0) for z0, z1 in ((4.2, 6.8), (-7.4, -4.6))]
    toface = np.array([[1, 0, 0], [0, 0, -1.0], [0, 1, 0]])     # local XY -> world XZ, extruding toward -Y
    cuts = [place(p, toface) for p in ports_f] + [place(p, np.array([[1, 0, 0], [0, 0, 1.0], [0, -1, 0]])) for p in ports_b]
    side = [mlib.drill_x(0.7, 0, 5, 0, z) for z in (7.6, -2.9)]
    pinh = mlib.drill_x(0.42, -5, 5, 0, 17.0)
    bar = cut(bar, [bore] + cuts + side + [pinh]); edges = cut(edges, [bore] + cuts + side + [pinh])
    pc.add("body", bar, "black")
    pc.add("body_edges", edges, "bright", layer=True)
    sp = [(0, -12.6), (1.75, -12.6), (1.96, -12.4), (1.96, -8.6), (1.75, -8.4), (1.2, -8.4), (1.2, -3.0), (1.75, -3.0),
          (1.96, -2.8), (1.96, 0.9), (1.75, 1.1), (1.2, 1.1), (1.2, 6.4), (1.75, 6.4), (1.96, 6.6), (1.96, 10.4),
          (1.75, 10.6), (1.2, 10.6), (1.2, 12.2), (1.75, 12.2), (1.96, 12.4), (1.96, 14.0), (1.75, 14.2), (0, 14.2)]
    pc.add("spool", lathe(sp), "bright")
    pc.add("spring", mlib.helix_spring(1.35, 0.33, 1.0, -17.45, -12.65), "steel", bought=True)
    plug = lathe([(0, 14.3), (1.96, 14.3), (1.96, 20.05), (0, 20.05)]) - mlib.drill_x(0.42, -3, 3, 0, 17.0)
    hexc = mlib.hex_nut(4.6, 1.8, 0.0, z0=20.0)
    eye = M.batch_hull([cyl(1.1, 0.1, 21.75), cyl(1.4, 0.1, 22.4)])
    tor = place(M.revolve(mlib.circle2(0.8, (2.4, 0), 48), 96), rotx(90)).translate((0, 0, 25.0))
    shank = cyl(1.0, 1.6, 21.7)
    pc.add("eyebolt", union([plug, hexc, eye, tor, shank]), "bright")
    pc.add("pin", mlib.drill_x(0.4, -3.4, 3.4, 0, 17.0), "steel")
    pc.notes["views"] = [(0.45, -1.0, 0.35), (0.0, -1.0, 0.0), (1.0, 0.0, 0.1), (-0.5, 1.0, 0.3)]
    return pc


# ------------------------------------------------------------------ 07 SEPARATOR PLATE money clip
SEP_HOLES = [(-22.5, 4.2, 1.1), (-19.0, -5.6, 0.7), (-15.2, 1.0, 1.45), (-11.6, 6.2, 0.55), (-9.8, -3.6, 0.9),
             (-5.2, 4.8, 0.75), (-3.0, -6.4, 0.5), (0.6, 0.4, 1.25), (4.4, 6.5, 0.6), (5.6, -4.2, 0.95),
             (9.4, 2.8, 0.5), (12.6, -1.6, 1.2), (15.8, 5.4, 0.8), (18.4, -6.0, 0.6), (21.8, 1.6, 0.9)]


@reg("gv_separator_clip")
def separator_clip():
    """The separator plate: a thin steel plate between the valve body's halves, drilled with orifices of
    exact, different sizes. Each hole meters how fast a clutch fills, so it sets how hard each shift lands
    (shift kits drill them bigger). Money clip: the plate, its outline, bolt holes and fifteen orifices, folded
    back on itself as the spring clip."""
    pc = Piece("gv_separator_clip", "flat")
    T = 1.3; Lf = 54.0; W = 18.0
    out = mlib.poly([(-27, -9), (-6, -9), (-4.5, -7.6), (4.5, -7.6), (6, -9), (27, -9), (27, 9), (10, 9), (8.6, 10.6),
                     (2.2, 10.6), (0.8, 9), (-27, 9)])
    # back leaf continues past the fold (+x), plain, 40 mm
    Rin = 0.85; Rn = Rin + T / 2; arc = math.pi * Rn
    back = mlib.rounded_rect2(40.0 + arc + 2, W - 1.0, 1.2, (27 + (arc + 40.0) / 2 - 1, 0))
    blank = (out + back) - mlib.circle2(1.0, (-27, -9)) - mlib.circle2(1.0, (-27, 9))
    blank = blank.offset(0, m3.JoinType.Round)
    # the valve body's worm tracks leave their imprint on a used plate; the orifices sit where the tracks end
    pitch = 2.8; nx, ny = 17, 5; x0 = -(nx - 1) * pitch / 2 - 1.0; y0 = -(ny - 1) * pitch / 2
    bolts = [(-24.0, -6.2), (-24.0, 6.2), (24.0, 6.0), (5.4, 8.9), (24.0, -6.0)]
    keep = []
    for bx, by in bolts:
        i = int(round((bx - x0) / pitch)); j = int(round((by - y0) / pitch)); keep.append((max(0, i - 1), max(0, j - 1), i + 2, j + 2))
    paths = worm_paths(nx, ny, pitch, seed=3, n_paths=14, minlen=3, maxlen=9, keep_out=keep)
    rng = np.random.default_rng(9)
    rings, holes = [], []
    for P in paths:
        pts = [(x0 + i * pitch, y0 + j * pitch) for i, j in P]
        w = float(rng.choice([1.2, 1.5, 1.8]))
        rings.append(mlib.path2(pts, w / 2 + 0.2, 24) - mlib.path2(pts, w / 2 - 0.2, 24))
        for e in (pts[0], pts[-1]):
            if rng.random() < 0.55: holes.append(mlib.circle2(float(rng.choice([0.45, 0.6, 0.75, 0.95])), e, 40))
    imprint = CS.batch_boolean(rings, m3.OpType.Add) ^ out.offset(-1.2, m3.JoinType.Round, 2, 48)
    blank = blank - CS.batch_boolean(holes + [mlib.circle2(1.15, b_, 48) for b_ in bolts], m3.OpType.Add)
    plate = mlib.chamfered_plate(blank, T, c=0.15)
    groove = extrude(imprint, 0.5, T - 0.25)
    plate = plate - groove
    niello = extrude(imprint.offset(-0.012, m3.JoinType.Round, 2, 24), 0.21, T - 0.24)      # black niello laid in the lines, flush
    plate = plate.refine_to_length(0.8)
    xf = 27.0
    def fold(p):
        x, y, z = p
        if x <= xf: return (x, y, z)
        s = x - xf
        r = Rin + (T - z)                  # top face (z=T) outermost? no: bottom face z=0 is the inner face
        r = Rin + z
        if s <= arc:
            a = s / Rn
            return (xf + r * math.sin(a), y, -Rin + r * math.cos(a) + 0.0)
        u = s - arc
        tilt = math.radians(2.2)            # the back leaf springs toward the front
        return (xf - u * math.cos(tilt), y, -Rin - r + u * math.sin(tilt) * 1.0)
    clip = plate.warp(fold)
    pc.add("plate", clip, "satin")
    pc.add("niello", niello, "black", layer=True)
    pc.notes["views"] = [(0.2, -0.45, 1.0), (0.0, -0.02, 1.0), (0.2, -1.0, 0.25), (-1.0, -0.5, 0.5)]
    return pc


# ------------------------------------------------------------------ 08 WORM TRAIL cuff
def worm_paths(nx, ny, pitch, seed=7, n_paths=40, minlen=4, maxlen=16, keep_out=()):
    """Valve-body 'worm tracks': channels that wind on a grid and never share a cell, so every pair of
    neighbouring channels keeps a land (wall) between them. Deterministic for a seed."""
    rng = np.random.default_rng(seed)
    used = np.zeros((nx, ny), int)
    for (i0, j0, i1, j1) in keep_out: used[i0:i1, j0:j1] = -1
    paths = []
    dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    for k in range(n_paths * 6):
        if len(paths) >= n_paths: break
        free = np.argwhere(used == 0)
        if not len(free): break
        i, j = free[rng.integers(len(free))]
        d = dirs[rng.integers(4)] if rng.random() < 0.5 else (1, 0)
        L = int(rng.integers(minlen, maxlen + 1)); P = [(i, j)]; used[i, j] = k + 1
        for _ in range(L):
            opts = []
            if rng.random() < 0.72: opts.append(d)
            opts += [dd for dd in dirs if dd != (-d[0], -d[1]) and dd != d]
            moved = False
            for dd in opts:
                a, b = P[-1][0] + dd[0], P[-1][1] + dd[1]
                if 0 <= a < nx and 0 <= b < ny and used[a, b] == 0:
                    P.append((a, b)); used[a, b] = k + 1; d = dd; moved = True; break
            if not moved: break
        if len(P) >= minlen: paths.append(P)
        else:
            for (a, b) in P: used[a, b] = 0
    return paths


@reg("gv_wormtrail_cuff")
def wormtrail_cuff():
    """The valve body's face: the 'worm tracks', a maze of channels cast and machined into the body that
    route oil between the valves; the separator plate closes them. This is the circuit board of the
    hydraulic computer. Cuff: an oxidised back plate under a bright face plate with the worm tracks milled
    right through it, so every channel floor is black; held by six socket screws, two spool bores at the ends."""
    pc = Piece("gv_wormtrail_cuff", "cuff")
    Lc, Wc = 150.0, 26.0               # length (wraps) along Y, width along X
    Tb, Tt = 0.9, 1.3
    out = mlib.rounded_rect2(Wc, Lc, 5.0)
    pitch, wch = 2.8, 1.5
    nx, ny = int((Wc - 5) / pitch), int((Lc - 14) / pitch)
    x0 = -(nx - 1) * pitch / 2; y0 = -(ny - 1) * pitch / 2
    scr = [(-8.9, -66.0), (8.9, -66.0), (-8.9, 0.0), (8.9, 0.0), (-8.9, 66.0), (8.9, 66.0)]
    keep = []
    for sx, sy in scr:
        i = int(round((sx - x0) / pitch)); j = int(round((sy - y0) / pitch)); keep.append((max(0, i - 1), max(0, j - 1), i + 2, j + 2))
    # spool bores along the cuff ends: keep their strip free
    keep.append((3, 0, nx - 3, 3)); keep.append((3, ny - 3, nx - 3, ny))
    paths = worm_paths(nx, ny, pitch, seed=11, n_paths=70, minlen=3, maxlen=14, keep_out=keep)
    rng = np.random.default_rng(5)
    chs = []
    for P in paths:
        pts = [np.array((x0 + i * pitch, y0 + j * pitch)) for i, j in P]
        # cast-in channels turn on 45 deg cut corners, not square ones
        sm = [pts[0]]
        for k in range(1, len(pts) - 1):
            d0 = pts[k] - pts[k - 1]; d1 = pts[k + 1] - pts[k]
            if abs(np.dot(d0, d1)) < 1e-6: sm += [pts[k] - d0 * 0.42, pts[k] + d1 * 0.42]
            else: sm.append(pts[k])
        sm.append(pts[-1])
        w = float(rng.choice([1.2, 1.5, 1.8], p=[0.4, 0.35, 0.25]))
        chs.append(mlib.path2(sm, w / 2, 24))
        if w < 1.3:                                   # feed ports: a round pocket at the channel's ends
            for e in (sm[0], sm[-1]):
                if rng.random() < 0.6: chs.append(mlib.circle2(1.2, tuple(e), 40))
    ch = CS.batch_boolean(chs, m3.OpType.Add)
    top2 = out.offset(-0.0, m3.JoinType.Round) - ch
    base = mlib.chamfered_plate(out, Tb, c=0.3, z0=0.0)
    top = mlib.chamfered_plate(top2, Tt, c=0.18, z0=Tb + 0.012)       # (a hair off the back so bent chords never cross)
    # spool bores at each end: half-round troughs milled across, with a bright spool lying in each
    sp_parts = []
    for yy in (-(Lc / 2 - 4.6), (Lc / 2 - 4.6)):
        trough = mlib.drill_x(1.25, -8.5, 8.5, yy, Tb + 0.15)
        top = top - trough; base = base - trough
        prof = [(0, -8.2), (1.1, -8.2), (1.2, -8.1), (1.2, -5.4), (0.75, -5.4), (0.75, -2.0), (1.2, -2.0), (1.2, 2.0), (0.75, 2.0),
                (0.75, 5.4), (1.2, 5.4), (1.2, 8.1), (1.1, 8.2), (0, 8.2)]
        sp_parts.append(place(lathe(prof, 96), roty(90)).translate((0, yy, Tb + 0.15)))
    # screws: socket head cap screws in counterbores, shanks into the back plate
    screws = []
    for sx, sy in scr:
        top = top - cyl(1.0, Tt + 0.2, Tb - 0.1).translate((sx, sy, 0))
        base = base - cyl(1.0, 0.3, Tb - 0.12).translate((sx, sy, 0)) - cyl(0.66, Tb + 0.5, -0.3).translate((sx, sy, 0))
        screws.append(mlib.socket_screw(1.2, 0.75, z_head_top=Tb + Tt - 0.15).translate((sx, sy, 0)))
    R = 29.0
    pc.add("back", mlib.bend_cyl(base, R, refine=0.9), "black")
    pc.add("face", mlib.bend_cyl(top, R, refine=0.9), "bright")
    for i, s in enumerate(screws): pc.add(f"screw{i}", mlib.bend_cyl(s, R, refine=0.4), "steel", bought=True)
    for i, s in enumerate(sp_parts): pc.add(f"spool{i}", mlib.bend_cyl(s, R, refine=0.4), "bright")
    pc.notes["views"] = [(0.3, -0.25, 1.0), (0.0, -0.02, 1.0), (1.0, -0.2, 0.3), (0.0, -1.0, 0.3)]
    return pc


# ------------------------------------------------------------------ 09 DETENT bolo tie
@reg("gv_detent_bolo")
def detent_bolo():
    """The manual valve and its detent: the shift lever turns a plate whose edge is notched once for each
    position, P R N D 2 1, and a spring-loaded roller drops into the notch you choose; the plate's pin
    moves the manual valve, which tells the computer which program to run. Bolo tie: the detent plate,
    the leaf spring and roller sitting in D, the double-D shaft with a knurled collar; black leather cord,
    knurled tips. Plate face toward -Y, plate in y 0..T, outline drawn in (x, z)."""
    pc = Piece("gv_detent_bolo", "hang")
    T = 2.6
    def xz(cs, y0, y1):                                   # extrude an (x, z) outline from y0 to y1
        return place(extrude(cs, y1 - y0), rotx(90)).translate((0, y1, 0))
    piv = (0.0, -12.0); Rt = 31.0; rr = 2.0
    angs = [-35, -21.5, -8.0, 5.5, 19.0, 32.5]                     # P R N D 2 1
    npos = lambda a: (piv[0] + (Rt + 0.75) * math.sin(math.radians(a)), piv[1] + (Rt + 0.75) * math.cos(math.radians(a)))   # shallow valleys
    fan = mlib.poly([piv] + [(piv[0] + Rt * math.sin(math.radians(a)), piv[1] + Rt * math.cos(math.radians(a))) for a in np.linspace(44, -44, 45)])
    fan = fan + mlib.circle2(7.0, piv, 96)
    plate2 = fan - CS.batch_boolean([mlib.circle2(rr + 0.05, npos(a), 64) for a in angs], m3.OpType.Add)
    plate2 = plate2.offset(-1.1, m3.JoinType.Round, 2, 48).offset(1.1, m3.JoinType.Round, 2, 48)   # round the crests into a detent wave
    dd = mlib.circle2(3.12, piv, 64) ^ mlib.rect2(10, 4.62, piv)                  # double-D shaft hole
    plate2 = plate2 - dd - mlib.circle2(1.3, (13.0, 3.0), 48) - mlib.slot2((-9.0, 6.0), (-4.0, 12.5), 1.1)   # valve pin hole, park rod slot
    core2, edge2 = None, None
    core, edges = mlib.edge_split(plate2, T, c=0.35)
    core = place(core, rotx(90)).translate((0, T, 0)); edges = place(edges, rotx(90)).translate((0, T, 0))
    # bolo slide behind: a milled block with a channel for the two cords
    blk = xz(mlib.rounded_rect2(12.0, 16.0, 1.2, (0, 5.0)), T - 0.01, T + 6.6)
    blk = blk - box(9.6, 4.6, 22).translate((0, T + 3.3, 5.0))
    sx, sz = -11.5, -4.0                                                          # leaf anchor screw
    hole_p = drill_y_(0.64, -1, T + 1, sx, sz)
    core = union([core, blk]) - edges - hole_p
    pc.add("plate", core, "black")
    pc.add("plate_edges", edges - hole_p, "bright", layer=True)
    # shaft: double-D through the plate, knurled collar in front
    sh2 = mlib.circle2(3.05, piv, 64) ^ mlib.rect2(10, 4.52, piv)
    shaft = xz(sh2, -0.4, T - 0.02)
    col = place(union([knurl(4.6, 0.0, 2.6, pitch=0.65, depth=0.32), cyl(4.0, 2.6, 0)]) - cyl(1.4, 3, 1.6), rotx(90)).translate((piv[0], -0.03, piv[1]))
    pc.add("shaft", union([shaft, col]), "bright", probe=union([shaft, place(cyl(4.0, 2.6, 0), rotx(90)).translate((piv[0], -0.03, piv[1]))]))
    # roller in D, its pin and the leaf spring in front of the plate
    rc = npos(angs[3])
    roller = xz(mlib.circle2(rr, rc, 96) - mlib.circle2(0.66, rc, 48), 0.1, T - 0.1)
    pc.add("roller", roller, "steel")
    leaf = xz(mlib.slot2((sx, sz), rc, 1.7, 48), -2.0, -0.2)          # a straight flat spring, bolted at one end
    leafb = xz(mlib.circle2(2.6, (sx, sz), 64), -2.9, -0.03)
    pin = drill_y_(0.6, -2.8, T + 0.9, rc[0], rc[1])
    cheek = xz(mlib.circle2(1.8, rc, 48), T + 0.1, T + 0.9)
    eye = xz(mlib.circle2(2.1, rc, 48), -2.8, -0.2)
    arm = union([leaf, leafb, pin, cheek, eye])
    arm = arm - drill_y_(1.02, -3.0, -2.9 + 1.25, sx, sz) - drill_y_(0.62, -3, 0.2, sx, sz)
    pc.add("arm", arm, "bright")
    scr = place(mlib.socket_screw(1.2, 2.6, z_head_top=0.0), rotx(90)).translate((sx, -2.9 + 0.01, sz))
    pc.add("screw", scr, "steel", bought=True)
    # cord: 4 mm black leather, both ends down through the slide; neck loop shortened for the picture
    yc = T + 3.3; loopR = 15.0
    loop = [(loopR * 0.7 * math.cos(a), yc, 40 + loopR * math.sin(a)) for a in np.linspace(math.pi, 0, 20)]
    left = [(-2.4, yc, 30.0), (-2.4, yc, 16.0), (-2.4, yc, -4.0), (-3.6, yc, -20.0), (-4.4, yc, -30.0), (-5.0, yc, -38.0)]
    right = [(2.4, yc, 30.0), (2.4, yc, 16.0), (2.4, yc, -4.0), (3.4, yc, -18.0), (4.0, yc, -26.0), (4.6, yc, -33.0)]
    path = list(reversed(left)) + loop + right
    pc.add("cord", tube_path(path, 2.0), "leather", bought=True)
    for i, (p0, p1) in enumerate(((left[-2], left[-1]), (right[-2], right[-1]))):
        d = np.subtract(p1, p0); d = d / np.linalg.norm(d)
        prof = [(2.3, -7.0), (2.7, -7.0), (2.95, -6.75), (2.95, 3.6), (1.3, 9.0), (0, 9.0), (0, 2.4), (2.3, 2.4)]
        bodyt = lathe(prof, 96)
        tip = union([bodyt, knurl(2.96, -5.4, 1.4, pitch=0.6, depth=0.3)]) - cyl(2.3, 9.4, -7.2)
        Rd = _rot_to(d)
        pc.add(f"tip{i}", place(tip, Rd).translate(tuple(p1)), "bright", probe=place(bodyt, Rd).translate(tuple(p1)))
    pc.notes["views"] = [(0.3, -1.0, 0.3), (0.0, -1.0, 0.0), (1.0, -0.2, 0.15), (-0.4, -0.6, 1.0)]
    pc.notes["cord"] = "4 mm round black leather bolo cord, about 95 cm; tips crimped on; neck loop shown shortened"
    return pc


def drill_y_(r, y0, y1, x, z):
    return place(cyl(r, y1 - y0, 0), rotx(-90)).translate((x, y0, z))


def _rot_to(d):
    d = np.asarray(d, float); d /= np.linalg.norm(d); z = np.array([0, 0, 1.0])
    v = np.cross(z, d); c = float(np.dot(z, d))
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else rotx(180)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def sdf_smooth(pts, n=10):
    import sdf
    return [tuple(p[:2]) for p in sdf.catmull(np.array([(x, y, 0.0) for x, y in pts]), n)]


def tube_path(pts, r, n=8):
    import sdf
    P = sdf.catmull(np.asarray(pts, float), n)
    P = sdf.resample(P, 1.0)
    sph = [M.sphere(r, 24).translate(tuple(p)) for p in P]
    return union([M.batch_hull([sph[i], sph[i + 1]]) for i in range(len(sph) - 1)])


# ------------------------------------------------------------------ 10 BAND & SERVO bangle
@reg("gv_servo_bangle")
def servo_bangle():
    """The band and servo: a steel band, lined with friction material, wraps a drum; oil pushes the servo
    piston, the apply pin squeezes the band's ends together and the drum stops. Bangle: a dual-wrap band (it
    splits into two straps round the back and joins again at the ends, as heavy-duty bands do), bright over an
    oxidised lining that shows between the straps; the anchor end sits on an adjusting screw and jam nut, the
    apply end on the servo's piston; they face each other across the opening."""
    pc = Piece("gv_servo_bangle", "cuff")
    Lb, Wb = 146.0, 11.0
    Tl, Ts = 0.9, 1.5
    R = 29.0
    out = mlib.rounded_rect2(Wb, Lb, 1.0)
    gap = mlib.slot2((0, -Lb / 2 + 17), (0, Lb / 2 - 17), 1.25)          # the split between the two straps
    lining = mlib.chamfered_plate(out.offset(-0.4, m3.JoinType.Round, 2, 48), Tl, c=0.15)
    steel = mlib.chamfered_plate(out - gap, Ts, c=0.3, z0=Tl + 0.012)
    for yy in (-Lb / 2 + 12.0, Lb / 2 - 12.0):                         # oil drain holes in the solid ends
        steel = steel - cyl(0.75, 5, -1).translate((0, yy, 0)); lining = lining - cyl(0.75, 5, -1).translate((0, yy, 0))
    lugA = mlib.chamfered_plate(mlib.rounded_rect2(Wb, 8.0, 1.2, (0, -Lb / 2 + 4.0)), 4.2, c=0.4, z0=Tl + Ts - 0.2)
    lugB = mlib.chamfered_plate(mlib.rounded_rect2(Wb, 8.0, 1.2, (0, Lb / 2 - 4.0)), 4.2, c=0.4, z0=Tl + Ts - 0.2)
    zc = Tl + Ts + 1.9
    steel = union([steel, lugA, lugB])
    bandS = mlib.bend_cyl(steel, R, refine=1.0)
    def at_end(solid, sgn):
        a = (sgn * Lb / 2) / R
        s = solid.translate((0, -sgn * Lb / 2, 0))
        s = place(s, rotx(math.degrees(-a)))
        return s.translate((0, R * math.sin(a), R * math.cos(a) - R))
    # adjusting screw (anchor end): M2.5 thread out of lug A into the opening, jam nut, cone tip
    scr = union([mlib.thread(1.25, 1.02, 0.45, 0.0, 9.4), cyl(1.02, 9.4, 0.0),
                 lathe([(0, 9.4), (1.2, 9.4), (1.2, 9.9), (0.35, 11.0), (0, 11.0)], 64)])
    scr = place(scr, rotx(90)).translate((0, -Lb / 2 + 7.0, zc))
    nut = place(mlib.hex_nut(4.4, 2.0, 1.27), rotx(90)).translate((0, -Lb / 2 - 0.05, zc))
    pis = lathe([(0, 0.0), (2.5, 0.0), (2.8, 0.3), (2.8, 2.4), (2.5, 2.7), (1.1, 2.7), (1.1, 3.9), (0.8, 4.2), (0, 4.2)], 96)
    pis = pis - lathe([(2.3, 0.75), (3, 0.75), (3, 1.15), (2.3, 1.15)]) - lathe([(2.3, 1.6), (3, 1.6), (3, 2.0), (2.3, 2.0)])
    servo = union([pis, cyl(1.6, 6.0, -6.0)])
    servo = place(servo, rotx(-90)).translate((0, Lb / 2 + 0.05, zc))
    bandS = bandS - at_end(place(cyl(1.28, 8.5, -1.0), rotx(90)).translate((0, -Lb / 2 + 7.5, zc)), -1)
    bandS = bandS - at_end(place(cyl(1.65, 7.0, -1.0), rotx(-90)).translate((0, Lb / 2 - 6.0, zc)), 1)
    pc.add("lining", mlib.bend_cyl(lining, R, refine=1.0), "black")
    pc.add("band", bandS, "bright")
    pc.add("adjuster", at_end(scr, -1), "bright", probe=at_end(place(cyl(1.02, 11.0, 0.0), rotx(90)).translate((0, -Lb / 2 + 7.0, zc)), -1))
    pc.add("jam_nut", at_end(nut, -1), "bright")
    pprobe = place(union([lathe([(0, 0.0), (2.8, 0.0), (2.8, 2.7), (1.1, 2.7), (1.1, 4.2), (0, 4.2)], 96), cyl(1.6, 6.0, -6.0)]), rotx(-90)).translate((0, Lb / 2 + 0.05, zc))
    pc.add("servo", at_end(servo, 1), "bright", probe=at_end(pprobe, 1))
    pc.notes["views"] = [(0.35, -0.55, 1.0), (0.0, -0.02, 1.0), (1.0, -0.2, 0.3), (0.0, -1.0, 0.25)]
    return pc


# ------------------------------------------------------------------ 11 CLUTCH PACK stacking rings
@reg("gv_clutch_stack")
def clutch_stack():
    """A clutch pack: steel plates with lugs on the outside, splined to the case, interleaved with friction
    plates splined on the inside to the drum; oil pushes a piston, the pack squeezes and the two lock. Four
    stacking rings: two lugged steels (bright), two frictions with oxidised lining bonded both faces, the
    lining cut with the oil grooves that let the pack breathe; worn together they lock up the finger."""
    pc = Piece("gv_clutch_stack", "ring")
    def steel(z0, rot):
        w = 1.9
        body2 = mlib.circle2(11.7, (0, 0), 240) + CS.batch_boolean(
            [mlib.rounded_rect2(3.4, 4.0, 0.6, (0, 12.6)).rotate(rot + 60 * k) for k in range(6)], m3.OpType.Add)
        body2 = body2 - mlib.circle2(FINGER, (0, 0), 240)
        s = mlib.chamfered_plate(body2, w, c=0.3, z0=z0)
        return s - lathe([(0, z0 - 1), (FINGER + 0.7, z0 - 1), (FINGER, z0 + 0.45), (FINGER, z0 + w - 0.45), (FINGER + 0.7, z0 + w + 1), (0, z0 + w + 1)])
    def friction(z0, nseed):
        core_w, lin = 1.0, 0.45
        Ro = 12.3
        core = mlib.chamfered_plate(mlib.circle2(Ro - 0.3, (0, 0), 240) - mlib.circle2(FINGER, (0, 0), 240), core_w, c=0.2, z0=z0 + lin + 0.01)
        core = core - lathe([(0, z0 - 1), (FINGER + 0.5, z0 - 1), (FINGER, z0 + lin + 0.3), (FINGER, z0 + lin + core_w - 0.3), (FINGER + 0.5, z0 + 3), (0, z0 + 3)])
        ann = mlib.circle2(Ro, (0, 0), 240) - mlib.circle2(FINGER + 1.0, (0, 0), 240)
        # oil grooves through the lining: a pair at each of 9 stations, alternately radial and angled
        gr = []
        for k in range(9):
            a = 40 * k + nseed * 20
            for da, sk in ((0, 0.0), (9 if k % 2 else -9, 18.0)):
                aa = math.radians(a + da)
                p0 = ((FINGER + 0.6) * math.cos(aa), (FINGER + 0.6) * math.sin(aa))
                p1 = ((Ro + 1) * math.cos(aa + math.radians(sk) * 0.08), (Ro + 1) * math.sin(aa + math.radians(sk) * 0.08))
                gr.append(mlib.slot2(p0, p1, 0.28, 16))
        ann = ann - CS.batch_boolean(gr, m3.OpType.Add)
        l1 = mlib.chamfered_plate(ann, lin, c=0.1, z0=z0)
        l2 = mlib.chamfered_plate(ann, lin, c=0.1, z0=z0 + lin + core_w + 0.02)
        return core, l1, l2
    z = -4.1
    pc.add("steel_a", steel(z, 0), "bright"); z += 1.9 + 0.08
    c, l1, l2 = friction(z, 0); pc.add("friction_a", c, "bright"); pc.add("lining_a1", l1, "black", layer=True); pc.add("lining_a2", l2, "black", layer=True); z += 0.45 * 2 + 1.0 + 0.03 + 0.08
    pc.add("steel_b", steel(z, 30), "bright"); z += 1.9 + 0.08
    c, l1, l2 = friction(z, 1); pc.add("friction_b", c, "bright"); pc.add("lining_b1", l1, "black", layer=True); pc.add("lining_b2", l2, "black", layer=True)
    for p in pc.parts:
        p["solid"] = ring_axis(p["solid"])
        if p.get("probe") is not None: p["probe"] = ring_axis(p["probe"])
    pc.notes["views"] = [(0.6, -1.0, 0.75), (0.0, -1.0, 0.05), (1.0, 0.0, 0.18), (0.3, -0.4, 1.0)]
    pc.notes["set"] = "four rings worn as one stack"
    return pc


# ------------------------------------------------------------------ 12 PLANETARY medallion
@reg("gv_planetary_medallion")
def planetary_medallion():
    """The planetary gearset: a sun, three planets on a carrier, all inside a ring gear. Hold one member, drive
    another, take power from the third, and one set gives several ratios; the clutches and bands pick which.
    Medallion: a real meshing set, 39-tooth ring gear knurled outside, three 12-tooth planets on steel pins
    in an oxidised carrier, a 15-tooth sun with a splined bore you can see through, a circlip in front, hung
    from an eye bolt."""
    pc = Piece("gv_planetary_medallion", "flat")
    mod = 0.6; Zs, Zp, Zr = 15, 12, 39
    a = (Zs + Zp) * mod / 2                      # 8.1 mm centre distance
    H0, H1 = 1.0, 4.4                            # gear face width z range
    ro = 14.6
    ring = lathe([(0, 0), (ro - 0.35, 0), (ro, 0.35), (ro, 5.2), (ro - 0.35, 5.55), (0, 5.55)])
    teeth_space = mlib.involute_gear2(Zr, mod, internal=True, backlash=0.06)
    ring2d_cut = mlib.circle2(Zr * mod / 2 - mod * 1.0 + 0.0, (0, 0), 240)          # tooth tips (internal)
    sp = mlib.circle2(Zr * mod / 2 + mod * 1.25, (0, 0), 240)
    # internal teeth = annulus minus the gear outline of a virtual external gear with Zr teeth (tooth spaces)
    ext = mlib.involute_gear2(Zr, mod, backlash=-0.06, clearance=0.0)
    cavity = (ext + mlib.circle2(Zr * mod / 2 - mod, (0, 0), 240)) ^ sp
    ring = ring - extrude(cavity, 5.0, H0 - 0.4 + 0.0) - cyl(10.0, 2, -1)
    ring = ring - lathe([(Zr * mod / 2 + 0.3, 4.5), (13.2, 4.5), (13.2, 4.95), (Zr * mod / 2 + 0.3, 4.95)])   # circlip groove
    kn = knurl(ro + 0.01, 1.2, 4.35, pitch=0.7, depth=0.35, kind="straight", chamfer=0.2)
    ring = (ring - lathe([(ro - 0.45, 1.2), (ro + 1, 1.2), (ro + 1, 4.35), (ro - 0.45, 4.35)])) + (kn - cyl(ro - 0.5, 3.4, 1.1))
    # eye bolt: drilled radially at the top (+Y), spot face, threaded shank, collar, eye
    ring = ring - drill_y_(1.05, 12.9, 16, 0, 2.775) - box(6, 2, 7).translate((0, ro + 0.6, 2.775))
    carrier = lathe([(2.48, 0.6), (10.6, 0.6), (10.85, 0.85), (10.85, H0 - 0.05), (2.48, H0 - 0.05)])
    carrier = lathe([(2.48, 0.05), (9.6, 0.05), (9.9, 0.35), (9.9, 0.95), (2.48, 0.95)])
    # carrier sits in the ring gear's back bore (r 10.0) on three ribs? keep it simple: a disc in the back bore
    pins = []
    planets = []
    sun2 = mlib.involute_gear2(Zs, mod, backlash=0.06) - spline_hole(2.0, 1.6, 10)
    sun = extrude(sun2, H1 - H0, H0 + 0.02) + extrude(mlib.circle2(2.42, (0, 0), 96) - spline_hole(2.0, 1.6, 10), H0 + 0.1, -0.05)
    sun = sun.rotate((0, 0, 0))
    best = []
    for k in range(3):
        ang = 90 + 120 * k
        c = (a * math.cos(math.radians(ang)), a * math.sin(math.radians(ang)))
        g = mlib.involute_gear2(Zp, mod, backlash=0.06)
        # find the planet rotation that meshes cleanly with the sun and the ring
        sun_c = mlib.involute_gear2(Zs, mod, backlash=0.06)
        best_r, best_s = 0, -1
        for rr_ in np.linspace(0, 360 / Zp, 61):
            gp = g.rotate(rr_).translate(c)
            ov = (gp ^ sun_c).area() + (gp ^ (mlib.circle2(ro, (0, 0), 240) - cavity)).area()
            if best_s < 0 or ov < best_s: best_s, best_r = ov, rr_
        gp = g.rotate(best_r).translate(c) - mlib.circle2(0.86, c, 48)
        planets.append(extrude(gp, H1 - H0, H0 + 0.02))
        pins.append(cyl(0.8, H1 - 0.1, 0.1).translate((c[0], c[1], 0)))
        carrier = carrier - cyl(0.82, 2, -0.5).translate((c[0], c[1], 0))
        best.append(round(best_s, 4))
    pc.notes["mesh_overlap_area"] = best
    pc.add("ring_gear", ring, "bright", probe=lathe([(12.5, 0.2), (ro - 0.5, 0.2), (ro - 0.5, 5.3), (12.5, 5.3)]))   # wall behind the teeth
    pc.add("carrier", carrier, "black")
    for i, p in enumerate(planets): pc.add(f"planet{i}", p, "bright")
    for i, p in enumerate(pins): pc.add(f"pin{i}", p, "steel")
    pc.add("sun", sun, "bright", probe=cyl(3.3, H1 - H0, H0 + 0.02) - cyl(2.0, 9, -1))
    # circlip in front: an open ring with two lug ends and their holes
    clip2 = (mlib.circle2(13.1, (0, 0), 240) - mlib.circle2(12.1, (0, 0), 240)) - mlib.poly([(0, 0), (-3.2, -16), (3.2, -16)])
    for sx in (-1.0, 1.0):
        lug = mlib.circle2(0.52, (sx * 2.5, -12.35), 48) - mlib.circle2(0.25, (sx * 2.5, -12.35), 32)
        clip2 = clip2 + lug
    pc.add("circlip", extrude(clip2, 0.4, 4.52), "steel", bought=True)
    eyeb = union([mlib.thread(1.02, 0.85, 0.45, 0.0, 1.7), cyl(0.85, 1.7, 0.0)])
    eyeb = place(eyeb, rotx(-90)).translate((0, 13.0, 2.775))
    collar = place(lathe([(0, 0), (1.9, 0), (2.05, 0.15), (2.05, 1.1), (1.6, 1.4), (0, 1.4)], 96), rotx(-90)).translate((0, ro - 0.4 + 0.02, 2.775))
    eye = place(M.revolve(mlib.circle2(0.85, (2.5, 0), 48), 96), roty(90)).translate((0, ro + 1.0 + 2.5 + 0.55, 2.775))
    pc.add("eyebolt", union([eyeb, collar, eye]), "bright", probe=union([cyl(0.85, 1.7, 0.0).transform(np.hstack([rotx(-90), [[0], [13.0], [2.775]]]).tolist()), collar, eye]))
    pc.notes["views"] = [(0.25, -0.5, 1.0), (0.0, -0.02, 1.0), (1.0, -0.3, 0.3), (0.0, 1.0, -0.6)]
    return pc


def spline_hole(r_out, r_in, z):
    return mlib.spline2(z, r_out, r_in, duty=0.5) + mlib.circle2(r_in + 0.01, (0, 0), 64)
