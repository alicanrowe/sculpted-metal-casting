"""Build one Stained-glass piece: SDF -> mesh (Taubin-smoothed) -> Blender scene in a
white light tent with real silver and gems, four cameras (hero + 3 angles) on frames 1-4,
no floor, no shadows, transparent film.
    python make.py <piece> preview   -> out3/<piece>_hero.png (quick local check)
    python make.py <piece> farm      -> farm3/<piece>.blend (GarageFarm job, frames 1-4)
    python make.py <piece> local4    -> $OUTDIR/<piece>_v0001-4.png (all four views on this machine)
    python make.py <piece> stl       -> $OUTDIR/<piece>.stl + .json (the casting file, no render)
    python make.py list              -> every piece name the kit knows
"""
import sys, os, json, math
import numpy as np
import sdf, v2
from glass64 import PIECES
from glassB import PIECES as _PB
from glassC import PIECES as _PC
from glassD import PIECES as _PD
from glassE import PIECES as _PE
from glassF import PIECES as _PF
from devel import PIECES as _PDV
PIECES = {**PIECES, **_PB, **_PC, **_PD, **_PE, **_PF, **_PDV}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUTDIR", os.path.join(HERE, "out3")); os.makedirs(OUT, exist_ok=True)
TMP = "/tmp/mb_stl"; os.makedirs(TMP, exist_ok=True)
FARM = os.environ.get("FARMDIR") or os.path.join(HERE, "farm3"); os.makedirs(FARM, exist_ok=True)

VIEWS = {
    "flat": [(0.14, -0.34, 1.0), (0.0, -0.04, 1.0), (0.95, -0.25, 0.45), (-0.35, -1.0, 0.3)],
    "ring": [(0.6, -1.0, 0.8), (0.0, -0.12, 1.0), (1.0, 0.0, 0.18), (0.0, -1.0, 0.12)],
    "cuff": [(0.25, -0.6, 1.0), (0.0, -0.05, 1.0), (1.0, -0.25, 0.35), (0.0, -1.0, 0.2)],
    "hang": [(0.3, -0.45, 1.0), (0.0, -0.03, 1.0), (1.0, -0.1, 0.25), (-0.6, -0.5, 0.6)],
}


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
    cams = []
    for i, v in enumerate(views):
        d = Vector(v).normalized()
        cd = bpy.data.cameras.new(f"cam{i}"); cd.lens = lens; cd.clip_start = 1; cd.clip_end = 1e5
        cam = bpy.data.objects.new(f"cam{i}", cd); bpy.context.collection.objects.link(cam)
        cam.location = ctr + d * dist
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cams.append(cam)
        mk = s.timeline_markers.new(f"view{i}", frame=i + 1); mk.camera = cam
    s.camera = cams[0]; s.frame_start = 1; s.frame_end = len(cams); s.frame_set(1)
    return cams


def bridge(s, units, vox_c=0.11, rounds=4):
    """Join any floating metal to the main body of its own unit (each earring of a pair is a unit)
    with a short liquid strut between the closest points, so every piece casts as one."""
    import trimesh
    from scipy.spatial import cKDTree
    for _ in range(rounds):
        V, Fa = sdf.mesh(s.array(), vox_c)
        mm = trimesh.Trimesh(V, Fa, process=True)
        parts = [p for p in mm.split(only_watertight=False) if p.area > 1.0]
        groups = {}
        for p in parts:
            u = int(np.argmin([abs(p.centroid[0] - ux) for ux in units])); groups.setdefault(u, []).append(p)
        added = 0
        for u, ps in groups.items():
            if len(ps) < 2: continue
            ps.sort(key=lambda p: -p.area); main = ps[0]; tree = cKDTree(main.vertices)
            for p in ps[1:]:
                d, j = tree.query(p.vertices); i = int(np.argmin(d))
                a = p.vertices[i]; b = main.vertices[j[i]]
                v = b - a; L = np.linalg.norm(v)
                if L < 1e-6: continue
                v /= L
                s.cone(a - v * 0.35, b + v * 0.35, 0.42, 0.42, k=0.35); added += 1
        if not added: break


