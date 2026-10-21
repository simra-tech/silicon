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
Revision E2: `first` nets are routed before all others in the given order (P/N pairs one after the other, CM-sense
nets); with `lock` they cannot be ripped up by later nets. `add_stub()` grows dead-end wires of a net on one layer
(capacitance/length trim of the lighter net of a pair); `net_stats()` gives the wire length per layer and the vias.
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
        self.lock = set()       # net ids that rip-up may not cross
        self.stubs = {}         # net id -> list of stub paths (also in self.paths)
        self.halo_cost = 0      # E2: soft cost on the nodes next to the priority nets (other nets keep one track away)
        self.fat = {}           # E2: net id -> list of (layer, i1, j1, i2, j2) wide-wire boxes (supply widening)
        self.xvia = {}          # E2: net id -> list of (lower layer, i, j) extra vias

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
                    if not soft or o in self.lock:
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

    def route_all(self, order=None, rounds=6, log=print, first=(), lock=False):
        ids = [k for k in self.pins if len(self.pins[k]) >= 2]
        def span(k):
            ns = [n for p in self.pins[k] for n in p]
            return (max(n[1] for n in ns) - min(n[1] for n in ns)) + (max(n[2] for n in ns) - min(n[2] for n in ns))
        ids.sort(key=span)
        fid = [self.nets[n] for n in first if n in self.nets and self.nets[n] in ids]
        ids = fid + [k for k in ids if k not in fid]
        if lock:
            self.lock = set(fid)
        failed = []
        for k in ids:
            if not self.route_net(k):
                self.unroute(k); failed.append(k)
            elif self.halo_cost and k in fid:
                self.add_halo(k, self.halo_cost)
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

    # ---- trim stubs and statistics ------------------------------------------------------------------
    def add_stub(self, k, layer, n_edges, log=print):
        """grow dead-end straight wires of net k on routing layer `layer` with n_edges grid edges in total,
        starting from nodes of the net on that layer (or one via from an adjacent layer). Preferred direction of the
        layer first. Returns the number of edges added on `layer`."""
        if n_edges <= 0:
            return 0
        dirs = {0: [(1, 0), (-1, 0), (0, 1), (0, -1)], 1: [(0, 1), (0, -1)], 2: [(1, 0), (-1, 0)]}[layer]
        def free(l, i, j):
            if not self.inside(i, j):
                return False
            r = self.res[l, i, j]
            return r == FREE and self.occ[l, i, j] == FREE
        added = 0
        for _ in range(200):
            left = n_edges - added
            if left <= 0:
                break
            best = None
            for n in sorted(self.used_nodes(k)):
                l0, i0, j0 = n
                if l0 == layer:
                    starts = [(n, None)]
                elif abs(l0 - layer) == 1 and free(layer, i0, j0):
                    starts = [(n, (layer, i0, j0))]
                else:
                    continue
                for (s0, via) in starts:
                    for (di, dj) in dirs:
                        run = 0
                        i, j = i0 + di, j0 + dj
                        while free(layer, i, j) and run < left:
                            # keep one free node beside the run end free of other-net pads: stop before a node next to a
                            # foreign via/pad on this layer is not needed (grid rules), so only the node itself is checked
                            run += 1; i += di; j += dj
                        if run >= 2 and (best is None or run > best[0]):
                            best = (run, s0, via, di, dj)
            if best is None:
                break
            run, s0, via, di, dj = best
            path = [s0]
            if via is not None:
                path.append(via)
            l0, i0, j0 = path[-1]
            for q in range(1, run + 1):
                path.append((layer, i0 + q * di, j0 + q * dj))
            for n in path:
                self.occ[n] = k
            self.paths.setdefault(k, []).append(path)
            self.stubs.setdefault(k, []).append(path)
            added += run
        if added < n_edges:
            log('stub: net %s layer %d: %d of %d edges placed' % (self.names[k], layer, added, n_edges))
        return added

    def add_halo(self, k, cost):
        """soft cost on the free nodes next to net k (same layer, four neighbours) for all other nets."""
        for (l, i, j) in self.used_nodes(k):
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if self.inside(a, b) and self.occ[l, a, b] == FREE:
                    self.pen[l, a, b] = min(int(self.pen[l, a, b]) + cost, 300)

    def widen(self, k, layers=(1, 2), sides=(1, -1)):
        """supply widening after routing: every wire edge of net k on `layers` takes the parallel free track on each
        side (one 1.1 um box per side, up to 1.9 um total width); then extra vias on the widened nodes next to each
        via of the net. Only free nodes are used, so the grid spacing rules still hold."""
        def free_or_own(l, i, j):
            return self.inside(i, j) and self.res[l, i, j] in (FREE, k) and self.occ[l, i, j] in (FREE, k)
        n_box = 0
        for path in list(self.paths.get(k, [])):
            for a, b in zip(path[:-1], path[1:]):
                if a[0] != b[0] or a[0] not in layers:
                    continue
                l = a[0]
                di, dj = b[1] - a[1], b[2] - a[2]
                for sd in sides:
                    oi, oj = (0, sd) if di else (sd, 0)
                    a2 = (l, a[1] + oi, a[2] + oj); b2 = (l, b[1] + oi, b[2] + oj)
                    if free_or_own(*a2) and free_or_own(*b2):
                        if self.res[a2] == k or self.res[b2] == k:
                            continue           # own pin node: leave it (pin shapes are drawn separately)
                        self.occ[a2] = k; self.occ[b2] = k
                        i1, i2 = sorted((a[1], b2[1])); j1, j2 = sorted((a[2], b2[2]))
                        i1, i2 = min(i1, a[1], b[1], a2[1]), max(i2, a[1], b[1], a2[1])
                        j1, j2 = min(j1, a[2], b[2], a2[2]), max(j2, a[2], b[2], a2[2])
                        self.fat.setdefault(k, []).append((l, i1, j1, i2, j2))
                        n_box += 1
        n_via = 0
        for path in self.paths.get(k, []):
            for a, b in zip(path[:-1], path[1:]):
                if a[0] == b[0]:
                    continue
                lo = min(a[0], b[0])
                if lo + 1 not in layers or (lo not in layers):
                    continue
                for (oi, oj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    i, j = a[1] + oi, a[2] + oj
                    if not self.inside(i, j):
                        continue
                    if self.occ[lo, i, j] == k and self.occ[lo + 1, i, j] == k and self.res[lo, i, j] in (FREE, k) \
                            and self.res[lo + 1, i, j] in (FREE, k):
                        self.xvia.setdefault(k, []).append((lo, i, j)); n_via += 1
        return n_box, n_via

    def net_stats(self, k):
        """edges per routing layer and via count of net k (stubs included)."""
        e = [0] * NL; v = [0, 0]
        seen = set()
        for path in self.paths.get(k, []):
            for a, b in zip(path[:-1], path[1:]):
                key = (min(a, b), max(a, b))
                if key in seen:
                    continue
                seen.add(key)
                if a[0] == b[0]:
                    e[a[0]] += 1
                else:
                    v[min(a[0], b[0])] += 1
        return dict(edges=e, um=[round(x * P, 2) for x in e], vias=v)

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

    def fat_shapes(self):
        """wide-wire boxes and extra vias of widen() (wire half width 0.15, pads 0.40, vias 0.19)."""
        hw, hp, hv = 0.15, 0.20, 0.095
        for k, boxes in self.fat.items():
            net = self.names[k]
            for (l, i1, j1, i2, j2) in boxes:
                x1, y1 = self.xy(i1, j1); x2, y2 = self.xy(i2, j2)
                yield ('wire', net, LNAME[l], x1 - hw, y1 - hw, x2 + hw, y2 + hw)
        for k, vs in self.xvia.items():
            net = self.names[k]
            for (lo, i, j) in vs:
                x, y = self.xy(i, j)
                for l in (lo, lo + 1):
                    yield ('pad', net, LNAME[l], x - hp, y - hp, x + hp, y + hp)
                yield ('via', net, 'Via2' if lo == 0 else 'Via3', x - hv, y - hv, x + hv, y + hv)

    def used_nodes(self, k):
        s = set()
        for p in self.paths.get(k, []):
            s.update(p)
        return s
