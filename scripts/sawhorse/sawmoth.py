"""Cast-metal sawhorse: the Krenov sawhorse (vB proportions kept) recast as a piece.
Units: 1 = 1 cm, Z up, X along the rail, front is -Y. Metal is one sterling/steel SDF body built
with the jewelry kit; the cushion is black leather (from krenov_model.py, slot filled, ends piped)
with two leather straps closed by metal buckles.

  python sawmoth.py mesh            -> builds and reports the metal (no render)
  python sawmoth.py render [tag]    -> renders views into $OUTDIR (default scratch)
"""
import sys, os, math, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
JW = os.environ.get("KIT_DIR", os.path.join(os.path.dirname(HERE), "kit"))
sys.path.insert(0, JW); sys.path.insert(0, os.path.dirname(HERE))
import sdf, v2
from sdf import Scene
import wisp
import wings2 as W2
import sculpt as K
import moira as Mo
from kit import Flat
from devel import body

IN = 2.54
RAIL_Z0 = (29.25 - 2.125) * IN          # 68.9
TOP = 29.25 * IN                         # 74.3  top of rail
LEG_TOP = RAIL_Z0 + 1.375 * IN           # 72.4  cushion sits here
LX = (22.75 / 2 + 0.875 / 2) * IN        # 30.0  leg centre
CU_HW = 4.25 * IN / 2                    # 5.4   cushion half width
PAL = ["londonblue", "amethyst", "aquamarine"]


def smoothstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def leg(s, sx, rng, ver):
    x0 = sx * LX
    zs = np.linspace(2.0, 67.5, 40); u = (zs - zs[0]) / (zs[-1] - zs[0])
    # a slow S: leans in through the waist, opens again under the rail (liquid, not a plank)
    xs = x0 - sx * 0.9 * np.sin(math.pi * u) + sx * 0.5 * np.sin(2 * math.pi * u) * 0.5
    pts = np.column_stack([xs, np.zeros_like(zs), zs])
    hw = lambda t: 3.3 - 1.95 * np.sin(math.pi * np.clip(t / 0.85, 0, 1)) ** 1.1 + 1.3 * smoothstep((t - 0.78) / 0.22)
    ht = lambda t: 1.1 - 0.35 * np.sin(math.pi * np.clip(t / 0.85, 0, 1)) + 0.1 * smoothstep((t - 0.8) / 0.2)
    v2.blade(s, pts, hw, ht, normal=(1, 0, 0), k=0.8, grooves=12, both=True, gr=0.24, barb=0.7, groove_span=(0.02, 0.2))
    s.ellipsoid((x0, 0, 3.6), (1.5, 3.4, 1.6), k=1.6)      # molten collar where leg meets foot
    # a liquid tendon laid over the outer face: wanders across the leg, swells, and runs out to a needle under the horns
    uu = u[3:-4]; tz = zs[3:-4]
    tx = xs[3:-4] + sx * (ht(uu) * 0.85)
    ty = 1.1 * np.sin(2.3 * math.pi * uu + 0.6) * (0.4 + 0.6 * np.sin(math.pi * uu))
    K.ribbon(s, np.column_stack([tx, ty, tz]), w=0.6, thin=0.7, ends=(0.2, 0.3), wkeys=[(0, 0.6), (0.3, 1.3), (0.6, 0.8), (1, 1.1)], k=0.5)
    top = pts[-1]
    # two horns fork off the leg head and cradle the leather's lower flanks, ending just under the work top so the bare frame stays a sawhorse
    for sy in (1, -1):
        h = np.array([[0, 64.5], [sy * 2.6, 68.6], [sy * 5.6, 71.2], [sy * 6.7, 73.3], [sy * 6.8, 73.9]])   # p6: tips stop under the 74.3 work top (seat-off rule)
        hp = sdf.catmull(np.column_stack([np.full(len(h), top[0]), h]), 10)
        v2.blade(s, hp, lambda t: 1.35 * (1 - t) ** 0.9 + 0.12, lambda t: 0.95 * (1 - t) ** 0.7 + 0.12, normal=(1, 0, 0), k=0.6,
                 grooves=10, both=True, gr=0.16, barb=0.5, groove_span=(0.1, 0.6))
        s.sphere(hp[-1], 0.42, k=0.15)


