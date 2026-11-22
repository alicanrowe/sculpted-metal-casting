"""The DynaMesh step for a layer-kit union: rebuild it on a voxel grid (Blender's voxel remesh, OpenVDB), which
seals hairline crevices and pinholes smaller than a voxel, then keep the main body (drops trapped voids and specks).
usage: python3 vox.py in.npz out_prefix [voxel_mm=0.03]
Keeps the per-vertex 'ground' mask by nearest-vertex transfer. Prints the main body's genus (a ring must be 1)."""
import sys, time, numpy as np, bpy, manifold3d as m3
from scipy.spatial import cKDTree
src, out = sys.argv[1], sys.argv[2]
vs = float(sys.argv[3]) if len(sys.argv) > 3 else 0.03
d = np.load(src); V, F, G = d["V"], d["F"], d["ground"]
t = time.time()
me = bpy.data.meshes.new("u"); me.vertices.add(len(V)); me.vertices.foreach_set("co", V.astype(np.float32).ravel())
me.loops.add(F.size); me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
me.polygons.add(len(F)); me.polygons.foreach_set("loop_start", np.arange(0, F.size, 3, dtype=np.int32))
me.polygons.foreach_set("loop_total", np.full(len(F), 3, np.int32))
me.update(); ob = bpy.data.objects.new("u", me); bpy.context.scene.collection.objects.link(ob)
md = ob.modifiers.new("r", "REMESH"); md.mode = "VOXEL"; md.voxel_size = vs; md.adaptivity = 0.0
dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); m2 = ev.to_mesh(); m2.calc_loop_triangles()
V2 = np.empty(len(m2.vertices) * 3, np.float32); m2.vertices.foreach_get("co", V2); V2 = V2.reshape(-1, 3).astype(np.float64)
F2 = np.empty(len(m2.loop_triangles) * 3, np.int32); m2.loop_triangles.foreach_get("vertices", F2); F2 = F2.reshape(-1, 3)
print("remesh", len(V2), "verts", len(F2), "tris", round(time.time() - t, 1), "s", flush=True)
M = m3.Manifold(m3.Mesh(vert_properties=V2.astype(np.float32), tri_verts=F2.astype(np.uint32)))
if M.status() != m3.Error.NoError: print("status", M.status())
if M.volume() < 0: F2 = F2[:, ::-1].copy(); M = m3.Manifold(m3.Mesh(vert_properties=V2.astype(np.float32), tri_verts=F2.astype(np.uint32)))
parts = sorted(M.decompose(), key=lambda p: -p.volume()); main = parts[0]
print("bodies", len(parts), "(voids and specks dropped)" if len(parts) > 1 else "", "main genus", main.genus(),
      "vol", round(main.volume(), 2), "sterling g", round(main.volume() / 1000 * 10.36, 2), flush=True)
mm = main.to_mesh(); V2 = np.asarray(mm.vert_properties)[:, :3].astype(np.float64); F2 = np.asarray(mm.tri_verts).astype(np.int64)
_, idx = cKDTree(V).query(V2, workers=-1); G2 = G[idx]
np.savez_compressed(out + ".npz", V=V2, F=F2, ground=G2)
import trimesh; trimesh.Trimesh(V2, F2, process=False).export(out + ".stl")
