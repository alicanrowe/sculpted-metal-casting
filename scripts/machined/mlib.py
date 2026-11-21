"""Governor machining kit: crisp, exact solids for turned, milled and knurled parts (manifold3d CSG).

Where the sculpting kit (sdf.py) grows liquid, cast forms, this one cuts metal the way a lathe
and a mill do: revolve a profile (turning), extrude and subtract a 2D pocket (milling), drill with a
118 deg point, cut a diamond or straight knurl, chamfer every edge. Units: mm. Z is up.

Every builder in pieces.py returns a Piece: a list of named parts (each one solid body, with a finish:
'bright' polished sterling, 'black' oxidised sterling, 'satin' brushed sterling, 'steel' blued/
polished steel), plus balls (precision synthetic ruby or sapphire balls) and a view kind."""
import math
import numpy as np
import manifold3d as m3

M = m3.Manifold
CS = m3.CrossSection
SEG = 192                       # circle segments for turned parts (crisp silhouettes)
m3.set_circular_segments(SEG) if hasattr(m3, "set_circular_segments") else None


# ------------------------------------------------------------------ basic solids
def cyl(r, h, z0=0.0, r2=None, seg=SEG):
    return M.cylinder(h, r, r if r2 is None else r2, seg).translate((0, 0, z0))


def box(x, y, z, center=True):
    return M.cube((x, y, z), center)


def lathe(profile, seg=SEG, angle=360.0):
    """Turn a part: profile = [(r, z), ...] closed polygon in the r-z half plane (r >= 0).
    The axis is Z."""
    pts = [(max(0.0, r), z) for r, z in profile]
    return M.revolve(CS([pts]), seg, angle)


def chamfer_profile(r_out, z0, z1, c=0.25, r_in=0.0, ci=None):
    """A plain turned cylinder (or tube) profile with chamfered corners."""
    ci = c if ci is None else ci
    if r_in > 0:
        return [(r_in + ci, z0), (r_out - c, z0), (r_out, z0 + c), (r_out, z1 - c), (r_out - c, z1),
                (r_in + ci, z1), (r_in, z1 - ci), (r_in, z0 + ci)]
    return [(0, z0), (r_out - c, z0), (r_out, z0 + c), (r_out, z1 - c), (r_out - c, z1), (0, z1)]


def tube(r_out, r_in, z0, z1, c=0.2):
    return lathe(chamfer_profile(r_out, z0, z1, c, r_in))


def drill(r, depth, at=(0, 0, 0), axis=(0, 0, -1), point=True):
    """A drilled hole with a 118 deg drill point, entering at `at` along `axis`."""
    tip = r / math.tan(math.radians(59)) if point else 0.0
    prof = [(0, -0.3), (r, -0.3), (r, depth), (0, depth + tip)] if point else [(0, -0.3), (r, -0.3), (r, depth), (0, depth)]
    h = lathe(prof, 64)
    return orient(h, axis).translate(at)


def orient(solid, axis):
    """Rotate a Z-axis solid so its +Z points along `axis`."""
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    z = np.array([0, 0, 1.0])
    v = np.cross(z, a); c = float(np.dot(z, a))
    if np.linalg.norm(v) < 1e-9:
        return solid if c > 0 else solid.rotate((180, 0, 0))
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + vx + vx @ vx * (1 / (1 + c))
    T = np.hstack([R, np.zeros((3, 1))])
    return solid.transform(T.tolist())


def place(solid, R=None, t=(0, 0, 0)):
    R = np.eye(3) if R is None else np.asarray(R, float)
    return solid.transform(np.hstack([R, np.asarray(t, float).reshape(3, 1)]).tolist())


