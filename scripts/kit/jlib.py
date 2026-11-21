"""jewelry parts library (Blender bpy, units = mm).

Every piece is built from a small menu of reusable parts, so the same parts
can later become a jewelry parts menu:

  stroke()     calligraphic tapered stroke (swash, thorn, vein, wire)
  thorn()      curved stroke that tapers to a castable 0.5 mm tip
  bezel()      cabochon cup: wall + seat ledge + light hole
  cab()        calibrated cabochon stone (render only, never cast)
  bead()       solid metal bead
  eye()        jump-ring eye (attachment point)
  pad()        flat solder pad (for bought findings: clip backs, posts)
  fuse()       voxel-union a list of parts into one watertight castable solid

Casting rules used throughout (Formlabs Castable Wax 40 -> sterling):
  min wire / stroke diameter 1.0 mm (veins), 1.4 mm structural
  tips end at >= 0.5 mm diameter
  bezel wall 0.7 mm, seat ledge 0.6 mm
  ring shank >= 1.6 mm thick
  eyes: 0.9 mm radius wire, 1.6 mm hole
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

TAU = math.tau
EXPO = 6.0


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001
    s.unit_settings.length_unit = 'MILLIMETERS'


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


_profiles = {}


def _profile(flat):
    key = round(flat, 3)
    if key in _profiles:
        return _profiles[key]
    cu = bpy.data.curves.new(f"prof_{key}", 'CURVE')
    sp = cu.splines.new('NURBS')
    n = 16
    sp.points.add(n - 1)
    for i in range(n):
        a = TAU * i / n
        sp.points[i].co = (math.cos(a), math.sin(a) * flat, 0, 1)
    sp.use_cyclic_u = True
    sp.order_u = 3
    cu.resolution_u = 3
    ob = bpy.data.objects.new(f"prof_{key}", cu)
    _profiles[key] = ob
    return ob


def stroke(pts, radii, name="stroke", res=12, flat=1.0, tilt=0.0, closed=False, twist='MINIMUM'):
    """Tapered tube through pts (list of xyz) with per-point radius (mm)."""
    if isinstance(radii, (int, float)):
        radii = [radii] * len(pts)
    if callable(radii):
        n = len(pts)
        radii = [radii(i / max(n - 1, 1)) for i in range(n)]
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = res
    cu.twist_mode = twist
    cu.use_fill_caps = True
    if flat != 1.0:
        cu.bevel_mode = 'OBJECT'
        cu.bevel_object = _profile(flat)
    else:
        cu.bevel_depth = 1.0
        cu.bevel_resolution = 6
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for bp, p, r in zip(sp.bezier_points, pts, radii):
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
        bp.radius = r
        bp.tilt = tilt
    sp.use_cyclic_u = closed
    return _link(bpy.data.objects.new(name, cu))


def taper(r0, r1, power=1.0):
    return lambda t: r0 + (r1 - r0) * (t ** power)


def swell(r_end, r_mid, r_end2=None):
    r_end2 = r_end if r_end2 is None else r_end2
    def f(t):
        base = r_end + (r_end2 - r_end) * t
        return base + (r_mid - (r_end + r_end2) / 2) * math.sin(math.pi * t)
    return f


def thorn(base, direction, length, r0=0.9, curl=0.35, up=(0, 0, 1), name="thorn", n=7, rtip=0.25):
    """Curved thorn from base point along direction, bending toward `up`."""
    b, d, u = Vector(base), Vector(direction).normalized(), Vector(up).normalized()
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append(b + d * (length * t) + u * (length * curl * t * t))
    return stroke(pts, taper(r0, rtip, 0.8), name=name)


def spiral(end, e1, e2, rho0, rho1, phi0, turns, n=14):
    """Points of a scroll curl starting exactly at `end`, in plane (e1,e2).
    phi0 = angle of `end` as seen from the curl centre."""
    e1, e2 = Vector(e1).normalized(), Vector(e2).normalized()
    o = Vector(end) - rho0 * (math.cos(phi0) * e1 + math.sin(phi0) * e2)
    pts = []
    for i in range(1, n + 1):
        t = i / n
        ph = phi0 + turns * TAU * t
        rho = rho0 + (rho1 - rho0) * t
        pts.append(o + rho * (math.cos(ph) * e1 + math.sin(ph) * e2))
    return pts, o


def pointed(r_max, start=0.3, end=0.25, peak=0.45, p=0.9):
    """Calligraphic radius profile: fine start, swell at `peak`, fine end."""
    def f(t):
        if t < peak:
            return start + (r_max - start) * math.sin(0.5 * math.pi * (t / peak)) ** p
        return end + (r_max - end) * math.cos(0.5 * math.pi * ((t - peak) / (1 - peak))) ** p
    return f


def bead(c, r, name="bead"):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c, segments=32, ring_count=16)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def eye(c, normal=(0, 1, 0), r=1.7, wire=0.9, name="eye"):
    """Jump-ring eye: torus centred at c, hole axis = normal."""
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=wire, location=c,
                                     major_segments=32, minor_segments=12)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(normal))
    return ob


def _ring_mesh(name, rx, ry, z0, z1, wall, n=64, inner_rx=None, inner_ry=None):
    """Elliptic annulus tube from z0 to z1."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    irx = inner_rx if inner_rx is not None else rx
    iry = inner_ry if inner_ry is not None else ry
    rings = []
    for (sx, sy, z) in ((irx, iry, z0), (rx + wall, ry + wall, z0), (rx + wall, ry + wall, z1), (irx, iry, z1)):
        rings.append([bm.verts.new((sx * math.cos(TAU * i / n), sy * math.sin(TAU * i / n), z)) for i in range(n)])
    for k in range(4):
        a, b = rings[k], rings[(k + 1) % 4]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    return _link(bpy.data.objects.new(name, me))


