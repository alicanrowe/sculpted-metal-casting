"""Governor r2: liquid lines (SDF, swelling and tapering) joined to crisp turned parts (exact CSG).

The oil is drawn as lines of liquid silver; the machine appears only at the nodes, as small turned and knurled
parts. sdf_part() meshes an SDF scene and hands it to manifold3d so it can be unioned or cut exactly with mlib
solids. Units mm."""
import math
import numpy as np
import manifold3d as m3
import sdf
from mlib import M

VOX = 0.05


def sdf_part(s, vox=None, smooth=6):
    """mesh, smooth, hand to manifold. Marching cubes can leave a non-manifold vertex where two surfaces almost
    touch; then re-mesh at a slightly shifted voxel (the same trick as the cast kit), up to five times."""
    import trimesh
    v0 = vox or VOX
    for f in (1.0, 0.97, 1.04, 0.93, 1.08):
        V, F = sdf.mesh(s.array(), vox=v0 * f, verbose=False)
        m = trimesh.Trimesh(V, F, process=False)
        if smooth:
            trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=smooth)
        mm = m3.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))
        mm.merge()
        out = M(mm)
        if out.status() == m3.Error.NoError: break
    else:
        raise RuntimeError(f"sdf mesh not manifold: {out.status()}")
    parts = out.decompose()
    if len(parts) > 1:      # marching-cube crumbs
        parts = [p for p in parts if p.volume() > 0.5]
        out = M.batch_boolean(parts, m3.OpType.Add)
    return out


def curve(ctrl, n=14, closed=False):
    return sdf.catmull(np.asarray(ctrl, float), n, closed=closed)


def prof(n, keys):
    """radius along a line: keys [(u, r), ...] with u in 0..1, smoothstep between keys."""
    u = np.linspace(0, 1, n); ks = np.asarray(keys, float)
    out = np.empty(n)
    for i, x in enumerate(u):
        j = np.searchsorted(ks[:, 0], x, side="right") - 1; j = min(max(j, 0), len(ks) - 2)
        a, b = ks[j], ks[j + 1]; t = (x - a[0]) / max(b[0] - a[0], 1e-9); t = t * t * (3 - 2 * t)
        out[i] = a[1] + (b[1] - a[1]) * t
    return out


def line(s, ctrl, keys, k=0.35, n=14, flat=1.0, normal=(0, 0, 1), op=0, closed=False, kseg=0.0):
    P = curve(ctrl, n, closed)
    r = prof(len(P), keys)
    nm = np.tile(np.asarray(normal, float), (len(P), 1)) if np.ndim(normal) == 1 else normal
    s.stroke(P, r, op=op, k=k, flat=flat, normals=nm, kseg=kseg)
    return P, r


def ring_pt(theta, R, y=0.0):
    """point on a ring round the finger (axis Y), theta 0 = top (+Z)."""
    return (R * math.sin(theta), y, R * math.cos(theta))