def rotz(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rotx(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def roty(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def union(parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    return M.batch_boolean(parts, m3.OpType.Add) if len(parts) > 1 else parts[0]


def cut(a, parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    if not parts: return a
    return a - union(parts)


# ------------------------------------------------------------------ 2D (milling)
def poly(pts):
    return CS([[(float(x), float(y)) for x, y in pts]])


def circle2(r, c=(0, 0), seg=96):
    return CS.circle(r, seg).translate(c)


def rect2(w, h, c=(0, 0)):
    return CS.square((w, h), True).translate(c)


def slot2(a, b, r, seg=48):
    """A milled slot: stadium between points a and b with end radius r (an end mill's path)."""
    return CS.batch_hull([circle2(r, a, seg), circle2(r, b, seg)])


def path2(pts, r, seg=32):
    """A channel milled along a polyline with a ball/flat end mill of radius r."""
    pts = [tuple(map(float, p)) for p in pts]
    segs = [slot2(pts[i], pts[i + 1], r, seg) for i in range(len(pts) - 1)]
    return CS.batch_boolean(segs, m3.OpType.Add)


def rounded_rect2(w, h, r, c=(0, 0)):
    return rect2(w - 2 * r, h - 2 * r, c).offset(r, m3.JoinType.Round, 2, 48)


def extrude(cs, h, z0=0.0, twist=0.0, ndiv=0, scale_top=(1.0, 1.0)):
    return M.extrude(cs, h, ndiv, twist, scale_top).translate((0, 0, z0))


def chamfered_plate(cs, t, c=0.2, z0=0.0, steps=3):
    """A plate cut from outline cs, thickness t, with its top and bottom edges broken by a c x 45 deg
    chamfer (built as `steps` thin offset slices: at render size it reads as a deburred machined edge)."""
    sl = [extrude(cs, t - 2 * c, z0 + c)]
    for i in range(steps):
        d = c * (i + 0.5) / steps; h = c / steps
        o = cs.offset(-d, m3.JoinType.Round, 2, 48)
        sl.append(extrude(o, h + 0.004, z0 + c - (i + 1) * h))       # slices overlap a hair so they fuse
        sl.append(extrude(o, h + 0.004, z0 + t - c + i * h - 0.004))
    return union(sl)


def perimeter(cs):
    p = 0.0
    for c in cs.to_polygons():
        c = np.asarray(c); p += np.linalg.norm(np.roll(c, -1, 0) - c, axis=1).sum()
    return p


# ------------------------------------------------------------------ knurling (lathe)
def knurl(r, z0, z1, pitch=0.7, depth=None, kind="diamond", angle=30.0, chamfer=0.25):
    """A knurled band on a cylinder of outer radius r from z0 to z1, as a lathe knurling wheel rolls it:
    'diamond' = two crossed helices at +-angle (the standard 30 deg diamond), 'straight' = axial ridges.
    The teeth are 90 deg V ridges at the given circumferential pitch, chamfered in at both ends."""
    n = max(12, int(round(2 * math.pi * r / pitch)))
    depth = depth or pitch * 0.5
    ri = r - depth
    pts = []
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = 2 * math.pi * (i + 0.5) / n
        pts.append((r * math.cos(a0), r * math.sin(a0))); pts.append((ri * math.cos(a1), ri * math.sin(a1)))
    star = CS([pts])
    L = z1 - z0
    if kind == "straight":
        k = extrude(star, L, z0)
    else:
        tw = math.degrees(L * math.tan(math.radians(angle)) / r)
        nd = max(8, int(L / 0.08))
        a = M.extrude(star, L, nd, tw).translate((0, 0, z0))
        b = M.extrude(star, L, nd, -tw).translate((0, 0, z0))
        k = a ^ b
    # chamfer the knurl in at both ends (a knurl always runs out into a chamfer)
    env = lathe([(0, z0), (ri, z0), (r + 0.01, z0 + chamfer + depth), (r + 0.01, z1 - chamfer - depth), (ri, z1), (0, z1)])
    return union([k ^ env, cyl(ri + 0.01, L, z0)])


# ------------------------------------------------------------------ gears
def involute_gear2(z, module, pressure=20.0, clearance=0.25, backlash=0.05, internal=False, seg_flank=10):
    """2D involute spur gear (external) outline, or for internal=True the outline of the tooth SPACE ring
    (subtract it from a disc). Centred at the origin."""
    m = module; rp = z * m / 2; rb = rp * math.cos(math.radians(pressure))
    if internal:
        ra = rp - m * 1.0; rf = rp + m * (1.0 + clearance)
    else:
        ra = rp + m; rf = max(rp - m * (1.0 + clearance), 0.2)
    def inv(a): return math.tan(a) - a
    ap = math.radians(pressure)
    half_tooth = math.pi / (2 * z) + (inv(ap)) - (backlash / (2 * rp)) * (-1 if internal else 1)
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        flank = []
        r0 = max(rb, rf)
        for i in range(seg_flank + 1):
            rr = r0 + (ra - r0) * i / seg_flank if not internal else r0 + (max(ra, rb) - r0) * i / seg_flank
            rr = max(rr, rb + 1e-6)
            al = math.acos(rb / rr)
            th = half_tooth - inv(al)
            flank.append((rr, th))
        left = [(c - th, rr) for rr, th in flank]
        right = [(c + th, rr) for rr, th in reversed(flank)]
        # root
        pts.append((rf * math.cos(c - math.pi / z + 0.0), rf * math.sin(c - math.pi / z)))
        if rb > rf:
            pts.append((rf * math.cos(c - half_tooth), rf * math.sin(c - half_tooth)))
        for a, rr in left: pts.append((rr * math.cos(a), rr * math.sin(a)))
        for a, rr in right: pts.append((rr * math.cos(a), rr * math.sin(a)))
        if rb > rf:
            pts.append((rf * math.cos(c + half_tooth), rf * math.sin(c + half_tooth)))
    return CS([pts])


def spline2(z, r_out, r_in, duty=0.5, seg=6):
    """Straight-sided spline teeth (clutch plate lugs, shaft splines)."""
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z; w = math.pi / z * duty * 2
        for a, rr in ((c - w / 2 - 0.03, r_in), (c - w / 2, r_out), (c + w / 2, r_out), (c + w / 2 + 0.03, r_in)):
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return CS([pts])


# ------------------------------------------------------------------ bending (a plate rolled into a cuff)
def bend_cyl(solid, R, axis="x", refine=0.35):
    """Roll a flat part (lying in XY, thickness along +Z) onto a cylinder of radius R about an axis
    parallel to X (axis='x': Y wraps round) with its outer face at radius R + z."""
    s = solid.refine_to_length(refine)
    def f(p):
        x, y, z = p
        a = y / R; rr = R + z
        return (x, rr * math.sin(a), rr * math.cos(a) - R)
    return s.warp(f)


# ------------------------------------------------------------------ export
def to_np(solid):
    mm = solid.to_mesh()
    V = np.asarray(mm.vert_properties, np.float64)[:, :3]
    F = np.asarray(mm.tri_verts, np.int64)
    return V, F


class Piece:
    def __init__(self, name, kind="flat"):
        self.name = name; self.kind = kind; self.parts = []; self.balls = []; self.notes = {}
        self.pair_dx = None

    def add(self, label, solid, finish="bright", fixed=True, probe=None, bought=False, layer=False):
        """probe: the part without its surface texture (knurl teeth, serrations), for the wall check.
        bought: a stock part bought in (springs, roll pins, cord); skips the machined-wall floor.
        layer: a finish zone of the part before it (bright cut edges on an oxidised body): same metal, so
        it is not counted as its own body or wall, only checked for clipping against the other parts."""
        self.parts.append(dict(label=label, solid=solid, finish=finish, fixed=fixed, probe=probe, bought=bought, layer=layer))
        return solid

    def ball(self, c, d, kind="ruby"):
        self.balls.append(dict(kind=kind, c=[float(x) for x in c], D=float(d), L=float(d), shape="ball"))

    def mirror_pair(self, dx):
        """Earring/cufflink pairs: duplicate every part and ball at +dx (mirrored in X)."""
        self.pair_dx = dx
        new = []
        for p in self.parts:
            s2 = p["solid"].mirror((1, 0, 0)).translate((dx, 0, 0))
            pr = p.get("probe")
            new.append(dict(p, label=p["label"] + "_R", solid=s2,
                            probe=None if pr is None else pr.mirror((1, 0, 0)).translate((dx, 0, 0))))
        for b in list(self.balls):
            c = list(b["c"]); c[0] = -c[0] + dx
            self.balls.append(dict(b, c=c))
        self.parts += new


# ------------------------------------------------------------------ hardware
def thread(r_major, r_minor, pitch, z0, z1, seg=64):
    """A helical single-start thread (rounded profile) from z0 to z1: an eccentric disc twisted along Z."""
    L = z1 - z0
    rm = (r_major + r_minor) / 2; off = (r_major - r_minor) / 2
    c = circle2(rm, (off, 0), seg)
    tw = 360.0 * L / pitch
    return M.extrude(c, L, max(16, int(L / pitch * 24)), tw).translate((0, 0, z0))


def hex2(af, c=(0, 0), rot=0.0):
    """Hexagon by width across flats."""
    R = af / math.sqrt(3)
    return poly([(c[0] + R * math.cos(math.radians(rot + 30 + 60 * k)), c[1] + R * math.sin(math.radians(rot + 30 + 60 * k)))
                 for k in range(6)])


def hex_nut(af, h, bore, z0=0.0, chamfer30=True):
    """A hex nut / hex body with the 30 deg corner chamfer both faces (the arcs on every nut)."""
    body = extrude(hex2(af), h, z0)
    if chamfer30:
        R = af / math.sqrt(3); d = (R - af / 2) * 1.0
        env = lathe([(0, z0), (af / 2 - 0.02, z0), (R + 0.05, z0 + (R + 0.05 - af / 2) * math.tan(math.radians(30))),
                     (R + 0.05, z0 + h - (R + 0.05 - af / 2) * math.tan(math.radians(30))), (af / 2 - 0.02, z0 + h), (0, z0 + h)])
        body = body ^ env
    if bore > 0:
        body = body - cyl(bore, h + 2, z0 - 1)
    return body


def socket_screw(d, L, z_head_top=0.0, seg=64):
    """Socket head cap screw pointing down -Z, head top at z_head_top: head 1.5 d, hex socket 0.75 d."""
    hd = 1.5 * d; hh = d
    head = lathe([(0, z_head_top - hh), (hd / 2 - 0.08, z_head_top - hh), (hd / 2, z_head_top - hh + 0.08),
                  (hd / 2, z_head_top - 0.12), (hd / 2 - 0.12, z_head_top), (0, z_head_top)], seg)
    # knurled head side (straight knurl, as on real cap screws)
    sock = extrude(hex2(0.42 * hd * 1.0), hh * 0.6 + 0.2, z_head_top - hh * 0.6)
    head = head - sock
    shank = cyl(d / 2, L + 0.1, z_head_top - hh - L)
    return union([head, shank])


def helix_spring(r_coil, r_wire, pitch, z0, z1, seg=18, ground=True):
    """A compression spring: a wire of radius r_wire on a helix of radius r_coil, ends closed and ground flat."""
    L = z1 - z0; turns = L / pitch
    n = max(8, int(turns * seg))
    pts = []
    for i in range(n + 1):
        t = i / n; a = 2 * math.pi * turns * t
        z = z0 + L * t
        pts.append((r_coil * math.cos(a), r_coil * math.sin(a), z))
    # closed ends: flatten the first and last half turn
    out = []
    balls = [M.sphere(r_wire, 16).translate(p) for p in pts]
    for i in range(n):
        out.append(M.batch_hull([balls[i], balls[i + 1]]))
    s = union(out)
    if ground:
        s = s ^ cyl(r_coil + r_wire + 1, L - 2 * r_wire * 0.5, z0 + r_wire * 0.5)
    return s


def drill_x(r, x0, x1, y, z):
    return orient(cyl(r, x1 - x0, 0), (1, 0, 0)).translate((x0, y, z))


def drill_y(r, y0, y1, x, z):
    return orient(cyl(r, y1 - y0, 0), (0, 1, 0)).translate((x, y0, z))


def edge_split(cs, t, c=0.3, z0=0.0, steps=3):
    """For a two-tone part: oxidise the plate, then the chamfer mill cuts its edges back to bright metal.
    Returns (black_core, bright_chamfers): two touching solids that are one piece of metal."""
    full = chamfered_plate(cs, t, c=c, z0=z0, steps=steps)
    keep = union([extrude(cs, t - 2 * c, z0 + c), extrude(cs.offset(-c - 0.002, m3.JoinType.Round, 2, 48), t + 1, z0 - 0.5)])
    return full ^ keep, full - keep
