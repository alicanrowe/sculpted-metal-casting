"""Build one Governor piece: exact CSG parts -> checks -> STL / render / web GLB.
    python gmake.py <piece> check     -> checks only (prints a report, writes OUT/<piece>.json + STLs)
    python gmake.py <piece> preview   -> checks + one hero render OUT/<piece>_hero.png
    python gmake.py <piece> local4    -> checks + four views OUT/<piece>_v0001..4.png (for square.py)
    python gmake.py <piece> glb       -> web GLB OUT/<piece>.glb (parts keep their finishes)
    python gmake.py list
env: OUTDIR, PRES (px), PSPP (samples), HEROVIEW (index of view to put first)
Checks (all must pass before a render is shown):
  bodies    every part is one closed solid (decompose == 1), manifold
  clip      no two parts overlap (exact boolean intersection volume < 0.001 mm3); min gap printed
  balls     every ball is a stock precision size, overlaps no metal, and is HELD (it cannot slide out
            along any of 98 directions without hitting metal)
  wall      thinnest wall (ray-sampled, 5th percentile) per part, >= 0.5 mm (machined sterling; knurl teeth are
            measured on the part's probe solid, without the texture)
"""
import sys, os, json, math, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, '..', 'kit'))   # jlib, v2, sdf, square: the shared render and studio code
import mlib
from mlib import M

OUT = os.environ.get("OUTDIR", os.path.join(HERE, "..", "out")); os.makedirs(OUT, exist_ok=True)
STERLING = 10.36
BALL_STOCK = [1.0, 1.5, 2.0, 2.5, 3.0, 3.175, 3.5, 3.969, 4.0, 4.5, 4.763, 5.0, 5.5, 6.0, 6.35]   # mm, ruby / sapphire precision balls
VIEWS = {
    "flat": [(0.14, -0.34, 1.0), (0.0, -0.04, 1.0), (0.95, -0.25, 0.45), (-0.35, -1.0, 0.3)],
    "ring": [(0.6, -1.0, 0.8), (0.0, -0.12, 1.0), (1.0, 0.0, 0.18), (0.0, -1.0, 0.12)],
    "cuff": [(0.25, -0.6, 1.0), (0.0, -0.05, 1.0), (1.0, -0.25, 0.35), (0.0, -1.0, 0.2)],
    "hang": [(0.3, -0.45, 1.0), (0.0, -0.03, 1.0), (1.0, -0.1, 0.25), (-0.6, -0.5, 0.6)],
    "front": [(0.35, -1.0, 0.45), (0.0, -1.0, 0.05), (1.0, -0.3, 0.3), (-0.5, -0.6, 1.0)],
}


def get_piece(name):
    from pieces import PIECES
    return PIECES[name]()


def ball_solid(b, shrink=0.0):
    r = b["D"] / 2 - shrink
    return M.sphere(r, 48).translate(tuple(b["c"]))


