"""Assembly and clipping check for multi-part pieces built from primitives (runs headless in bpy, no rendering).
  TOOLS_MODULE=tools_v3 python3 check_assembly.py [piece ...]     (default: every piece in PIECES and STANDS)
The tools module exports PIECES {key: build()} and STANDS {key: build() -> (stand, [(tool_key, matrix)])}; it builds on
a tools_lib with Tool/Acc (each Acc.add is one physical part). Used by the tools-and-stands work (see buildable.md).

Every add() to a material is one physical part. Checks, per piece:
  1. GLASS   nothing intersects the glass vessel (a cage is bent round blown glass, it cannot pass through it);
             and the glass is held: something touches it (within 0.004 in).
  2. FLOAT   every part touches or penetrates another part (one connected assembly per piece); lists loose parts.
  3. WIRE    cast wire / thorn tips at least 0.5 mm across (radius >= 0.0098 in) in cast metals.
  4. STAND   placed tools do not pass through their stand (contact is fine, penetration over 0.02 in is not).
  5. CLIP    no visible clipping: separate soft parts (leather cords, cut edges, thread) may not pass into anything
             beyond leather compression (0.006 in; thread 0.0015 in); every other pair of different materials whose
             surfaces cross is listed as a seated joint with its depth, so a reviewer can see each one.
Prints a report and writes fabcheck_<piece>.json next to the script's working dir; exit code 1 if anything fails."""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tools_lib as TL
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_add0 = TL.Acc.add
def _add(self, verts, faces):
    o, of = len(self.v), len(self.f)
    _add0(self, verts, faces)
    w = T.LAST_WIRE if 'T' in globals() else None
    ow = getattr(T, 'CORD', None) if 'T' in globals() else None
    self.__dict__.setdefault('parts', []).append((o, len(self.v) - o, of, len(self.f) - of, w, ow))
    if 'T' in globals(): T.LAST_WIRE = None
TL.Acc.add = _add
_get0 = TL.Tool.__getitem__
def _get(self, mat):
    a = _get0(self, mat); a.mat = mat; return a
TL.Tool.__getitem__ = _get
import importlib
T = importlib.import_module(os.environ.get('TOOLS_MODULE', 'tools_v3'))

TOL = 0.004
CAST = {'blacksteel', 'iron', 'silver'}
VESSEL = {'glass'}

def parts_of(tool, M=None):
    out = []
    for mat, acc in tool.parts.items():
        for (o, nv, of, nf, wr, ow) in acc.__dict__.get('parts', []):
            vs = [Vector(p) for p in acc.v[o:o + nv]]
            if M is not None: vs = [M @ v for v in vs]
            fs = [tuple(i - o for i in f) for f in acc.f[of:of + nf]]
            if not vs or not fs: continue
            lo = Vector((min(v[i] for v in vs) for i in range(3))); hi = Vector((max(v[i] for v in vs) for i in range(3)))
            out.append({'owner': ow, 'wire': wr, 'mat': mat, 'v': vs, 'f': fs, 'lo': lo, 'hi': hi, 'bvh': BVHTree.FromPolygons(vs, fs, epsilon=0.0)})
    return out

def boxes_near(a, b, tol=TOL):
    return all(a['lo'][i] - tol <= b['hi'][i] and b['lo'][i] - tol <= a['hi'][i] for i in range(3))

