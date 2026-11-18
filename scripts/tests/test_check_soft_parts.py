"""Planted soft parts: an open strap wrapped on a rail with a toggle on it passes; a closed ring, a fused blob,
a strap through the rail and a toggle floating clear each fail.   python3 tests/test_check_soft_parts.py"""
import os, sys, math, subprocess, tempfile
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
CHK = os.path.join(HERE, "..", "check_soft_parts.py")
T = 0.3
RX = trimesh.transformations.rotation_matrix(math.pi / 2, (0, 1, 0))


def rail():
    m = trimesh.creation.cylinder(radius=2.0, height=40, sections=64); m.apply_transform(RX); return m


def band(r0, open_=True):
    a = trimesh.creation.annulus(r_min=r0, r_max=r0 + T, height=1.8, sections=96); a.apply_transform(RX)
    if open_:
        cut = trimesh.creation.box((3, 1.0, 3)); cut.apply_translation((0, 0, r0 + 1.0))
        a = trimesh.boolean.difference([a, cut], engine="manifold")
    return a


def toggle(z):
    m = trimesh.creation.cylinder(radius=0.3, height=1.6, sections=24); m.apply_transform(RX); m.apply_translation((0, 0.9, z)); return m


def run(soft, closure=None):
    d = tempfile.mkdtemp()
    rail().export(os.path.join(d, "r.stl")); trimesh.util.concatenate(soft).export(os.path.join(d, "s.stl"))
    cmd = [sys.executable, CHK, "--rigid", os.path.join(d, "r.stl"), "--soft", os.path.join(d, "s.stl"), "--t", str(T)]
    if closure:
        trimesh.util.concatenate(closure).export(os.path.join(d, "c.stl")); cmd += ["--closure", os.path.join(d, "c.stl")]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout


def main():
    bad = 0
    def expect(name, rc_want, words, got):
        nonlocal bad
        rc, out = got
        ok = rc == rc_want and all(w in out for w in words)
        print("pass" if ok else "FAIL", name); bad += not ok
        if not ok: print(out)
    expect("open strap + toggle", 0, ["buildable"], run([band(2.0)], [toggle(-2.0 - T - 0.25)]))
    expect("closed ring", 1, ["RING"], run([band(2.0, open_=False)]))
    blob = trimesh.creation.icosphere(3, 1.0); blob.apply_translation((0, 0, 3.0))
    expect("fused blob", 1, ["THICKNESS"], run([band(2.0), blob]))
    expect("through the rail", 1, ["INSIDE"], run([band(1.4)]))
    expect("toggle fastens nothing", 1, ["FASTENS"], run([band(2.0)], [toggle(-6.0)]))
    print("all planted soft-part mistakes caught" if not bad else f"{bad} test(s) failed"); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
