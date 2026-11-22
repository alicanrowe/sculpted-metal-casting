# Grass-field-and-river environment (the jewelry reel world), before/after the environment rules (references/environments.md). Usage, on a cloud machine:
#   ENV_GLB=piece.glb blender -b -P field_env.py -- <before|after> <out.png> [res_x res_y samples]
# "before" rebuilds the v10 look (even grey light, 16 mm, camera over the grass); "after" applies the rules.
# A meshopt-compressed site GLB must be decoded first: npx @gltf-transform/cli copy in.glb piece.glb
# Then finish with: python3 env_grade.py out.png out_graded.png
import bpy, sys, os, math, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = argv[0], argv[1]
RX, RY, SPP = (int(argv[2]), int(argv[3]), int(argv[4])) if len(argv) > 4 else (540, 960, 96)
GLB = os.environ["ENV_GLB"]
AFTER = MODE == "after"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
random.seed(4)

def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links

def river_y(x):  # river centreline, meandering away from camera along +x
    return 1.6 * math.sin(x * 0.22) + 0.5 * math.sin(x * 0.61 + 1.0)

# ---------- ground with a river channel ----------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=360, y_subdivisions=240, size=1)
g = bpy.context.object; g.name = "ground"
g.scale = (90, 60, 1); bpy.ops.object.transform_apply(scale=True)
g.location.x = 38
RW = 1.15  # half width of the river
for v in g.data.vertices:
    wx = v.co.x + 38
    d = abs(v.co.y - river_y(wx))
    t = max(0.0, 1 - d / RW)
    v.co.z = -0.35 * (t ** 0.6) + 0.02 * math.sin(wx * 1.7) * math.cos(v.co.y * 1.3)