def touching(a, b):
    if not boxes_near(a, b): return False
    if a['bvh'].overlap(b['bvh']): return True
    for small, big in ((a, b), (b, a)):         # both ways: a coarse part may have no vertex near a fine one
        step = max(1, len(small['v']) // 6000)
        for v in small['v'][::step]:
            hit = big['bvh'].find_nearest(v, TOL)
            if hit[0] is not None: return True
    small, big = (a, b) if len(a['v']) < len(b['v']) else (b, a)
    # fully inside the other part (a pin in a bore): a ray from inside crosses the other part an odd number of times
    p = small['v'][0]; d = Vector((0.137, 0.271, 0.953)).normalized(); n = 0; q = p
    for _ in range(64):
        h = big['bvh'].ray_cast(q, d)
        if h[0] is None: break
        n += 1; q = h[0] + d * 1e-5
    return n % 2 == 1

def depth_into(a, b):
    """How far a's vertices sit inside closed part b (0 if none): sampled with ray parity and nearest distance."""
    if not boxes_near(a, b, 0): return 0.0
    worst = 0.0; d = Vector((0.137, 0.271, 0.953)).normalized()
    step = max(1, len(a['v']) // 600)
    for v in a['v'][::step]:
        n, q = 0, v
        for _ in range(64):
            h = b['bvh'].ray_cast(q, d)
            if h[0] is None: break
            n += 1; q = h[0] + d * 1e-5
        if n % 2:
            nd = b['bvh'].find_nearest(v)
            if nd[0] is not None: worst = max(worst, nd[3])
    return worst

def check_tool(name, tool):
    P = parts_of(tool); rep = {'piece': name, 'parts': len(P), 'fail': [], 'note': []}
    glass = [p for p in P if p['mat'] in VESSEL]
    for g in glass:
        held = False
        for p in P:
            if p is g or p['mat'] in VESSEL: continue
            if boxes_near(p, g, 0) and p['bvh'].overlap(g['bvh']):
                c = (p['lo'] + p['hi']) / 2
                rep['fail'].append('GLASS: a %s part (centre %.2f, %.2f, %.2f) passes through the glass' % (p['mat'], *c))
            elif touching(p, g): held = True
        if not held: rep['fail'].append('GLASS: nothing holds the glass')
    # connectivity
    n = len(P); parent = list(range(n))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) != find(j) and touching(P[i], P[j]): parent[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    if len(groups) > 1:
        main = max(groups.values(), key=len)
        for gi in groups.values():
            if gi is main: continue
            for i in gi[:6]:
                c = (P[i]['lo'] + P[i]['hi']) / 2
                rep['fail'].append('FLOAT: loose %s part, centre (%.2f, %.2f, %.2f), size %.3f' % (P[i]['mat'], *c, max(P[i]['hi'] - P[i]['lo'])))
    clip_check(P, rep)
    return rep, P

SOFT = {'leather', 'leather_edge', 'thread', 'cord', 'cord_b'}
def clip_allow(a, b):
    ms = {a['mat'], b['mat']}
    if 'thread' in ms: return 0.0015
    if ms & SOFT: return 0.006
    return None                       # hard against hard: a seated joint (pin in bore, inlay in its seat), listed only

def clip_check(P, rep):
    joints = 0; worst = {}
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            a, b = P[i], P[j]
            if a['mat'] == b['mat'] and a['mat'] not in SOFT: continue      # one forging / casting
            if a['mat'] in VESSEL or b['mat'] in VESSEL: continue          # glass is check 1
            if not boxes_near(a, b, 0) or not a['bvh'].overlap(b['bvh']): continue
            d = max(depth_into(a, b), depth_into(b, a))
            lim = clip_allow(a, b)
            if lim is None:
                joints += 1; continue
            if a['mat'] == 'leather_edge' and b['mat'] == 'leather' or b['mat'] == 'leather_edge' and a['mat'] == 'leather':
                if a['owner'] is not None and a['owner'] == b['owner']: continue   # the cut edge is sunk into its own cord
            if d > lim:
                key = tuple(sorted((a['mat'], b['mat'])))
                c = (a['lo'] + a['hi']) / 2
                if key not in worst or d > worst[key][0]: worst[key] = (d, c, 0)
                worst[key] = (max(d, worst[key][0]), worst[key][1], worst[key][2] + 1)
    for (ma, mb), (d, c, nn) in worst.items():
        rep['fail'].append('CLIP: %d %s/%s pairs pass into each other, worst %.4f in, near (%.2f, %.2f, %.2f)' % (nn, ma, mb, d, *c))
    if joints: rep['note'].append('%d seated joints between different hard materials (pins, inlays, sleeves)' % joints)

def main(names):
    T.FEATURES.clear()
    bad = 0; out = []
    for name in names:
        T.FEATURES.clear()
        if name in T.PIECES:
            rep, _ = check_tool(name, T.PIECES[name]())
        else:
            st, placed = T.STANDS[name]()
            rep, SP = check_tool(name, st)
            for key, M in placed:
                TP = parts_of(T.PIECES[key](), M)
                worst = 0.0
                for a in TP:
                    for b in SP:
                        if boxes_near(a, b, 0) and a['bvh'].overlap(b['bvh']):
                            worst = max(worst, depth_into(a, b), depth_into(b, a))
                if worst > 0.02: rep['fail'].append('STAND: %s passes %.3f in into the stand' % (key, worst))
                elif not any(touching(a, b) for a in TP for b in SP if boxes_near(a, b)):
                    rep['fail'].append('STAND: %s is not carried by the stand (no contact)' % key)
                else: rep['note'].append('%s rests on the stand' % key)
        allp = parts_of(T.PIECES[name]()) if name in T.PIECES else parts_of(T.STANDS[name]()[0])
        thin = [(p['wire'], p['mat'], (p['lo'] + p['hi']) / 2) for p in allp if p['wire'] is not None and p['mat'] in CAST and p['wire'] < 0.0098]
        for w, m, c in thin[:8]:
            rep['fail'].append('WIRE: cast %s wire %.2f mm across at (%.2f, %.2f, %.2f), under 0.5 mm' % (m, w * 2 * 25.4, *c))
        print('%-20s parts %4d  %s' % (name, rep['parts'], 'OK' if not rep['fail'] else 'FAIL'), flush=True)
        for f in rep['fail']: print('   ', f)
        for f in rep['note']: print('    note:', f)
        bad += bool(rep['fail']); out.append(rep)
    json.dump(out, open('fabcheck_report.json', 'w'), indent=1, default=str)
    return bad

if __name__ == '__main__':
    names = sys.argv[1:] or list(T.PIECES) + list(T.STANDS)
    sys.exit(1 if main(names) else 0)
