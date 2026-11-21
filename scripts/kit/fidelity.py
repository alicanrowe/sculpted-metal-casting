"""Photographic look for cast sterling (LOOK=fidelity in make.py, or call apply() yourself).

What it changes against v2.realism (see references/render-fidelity.md for why each one matters):
  - oxidised sterling: black left in every recess and engraved cut, high points rubbed back to a worn
    bright polish (mask = ambient occlusion over ~0.6 mm x convexity, broken up by a slow noise)
  - micro surface: fine pitting and polishing marks at 0.05 to 0.2 mm, never a low-frequency bump
  - one hard, warm, low sun (raking 20 to 30 deg) plus a sky fill whose lower band is dark, so polished
    planes mirror something dark the way they mirror asphalt or a table outdoors
  - a white sweep that keeps the cast shadow: the background stays white, the piece sits on something
  - a real macro depth of field, AgX Medium High Contrast, adaptive sampling
Scene units are mm (Blender treats them as metres), so the f-stop is scaled down by about 1000.

Tuning (env): EXPO 0.4, SKY 0.55, SUN 4.5, SUNEL 22, SUNAZ 140, AOD 0.6 (mm), FSTOP 0.035,
CAV_LO/CAV_HI pointiness window (0.455 / 0.505), AO_LO/AO_HI (0.3 / 0.85).
"""
import math
import os


def _env(k, d):
    return float(os.environ.get(k, d))


def oxidised_sterling():
    import bpy
    if "sterling_ox" in bpy.data.materials:
        return bpy.data.materials["sterling_ox"]
    mt = bpy.data.materials.new("sterling_ox"); mt.use_nodes = True
    T = mt.node_tree; N = T.nodes; L = T.links
    b = N["Principled BSDF"]; b.inputs["Metallic"].default_value = 1.0
    ao = N.new("ShaderNodeAmbientOcclusion"); ao.samples = 24; ao.only_local = True
    ao.inputs["Distance"].default_value = _env("AOD", 0.6)
    geo = N.new("ShaderNodeNewGeometry")
    cv = N.new("ShaderNodeMapRange")                  # pointiness: concave -> 0, flat and convex -> 1
    cv.inputs[1].default_value = _env("CAV_LO", 0.455); cv.inputs[2].default_value = _env("CAV_HI", 0.505)
    L.new(geo.outputs["Pointiness"], cv.inputs[0])
    aor = N.new("ShaderNodeMapRange")
    aor.inputs[1].default_value = _env("AO_LO", 0.3); aor.inputs[2].default_value = _env("AO_HI", 0.85)
    L.new(ao.outputs["AO"], aor.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    L.new(aor.outputs[0], mul.inputs[0]); L.new(cv.outputs[0], mul.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 6
    nzr = N.new("ShaderNodeMapRange"); nzr.inputs[3].default_value = 0.75; nzr.inputs[4].default_value = 1.25
    L.new(nz.outputs[0], nzr.inputs[0])
    mask = N.new("ShaderNodeMath"); mask.operation = 'MULTIPLY'; mask.use_clamp = True   # 0 oxide, 1 polish
    L.new(mul.outputs[0], mask.inputs[0]); L.new(nzr.outputs[0], mask.inputs[1])
    mixc = N.new("ShaderNodeMix"); mixc.data_type = 'RGBA'
    mixc.inputs[6].default_value = (0.035, 0.032, 0.03, 1); mixc.inputs[7].default_value = (0.96, 0.95, 0.93, 1)
    L.new(mask.outputs[0], mixc.inputs[0]); L.new(mixc.outputs[2], b.inputs["Base Color"])
    rn = N.new("ShaderNodeTexNoise"); rn.inputs["Scale"].default_value = 9.0; rn.inputs["Detail"].default_value = 8
    rnr = N.new("ShaderNodeMapRange"); rnr.inputs[3].default_value = 0.07; rnr.inputs[4].default_value = 0.2
    L.new(rn.outputs[0], rnr.inputs[0])
    mixr = N.new("ShaderNodeMix"); mixr.data_type = 'FLOAT'; mixr.inputs[2].default_value = 0.55
    L.new(mask.outputs[0], mixr.inputs[0]); L.new(rnr.outputs[0], mixr.inputs[3]); L.new(mixr.outputs[0], b.inputs["Roughness"])
    bn = N.new("ShaderNodeTexNoise"); bn.inputs["Scale"].default_value = 28.0; bn.inputs["Detail"].default_value = 10
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08; bump.inputs["Distance"].default_value = 0.01
    L.new(bn.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return mt


def sun_and_sky(s):
    import bpy
    from mathutils import Vector
    w = bpy.data.worlds.new("sky"); s.world = w; w.use_nodes = True; N = w.node_tree.nodes; L = w.node_tree.links
    bg = N["Background"]; bg.inputs[1].default_value = _env("SKY", 0.55)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position = 0.42; el[0].color = (0.05, 0.048, 0.045, 1)
    el[1].position = 0.75; el[1].color = (0.78, 0.86, 1.0, 1)
    e2 = el.new(0.52); e2.color = (0.32, 0.3, 0.28, 1)
    L.new(sep.outputs["Z"], rp.inputs[0]); L.new(rp.outputs[0], bg.inputs[0])
    ld = bpy.data.lights.new("sun", 'SUN'); ld.energy = _env("SUN", 4.5); ld.angle = math.radians(1.2)
    ld.color = (1.0, 0.86, 0.7)
    sun = bpy.data.objects.new("sun", ld); bpy.context.collection.objects.link(sun)
    el_, az_ = math.radians(_env("SUNEL", 22)), math.radians(_env("SUNAZ", 140))
    d = Vector((math.cos(el_) * math.cos(az_), math.cos(el_) * math.sin(az_), math.sin(el_)))
    sun.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return sun


def white_sweep(lo, hi):
    import bpy
    ctr = (lo + hi) / 2; size = (hi - lo).length
    bpy.ops.mesh.primitive_plane_add(size=size * 60, location=(ctr.x, ctr.y, lo.z - 0.01))
    f = bpy.context.active_object; f.name = "sweep"
    m = bpy.data.materials.new("paper"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 0.9
    f.data.materials.append(m)
    return f


def apply(objs, cams=None):
    """Swap the studio look for the photographic one. objs: metal objects carry ob['metal'], stones ob['kind']."""
    import bpy
    from mathutils import Vector
    import v2
    s = bpy.context.scene
    for o in list(s.objects):                          # drop the tent: softbox cards, flags, shadow catcher
        if o.type == 'MESH' and o not in objs and (o.name.startswith("Plane") or o.name == "floor"):
            bpy.data.objects.remove(o, do_unlink=True)
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    sun_and_sky(s); white_sweep(lo, hi)
    mt = oxidised_sterling()
    for o in objs:
        if o.get("metal"):
            o.data.materials.clear(); o.data.materials.append(mt)
        elif o.get("kind"):
            o.data.materials.clear(); o.data.materials.append(v2.gem_real(o["kind"]))
    s.render.film_transparent = False
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    s.view_settings.exposure = _env("EXPO", 0.4)
    s.cycles.use_adaptive_sampling = True; s.cycles.adaptive_threshold = 0.01
    s.cycles.blur_glossy = 0.3; s.cycles.caustics_refractive = False
    ctr = (lo + hi) / 2
    for cam in (cams or [s.camera]):
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = (cam.location - ctr).length
        cam.data.dof.aperture_fstop = _env("FSTOP", 0.035)
