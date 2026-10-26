"""Locate a short: shortest chain of shapes inside one extracted (merged) net between two seed points.
klayout -b -r tools/short_path.py -rd db=<lvsdb> -rd circuit=<c> -rd net=<layout net> -rd a=x,y,layer -rd b=x,y,layer
Layers are the lvsdb names (l10 Metal1, l11 Via1, l12 Metal2 ... l20 TopMetal1, l6 Cont, l7 GatPoly, l4/l5/l8/l9 diffusion).
Shapes touch-connect on the same layer and to the layers next to them in the stack (bounding-box test, then polygon test)."""
import pya, collections
SA, SB = globals()['a'], globals()['b']
l2n = pya.LayoutVsSchematic(); l2n.read(globals()['db'])
c = l2n.netlist().circuit_by_name(globals()['circuit'])
net = [x for x in c.each_net() if x.expanded_name() == globals()['net']][0]
dbu = l2n.internal_layout().dbu
STACK = {'l6': ['l4', 'l5', 'l8', 'l9', 'l7', 'l10'], 'l11': ['l10', 'l12'], 'l13': ['l12', 'l14'], 'l15': ['l14', 'l16'],
         'l17': ['l16', 'l18'], 'l19': ['l18', 'l20']}
adj = collections.defaultdict(set)
for v, ls in STACK.items():
    for l in ls:
        adj[v].add(l); adj[l].add(v)
shapes = []
for ln in l2n.layer_names():
    r = l2n.shapes_of_net(net, l2n.layer_by_name(ln), True)
    for p in r.each():
        shapes.append((ln, p))
print('shapes', len(shapes))
G = 2000   # grid hash cell in dbu
cells = collections.defaultdict(list)
for i, (ln, p) in enumerate(shapes):
    b = p.bbox()
    for gx in range(b.left // G, b.right // G + 1):
        for gy in range(b.bottom // G, b.top // G + 1):
            cells[(gx, gy)].append(i)
def nbrs(i):
    ln, p = shapes[i]; b = p.bbox()
    seen = set()
    for gx in range(b.left // G, b.right // G + 1):
        for gy in range(b.bottom // G, b.top // G + 1):
            for j in cells[(gx, gy)]:
                if j == i or j in seen: continue
                seen.add(j)
                lj, q = shapes[j]
                if lj != ln and lj not in adj[ln]: continue
                if not b.touches(q.bbox()): continue
                if pya.Region(p).interacting(pya.Region(q)).is_empty() and pya.Region(p).overlapping(pya.Region(q)).is_empty():
                    if not (pya.Region(p).sized(1) & pya.Region(q)).is_empty(): yield j
                    continue
                yield j
def seed(s):
    x, y, l = s.split(','); pt = pya.Point(int(round(float(x) / dbu)), int(round(float(y) / dbu)))
    c_ = [i for i, (ln, p) in enumerate(shapes) if ln == l and p.bbox().contains(pt)]
    if not c_: raise SystemExit('no shape at ' + s)
    return c_
A, B = seed(SA), set(seed(SB))
prev = {i: None for i in A}; dq = collections.deque(A); hit = None
while dq:
    i = dq.popleft()
    if i in B: hit = i; break
    for j in nbrs(i):
        if j not in prev: prev[j] = i; dq.append(j)
if hit is None: raise SystemExit('not connected')
chain = []
while hit is not None: chain.append(hit); hit = prev[hit]
for i in reversed(chain):
    ln, p = shapes[i]; b = p.bbox().to_dtype(dbu)
    print('%-4s (%.3f %.3f %.3f %.3f)' % (ln, b.left, b.bottom, b.right, b.top))