def foot(s, sx, rng):
    x0 = sx * LX
    yz = np.array([[-17.4, 4.6], [-17.2, 2.0], [-15.2, 0.95], [-10, 1.7], [-4, 3.2], [0, 3.6],
                   [4, 3.2], [10, 1.7], [15.2, 0.95], [17.2, 2.0], [17.4, 4.6]])
    pts = sdf.catmull(np.column_stack([np.full(len(yz), x0), yz]), 10)
    # crescent: deep at the leg, thin at the pads, the two ends curl up into needles
    hw = lambda t: 0.15 + 2.1 * np.sin(math.pi * np.clip(t, 0, 1)) ** 0.75 - 1.1 * np.exp(-((t - 0.13) / 0.06) ** 2) * 0
    ht = lambda t: 0.18 + 1.35 * np.sin(math.pi * np.clip(t, 0, 1)) ** 0.5
    v2.blade(s, pts, hw, ht, normal=(1, 0, 0), k=0.8, grooves=16, both=True, gr=0.24, barb=0.7, groove_span=(0.2, 0.8))
    for e in (pts[0], pts[-1]):
        s.sphere(e, 0.4, k=0.15)
    # ground pads: a molten drop under each contact point so it stands flat
    for sy in (1, -1):
        s.ellipsoid((x0, sy * 15.0, 0.75), (1.0, 1.9, 0.75), k=0.6)


def rail(s, rng):
    xz = [(-38.6, 63.2), (-39.2, 66.5), (-38.3, 69.8), (-36.2, 71.5), (-30, 71.6), (0, 71.6),
          (30, 71.6), (36.2, 71.5), (38.3, 69.8), (39.2, 66.5), (38.6, 63.2)]
    pts = sdf.catmull(np.array([(x, 0, z) for x, z in xz]), 10)
    e = 0.11
    hw = lambda t: 0.15 + 2.55 * smoothstep(np.minimum(t, 1 - t) / e) + 0.9 * np.exp(-((t - 0.5) / 0.16) ** 2)
    ht = lambda t: 0.15 + 1.28 * smoothstep(np.minimum(t, 1 - t) / e)
    v2.blade(s, pts, hw, ht, normal=(0, 1, 0), k=0.8, grooves=0)
    # removable seat: a flat 2.86 cm working top at 74.3 (the original rail top); the cushion's slot slides over it
    s.prism((-34.0, 0, 71.0), (34.0, 0, 71.0), 1.43, 1.43, 0.0, 3.3, normal=(0, 0, 1), k=0.4)
    for p in (pts[0], pts[-1]):
        s.sphere(p, 0.48, k=0.15)


def moth(s, st, rng, ver):
    """The stretcher: one moth in the plane y=0 between the legs. Wing tips run into the legs so the moth is the brace."""
    m = Flat(o=(0, 0, 0), u=(1, 0, 0), v=(0, 0, 1))      # local (x, z); local 'up' is -y (front)
    cz = 33.0
    wisp.WMUL[0] = 1.7
    tips = []
    for sx in (1, -1):
        f = W2.vein_wing(s, m, st, (sx * 2.2, cz + 1.0), 25.0, ang=0.26, sx=sx, rng=rng, shape="moth_f", stones=1,
                         pal=PAL, z=0.0)
        h = W2.vein_wing(s, m, st, (sx * 2.2, cz - 2.0), 17.5, ang=-0.4, sx=sx, rng=rng, shape="moth_h", stones=0,
                         pal=PAL[::-1], z=0.0)
        tips.append((sx, f["tip"], h["tip"]))
    wisp.WMUL[0] = 1.0
    body(s, m, st, (0, cz), 26.0, PAL, kind="butterfly", rng=rng)
    # back face: a second stone so the moth reads from behind too
    D = 26.0 * 0.13
    s.ellipsoid((0, D * 0.3, cz + 0.5), (D * 0.55, D * 0.5, D * 0.6), k=0.6)
    Mo.prong(s, st, (0, D * 0.5, cz + 0.5), D * 0.9, PAL[1], normal=(0, 1, 0), n=4, wire=0.26)
    for sx, ft, ht in tips:
        for t, w in ((ft, 1.0), (ht, 0.85)):
            t = np.asarray(t, float)
            xl = sx * (LX - 1.0)
            if abs(t[0]) > abs(xl):
                continue
            a = np.array([t[0], 0.0, t[1]]); b = np.array([xl + sx * 0.6, 0.0, t[1] + 0.6])
            mid = (a + b) / 2 + np.array([0, 0, 0.8])
            K.ribbon(s, np.array([a, mid, b]), w=w, thin=0.75, ends=(0.0, 0.0), wkeys=[(0, 0.7), (0.5, 0.85), (1, 1.4)], k=0.5)
    return tips


