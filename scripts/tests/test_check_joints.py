"""Planted cases for check_joints.py: a stone head on one thin stalk fails, the same head on a seat with four
roots passes. Run: python3 scripts/tests/test_check_joints.py"""
import json, os, subprocess, sys, tempfile
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); CJ = os.path.join(HERE, "..", "check_joints.py")


def case(roots):
    slab = trimesh.creation.box((30, 30, 2)); slab.apply_translation((0, 0, -1))
    cup = trimesh.creation.annulus(3.6, 4.2, 1.4); cup.apply_translation((0, 0, 6))
    parts = [slab, cup]
    for x, y, r in roots:
        a = np.array([x, y, 5.5]); b = np.array([x * 1.6, y * 1.6, 0.0])
        parts.append(trimesh.creation.cylinder(radius=r, segment=[a, b]))
    m = trimesh.boolean.union(parts) if trimesh.boolean.engines_available else trimesh.util.concatenate(parts)
    d = tempfile.mkdtemp(); stl = os.path.join(d, "p.stl"); js = os.path.join(d, "p.json")
    m.export(stl)
    json.dump(dict(name="planted", stones=[dict(kind="spinel", D=7.0, L=7.0, c=[0, 0, 6.6], n=[0, 0, 1])]), open(js, "w"))
    return subprocess.run([sys.executable, CJ, stl, js, "--pitch", "0.12"], capture_output=True, text=True)


weak = case([(3.8, 0.0, 0.45)])
strong = case([(2.7, 2.7, 0.8), (-2.7, 2.7, 0.8), (2.7, -2.7, 0.8), (-2.7, -2.7, 0.8)])
print(weak.stdout.splitlines()[0]); print(strong.stdout.splitlines()[0])
assert weak.returncode == 1, "one thin stalk must fail"
assert strong.returncode == 0, "a seat on four roots must pass"
print("test_check_joints OK")
