"""Planted settings: a good 4-claw seat passes; 2 claws, a floating stone, a buried stone and touching stones fail.
    python3 tests/test_check_settings.py"""
import os, sys, math
import numpy as np, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from check_settings import check

D = 6.0


def seat(c, claws=4):
    """A cup under the girdle plus `claws` posts that rise past the girdle and lean over the crown."""
    c = np.asarray(c, float)
    cup = trimesh.creation.annulus(r_min=D * 0.46, r_max=D * 0.56, height=D * 0.35)
    cup.apply_translation(c + [0, 0, -D * 0.175 - 0.05])
    parts = [cup]
    for k in range(claws):
        t = 2 * math.pi * k / claws + math.pi / 4
        d = np.array([math.cos(t), math.sin(t), 0])
        a = c + d * (D / 2 + 0.25) + [0, 0, -D * 0.3]; b = c + d * (D / 2 - 0.1) + [0, 0, D * 0.2]
        parts.append(trimesh.creation.cylinder(radius=0.45, segment=[a, b], sections=16))
    return parts


def stone(c):
    return dict(kind="garnet", D=D, L=D, c=list(map(float, c)), n=[0, 0, 1], e1=[1, 0, 0])


def run(parts, stones):
    m = trimesh.boolean.union(parts, engine="manifold") if len(parts) > 1 else parts[0]
    return [r["verdict"] for r in check(m, stones)]


def main():
    bad = 0
    def expect(name, got, want):
        nonlocal bad
        ok = all((w in g) if w != "OK" else g == "OK" for g, w in zip(got, want))
        print(("pass" if ok else "FAIL"), name, got); bad += not ok
    base = trimesh.creation.box((40, 40, 1)); base.apply_translation((0, 0, -D * 0.4))
    expect("good 4-claw", run([base] + seat((0, 0, 0)), [stone((0, 0, 0))]), ["OK"])
    expect("2 claws", run([base] + seat((0, 0, 0), claws=2), [stone((0, 0, 0))]), ["HOLD"])
    expect("floating", run([base], [stone((0, 0, 5))]), ["FLOATING"])
    blk = trimesh.creation.box((12, 12, 6)); expect("buried", run([base, blk], [stone((0, 0, 0))]), ["CLEAR"])
    expect("touching", run([base] + seat((0, 0, 0)) + seat((D + 0.1, 0, 0)), [stone((0, 0, 0)), stone((D + 0.1, 0, 0))]),
           ["SPACING", "SPACING"])
    print("all planted settings caught" if not bad else f"{bad} test(s) failed"); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