def checks(pc, verbose=True):
    rep = dict(name=pc.name, parts=[], fails=[])
    allm = []
    for p in pc.parts:
        s = p["solid"]
        comps = s.decompose()
        if len(comps) > 1:                 # drop zero-volume slivers a warp can leave (not metal)
            keep = [c for c in comps if c.volume() > 0.01]
            if len(keep) < len(comps):
                s = M.compose(keep) if len(keep) > 1 else keep[0]; p["solid"] = s
        st = str(s.status())
        n = len(s.decompose())
        v = s.volume()
        p["bodies"] = n
        rep["parts"].append(dict(label=p["label"], finish=p["finish"], bodies=n, status=st, volume_mm3=round(v, 2),
                                 tris=s.num_tri()))
        if n != 1 and not p.get("layer"): rep["fails"].append(f"bodies {p['label']} = {n}")
        if "NoError" not in st: rep["fails"].append(f"status {p['label']} {st}")
        allm.append(s)
    # clipping: exact intersections between every pair of parts
    clip = []
    for i in range(len(pc.parts)):
        for j in range(i + 1, len(pc.parts)):
            a, b = pc.parts[i]["solid"], pc.parts[j]["solid"]
            if pc.parts[j].get("layer") and j == i + 1: 
                iv = (a ^ b).volume()
                if iv > 1e-3: rep["fails"].append(f"layer overlap {pc.parts[j]['label']} {iv:.4f} mm3")
                continue
            ba, bb = a.bounding_box(), b.bounding_box()
            if any(ba[k] > bb[k + 3] + 0.5 or bb[k] > ba[k + 3] + 0.5 for k in range(3)):
                continue
            iv = (a ^ b).volume()
            gap = a.min_gap(b, 0.5)
            clip.append((pc.parts[i]["label"], pc.parts[j]["label"], round(iv, 4), round(gap, 3)))
            if iv > 1e-3: rep["fails"].append(f"clip {pc.parts[i]['label']} x {pc.parts[j]['label']} {iv:.4f} mm3")
    rep["clip"] = clip
    metal = mlib.union([p["solid"] for p in pc.parts if p["finish"] != "leather"])
    # balls
    bl = []
    dirs = fib_dirs(98)
    for b in pc.balls:
        okstock = min(abs(b["D"] - s_) for s_ in BALL_STOCK) < 0.01
        bs = ball_solid(b)
        ov = (bs ^ metal).volume()
        gap = bs.min_gap(metal, 1.0)
        # held: try to slide the ball out along every direction; it must collide (with a 0.02 mm allowance) every time
        small = ball_solid(b, 0.03)
        free = 0
        for d in dirs:
            hit = False
            for t in np.linspace(0.1, 1.6, 12) * b["D"]:
                if (small.translate(tuple(d * t)) ^ metal).volume() > 1e-4:
                    hit = True; break
            if not hit: free += 1
        held = free == 0
        res = dict(kind=b["kind"], D=b["D"], stock=okstock, overlap_mm3=round(ov, 4), seat_gap=round(gap, 3), escapes=free, held=held)
        bl.append(res)
        if not okstock: rep["fails"].append(f"ball {b['D']} mm not a stock size")
        if ov > 2e-3: rep["fails"].append(f"ball overlaps metal {ov:.4f} mm3")
        if gap > 0.08: rep["fails"].append(f"ball not seated (gap {gap:.3f} mm)")
        if not held: rep["fails"].append(f"ball can escape along {free} of {len(dirs)} directions")
    rep["balls"] = bl
    V, F = mlib.to_np(metal)
    import trimesh
    tm = trimesh.Trimesh(V, F, process=False)
    rep["size_mm"] = [round(float(x), 1) for x in tm.extents]
    rep["volume_cm3"] = round(metal.volume() / 1000, 3)
    rep["sterling_g"] = round(metal.volume() / 1000 * STERLING, 1)
    rep["watertight"] = bool(tm.is_watertight)
    rep["bodies_total"] = sum(p["bodies"] for p in pc.parts if not p.get("layer"))
    # wall thickness (ray-sampled inward), per part
    walls = []
    for p in pc.parts:
        if p.get("layer"): continue
        th = thickness(p.get("probe") or p["solid"])
        walls.append((p["label"], th[0], th[1]))
        if th[0] < 0.5 and not p.get("bought"): rep["fails"].append(f"thin wall {p['label']} p5 {th[0]} mm")
    rep["walls"] = walls
    rep["ok"] = not rep["fails"]
    if verbose:
        print(json.dumps(rep, indent=None, default=str)[:4000], flush=True)
    return rep, metal


def fib_dirs(n):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


def thickness(solid, n=1500):
    """Ray-sampled wall: from points on the surface, cast inward along -normal to the far side (Blender BVH:
    fast and light on long, curved parts where trimesh's ray test ran out of memory)."""
    import trimesh
    import bpy  # noqa: F401  (loads mathutils)
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    V, F = mlib.to_np(solid)
    tm = trimesh.Trimesh(V, F, process=False)
    pts, fi = trimesh.sample.sample_surface_even(tm, n, seed=1)
    nrm = tm.face_normals[fi]
    bvh = BVHTree.FromPolygons(V.tolist(), F.tolist())
    th = []
    for p_, n_ in zip(pts, nrm):
        o = Vector(p_ - n_ * 0.003)
        hit = bvh.ray_cast(o, Vector(-n_), 60.0)
        if hit[0] is not None: th.append((hit[0] - o).length)
    th = np.array(th); th = th[th > 0.02]
    if not len(th): return (9.9, 9.9)
    return (round(float(np.percentile(th, 5)), 2), round(float(th.min()), 2))


def export(pc, metal, rep):
    import trimesh
    sd = os.path.join(OUT, "parts"); os.makedirs(sd, exist_ok=True)
    V, F = mlib.to_np(metal)
    trimesh.Trimesh(V, F, process=False).export(os.path.join(OUT, pc.name + ".stl"))
    for p in pc.parts:
        V, F = mlib.to_np(p["solid"])
        trimesh.Trimesh(V, F, process=False).export(os.path.join(sd, f"{pc.name}__{p['label']}.stl"))
    info = dict(name=pc.name, kind=pc.kind, watertight=rep["watertight"], volume_cm3=rep["volume_cm3"],
                sterling_g=rep["sterling_g"], size_mm=rep["size_mm"],
                parts=[dict(label=p["label"], finish=p["finish"]) for p in pc.parts],
                stones=[dict(kind=b["kind"], D=b["D"], L=b["L"], c=b["c"], shape="ball", setting="caged ball") for b in pc.balls],
                notes=pc.notes, checks=dict(ok=rep["ok"], fails=rep["fails"], clip=rep["clip"], balls=rep["balls"], walls=rep["walls"]))
    json.dump(info, open(os.path.join(OUT, pc.name + ".json"), "w"), indent=1, default=str)