def buckle(s, sx, rng):
    """Strap buckle on the front flank of the cushion: a swelling liquid frame, a bar and a needle tongue ending in a bead."""
    x0 = sx * 20.0; y0 = -(CU_HW + 0.55); z0 = 75.4
    a, b = 2.3, 1.8
    th = np.linspace(0, 2 * math.pi, 49)
    ring = np.column_stack([x0 + a * np.sign(np.cos(th)) * np.abs(np.cos(th)) ** 0.6, np.full_like(th, y0),
                            z0 + b * np.sign(np.sin(th)) * np.abs(np.sin(th)) ** 0.6])
    r = 0.32 + 0.16 * (0.5 + 0.5 * np.cos(2 * th + rng.uniform(0, 1)))
    s.stroke(ring, r, k=0.12, normals=np.tile([0, 1, 0], (len(th), 1)), flat=1.4)
    tong = np.array([(x0 - sx * 0.2, y0 - 0.15, z0), (x0 + sx * 0.8, y0 - 0.35, z0 + 0.1), (x0 + sx * (a + 0.7), y0 - 0.25, z0 + 0.25)])
    K.ribbon(s, tong, w=0.28, thin=0.8, ends=(0.0, 0.6), k=0.15)
    s.sphere(tong[-1], 0.2, k=0.1)


# Furniture stones are real stones: the kit works in jewelry units, but here 1 unit = 1 cm, so a "5" stone would be
# 50 mm. Cap every claw-set stone at the largest common calibrated faceted size for its species (stone check, Nov 18).
STONE_CAP_CM = {"amethyst": 2.0, "citrine": 2.0, "topaz": 1.8, "londonblue": 1.6, "aquamarine": 1.0, "garnet": 1.0,
                "moonstone": 0.8, "labradorite": 1.0, "peridot": 0.8}
_prong0 = Mo.prong


def _capped_prong(s, st, c, D, kind, L=None, **kw):
    cap = STONE_CAP_CM.get(kind, 1.0)      # furniture stones are rounds (the jewelry oval table is in mm)
    return _prong0(s, st, c, min(D, cap), kind, L=None, **kw)


Mo.prong = _capped_prong


def build_metal(ver="p1", seed=7):
    rng = np.random.default_rng(seed)
    st = []
    with wisp.organic():
        s = Scene()
        for sx in (1, -1):
            foot(s, sx, rng)
            leg(s, sx, rng, ver)
        rail(s, rng)
        moth(s, st, rng, ver)
        s2 = Scene()        # buckles are separate castings (they live on the straps)
        for sx in (1, -1):
            buckle(s2, sx, rng)
    return s, st, s2


def build_leather(straps=((20.0, 2.0),), strap_sc=1.028, mirror=True):
    strap_spec = straps
    import trimesh, manifold3d as m3
    sys.path.insert(0, os.path.dirname(HERE))
    import importlib.util
    spec = importlib.util.spec_from_file_location("krenov_model", os.path.join(HERE, "krenov_model.py"))
    km = importlib.util.module_from_spec(spec); spec.loader.exec_module(km)
    cu = km.build(km.P)["Cushion"]
    P = km.P
    rz0 = P["top"] - P["rail_H"]; lt = rz0 + P["slot_D"]
    fill = km.box(-P["rail_L"] / 2, P["rail_L"] / 2, -P["rail_T"] / 2 - 0.01, P["rail_T"] / 2 + 0.01, lt - 0.01, P["top"] + 0.01)
    cu = cu + fill
    cu = cu.scale([IN, IN, IN])
    zc = 76.0
    def ring(x0, x1, sc):
        sl = cu - km.box(-99, x0, -99, 99, -99, 199) - km.box(x1, 99, -99, 99, -99, 199)
        return sl.translate([0, 0, -zc]).scale([1, sc, sc]).translate([0, 0, zc])
    straps = None
    for xc, wd in strap_spec:
        for sx in ((1, -1) if mirror else (1,)):
            x0, x1 = sorted([sx * (xc - wd / 2), sx * (xc + wd / 2)])
            band = ring(x0, x1, strap_sc) - cu
            straps = band if straps is None else straps + band
    L = P["rail_L"] / 2 * IN
    piping = None
    for sx in (1, -1):      # piped welt around each end panel, the way a bolster is sewn
        x0, x1 = sorted([sx * (L - 0.2), sx * (L - 0.75)])
        wl = ring(x0, x1, 1.035) - cu
        piping = wl if piping is None else piping + wl
    tm = lambda mf: trimesh.Trimesh(mf.to_mesh().vert_properties[:, :3], mf.to_mesh().tri_verts)
    return tm(cu), tm(straps), tm(piping)


