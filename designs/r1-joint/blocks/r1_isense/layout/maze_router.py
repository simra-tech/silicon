#!/usr/bin/env python3
"""Grid maze router for the r1_afe layout generator (pure Python + numpy, no KLayout).

Three routing layers on one grid (pitch P = 0.8 um): index 0 = Metal2, 1 = Metal3 (vertical preferred),
2 = Metal4 (horizontal preferred). Wires are 0.30 um wide, every visited node carries a 0.40 um pad on the
layers it touches, vias (Via2, Via3) sit on grid nodes. With P = 0.8 the worst gap is pad-to-wire 0.45 um and
wire-to-wire 0.50 um, above the Metal2-4 space rules (0.21; 0.24 next to lines wider than 0.39 um).

Fixed shapes (device Metal2 rails, pads, edge pins) reserve the nodes whose pad would come closer than
0.25 um to them for their own net (`reserve()`); nodes reserved by two nets are blocked.
Pins are sets of nodes; reaching any node of a pin connects it (the pin's own metal joins its nodes, or
the router joins them itself when they are on the routing layers).
Algorithm: nets one after the other (A* from the growing tree to the nearest unconnected pin), then
rip-up and re-route of the nets that failed, moved to the front of the order.
"""
import heapq, itertools
import numpy as np

P = 0.8
NL = 3
LNAME = ['M2', 'M3', 'M4']
# cost of one step: [layer][0 = horizontal (x), 1 = vertical (y)]
STEP = [(3, 3), (4, 1), (1, 4)]
VIA = 4
FREE, BLOCK = -1, -2