# ------------------------------------------------------------------ Blender
def materials():
    import bpy
    def princ(name, col, rough, aniso=0.0, noise=(0.0, 0.0)):
        m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; N = t.nodes
        b = N["Principled BSDF"]; b.inputs["Metallic"].default_value = 1.0
        b.inputs["Base Color"].default_value = (*col, 1)
        if aniso: b.inputs["Anisotropic"].default_value = aniso
        if noise[1] > 0:
            nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 80.0; nz.inputs["Detail"].default_value = 2
            rr = N.new("ShaderNodeMapRange"); rr.inputs[3].default_value = noise[0]; rr.inputs[4].default_value = noise[1]
            t.links.new(nz.outputs[0], rr.inputs[0]); t.links.new(rr.outputs[0], b.inputs["Roughness"])
        else:
            b.inputs["Roughness"].default_value = rough
        return m
    return {
        "bright": princ("g_bright", (0.97, 0.96, 0.945), 0, noise=(0.03, 0.065)),
        "satin": princ("g_satin", (0.95, 0.945, 0.935), 0, noise=(0.13, 0.19)),
        "black": princ("g_black", (0.15, 0.145, 0.14), 0, noise=(0.2, 0.28)),
        "steel": princ("g_steel", (0.6, 0.62, 0.65), 0.09),
        "leather": leather(),
    }


def leather():
    import bpy
    m = bpy.data.materials.new("g_leather"); m.use_nodes = True; N = m.node_tree.nodes; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.022, 0.019, 0.017, 1); b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.5
    if "Sheen Weight" in b.inputs: b.inputs["Sheen Weight"].default_value = 0.3
    return m


def ball_mat(kind):
    import bpy
    col, dens, ior = {"ruby": ((0.9, 0.06, 0.16), 1.1, 1.76), "sapphire": ((0.93, 0.95, 1.0), 0.05, 1.76)}[kind]
    m = bpy.data.materials.new("ball_" + kind); m.use_nodes = True; t = m.node_tree; N = t.nodes
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*[0.8 + 0.2 * c for c in col], 1)
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.0
    b.inputs["IOR"].default_value = ior
    va = N.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (*col, 1); va.inputs["Density"].default_value = dens
    t.links.new(va.outputs[0], N["Material Output"].inputs["Volume"])
    return m


def to_blender(V, F, name, sharp=32.0):
    import bpy
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set("co", np.asarray(V, np.float32).ravel())
    F = np.asarray(F, np.int32)
    me.loops.add(F.size); me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set("loop_start", np.arange(0, F.size, 3, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(F), 3, np.int32))
    me.update(); me.validate()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    thr = math.radians(sharp)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > thr: e.smooth = False
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    return ob


def scene_objs(pc, glb=False, scale=1.0):
    import bpy
    mats = materials()
    objs = []
    for p in pc.parts:
        V, F = mlib.to_np(p["solid"])
        ob = to_blender(V * scale, F, f"{pc.name}_{p['label']}")
        ob.data.materials.append(mats[p["finish"]]); ob["finish"] = p["finish"]
        objs.append(ob)
    for i, b in enumerate(pc.balls):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=b["D"] / 2 * scale,
                                             location=tuple(np.asarray(b["c"]) * scale))
        o = bpy.context.active_object; o.name = f"ball{i}"
        bpy.ops.object.shade_smooth()
        o.data.materials.append(ball_mat(b["kind"])); o["kind"] = b["kind"]
        objs.append(o)
    return objs


def place_cams(objs, views, lens=100, margin=1.15):
    import bpy
    from mathutils import Vector
    s = bpy.context.scene
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    ctr = (lo + hi) / 2; size = (hi - lo).length
    fov = 2 * math.atan(36 / 2 / lens); dist = (size * margin / 2) / math.tan(fov / 2)
    for i, v in enumerate(views):
        d = Vector(v).normalized()
        cd = bpy.data.cameras.new(f"cam{i}"); cd.lens = lens; cd.clip_start = 1; cd.clip_end = 1e5
        cam = bpy.data.objects.new(f"cam{i}", cd); bpy.context.collection.objects.link(cam)
        cam.location = ctr + d * dist
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        mk = s.timeline_markers.new(f"view{i}", frame=i + 1); mk.camera = cam
        if i == 0: s.camera = cam
    s.frame_start = 1; s.frame_end = len(views); s.frame_set(1)


