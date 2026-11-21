"""Close the small open loops a mesher leaves where two strokes graze (casting-rules: repair before printing).
Each boundary loop is capped with a fan to its centroid, wound to match the faces around it.
usage: python repair_stl.py in.stl out.stl  -> prints loops, watertight, volume change"""
import sys, numpy as np, trimesh, networkx as nx
m = trimesh.load(sys.argv[1]); m.merge_vertices(); v0 = abs(m.volume)
F = m.faces.copy(); V = m.vertices.copy()
# directed boundary edges: an edge (a,b) used once; the cap must use (b,a)
e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
key = np.sort(e, 1); u, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
bd = e[cnt[inv] == 1]
G = nx.DiGraph(); G.add_edges_from([(b, a) for a, b in bd])          # reversed: the cap's winding
newF, newV = [], []
loops = 0
for comp in nx.weakly_connected_components(G):
    sub = G.subgraph(comp)
    if any(d != 1 for _, d in sub.out_degree()) or len(comp) > 400:
        print("skip loop", len(comp)); continue
    start = next(iter(comp)); cyc = [start]
    while True:
        nxt = next(iter(sub.successors(cyc[-1])))
        if nxt == start: break
        cyc.append(nxt)
    c = len(V) + len(newV); newV.append(V[cyc].mean(0))
    for i in range(len(cyc)):
        newF.append([cyc[i], cyc[(i + 1) % len(cyc)], c])
    loops += 1
if newV:
    m = trimesh.Trimesh(np.vstack([V, newV]), np.vstack([F, newF]), process=True)
print(f"capped {loops} loops, watertight {m.is_watertight}, winding {m.is_winding_consistent}, "
      f"volume change {100*(abs(m.volume)-v0)/v0:+.4f}%, bodies {m.body_count}")
if m.is_watertight: m.export(sys.argv[2])