def mesh_metal(ver="p1", vox=0.09):
    import trimesh
    s, st, s2 = HOOK["metal"](ver)
    import make
    make.bridge(s, [0.0], vox_c=0.15, rounds=3)
    P = s.array(); print("metal prims", len(P), "stones", len(st), flush=True)
    V, F = sdf.mesh(P, vox)
    path = f"/tmp/sawmoth_{os.getpid()}.stl"
    m = sdf.save_stl(V, F, path, smooth=3); os.remove(path)
    # one casting: keep the main body. Anything else is engraving debris (islands the groove cuts free), dropped here.
    parts = sorted(m.split(only_watertight=False), key=lambda p: -p.area)
    print("dropped islands", [round(p.area, 2) for p in parts[1:] if p.area > 0.05], flush=True)
    parts = parts[:1]; m = parts[0]
    V2, F2 = sdf.mesh(s2.array(), 0.04)
    b = sdf.save_stl(V2, F2, path, smooth=2); os.remove(path)
    return m, st, b, len(parts)


HOOK = {}


def finish(kind):
    """Metal finish: polished (default sterling), oxidised (washed: dark recesses, polished highs), brushed steel."""
    import bpy
    m = bpy.data.materials.get("sterling_real")
    if kind == "polished" or m is None: return
    t = m.node_tree; N = t.nodes; b = N["Principled BSDF"]
    if kind == "steel":
        b.inputs["Base Color"].default_value = (0.62, 0.63, 0.65, 1)
        for l in list(b.inputs["Roughness"].links): t.links.remove(l)
        b.inputs["Roughness"].default_value = 0.22
        if "Anisotropic" in b.inputs: b.inputs["Anisotropic"].default_value = 0.6
    elif kind == "oxidised":
        g = N.new("ShaderNodeNewGeometry"); cr = N.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
        el[0].position = 0.47; el[0].color = (0.05, 0.048, 0.045, 1); el[1].position = 0.56; el[1].color = (0.8, 0.79, 0.77, 1)
        t.links.new(g.outputs["Pointiness"], cr.inputs[0]); t.links.new(cr.outputs[0], b.inputs["Base Color"])
        for l in list(b.inputs["Roughness"].links): t.links.remove(l)
        b.inputs["Roughness"].default_value = 0.3


def look_at(cam, target, d, dist):
    from mathutils import Vector
    d = Vector(d).normalized(); cam.location = Vector(target) + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()


def leather_mat():
    import bpy
    m = bpy.data.materials.new("leather_black"); m.use_nodes = True; t = m.node_tree; N = t.nodes
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.014, 0.013, 0.013, 1)
    b.inputs["Roughness"].default_value = 0.46
    if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = 0.12; b.inputs["Coat Roughness"].default_value = 0.35
    if "Sheen Weight" in b.inputs: b.inputs["Sheen Weight"].default_value = 0.15
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 9.0
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 3
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.05
    t.links.new(tc.outputs["Object"], vo.inputs["Vector"]); t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMath"); mx.operation = 'ADD'
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.35
    t.links.new(vo.outputs["Distance"], mx.inputs[0]); t.links.new(nz.outputs[0], sc.inputs[0]); t.links.new(sc.outputs[0], mx.inputs[1])
    t.links.new(mx.outputs[0], bp.inputs["Height"]); t.links.new(bp.outputs[0], b.inputs["Normal"])
    # wear: a touch glossier where the seat is sat on (top)
    return m


