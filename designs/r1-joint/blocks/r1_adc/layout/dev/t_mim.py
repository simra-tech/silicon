# DRC probe: unit MIM mesh with TM1 bridges, Via4 under MIM, TV1 island in an empty slot, MIM over LV MOS.
import os, sys
sys.path.insert(0, '/work/designs/g1-guardian/blocks/g1_sense/layout')
from g1_layout_lib import *
OUT = globals().get('out', 't_mim.gds')
ly, top, D = new_layout('t_mim')
s = 3.78; p = 5.2
for i in range(3):
    for j in range(3):
        if (i, j) == (2, 1):
            continue
        x, y = 10 + i * p, 10 + j * p
        D.pcell('cmim', {'Calculate': 'C', 'w': '%gu' % s, 'l': '%gu' % s}, x, y)
        D.sq('Via4', x + s / 2, y + s / 2, VIA); D.sq('M4', x + s / 2, y + s / 2, 0.40)
        if i < 2 and (i + 1, j) != (2, 1):
            D.box('TM1', x + s - 0.2, y + s / 2 - 0.82, x + p + 0.2, y + s / 2 + 0.82)
        if j < 2:
            D.box('TM1', x + s / 2 - 0.82, y + s - 0.2, x + s / 2 + 0.82, y + p + 0.2)
# tab from (1,1) east into the empty slot (2,1)
x, y = 10 + p, 10 + p
xt = 10 + 2 * p + s / 2
D.box('TM1', x + s - 0.2, y + s / 2 - 0.82, xt + 0.82, y + s / 2 + 0.82)
D.sq('TV1', xt, y + s / 2, TV1); D.sq('M5', xt, y + s / 2, 1.0); D.sq('Via4', xt, y + s / 2, VIA); D.sq('M4', xt, y + s / 2, 0.4)
# bridge cap 4.23 at pitch 5.45 next to a unit
D.pcell('cmim', {'Calculate': 'C', 'w': '4.23u', 'l': '4.23u'}, 40, 10)
D.pcell('cmim', {'Calculate': 'C', 'w': '3.78u', 'l': '3.78u'}, 40 + 5.45, 10)
D.box('TM1', 40 + 4.23 - 0.2, 10 + 1.9 - 0.82, 45.45 + 0.2, 10 + 1.9 + 0.82)
D.sq('Via4', 42, 12, VIA); D.sq('M4', 42, 12, 0.4); D.sq('Via4', 47.3, 12, VIA); D.sq('M4', 47.3, 12, 0.4)
D.box('TM1', 41.5, 13.5, 43.14, 20); D.sq('TV1', 42.32, 19, TV1); D.sq('M5', 42.32, 19, 1.0)
# 70 x 70 MIM over LV MOS rows
D.pcell('cmim', {'Calculate': 'C', 'w': '70u', 'l': '70u'}, 10, 40)
m = Mos(D, 'nmos', 2.0, 0.13, 2, 20, 60); m.gate_bar('bot'); m.rail('top', m.strips(1))
mp = Mos(D, 'pmos', 2.0, 0.13, 2, 30, 60); mp.gate_bar('bot'); mp.rail('top', mp.strips(1))
D.box('NWell', 29, 58, 33, 64)
D.tap_strip(18, 26, 57, ptype=True)
D.tap_strip(29.5, 32.5, 63.0, ptype=False)
D.box('M2', 15, 70, 70, 70.4); D.box('M3', 15, 72, 70, 72.4); D.box('M4', 15, 74, 70, 74.4)
D.sq('Via4', 50, 80, VIA); D.sq('M4', 50, 80, 0.4)
D.box('TM1', 76, 75, 80, 77); D.sq('TV1', 79, 76, TV1); D.sq('M5', 79, 76, 1.0)
D.tap_ring(5, 5, 90, 115, w=0.6)
D.boundary(0, 0, 95, 120)
ly.write(OUT)
print('wrote', OUT)