def build(name, mode="preview"):
    fn, kind = PIECES[name]
    s, stones = fn()
    if getattr(s, "units", None) is not None: bridge(s, s.units)
    P = s.array()
    print(name, len(P), "prims", len(stones), "stones", flush=True)
    vox = float(os.environ.get("VOX", 0.04 if mode == "farm" else 0.06))
    small = (P[:, 22:25].max(0) - P[:, 19:22].min(0)).max() < 25
    if small: vox *= 0.6
    V, F = sdf.mesh(P, vox)
    m = sdf.save_stl(V, F, os.path.join(TMP, f"{name}_{os.getpid()}.stl"), smooth=int(os.environ.get("SMOOTH", 3))); os.remove(os.path.join(TMP, f"{name}_{os.getpid()}.stl"))
    parts = m.split(only_watertight=False)
    if len(parts) > 1:                      # drop sub-millimetre slivers left by stone-seat cuts
        import trimesh
        main = max(abs(p.volume) for p in parts)
        keep = [p for p in parts if abs(p.volume) > max(1.0, main * 0.002)]
        dd_ = [round(abs(p.volume), 2) for p in parts if p not in keep and abs(p.volume) > 0.01]
        if dd_: print('dropped debris', dd_, flush=True)
        m = trimesh.util.concatenate(keep)
    info = dict(name=name, watertight=bool(m.is_watertight), volume_cm3=round(abs(m.volume) / 1000, 3),
                sterling_g=round(abs(m.volume) / 1000 * 10.36, 1), size_mm=[round(float(x), 1) for x in m.extents],
                stones=[dict(kind=r["kind"], D=r["D"], L=r["L"], bead=bool(r.get("bead")),
                             **{k: r[k] for k in ("c", "n", "e1", "setting", "shape", "outline") if k in r}) for r in stones])   # c/n/e1: check_settings.py
    json.dump(info, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    print(info["sterling_g"], "g", info["size_mm"], "bodies", m.body_count, flush=True)
    if mode == "stl":          # casting file only, no render: <OUTDIR>/<piece>.stl + .json (run check.py on the folder)
        m.export(os.path.join(OUT, name + ".stl")); print("stl", os.path.join(OUT, name + ".stl"), flush=True)
        return
    import bpy, jlib
    jlib.reset()
    ob = v2.to_blender(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.int32), name)
    cap = int(os.environ.get("FACECAP", 8000000))
    if len(m.faces) > cap:
        d = ob.modifiers.new("d", 'DECIMATE'); d.ratio = cap / len(m.faces)
    objs = [ob]
    for r in stones:
        st = v2.stone_mesh(r, r["kind"]); st.data.materials.append(v2.facet_mat(r["kind"])); st["kind"] = r["kind"]
        objs.append(st)
    views = VIEWS[kind]
    if os.environ.get("HEROVIEW"): views = [views[int(os.environ["HEROVIEW"])]] + views
    res, spp = (int(os.environ.get("PRES", 520)), int(os.environ.get("PSPP", 28))) if mode in ("preview", "local4") else (1200, 192)
    jlib.studio_white(objs, view=views[0], res=res, samples=spp, margin=1.15, lens=100)
    for o in list(bpy.context.scene.objects):          # white only: no floor, no shadow catcher, no default cam
        if o.name == "floor" or (o.type == 'CAMERA'):
            bpy.data.objects.remove(o, do_unlink=True)
    v2.realism(objs)
    place_cams(objs, views)
    sc = bpy.context.scene
    if mode == "preview":
        sc.render.filepath = os.path.join(OUT, name + os.environ.get("TAG", "") + "_hero.png")
        bpy.ops.render.render(write_still=True)
        return
    if mode == "local4":       # all four views rendered here (CPU), for a finished square without the farm
        sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100
        sc.cycles.samples = spp; sc.cycles.use_denoising = True
        sc.render.film_transparent = True
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
        sc.render.filepath = os.path.join(OUT, name + "_v")
        bpy.ops.render.render(animation=True)
        return
    # farm job: GPU, adaptive, 4 frames = 4 views, transparent PNGs next to the blend
    sc.cycles.device = 'GPU'; sc.cycles.samples = spp
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = "//" + name + "_v"
    if ob.modifiers:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); ob.modifiers.clear(); ob.data = me
        for p in me.polygons: p.use_smooth = True
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FARM, name + ".blend"), compress=True)
    print("farm job", name, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "list":
        print("\n".join(sorted(PIECES))); sys.exit(0)
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "preview")