def render(tag="p1", ver="p1"):
    import bpy, jlib
    from mathutils import Vector
    OUT = os.environ.get("OUTDIR", "/tmp/sawmoth"); os.makedirs(OUT, exist_ok=True)
    m, st, bk, nparts = mesh_metal(ver, float(os.environ.get("VOX", 0.09)))
    OFF = bool(os.environ.get("OFF"))          # seat lifted off: the bare sawhorse
    cu, straps, piping = HOOK["leather"]()
    info = dict(metal_parts=nparts, metal_watertight=bool(m.is_watertight), metal_extents_cm=[round(float(x), 1) for x in m.extents],
                stones=[dict(kind=r["kind"], D=round(r["D"], 2)) for r in st])
    print(info, flush=True); json.dump(info, open(os.path.join(OUT, f"sawmoth_{tag}.json"), "w"), indent=1)
    jlib.reset()
    ob = v2.to_blender(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.int32), "metal")
    objs = [ob]
    if not OFF:
        objs.append(v2.to_blender(np.asarray(bk.vertices, np.float32), np.asarray(bk.faces, np.int32), "buckles"))
    lm = leather_mat()
    lm2 = lm.copy(); lm2.name = "leather_strap"; lm2.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.28
    lm2.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.019, 0.018, 1)
    for nm, tmesh, bev in (() if OFF else (("cushion", cu, 0.9), ("straps", straps, 0.12), ("piping", piping, 0.1))):
        o = v2.to_blender(np.asarray(tmesh.vertices, np.float32), np.asarray(tmesh.faces, np.int32), nm)
        o["metal"] = False
        if "metal" in o.keys(): del o["metal"]
        o.data.materials.clear(); o.data.materials.append(lm)
        bv = o.modifiers.new("bev", 'BEVEL'); bv.width = bev; bv.segments = 5; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(50)
        bv.harden_normals = False
        for p in o.data.polygons: p.use_smooth = True
        try: o.data.set_sharp_from_angle(angle=math.radians(40))
        except Exception: pass
        objs.append(o)
    for r in st:
        so = v2.stone_mesh(r, r["kind"]); so.data.materials.append(v2.facet_mat(r["kind"])); so["kind"] = r["kind"]; objs.append(so)
    res = int(os.environ.get("PRES", 900)); spp = int(os.environ.get("PSPP", 24))
    jlib.studio_white(objs, view=(0.8, -1, 0.45), res=res, samples=spp, margin=1.1, lens=85)
    for o in list(bpy.context.scene.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o, do_unlink=True)
    v2.realism(objs)
    finish(HOOK.get("finish", "polished"))
    for nm in (() if OFF else ("cushion", "straps", "piping")):
        o = bpy.data.objects.get(nm); o.data.materials.clear(); o.data.materials.append(lm if nm == "cushion" else lm2)
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = True; sc.cycles.use_denoising = True
    views = HOOK.get("views") or {
        "hero": ((0.85, -1.0, 0.42), (0, 0, 40), 165),
        "front": ((0.0, -1.0, 0.06), (0, 0, 40), 160),
        "side": ((1.0, 0.0, 0.06), (0, 0, 40), 160),
        "moth": ((0.12, -1.0, 0.12), (0, 0, 31), 95),
        "top": ((0.55, -0.7, 0.55), (22, -2, 72), 60),
        "foot": ((0.9, -0.8, 0.35), (30, 0, 6), 70),
    }
    want = os.environ.get("VIEWS", "hero,front,side,moth,top,foot").split(",")
    cd = bpy.data.cameras.new("cam"); cd.lens = 85; cd.clip_start = 1; cd.clip_end = 1e5
    cam = bpy.data.objects.new("cam", cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    for k in want:
        d, tg, dist = views[k]
        look_at(cam, tg, d, dist * 85 / 50 * 1.0)
        sc.render.filepath = os.path.join(OUT, f"sawmoth_{tag}_{k}{'_off' if OFF else ''}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", k, flush=True)


HOOK.update(metal=build_metal, leather=build_leather)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "mesh"
    if mode == "mesh":
        m, st, bk, n = mesh_metal()
        print("parts", n, "watertight", m.is_watertight, "extents", m.extents, "stones", len(st))
    else:
        render(sys.argv[2] if len(sys.argv) > 2 else "p1")