def bezel(c, w, l=None, depth=None, normal=(0, 0, 1), spin=0.0, wall=0.7, name="bezel"):
    """Cabochon cup for a w x l stone, girdle at c, stone faces along normal.
    Returns (metal parts list, stone placement matrix)."""
    l = w if l is None else l
    rx, ry = l / 2 + 0.05, w / 2 + 0.05
    h_above = 0.9 if depth is None else depth
    wallo = _ring_mesh(name + "_wall", rx, ry, -0.7, h_above, wall)
    ledge = _ring_mesh(name + "_ledge", rx * 0.72, ry * 0.72, -0.7, -0.1, 0.0,
                       inner_rx=rx * 0.62, inner_ry=ry * 0.62)
    # ledge: annulus from 0.62r to 0.72r+... widen to meet wall
    bpy.data.objects.remove(ledge)
    ledge = _ring_mesh(name + "_ledge", rx + 0.2, ry + 0.2, -0.7, -0.1, 0.0,
                       inner_rx=rx - min(1.0, rx * 0.3), inner_ry=ry - min(1.0, ry * 0.3))
    M = Matrix.Translation(Vector(c)) @ Vector((0, 0, 1)).rotation_difference(Vector(normal)).to_matrix().to_4x4() \
        @ Matrix.Rotation(spin, 4, 'Z')
    for ob in (wallo, ledge):
        ob.matrix_world = M
    return [wallo, ledge], M


STONES = {
    "spinel": dict(color=(0.99, 0.6, 0.72), transmission=0.9, ior=1.72, rough=0.02),
    "citrine": dict(color=(1.0, 0.62, 0.12), transmission=0.85, ior=1.55, rough=0.02),
    "aquamarine": dict(color=(0.5, 0.82, 0.95), transmission=0.6, ior=1.58, rough=0.02),
    "labradorite": dict(color=(0.035, 0.045, 0.06), transmission=0.0, ior=1.56, rough=0.05, film=330),
    "garnet": dict(color=(0.45, 0.02, 0.04), transmission=0.85, ior=1.75, rough=0.02),
    "moonstone": dict(color=(0.85, 0.88, 0.95), transmission=0.4, ior=1.52, rough=0.08, film=380),
    "peridot": dict(color=(0.55, 0.78, 0.12), transmission=0.9, ior=1.67, rough=0.02),
    "amethyst": dict(color=(0.55, 0.25, 0.85), transmission=0.9, ior=1.55, rough=0.02),
    "topaz": dict(color=(0.18, 0.45, 0.85), transmission=0.9, ior=1.62, rough=0.02),
    "londonblue": dict(color=(0.08, 0.22, 0.42), transmission=0.9, ior=1.62, rough=0.02),
}


