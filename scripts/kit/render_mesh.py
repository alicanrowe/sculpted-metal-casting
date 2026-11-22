"""Render a meshed piece (STL + JSON stones) with the fidelity look, any of the ring views.
usage: python render_mesh.py <stl> <json> <outprefix> [view indices e.g. 0123]   env PRES PSPP LOOK(fidelity default) ZOOM"""
import os, sys, json
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make, v2, jlib, fidelity
import bpy
stl, js, outp = sys.argv[1:4]; vi = sys.argv[4] if len(sys.argv) > 4 else "0123"
info = json.load(open(js))
npz = stl[:-4] + ".npz"
jlib.reset()
if os.path.exists(npz):                     # verts, faces and the per-vertex ground mask from the layer kit
    z = np.load(npz); Vv, Ff = z["V"], z["F"]
else:
    m = trimesh.load(stl, process=False); Vv, Ff = np.asarray(m.vertices), np.asarray(m.faces)
ob = v2.to_blender(np.asarray(Vv, np.float32), np.asarray(Ff, np.int32), "piece")
import math as _m
ob.data.set_sharp_from_angle(angle=_m.radians(float(os.environ.get("SHARP", 40))))   # crisp insert edges, no shading streaks
if os.path.exists(npz) and "ground" in z:
    at = ob.data.attributes.new("ground", 'FLOAT', 'POINT'); at.data.foreach_set("value", z["ground"].astype(np.float32))
objs = [ob]
for r in info["stones"]:
    r = dict(r); r.setdefault("e1", [1, 0, 0])
    st = v2.stone_mesh(r, r["kind"]); st.data.materials.append(v2.facet_mat(r["kind"])); st["kind"] = r["kind"]; objs.append(st)
views = [make.VIEWS["ring"][int(c)] for c in vi]
res = int(os.environ.get("PRES", 700)); spp = int(os.environ.get("PSPP", 32))
jlib.studio_white(objs, view=views[0], res=res, samples=spp, margin=1.15, lens=100)
for o in list(bpy.context.scene.objects):
    if o.name == "floor" or o.type == 'CAMERA': bpy.data.objects.remove(o, do_unlink=True)
v2.realism(objs)
cams = make.place_cams(objs, views, margin=float(os.environ.get("ZOOM", 1.15)))
sc = bpy.context.scene
if os.environ.get("LOOK", "fidelity") == "fidelity":
    fidelity.apply(objs, cams)
sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100
sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.render.filepath = outp + "_v"
bpy.ops.render.render(animation=True)
