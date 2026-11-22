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

Tuning (env): EXPO 0.6, SKY 0.15, SUN 7 (overhaul 22 Nov: the old 0.55 sky washed polished faces white), SUNEL 32 (ov4: was 22, whose long shadows ran off the frame), SUNAZ 140, AOD 0.6 (mm), FSTOP 0.035,
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
    # a stippled or matte ground (mesh float attribute "ground", 0..1, written by the insert-and-layer kit) takes
    # the oxide hard and stays matte, so the polished inserts stand bright on black, as on the real piece
    ga = N.new("ShaderNodeAttribute"); ga.attribute_name = "ground"
    gm = N.new("ShaderNodeMapRange"); gm.inputs[3].default_value = 1.0; gm.inputs[4].default_value = 1.0 - _env("GROUND_OX", 0.88)
    L.new(ga.outputs["Fac"], gm.inputs[0])
    mask2 = N.new("ShaderNodeMath"); mask2.operation = 'MULTIPLY'; mask2.use_clamp = True
    L.new(mask.outputs[0], mask2.inputs[0]); L.new(gm.outputs[0], mask2.inputs[1])
    mask = mask2
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
    bg = N["Background"]; bg.inputs[1].default_value = _env("SKY", 0.15)
    # glossy rays see a brighter sky than diffuse ones (22 Nov overhaul): a dim fill keeps the sweep and the oxide
    # from washing out, but polished and chrome faces that mirror the sky must still read bright, as in a photo
    lp = N.new("ShaderNodeLightPath"); mx = N.new("ShaderNodeMix"); mx.data_type = 'FLOAT'
    mx.inputs[2].default_value = _env("SKY", 0.15); mx.inputs[3].default_value = _env("SKYGLOSS", 0.4)
    L.new(lp.outputs["Is Glossy Ray"], mx.inputs[0]); L.new(mx.outputs[0], bg.inputs[1])
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position = 0.42; el[0].color = (0.05, 0.048, 0.045, 1)
    el[1].position = 0.75; el[1].color = (0.78, 0.86, 1.0, 1)
    e2 = el.new(0.52); e2.color = (0.32, 0.3, 0.28, 1)
    L.new(sep.outputs["Z"], rp.inputs[0]); L.new(rp.outputs[0], bg.inputs[0])
    ld = bpy.data.lights.new("sun", 'SUN'); ld.energy = _env("SUN", 7.0); ld.angle = math.radians(1.2)
    ld.color = (1.0, 0.86, 0.7)
    sun = bpy.data.objects.new("sun", ld); bpy.context.collection.objects.link(sun)
    el_, az_ = math.radians(_env("SUNEL", 32)), math.radians(_env("SUNAZ", 140))
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
    # 22 Nov overhaul: the sweep is a shadow catcher on a transparent film. An opaque sweep showed its horizon and
    # its grey falloff as tile edges in side views and squares; the catcher keeps only the cast shadow on white.
    f.is_shadow_catcher = True
    return f


def apply(objs, cams=None, keep_mats=False):
    """Swap the studio look for the photographic one. objs: metal objects carry ob['metal'], stones ob['kind'].
    keep_mats: light, sweep, tone and lens only; the kit keeps its own materials (machined two-tone, forged patina)."""
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
    for o in (objs if keep_mats else []):
        # ov4: a flush-set transmissive ball shows the dark seat behind it under the dim sky and reads as an
        # empty hole. Keep it glassy but give it enough body colour to read as ruby / sapphire.
        k = o.get("kind")
        if k in ("ruby", "sapphire") and o.data.materials:
            b = o.data.materials[0].node_tree.nodes.get("Principled BSDF")
            if b:
                b.inputs["Transmission Weight"].default_value = 0.45
                b.inputs["Base Color"].default_value = (0.62, 0.02, 0.06, 1) if k == "ruby" else (0.9, 0.92, 1.0, 1)
                b.inputs["Coat Weight"].default_value = 0.6
    for o in ([] if keep_mats else objs):
        if o.get("metal"):
            o.data.materials.clear(); o.data.materials.append(mt)
        elif o.get("kind"):
            o.data.materials.clear(); o.data.materials.append(v2.gem_real(o["kind"]))
    s.render.film_transparent = True
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    s.view_settings.exposure = _env("EXPO", 0.6)
    s.cycles.use_adaptive_sampling = True; s.cycles.adaptive_threshold = 0.01
    s.cycles.blur_glossy = 0.3; s.cycles.caustics_refractive = False
    ctr = (lo + hi) / 2
    # focus on the focal point, not the bbox centre (a ring's bbox centre is the empty finger hole, which put the
    # head out of focus, 22 Nov overhaul): the stones' centroid if there are stones, else the centre of the top third
    sts = [o for o in objs if o.get("kind")]
    if sts:
        foc = sum((o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8) for o in sts), Vector()) / len(sts)
    else:
        foc = Vector((ctr.x, ctr.y, lo.z + 0.8 * (hi.z - lo.z)))
    for cam in (cams or [s.camera]):
        # ov4: a camera below the floor sees only the transparent shadow catcher and renders an empty tile.
        # Mirror it above the floor (same azimuth, same distance) and aim it back at the focal point.
        if cam.location.z < lo.z + 0.05 * (hi.z - lo.z):
            cam.location.z = ctr.z + abs(cam.location.z - ctr.z) * 0.45 + 0.05 * (hi.z - lo.z)
            cam.rotation_euler = (foc - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = (cam.location - foc).length
        cam.data.dof.aperture_fstop = _env("FSTOP", 0.07)