def stone_mat(kind):
    name = "stone_" + kind
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    s = STONES[kind]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*s["color"], 1)
    b.inputs["Transmission Weight"].default_value = s["transmission"]
    b.inputs["IOR"].default_value = s["ior"]
    b.inputs["Roughness"].default_value = s["rough"]
    b.inputs["Coat Weight"].default_value = 1.0
    if "film" in s:
        b.inputs["Thin Film Thickness"].default_value = s["film"]
        b.inputs["Thin Film IOR"].default_value = 1.9
    return m


def cab(M, w, l=None, dome=None, kind="aquamarine", name="cab"):
    """Calibrated cabochon, flat base on the girdle plane of M."""
    l = w if l is None else l
    dome = 0.45 * w if dome is None else dome
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24)
    ob = bpy.context.active_object
    ob.name = name
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0),
                           plane_no=(0, 0, 1), clear_inner=True)
    edges = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=edges)
    bm.to_mesh(me); bm.free()
    ob.matrix_world = M @ Matrix.Diagonal((l / 2, w / 2, dome, 1))
    ob.data.materials.append(stone_mat(kind))
    bpy.ops.object.shade_smooth()
    ob["stone"] = f"{kind} cabochon {l:g}x{w:g} mm" if l != w else f"{kind} cabochon {w:g} mm round"
    return ob