bpy.ops.object.shade_smooth()
gm, n, l = mat("soil")
n["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1)
n["Principled BSDF"].inputs["Roughness"].default_value = 0.9
n["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.05
g.data.materials.append(gm)

# grass: mesh blades (3 segments, tapered), denser near camera, thinned with distance
import numpy as np
rng = np.random.default_rng(7)
def blades(n, x0, x1, y0, y1):
    x = rng.uniform(x0, x1, n); y = rng.uniform(y0, y1, n)
    keep = np.abs(y - (1.6*np.sin(x*0.22) + 0.5*np.sin(x*0.61+1.0))) > RW*0.72
    return x[keep], y[keep]
parts = [blades(330000, -3, 8, -5, 6), blades(260000, 8, 22, -9, 10), blades(180000, 22, 60, -20, 22)]
X = np.concatenate([p[0] for p in parts]); Y = np.concatenate([p[1] for p in parts])
N = len(X)
H = rng.uniform(0.10, 0.24, N) * (1 + 0.6*(X > 22))
if AFTER:  # tufts: a few tall seed heads break the horizon line, like the reel's silhouettes
    H = H * np.where(rng.random(N) < 0.06, rng.uniform(1.6, 2.6, N), 1.0)   # far blades a bit taller so the field reads as a mass
W = rng.uniform(0.004, 0.007, N) * (1 + 1.5*(X > 22))
ang = rng.uniform(0, 2*np.pi, N)
lean = rng.uniform(0.1, 0.55, N); ldir = rng.uniform(0, 2*np.pi, N)
_d = np.abs(Y - (1.6*np.sin(X*0.22) + 0.5*np.sin(X*0.61+1.0))); _t = np.clip(1 - _d/RW, 0, 1)
Z0 = -0.35*_t**0.6 + 0.02*np.sin((X)*1.7)*np.cos(Y*1.3)
segs = 3
verts = []
for k in range(segs + 1):
    t = k / segs
    off = lean * H * t**1.6
    cx = X + np.cos(ldir)*off; cy = Y + np.sin(ldir)*off; cz = Z0 + H*t*(1 - 0.25*lean*t)
    w = W * (1 - t) ** 0.8 if k < segs else np.zeros(N)
    for side in (-1, 1):
        if k == segs and side == 1: continue
        verts.append(np.stack([cx + side*np.cos(ang)*w, cy + side*np.sin(ang)*w, cz], 1))
V = np.stack(verts, 1)  # N x 7 x 3   (2 per level for 3 levels + tip)
nv = V.shape[1]
base = (np.arange(N) * nv)[:, None]
faces = []
for k in range(segs - 1):
    a = 2*k
    faces.append(np.array([a, a+1, a+3, a+2]))
tip = 2*segs
faces_q = np.stack(faces)  # (segs-1) x 4
gm_ = bpy.data.meshes.new("grass")
allv = V.reshape(-1, 3)
q = (base[:, None, :] + faces_q[None]).reshape(-1, 4)
t = (base + np.array([[2*(segs-1), 2*(segs-1)+1, tip]]))
loops = np.concatenate([q.ravel(), t.ravel()])
counts = np.concatenate([np.full(len(q), 4), np.full(len(t), 3)])
starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
gm_.vertices.add(len(allv)); gm_.vertices.foreach_set("co", allv.astype(np.float32).ravel())
gm_.loops.add(len(loops)); gm_.loops.foreach_set("vertex_index", loops.astype(np.int32))
gm_.polygons.add(len(counts)); gm_.polygons.foreach_set("loop_start", starts.astype(np.int32)); gm_.polygons.foreach_set("loop_total", counts.astype(np.int32))
gm_.update(); gm_.validate()
gr = bpy.data.objects.new("grass", gm_); sc.collection.objects.link(gr)
gr.data.polygons.foreach_set("use_smooth", [True]*len(gr.data.polygons))
hm, n, l = mat("grass")
bs = n["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.82, 0.81, 0.78, 1)
bs.inputs["Roughness"].default_value = 0.45 if AFTER else 0.7
if AFTER:  # thin blades pass light: backlit grass glows instead of reading grey
    bs.inputs["Transmission Weight"].default_value = 0.35
    bs.inputs["Subsurface Weight"].default_value = 0.0
gr.data.materials.append(hm)
if AFTER:  # per-blade tone so the lit field shows texture instead of a flat white carpet
    tone = rng.uniform(0.45, 1.0, N) ** 1.5
    ca = gm_.color_attributes.new("tone", "FLOAT_COLOR", "POINT")
    col = np.repeat(np.stack([tone, tone*0.99, tone*0.96, np.ones(N)], 1), nv, 0)
    ca.data.foreach_set("color", col.astype(np.float32).ravel())
    at = n.new("ShaderNodeVertexColor"); at.layer_name = "tone"
    mm = n.new("ShaderNodeMixRGB"); mm.blend_type = "MULTIPLY"; mm.inputs[0].default_value = 1
    mm.inputs[1].default_value = (0.85, 0.84, 0.81, 1)
    l.new(at.outputs["Color"], mm.inputs[2]); l.new(mm.outputs[0], bs.inputs["Base Color"])
print("blades", N)

# scattered red petals (existing reel motif), tiny
bpy.ops.mesh.primitive_circle_add(vertices=6, radius=0.025, fill_type="NGON")
petal = bpy.context.object; petal.name = "petal"; petal.hide_render = False
pm, n, l = mat("petal")
n["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.01, 0.015, 1)
petal.data.materials.append(pm)
for i in range(260):
    x = random.uniform(0, 22); y = random.uniform(-7, 7)
    if abs(y - river_y(x)) < RW: continue
    o = petal.copy(); o.data = petal.data
    o.location = (x, y, 0.06); o.rotation_euler = (random.uniform(-.4, .4), random.uniform(-.4, .4), random.random() * 6)
    sc.collection.objects.link(o)
petal.location = (0, 0, -5)

# water
bpy.ops.mesh.primitive_plane_add(size=1, location=(38, 0, -0.16))
w = bpy.context.object; w.name = "water"; w.scale = (90, 60, 1)
wm, n, l = mat("water")
b = n["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.006, 0.0, 0.0, 1) if AFTER else (0.012, 0.0, 0.0, 1)
b.inputs["Roughness"].default_value = 0.05 if AFTER else 0.02
b.inputs["IOR"].default_value = 1.33
if AFTER:  # slow ripples so the reflection breaks up like a satin floor
    tex = n.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = 3.0; tex.inputs["Detail"].default_value = 6
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.05
    l.new(tex.outputs["Fac"], bump.inputs["Height"]); l.new(bump.outputs[0], b.inputs["Normal"])
w.data.materials.append(wm)

# ---------- jewelry piece ----------
bpy.ops.import_scene.gltf(filepath=GLB)
objs = [o for o in bpy.context.selected_objects]
root = bpy.data.objects.new("piece", None); sc.collection.objects.link(root)
for o in objs:
    if o.parent is None: o.parent = root
bpy.context.view_layer.update()
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in objs:
    if o.type == "MESH":
        for c in o.bound_box:
            wc = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, wc)); mx = Vector(map(max, mx, wc))
size = max(mx - mn); s = (1.35 if AFTER else 0.9) / size
root.scale = (s, s, s)
root.location = -((mn + mx) / 2) * s + (Vector((6.0, river_y(6.0) + 0.25, 1.0)) if AFTER else Vector((6.0, river_y(6.0) + 0.9, 1.45)))
root.rotation_euler = (math.radians(70), 0, math.radians(-15))

# ---------- camera ----------
cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
if AFTER:
    cam.lens = 30; co.location = (-1.5, river_y(-1.5) + 1.6, 0.62)
else:
    cam.lens = 16; co.location = (-0.5, river_y(-0.5) + 0.6, 1.1)
tgt = Vector((9, river_y(9) + (0.3 if AFTER else 0.4), 0.95 if AFTER else 0.9))
co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
if AFTER:
    cam.dof.use_dof = True; cam.dof.focus_distance = (root.location - co.location).length; cam.dof.aperture_fstop = 2.8

# ---------- world + light ----------
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
if AFTER:
    # sky reads black to the camera, but jewelry still gets a faint top-lit gradient to reflect
    wn, wl = world.node_tree.nodes, world.node_tree.links
    lp = wn.new("ShaderNodeLightPath"); gr_ = wn.new("ShaderNodeTexGradient"); gr_.gradient_type = "EASING"
    tcw = wn.new("ShaderNodeTexCoord"); mp_ = wn.new("ShaderNodeMapping"); mp_.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
    wl.new(tcw.outputs["Generated"], mp_.inputs[0]); wl.new(mp_.outputs[0], gr_.inputs[0])
    sub = wn.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[0].default_value = 1
    wl.new(lp.outputs["Is Camera Ray"], sub.inputs[1])
    mul = wn.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; wl.new(sub.outputs[0], mul.inputs[0]); wl.new(gr_.outputs["Fac"], mul.inputs[1])
    mul2 = wn.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = 0.35
    wl.new(mul.outputs[0], mul2.inputs[0]); wl.new(mul2.outputs[0], bg.inputs["Strength"])
    # one motivated key: a big soft "moon slot" high behind the piece, just out of frame, rim-lighting the grass
    ld = bpy.data.lights.new("key", "AREA"); ld.shape = "DISK"; ld.size = 2.5; ld.energy = 3000; ld.spread = math.radians(26)
    ld.color = (1.0, 0.95, 0.9)
    lo = bpy.data.objects.new("key", ld); sc.collection.objects.link(lo); 
    lo.location = (11, river_y(11) + 0.4, 6.0)
    lo.rotation_euler = (Vector((6.5, river_y(6.5) + 0.3, 0)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    # light linking: the key lights everything but the water, so the river mirrors the lit grass and the
    # piece instead of showing a blown-out reflection of the lamp itself
    rc = bpy.data.collections.new("key_receivers")
    for o in sc.objects:
        if o.name != "water" and o.type != "LIGHT" and o.type != "CAMERA": rc.objects.link(o)
    lo.light_linking.receiver_collection = rc
    # cool low fill from camera side, very weak, so near grass doesn't go dead black
    fd = bpy.data.lights.new("fill", "AREA"); fd.size = 10; fd.energy = 140; fd.color = (0.8, 0.85, 1.0)
    fo = bpy.data.objects.new("fill", fd); sc.collection.objects.link(fo)
    fo.location = (-6, 0, 3); fo.rotation_euler = (Vector((4, 0, 0)) - fo.location).to_track_quat("-Z", "Y").to_euler()
    # thin ground mist: catches the key and fades the field to black with depth
    bpy.ops.mesh.primitive_cube_add(size=1, location=(30, 0, 1.55)); m = bpy.context.object; m.name = "mist"
    m.scale = (70, 40, 3.0)
    vm, n, l = mat("mist"); n.remove(n["Principled BSDF"])
    vol = n.new("ShaderNodeVolumePrincipled")
    vol.inputs["Anisotropy"].default_value = 0.6
    vol.inputs["Color"].default_value = (1, 1, 1, 1)
    # density falls off with height (ground-hugging), so the sky above stays black
    tc = n.new("ShaderNodeTexCoord"); sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Generated"], sep.inputs[0])
    e = n.new("ShaderNodeMath"); e.operation = "MULTIPLY"; e.inputs[1].default_value = -22.0
    l.new(sep.outputs["Z"], e.inputs[0])
    ex = n.new("ShaderNodeMath"); ex.operation = "EXPONENT"; l.new(e.outputs[0], ex.inputs[0])
    dm = n.new("ShaderNodeMath"); dm.operation = "MULTIPLY"; dm.inputs[1].default_value = 0.018
    l.new(ex.outputs[0], dm.inputs[0]); l.new(dm.outputs[0], vol.inputs["Density"])
    l.new(vol.outputs[0], n["Material Output"].inputs["Volume"]); m.data.materials.append(vm)
else:
    # v10 look: even grey world light, no direction
    bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 0.6
    mp = world.node_tree.nodes.new("ShaderNodeLightPath")
    mix = world.node_tree.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0, 0, 0, 1); mix.inputs[2].default_value = (1, 1, 1, 1)
    world.node_tree.links.new(mp.outputs["Is Camera Ray"], mix.inputs[0])
    inv = world.node_tree.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
    world.node_tree.links.new(mp.outputs["Is Camera Ray"], inv.inputs[1])
    world.node_tree.links.new(inv.outputs[0], bg.inputs["Strength"])

# ---------- render ----------
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.volume_bounces = 1
sc.render.resolution_x, sc.render.resolution_y = RX, RY
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast" if AFTER else "None"
sc.view_settings.exposure = 0.0
sc.render.filepath = OUT
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("DONE", OUT)