def drop_front_flag(sc_, objs):
    """studio_white's low front grey card turns every face that looks at the camera black; machined pieces have
    big flat fronts, so take it out (the side flags still draw the edges)."""
    import bpy
    from mathutils import Vector
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    ctr = (lo + hi) / 2
    for o in list(sc_.objects):
        if o.type == 'MESH' and o.data.materials and o.data.materials[0].name.startswith("card"):
            d = o.location - ctr
            if d.y < 0 and d.z < 0.05 * (hi - lo).length and abs(d.x) < abs(d.y) * 1.2:
                bpy.data.objects.remove(o, do_unlink=True)


def tent(sc_):
    """Machined parts photograph on a bright sweep: the floor half of the tent is light, with one narrow dark
    line just under the horizon (it draws the crisp edge on every chamfer) instead of the cast-silver dark floor."""
    w = sc_.world
    for nd in w.node_tree.nodes:
        if nd.type == "VALTORGB":
            el = nd.color_ramp.elements
            while len(el) > 2: el.remove(el[1])
            el[0].position = 0.0; el[0].color = (0.62, 0.62, 0.62, 1)
            el[1].position = 1.0; el[1].color = (0.9, 0.9, 0.9, 1)
            for pos, g in ((0.44, 0.95), (0.49, 0.05), (0.52, 0.05), (0.56, 0.78)):
                e = el.new(pos); e.color = (g, g, g, 1)
            nd.color_ramp.interpolation = 'LINEAR'


def render(pc, mode):
    import bpy
    sys.path.insert(0, HERE)
    import jlib, v2
    jlib.reset()
    objs = scene_objs(pc)
    views = list(pc.notes.get("views") or VIEWS[pc.kind])
    if os.environ.get("HEROVIEW"): views = [views[int(os.environ["HEROVIEW"])]] + views
    res, spp = int(os.environ.get("PRES", 720)), int(os.environ.get("PSPP", 32))
    keep = {o.name: o.data.materials[0] for o in objs if o.data.materials}
    jlib.studio_white(objs, view=views[0], res=res, samples=spp, margin=1.15, lens=100)
    for o in list(bpy.context.scene.objects):
        if o.name == "floor" or o.type == 'CAMERA':
            bpy.data.objects.remove(o, do_unlink=True)
    os.environ.setdefault("EXPO", "0.35")
    v2.realism([])                     # world, tone mapping, bounces (materials stay ours)
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(keep[o.name])
    tent(sc_=bpy.context.scene)
    drop_front_flag(bpy.context.scene, objs)
    place_cams(objs, views)
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.cycles.samples = spp; sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    if mode == "preview":
        sc.render.filepath = os.path.join(OUT, pc.name + os.environ.get("TAG", "") + "_hero.png")
        bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = os.path.join(OUT, pc.name + "_v")
        bpy.ops.render.render(animation=True)


def glb(pc):
    import bpy
    sys.path.insert(0, HERE)
    import jlib
    jlib.reset()
    objs = scene_objs(pc, glb=True, scale=0.001)
    cap = int(os.environ.get("GLBFACES", 120000))
    tot = sum(len(o.data.polygons) for o in objs if not o.get("kind"))
    if tot > cap:
        for o in objs:
            if o.get("kind"): continue
            d = o.modifiers.new("d", 'DECIMATE'); d.ratio = max(0.05, cap / tot)
    for o in objs:   # glTF has no volume absorption: give the balls a flat transmissive tint
        if o.get("kind"):
            mt = o.data.materials[0]; b = mt.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (0.85, 0.1, 0.18, 1) if o["kind"] == "ruby" else (0.95, 0.96, 1, 1)
            b.inputs["Transmission Weight"].default_value = 0.6
    out = os.path.join(OUT, pc.name + ".glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True)
    print("glb", out, os.path.getsize(out), flush=True)


if __name__ == "__main__":
    name = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else "check"
    if name == "list":
        from pieces import PIECES
        print("\n".join(PIECES)); sys.exit()
    t0 = time.time()
    pc = get_piece(name)
    print(name, "built", round(time.time() - t0, 1), "s", flush=True)
    if mode == "glb":
        glb(pc); sys.exit()
    rep, metal = checks(pc)
    export(pc, metal, rep)
    print("CHECK", name, "OK" if rep["ok"] else "FAIL " + "; ".join(rep["fails"]), "|", rep["sterling_g"], "g", rep["size_mm"],
          "bodies", rep["bodies_total"], "parts", len(pc.parts), round(time.time() - t0, 1), "s", flush=True)
    if mode in ("preview", "local4"):
        render(pc, mode)