def pad(c, w, l, t=0.9, name="pad", normal=(0, 0, -1)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (l, w, t)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(Vector(normal))
    return ob


def wrap_cyl(u, v, rx, ry, h_off=0.0, r_off=0.0):
    """Map flat (u along circumference in mm, v height) onto an elliptic cylinder
    with axis Y. u=0 at the top (+Z). Returns xyz."""
    # approximate arclength param on ellipse by angle using mean radius
    rm = (rx + ry) / 2
    a = u / rm
    x = (rx + r_off) * math.sin(a)
    z = (ry + r_off) * math.cos(a)
    return (x, v + h_off, z)


def fuse(objs, name, voxel=0.05, smooth=2):
    """Union parts into one watertight solid via voxel remesh."""
    bpy.ops.object.select_all(action='DESELECT')
    meshes = []
    for ob in objs:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    m = ob.modifiers.new("remesh", 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = voxel
    m.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier="remesh")
    if smooth:
        sm = ob.modifiers.new("smooth", 'CORRECTIVE_SMOOTH')
        sm.factor = 0.5
        sm.iterations = smooth
        sm.use_only_smooth = True
        bpy.ops.object.modifier_apply(modifier="smooth")
    nf = len(ob.data.polygons)
    if nf > 450000:
        dm = ob.modifiers.new("dec", 'DECIMATE')
        dm.ratio = 450000 / nf
        bpy.ops.object.modifier_apply(modifier="dec")
    bpy.ops.object.shade_smooth()
    ob.rotation_mode = "XYZ"
    ob["castable"] = True
    return ob


def silver_mat():
    if "sterling" in bpy.data.materials:
        return bpy.data.materials["sterling"]
    m = bpy.data.materials.new("sterling")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.97, 0.96, 0.94, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.09
    return m


def export_stl(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, apply_modifiers=True,
                          global_scale=1.0, ascii_format=False)


# ---------------------------------------------------------------- studio

def studio(objs, view=(0.0, -1.0, 0.55), res=1400, samples=128, margin=1.18, bg=(0.012, 0.012, 0.014),
           lens=100, target_offset=(0, 0, 0)):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 10
    s.cycles.transmission_bounces = 10
    s.cycles.glossy_bounces = 8
    s.render.resolution_x = s.render.resolution_y = res
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Base Contrast'
    s.render.film_transparent = False
    # bounds
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    ctr = (lo + hi) / 2 + Vector(target_offset)
    size = (hi - lo).length
    # world: soft gradient
    w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
    bgn = w.node_tree.nodes["Background"]
    bgn.inputs[0].default_value = (*bg, 1); bgn.inputs[1].default_value = 0.0
    # backdrop: big seamless sphere-ish plane under/behind
    bpy.ops.mesh.primitive_plane_add(size=size * 40, location=(ctr.x, ctr.y, lo.z - 0.02))
    floor = bpy.context.active_object; floor.name = "floor"
    fm = bpy.data.materials.new("floor"); fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (*bg, 1); fb.inputs["Roughness"].default_value = 0.25
    fb.inputs["Specular IOR Level"].default_value = 0.3
    floor.data.materials.append(fm)
    # camera
    d = Vector(view).normalized()
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = lens; cam_d.clip_start = 1; cam_d.clip_end = 1e5
    cam = bpy.data.objects.new("cam", cam_d); _link(cam); s.camera = cam
    fov = 2 * math.atan(36 / 2 / lens)
    dist = (size * margin / 2) / math.tan(fov / 2)
    cam.location = ctr + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    # lights: two big softboxes + strip, black flags for contrast in chrome
    def area(loc, strength, sz, sx=1, sy=1, col=(1, 1, 1)):
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        o = bpy.context.active_object; o.name = "softbox"
        o.scale = (sz * sx, sz * sy, 1)
        o.rotation_euler = (ctr - Vector(loc)).to_track_quat('Z', 'Y').to_euler()
        em = bpy.data.materials.new("sb"); em.use_nodes = True
        nt = em.node_tree; nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = strength * EXPO
        e.inputs[0].default_value = (*col, 1)
        out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], out.inputs[0])
        o.data.materials.append(em); o.visible_camera = False
        return o
    k = size * 1.6
    area(ctr + Vector((-1.0, -0.7, 1.1)) * k, 6.0, size * 1.5, sx=1, sy=0.3)
    area(ctr + Vector((1.2, -0.4, 0.6)) * k, 4.0, size * 1.4, sx=0.22, sy=1)
    area(ctr + Vector((0.2, 1.0, 1.3)) * k, 3.0, size * 1.8)
    area(ctr + Vector((0.0, -0.2, 2.0)) * k, 2.0, size * 0.9, sx=1, sy=0.15)
    # flags (black cards) to put dark shapes in the reflections
    fl = bpy.data.materials.new("flag"); fl.use_nodes = True
    flb = fl.node_tree.nodes["Principled BSDF"]; flb.inputs["Base Color"].default_value = (0.005, 0.005, 0.005, 1)
    flb.inputs["Roughness"].default_value = 1.0
    for loc in (Vector((1.3, -1.2, 0.3)), Vector((-1.4, 0.4, 0.3)), Vector((0.2, -1.6, 1.6))):
        bpy.ops.mesh.primitive_plane_add(size=size * 1.6, location=ctr + loc * size * 1.5)
        f = bpy.context.active_object
        f.rotation_euler = (ctr - f.location).to_track_quat('Z', 'Y').to_euler()
        f.data.materials.append(fl)
        f.visible_camera = False
    for ob in objs:
        if ob.get("castable") or ob.get("metal"):
            ob.data.materials.clear(); ob.data.materials.append(silver_mat())
    return cam


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- white studio (the teaser look)

