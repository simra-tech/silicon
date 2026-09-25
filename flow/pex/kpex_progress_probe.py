#!/usr/bin/env python3
"""kpex_named_top.py plus progress counters (diagnostic only; results identical): prints, per
extraction phase and layer, the number of merged polygons to visit and a running count of
visited polygons/edges with wall time, so the total 2.5D runtime can be extrapolated."""
import sys, time
from klayout_pex.rcx25.c import overlap_extractor as oe, sidewall_and_fringe_extractor as se
T0 = time.time()
def log(msg): print('[probe %8.1f s] %s' % (time.time() - T0, msg), flush=True)
def wrap_extract(cls, phase):
    orig = cls.extract
    def extract(self):
        for ln, r in self.layer_regions_by_name.items():
            log('%s: layer %s polygons %d' % (phase, ln, r.count()))
        return orig(self)
    cls.extract = extract
wrap_extract(oe.OverlapExtractor, 'overlap'); wrap_extract(se.SidewallAndFringeExtractor, 'sidewall')
cnt = {'ovl': 0, 'edge': 0, 'poly': 0}
V = oe.OverlapExtractor.PEXPolygonNeighborhoodVisitor; _n = V.neighbors
last = {'ovl': -1, 'sw': -1}
def neighbors(self, *a):
    cnt['ovl'] += 1
    if self.inside_layer_index != last['ovl']:
        last['ovl'] = self.inside_layer_index; log('overlap: start layer idx %d (visited so far %d)' % (self.inside_layer_index, cnt['ovl']))
    if cnt['ovl'] % 1000 == 0: log('overlap polygons visited %d (layer idx %d)' % (cnt['ovl'], self.inside_layer_index))
    return _n(self, *a)
V.neighbors = neighbors
E = se.SidewallAndFringeExtractor.PEXEdgeNeighborhoodVisitor; _b = E.begin_polygon; _e = E.on_edge
def begin_polygon(self, *a):
    cnt['poly'] += 1
    if self.inside_layer_index != last['sw']:
        last['sw'] = self.inside_layer_index; log('sidewall: start layer idx %d (visited so far %d)' % (self.inside_layer_index, cnt['poly']))
    if cnt['poly'] % 1000 == 0: log('sidewall polygons visited %d edges %d (layer idx %d)' % (cnt['poly'], cnt['edge'], self.inside_layer_index))
    return _b(self, *a)
def on_edge(self, *a):
    cnt['edge'] += 1
    return _e(self, *a)
E.begin_polygon = begin_polygon; E.on_edge = on_edge
import klayout.db as kdb
_and = kdb.Region.__and__
cnt['and'] = 0
def region_and(self, other):
    cnt['and'] += 1
    if cnt['and'] % 2000 == 0: log('Region.__and__ calls %d (overlap visitor inner loop)' % cnt['and'])
    return _and(self, other)
kdb.Region.__and__ = region_and
exec(open('/work/flow/pex/kpex_named_top.py').read())
