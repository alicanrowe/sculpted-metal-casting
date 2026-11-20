"""Planted cases for check_soft_build.py: a good laced seat passes; each way a soft part can be unbuildable fails.
    python scripts/tests/test_check_soft_build.py      (needs trimesh, manifold3d, numpy)"""
import os, sys, json, copy, tempfile, subprocess
import numpy as np
import manifold3d as m3
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "check_soft_build.py")


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def rod_y(x, z, y0, y1, r):
    return m3.Manifold.cylinder(y1 - y0, r, r, 24).rotate([-90, 0, 0]).translate([x, y0, z])


def save(mf, path):
    m = mf.to_mesh()
    trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts)).export(path)


GOOD = {
    "seat": {"z_min": 3.0},
    "parts": [
        {"name": "pad", "kind": "cushion", "mesh": "pad.stl", "thickness_mm": 30, "material": "foam in 1.3 mm leather",
         "cut": "foam block, cover stapled under", "attach": {"method": "rests", "to": ["frame"], "fasteners": "none needed"},
         "load": "the sitter onto the bar", "replace": "re-cover"},
        {"name": "flap_a", "kind": "flap", "mesh": "flap_a.stl", "thickness_mm": 2.8, "material": "2.8 mm veg-tan",
         "cut": "hand cut, two 5 mm holes", "attach": {"method": "stitch", "to": ["pad"], "fasteners": "saddle stitch, waxed thread"},
         "load": "holds the lace", "replace": "unpick and re-stitch"},
        {"name": "flap_b", "kind": "flap", "mesh": "flap_b.stl", "thickness_mm": 2.8, "material": "2.8 mm veg-tan",
         "cut": "hand cut, two 5 mm holes", "attach": {"method": "stitch", "to": ["pad"], "fasteners": "saddle stitch, waxed thread"},
         "load": "holds the lace", "replace": "unpick and re-stitch"},
        {"name": "lace", "kind": "lace", "mesh": "lace.stl", "diameter_mm": 3, "material": "3 mm latigo lace",
         "cut": "stock", "attach": {"method": "laced", "to": ["flap_a", "flap_b"], "fasteners": "through the holes"},
         "tension": "pulled snug by hand", "closure": {"type": "bow", "release": "pull a tail"},
         "load": "uplift", "replace": "new lace"},
    ],
    "load_paths": [{"name": "seat", "chain": ["pad", "frame"]},
                   {"name": "uplift", "chain": ["pad", "flap_a", "lace", "frame"], "travel_ok_cm": 1.0}],
}


def build(d, holes=True, lace_z=-1.0):
    save(box(-20, 20, -1.5, 1.5, 0, 1), os.path.join(d, "frame.stl"))
    save(box(-15, 15, -4.28, 4.28, 1, 4), os.path.join(d, "pad.stl"))
    for nm, y0 in (("flap_a", -4.28), ("flap_b", 4.0)):
        f = box(-5, 5, y0, y0 + 0.28, -2, 1)
        if holes:
            f = f - rod_y(0, lace_z, y0 - 1, y0 + 1.28, 0.25)
        save(f, os.path.join(d, f"{nm}.stl"))
    save(rod_y(0, lace_z, -4.6, 4.6, 0.15), os.path.join(d, "lace.stl"))


def run(d, spec):
    json.dump(spec, open(os.path.join(d, "spec.json"), "w"))
    p = subprocess.run([sys.executable, CHECK, "--frame", os.path.join(d, "frame.stl"), "--spec", os.path.join(d, "spec.json")],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def main():
    bad = 0
    cases = []
    cases.append(("good laced seat", {}, GOOD, 0, None))
    s = copy.deepcopy(GOOD); s["parts"][3]["material"] = ""
    cases.append(("lace with no material", {}, s, 1, "SPEC"))
    s = copy.deepcopy(GOOD); del s["parts"][3]["tension"]
    cases.append(("lace with no tensioning", {}, s, 1, "SPEC"))
    s = copy.deepcopy(GOOD); del s["parts"][1]["attach"]["fasteners"]
    cases.append(("stitched flap with no thread named", {}, s, 1, "SPEC"))
    s = copy.deepcopy(GOOD); s["parts"][3]["closure"] = {"type": "knot"}
    cases.append(("lace that can't be undone", {}, s, 1, "SPEC"))
    cases.append(("lace through leather with no holes", {"holes": False}, GOOD, 1, "CLIP"))
    s = copy.deepcopy(GOOD); s["seat"]["z_min"] = -5
    cases.append(("lace over the sitting surface", {}, s, 1, "SEAT"))
    cases.append(("no spec at all", {}, {"parts": []}, 1, "SPEC"))
    for name, kw, spec, want, word in cases:
        with tempfile.TemporaryDirectory() as d:
            build(d, **kw)
            code, out = run(d, spec)
        ok = code == want and (word is None or word in out)
        print(("ok  " if ok else "BAD ") + name + ("" if ok else "\n" + out))
        bad += not ok
    print("all planted cases behave" if not bad else f"{bad} cases wrong")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