def studio_white(objs, view=(0.0, -1.0, 0.55), res=1400, samples=128, margin=1.18, lens=100,
                 target_offset=(0, 0, 0), bg=None):
    """Pure white seamless, soft top light, floating object with a soft contact
    shadow (shadow catcher, composited onto #FFFFFF afterwards). Grey cards give
    the polished silver its definition without darkening the page."""
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.glossy_bounces = 8
    s.cycles.transmission_bounces = 10
    s.render.resolution_x = s.render.resolution_y = res
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    s.view_settings.exposure = 0.0
    s.render.film_transparent = True
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    ctr = (lo + hi) / 2 + Vector(target_offset)
    size = (hi - lo).length
    w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
    bgn = w.node_tree.nodes["Background"]
    bgn.inputs[0].default_value = (1, 1, 1, 1); bgn.inputs[1].default_value = 0.5
    bpy.ops.mesh.primitive_plane_add(size=size * 40, location=(ctr.x, ctr.y, lo.z - 0.02))
    floor = bpy.context.active_object; floor.name = "floor"; floor.is_shadow_catcher = True
    d = Vector(view).normalized()
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = lens; cam_d.clip_start = 1; cam_d.clip_end = 1e5
    cam = bpy.data.objects.new("cam", cam_d); _link(cam); s.camera = cam
    fov = 2 * math.atan(36 / 2 / lens)
    dist = (size * margin / 2) / math.tan(fov / 2)
    cam.location = ctr + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    def card(loc, strength, sz, sx=1, sy=1, grey=None):
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        o = bpy.context.active_object
        o.scale = (sz * sx, sz * sy, 1)
        o.rotation_euler = (ctr - Vector(loc)).to_track_quat('Z', 'Y').to_euler()
        m = bpy.data.materials.new("card"); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        if grey is None:
            e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = strength
            nt.links.new(e.outputs[0], out.inputs[0])
        else:
            e = nt.nodes.new("ShaderNodeBsdfDiffuse"); e.inputs[0].default_value = (grey, grey, grey, 1)
            nt.links.new(e.outputs[0], out.inputs[0])
        o.data.materials.append(m); o.visible_camera = False; o.visible_shadow = False
        if grey is not None:
            o.visible_diffuse = False; o.visible_transmission = False; o.visible_volume_scatter = False
        return o
    k = size * 1.6
    card(ctr + Vector((0.0, -0.2, 2.0)) * k, 3.0, size * 1.6, sx=1, sy=0.5)       # top softbox
    card(ctr + Vector((-1.2, -0.8, 0.9)) * k, 5.0, size * 1.4, sx=1, sy=0.3)   # key strip
    card(ctr + Vector((1.3, -0.3, 0.5)) * k, 4.0, size * 1.2, sx=0.25, sy=1)  # rim strip
    for loc in (Vector((1.2, -1.3, 0.25)), Vector((-1.4, 0.6, 0.2)), Vector((0.0, 1.6, 0.6)),
                Vector((-0.9, -1.4, -0.1))):
        card(ctr + loc * size * 1.3, 0, size * 1.8, grey=0.01)                 # grey cards for contrast
    for ob in objs:
        if ob.get("castable") or ob.get("metal"):
            ob.data.materials.clear(); ob.data.materials.append(silver_mat())
    return cam


def flatten_white(path):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    bg.convert("RGB").save(path)


def farm_save(blend_path, max_faces=250000):
    """Turn the current lit scene into a GarageFarm job: Cycles GPU, 2000 px,
    256 adaptive samples, transparent PNG RGBA to //<name>.png, everything packed."""
    import os
    s = bpy.context.scene
    for ob in s.objects:
        if ob.type == 'MESH' and len(ob.data.polygons) > max_faces and ob.data.users == 1 + 0:
            pass
    seen = set()
    for ob in list(s.objects):
        if ob.type != 'MESH' or ob.data.name in seen:
            continue
        seen.add(ob.data.name)
        nf = len(ob.data.polygons)
        if nf > max_faces:
            users = [o for o in s.objects if o.type == 'MESH' and o.data == ob.data]
            m = ob.modifiers.new("d", 'DECIMATE'); m.ratio = max_faces / nf
            dg = bpy.context.evaluated_depsgraph_get()
            newme = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            ob.modifiers.remove(m)
            for u in users:
                u.data = newme
            for poly in newme.polygons:
                poly.use_smooth = True
    s.cycles.device = 'GPU'
    s.cycles.samples = 256
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.01
    s.cycles.use_denoising = True
    s.cycles.denoiser = 'OPENIMAGEDENOISE'
    s.render.resolution_x = s.render.resolution_y = 2000
    s.render.resolution_percentage = 100
    s.render.film_transparent = True
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA'
    s.frame_start = s.frame_end = 1
    name = os.path.splitext(os.path.basename(blend_path))[0]
    s.render.filepath = "//" + name + ".png"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