class Router:
    def __init__(self, x0, y0, nx, ny):
        self.x0, self.y0, self.nx, self.ny = x0, y0, nx, ny
        self.res = np.full((NL, nx, ny), FREE, dtype=np.int32)    # reservation / blocking
        self.occ = np.full((NL, nx, ny), FREE, dtype=np.int32)    # routed net per node
        self.pen = np.zeros((NL, nx, ny), dtype=np.int16)         # soft extra cost
        self.nets = {}          # name -> id
        self.names = []
        self.pins = {}          # net id -> list of pins (list of node tuples)
        self.paths = {}         # net id -> list of node lists
        self.failed = []

    # ---- coordinates --------------------------------------------------------------------------
    def nid(self, name):
        if name not in self.nets:
            self.nets[name] = len(self.names); self.names.append(name)
        return self.nets[name]

    def xy(self, i, j):
        return (round(self.x0 + i * P, 4), round(self.y0 + j * P, 4))

    def ij(self, x, y):
        i = (x - self.x0) / P; j = (y - self.y0) / P
        ri, rj = int(round(i)), int(round(j))
        if abs(i - ri) > 1e-6 or abs(j - rj) > 1e-6:
            raise ValueError('off grid %s %s' % (x, y))
        return ri, rj

    def inside(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny

    # ---- obstacles ------------------------------------------------------------------------------
    def reserve(self, layer, x1, y1, x2, y2, net=None, clear=0.45):
        """a fixed shape of `net` (None = blocks everybody) on routing layer index `layer`."""
        k = BLOCK if net is None else self.nid(net)
        i1 = int(np.ceil((x1 - clear - self.x0) / P - 1e-9)); i2 = int(np.floor((x2 + clear - self.x0) / P + 1e-9))
        j1 = int(np.ceil((y1 - clear - self.y0) / P - 1e-9)); j2 = int(np.floor((y2 + clear - self.y0) / P + 1e-9))
        i1, j1 = max(i1, 0), max(j1, 0); i2, j2 = min(i2, self.nx - 1), min(j2, self.ny - 1)
        if i1 > i2 or j1 > j2:
            return
        sub = self.res[layer, i1:i2 + 1, j1:j2 + 1]
        if k == BLOCK:
            sub[...] = BLOCK
        else:
            m_free = sub == FREE
            m_other = (sub != FREE) & (sub != k)
            sub[m_free] = k
            sub[m_other] = BLOCK

    def block_area(self, layers, x1, y1, x2, y2):
        for l in layers:
            self.reserve(l, x1, y1, x2, y2, None, clear=0.0)

    def block_edges(self):
        for l in range(NL):
            self.res[l, 0, :] = BLOCK; self.res[l, -1, :] = BLOCK
            self.res[l, :, 0] = BLOCK; self.res[l, :, -1] = BLOCK

    def unblock(self, layer, x, y):
        i, j = self.ij(x, y)
        self.res[layer, i, j] = FREE

    def add_pin(self, net, nodes, protect=True):
        """nodes: [(layer, x, y)] on grid. Reserves them for the net; with `protect` and a single access node
        on Metal2, the Metal3 node above is reserved too (keeps the pin reachable)."""
        k = self.nid(net)
        pin = []
        for (l, x, y) in nodes:
            i, j = self.ij(x, y)
            if not self.inside(i, j):
                continue
            if self.res[l, i, j] not in (FREE, k):
                continue          # conflicting node: drop it from the pin
            self.res[l, i, j] = k
            pin.append((l, i, j))
        if not pin:
            raise RuntimeError('pin of %s has no usable node: %s' % (net, nodes[:3]))
        if protect:
            if len(pin) <= 2:
                for (l, i, j) in pin:
                    if l == 0 and self.res[1, i, j] == FREE:
                        self.res[1, i, j] = k
            for (l, i, j) in pin:     # soft: others avoid the nodes above a pin
                if l + 1 < NL:
                    self.pen[l + 1, i, j] += 6
        self.pins.setdefault(k, []).append(pin)
        return pin

    # ---- routing ----------------------------------------------------------------------------------
    def usable(self, k, l, i, j):
        r = self.res[l, i, j]
        if r == BLOCK or (r != FREE and r != k):
            return False
        o = self.occ[l, i, j]
        return o == FREE or o == k

    def astar(self, k, sources, targets, soft=0):
        tset = set(targets)
        ti = np.array([t[1] for t in targets]); tj = np.array([t[2] for t in targets])
        bi1, bi2, bj1, bj2 = ti.min(), ti.max(), tj.min(), tj.max()
        def h(i, j):
            di = bi1 - i if i < bi1 else (i - bi2 if i > bi2 else 0)
            dj = bj1 - j if j < bj1 else (j - bj2 if j > bj2 else 0)
            return di + dj
        g = {}
        prev = {}
        heap = []
        cnt = itertools.count()
        for s in sources:
            g[s] = 0
            prev[s] = None
            heapq.heappush(heap, (h(s[1], s[2]), next(cnt), s))
        nx, ny = self.nx, self.ny
        res, occ, pen = self.res, self.occ, self.pen
        while heap:
            f, _, u = heapq.heappop(heap)
            gu = g[u]
            if f - h(u[1], u[2]) > gu + 1e-9:
                continue
            if u in tset:
                path = []
                while u is not None:
                    path.append(u); u = prev[u]
                return path[::-1]
            l, i, j = u
            nbrs = []
            if i > 0: nbrs.append(((l, i - 1, j), STEP[l][0]))
            if i < nx - 1: nbrs.append(((l, i + 1, j), STEP[l][0]))
            if j > 0: nbrs.append(((l, i, j - 1), STEP[l][1]))
            if j < ny - 1: nbrs.append(((l, i, j + 1), STEP[l][1]))
            if l > 0: nbrs.append(((l - 1, i, j), VIA))
            if l < NL - 1: nbrs.append(((l + 1, i, j), VIA))
            for v, c in nbrs:
                vl, vi, vj = v
                r = res[vl, vi, vj]
                if r == BLOCK or (r != FREE and r != k):
                    continue
                o = occ[vl, vi, vj]
                extra = 0
                if o != FREE and o != k:
                    if not soft:
                        continue
                    extra = soft
                ng = gu + c + extra + (pen[vl, vi, vj] if o != k else 0)
                if ng < g.get(v, 1e18):
                    g[v] = ng; prev[v] = u
                    heapq.heappush(heap, (ng + h(vi, vj), next(cnt), v))
        return None

    def soft_conflicts(self, k):
        """route k through other nets at a high cost; return the set of nets it crosses (None: unreachable)."""
        pins = self.pins.get(k, [])
        tree = set(pins[0]); left = list(pins[1:]); hit_nets = set()
        while left:
            targets = [n for p in left for n in p]
            path = self.astar(k, list(tree), targets, soft=60)
            if path is None:
                self.unreach = (self.names[k], [self.xy(n[1], n[2]) + (n[0],) for p in left for n in p][:4])
                return None
            end = path[-1]
            hit = [p for p in left if end in p][0]; left.remove(hit)
            for n in path:
                o = self.occ[n]
                if o != FREE and o != k:
                    hit_nets.add(int(o))
                    self.pen[n] = min(self.pen[n] + 10, 200)   # history cost on contested nodes
                tree.add(n)
            tree.update(hit)
        return hit_nets

    def route_net(self, k):
        pins = self.pins.get(k, [])
        if len(pins) < 2:
            self.paths[k] = []
            return True
        # start from the pin nearest to the centroid of all pins
        allp = [n for p in pins for n in p]
        ci = np.mean([n[1] for n in allp]); cj = np.mean([n[2] for n in allp])
        order = sorted(range(len(pins)), key=lambda q: min(abs(n[1] - ci) + abs(n[2] - cj) for n in pins[q]))
        tree = set(pins[order[0]])
        left = [pins[q] for q in order[1:]]
        paths = []
        while left:
            targets = [n for p in left for n in p]
            path = self.astar(k, list(tree), targets)
            if path is None:
                return False
            end = path[-1]
            hit = [p for p in left if end in p][0]
            left.remove(hit)
            for n in path:
                tree.add(n)
                self.occ[n] = k
            for n in hit:
                tree.add(n)
            paths.append(path)
        self.paths[k] = paths
        return True

    def unroute(self, k):
        self.occ[self.occ == k] = FREE
        self.paths.pop(k, None)

    def route_guarded(self, names, halo=1, cost=None, log=print):
        """route the listed (sensitive) nets first and give them a keep-out: their path nodes and the nodes within
        `halo` grid steps on the same layer, and directly above/below, are reserved for the net (cost None: no other
        net runs next to, over or under them) or get the extra path cost `cost` (other nets avoid them where they can).
        route_all() keeps these routes unless a rip-up needs them (r1_isense addition)."""
        if not hasattr(self, 'guarded'):
            self.guarded = set()
        for name in names:
            k = self.nid(name)
            if not self.route_net(k):
                self.unroute(k); log('guarded route failed: %s' % name); continue
            self.guarded.add(k)
            for path in self.paths[k]:
                for (l, i, j) in path:
                    for (ll, ii, jj) in [(l, i + di, j + dj) for di in range(-halo, halo + 1) for dj in range(-halo, halo + 1)] + \
                            [(l - 1, i, j), (l + 1, i, j)]:
                        if 0 <= ll < NL and self.inside(ii, jj) and self.res[ll, ii, jj] == FREE and \
                                self.occ[ll, ii, jj] in (FREE, k):
                            if cost is None:
                                self.res[ll, ii, jj] = k
                            else:
                                self.pen[ll, ii, jj] = max(self.pen[ll, ii, jj], cost)
        return self.guarded

    def route_shielded(self, names, shield_net, halo=1, min_comp=3, log=print):
        """r1_isense layout b: route the listed (hold) nets first and wrap them in a grounded shield. Every free node
        within `halo` grid steps of a path node on the same layer and on the layers directly above and below becomes a
        node of `shield_net` (drawn by the layout as solid metal, stacked with vias); nodes next to or above another
        net's pin are left free so that the pin stays reachable. Every 3D-connected shield component becomes one pin
        of `shield_net` (the router then ties it to the rest of that net); components smaller than `min_comp` nodes are
        released. Returns the set of routed nets."""
        if not hasattr(self, 'guarded'):
            self.guarded = set()
        ks = shield_net if isinstance(shield_net, int) else self.nid(shield_net)
        done = []
        for name in names:
            k = self.nid(name)
            if not self.route_net(k):
                self.unroute(k); log('shielded route failed: %s' % name); continue
            self.guarded.add(k); done.append(k)
            for path in self.paths[k]:          # keep the route: no rip-up may cross it later
                for n in path:
                    self.res[n] = k
        pinnear = set()
        for kk, plist in self.pins.items():
            if kk == ks:
                continue
            for pin in plist:
                for (l, i, j) in pin:
                    for di in (-1, 0, 1):
                        for dj in (-1, 0, 1):
                            pinnear.add((l, i + di, j + dj))
                    if l + 1 < NL:
                        pinnear.add((l + 1, i, j))
        cand = set()
        for k in done:
            for path in self.paths[k]:
                for (l, i, j) in path:
                    for ll in (l - 1, l, l + 1):
                        if not 0 <= ll < NL:
                            continue
                        for di in range(-halo, halo + 1):
                            for dj in range(-halo, halo + 1):
                                n = (ll, i + di, j + dj)
                                if not self.inside(n[1], n[2]) or n in pinnear:
                                    continue
                                if self.res[n] == FREE and self.occ[n] == FREE:
                                    cand.add(n)
        # 3D components (same-layer orthogonal neighbours, vertical neighbours)
        comps, seen = [], set()
        for n in cand:
            if n in seen:
                continue
            st, comp = [n], []
            seen.add(n)
            while st:
                u = st.pop(); comp.append(u)
                l, i, j = u
                for v in ((l, i + 1, j), (l, i - 1, j), (l, i, j + 1), (l, i, j - 1), (l + 1, i, j), (l - 1, i, j)):
                    if v in cand and v not in seen:
                        seen.add(v); st.append(v)
            comps.append(comp)
        self.shield = getattr(self, 'shield', {})
        sh = self.shield.setdefault(ks, set())
        nkeep = 0
        for comp in comps:
            if len(comp) < min_comp:
                continue
            for n in comp:
                self.res[n] = ks
            sh.update(comp)
            self.pins.setdefault(ks, []).append(list(comp))
            nkeep += 1
        log('shield: %d nets, %d nodes, %d components kept of %d' % (len(done), len(sh), nkeep, len(comps)))
        return set(done)

    def shield_shapes(self):
        """solid shield geometry: (layer name, x1, y1, x2, y2); pads 0.40, orthogonal links 0.40 wide, full 2 x 2
        node squares filled, vias (Via2 / Via3, 0.19) where two shield nodes are stacked."""
        hp, hv = 0.20, 0.095
        for ks, nodes in getattr(self, 'shield', {}).items():
            for (l, i, j) in nodes:
                x, y = self.xy(i, j)
                yield (LNAME[l], x - hp, y - hp, x + hp, y + hp)
                if (l, i + 1, j) in nodes:
                    yield (LNAME[l], x - hp, y - hp, x + P + hp, y + hp)
                if (l, i, j + 1) in nodes:
                    yield (LNAME[l], x - hp, y - hp, x + hp, y + P + hp)
                if (l, i + 1, j) in nodes and (l, i, j + 1) in nodes and (l, i + 1, j + 1) in nodes:
                    yield (LNAME[l], x - hp, y - hp, x + P + hp, y + P + hp)
                if (l + 1, i, j) in nodes:
                    yield ('Via2' if l == 0 else 'Via3', x - hv, y - hv, x + hv, y + hv)

    def route_all(self, order=None, rounds=6, log=print):
        ids = [k for k in self.pins if len(self.pins[k]) >= 2 and k not in getattr(self, 'guarded', set())]
        self.guarded = set()
        def span(k):
            ns = [n for p in self.pins[k] for n in p]
            return (max(n[1] for n in ns) - min(n[1] for n in ns)) + (max(n[2] for n in ns) - min(n[2] for n in ns))
        ids.sort(key=span)
        failed = []
        for k in ids:
            if not self.route_net(k):
                self.unroute(k); failed.append(k)
        log('initial pass: %d nets, %d failed %s' % (len(ids), len(failed), [self.names[k] for k in failed]))
        hist = {}
        for it in range(rounds * 10):
            if not failed:
                break
            k = failed.pop(0)
            hist[k] = hist.get(k, 0) + 1
            if hist[k] > rounds:
                self.unreach_list = getattr(self, 'unreach_list', []) + [self.names[k]]
                continue
            conf = self.soft_conflicts(k)
            if conf is None:
                log('unreachable pin: %s' % (self.unreach,))
                continue
            for c in conf:
                self.unroute(c)
            if not self.route_net(k):
                self.unroute(k); failed.append(k)
            for c in sorted(conf, key=span):
                if not self.route_net(c):
                    self.unroute(c); failed.append(c)
            log('rip-up %d: %s crossed %d nets, now failed %s' % (it, self.names[k], len(conf), [self.names[q] for q in failed]))
        left = [k for k in ids if k not in self.paths or (len(self.pins[k]) >= 2 and not self.paths.get(k))]
        self.failed = [self.names[k] for k in ids if k in failed or k not in self.paths]
        return not self.failed

    # ---- geometry output ----------------------------------------------------------------------------
    def shapes(self):
        """yields (kind, net, layer_name, x1, y1, x2, y2): wires 0.30, pads 0.40, vias 0.19."""
        hw, hp, hv = 0.15, 0.20, 0.095
        for k, paths in self.paths.items():
            net = self.names[k]
            for path in paths:
                for a, b in zip(path[:-1], path[1:]):
                    xa, ya = self.xy(a[1], a[2]); xb, yb = self.xy(b[1], b[2])
                    if a[0] == b[0]:
                        yield ('wire', net, LNAME[a[0]], min(xa, xb) - hw, min(ya, yb) - hw, max(xa, xb) + hw, max(ya, yb) + hw)
                    else:
                        lo = min(a[0], b[0])
                        for l in (lo, lo + 1):
                            yield ('pad', net, LNAME[l], xa - hp, ya - hp, xa + hp, ya + hp)
                        yield ('via', net, 'Via2' if lo == 0 else 'Via3', xa - hv, ya - hv, xa + hv, ya + hv)
                for n in (path[0], path[-1]):
                    x, y = self.xy(n[1], n[2])
                    yield ('pad', net, LNAME[n[0]], x - hp, y - hp, x + hp, y + hp)

    def used_nodes(self, k):
        s = set()
        for p in self.paths.get(k, []):
            s.update(p)
        return s
