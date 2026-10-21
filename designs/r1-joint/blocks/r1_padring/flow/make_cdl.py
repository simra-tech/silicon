#!/usr/bin/env python3
"""Write the R1 ring canonical CDL and the comparison-only (projected) source CDL.
Library part: the PDK IO CDL with the G1 design-local IO cell copies and the explicit-VSS derivatives, copied
unchanged from the G1 r4 canonical CDL (sections sg13g2_io.cdl, bondpad, EXPLICIT_VSS_DESIGN_LOCAL_DERIVATIVES).
Top part: new, from the R1 pin map (24 pads, 24 bondpads, 4 corners, the same 112 IO fillers as G1).
  make_cdl.py <g1_r4_canonical.cdl> <out_canonical.cdl> <out_projection_source.cdl> [<out_ringonly_source.cdl>]
              [--fillers=<build report json>]
--fillers (revision c, 2026-10-21): take the IO filler population from the ring build report (key 'fillers', counts
per cell, e.g. build_ring_1600.json) instead of the 112 G1 fillers. The ptap1 devices of all IO cells are combined in
parallel by the deck, so the reference tap area and perimeter depend on the filler population; a reference with the
wrong filler set fails on the two tap devices (revision b). The 1 um filler needs its own explicit-VSS derivative.
The projection removes only the dummy all-VDD PMOS 'MP0' of G1_VSS_DERIVATIVE__sg13g2_LevelDown, which the stock
extractor purges (same rule as G1 r3/r4, signoff-1414r4-20260927 README 'Digital macro identity' / RESULTS)."""
import sys, re, hashlib
import json
opts = [a for a in sys.argv[1:] if a.startswith('--')]
args = [a for a in sys.argv[1:] if not a.startswith('--')]
src, out_can, out_proj = args[0:3]
out_ring = args[3] if len(args) > 3 else None
fill_report = next((a.split('=', 1)[1] for a in opts if a.startswith('--fillers=')), None)
L = open(src).read().split('\n')
def find(prefix, start=0):
    return next(i for i in range(start, len(L)) if L[i].startswith(prefix))
io_a = find('* BEGIN_SOURCE sg13g2_io.cdl'); io_b = find('* END_SOURCE sg13g2_io.cdl')
bp_a = find('.SUBCKT bondpad_70x70_tm1'); bp_b = find('.ENDS', bp_a)
dv_a = find('* BEGIN_EXPLICIT_VSS_DESIGN_LOCAL_DERIVATIVES')
top_a = find('* BEGIN_TOP'); top_b = find('* END_TOP')
fills = [l for l in L[top_a:top_b] if l.startswith('XIO_FILL_') or l.startswith('XIO_EXPAND_') or l.startswith('XIO_CORNER_')]
assert len(fills) == 116, len(fills)       # 112 fillers + 4 corners
n_fill_cells = 116
# Explicit-VSS derivative of the PDK 1 um filler. The tap values are those of the KLayout extraction of the cell in the
# ring (deck tap_extraction.lvs, deep mode): revision b ring extraction minus revision a, less the counted change of
# the 4000/2000/400 fillers, divided by 8 (see README revision c). Same form as the G1 derivatives of Filler400/4000.
F200 = ['.SUBCKT G1_VSS_DERIVATIVE__sg13g2_Filler200 vdd vss iovdd iovss G1_EXPLICIT_SUBSTRATE_VSS',
        '*.PININFO iovdd:B iovss:B vdd:B vss:B',
        'R_G1_TAP_SYNTAX_XR1 vss G1_EXPLICIT_SUBSTRATE_VSS ptap1 A=0.678p P=5.12u',
        'R_G1_TAP_SYNTAX_XR0 iovss G1_EXPLICIT_SUBSTRATE_VSS ptap1 A=40.9752p P=149.7u',
        '.ENDS']
if fill_report:
    counts = json.load(open(fill_report))['fillers']
    corners = [l for l in fills if l.startswith('XIO_CORNER_')]
    assert len(corners) == 4
    fills = list(corners)
    for cell in sorted(counts):
        sub = cell.replace('retained_fullchip_sg13g2_', '')
        assert sub in ('Filler200', 'Filler400', 'Filler2000', 'Filler4000'), cell
        for k in range(counts[cell]):
            fills.append('XIO_FILL_R1_%s_%d VDD VSS IOVDD IOVSS VSS / G1_VSS_DERIVATIVE__sg13g2_%s' % (sub, k, sub))
    n_fill_cells = len(fills)
PINS = [(1,'VDD','Vdd'),(2,'VSS','Vss'),(3,'IOVDD','IOVdd'),(4,'IOVSS','IOVss'),(5,'VSS','Vss'),(6,'IOVSS','IOVss'),
 (7,'VDDA','Analog'),(8,'ISA_P','Analog'),(9,'ISA_N','Analog'),(10,'ISB_P','Analog'),(11,'ISB_N','Analog'),
 (12,'FAULT_N','Out4mA'),(13,'GATE_A','Out30mA'),(14,'GATE_B','Out30mA'),(15,'GATE_C','Out30mA'),
 (16,'CS_N','In'),(17,'MA_SCLK','In'),(18,'SLO_SDO','Out4mA'),(19,'SDI','In'),(20,'EN_STO_IN','In'),
 (21,'SIN_P','Analog'),(22,'SIN_N','Analog'),(23,'COS_P','Analog'),(24,'COS_N','Analog')]
ports = []
for _, n, _ in PINS:
    if n not in ports: ports.append(n)
ports = [p for p in ports if p not in ('VDD','VSS','IOVDD','IOVSS')]
ports += ['VDD','VSS','IOVDD','IOVSS']
D = 'G1_VSS_DERIVATIVE__sg13g2_'
top = ['.SUBCKT r1_padring ' + ' '.join(ports)]
nc = 0
for n, net, t in PINS:
    name = 'pad%02d_%s' % (n, net.lower())
    sup = 'VDD VSS IOVDD IOVSS VSS'
    if t in ('Vdd','Vss','IOVdd','IOVss'): top.append('X%s %s / %sIOPad%s' % (name, sup, D, t))
    elif t == 'Analog': nc += 1; top.append('X%s %s _nc%d VDD VSS IOVDD IOVSS VSS / %sIOPadAnalog' % (name, net, nc, D))
    elif t == 'In': top.append('X%s %s %s_p2c VDD VSS IOVDD IOVSS VSS / %sIOPadIn' % (name, net, net.lower(), D))
    else: top.append('X%s %s %s_c2p VDD VSS IOVDD IOVSS VSS / %sIOPad%s' % (name, net, net.lower(), D, t))
for n, net, t in PINS: top.append('XIO_BOND_pad%02d_%s %s / bondpad_70x70_tm1' % (n, net.lower(), net))
top += fills + ['.ENDS']
hdr = ['* r1_padring canonical reference (R1 ring, empty core). Library sections copied unchanged from the G1 r4 canonical',
       '* CDL ' + src + ' sha256 ' + hashlib.sha256(open(src,'rb').read()).hexdigest() + '; top subckt generated by flow/make_cdl.py from the R1 pin map.',
       '* Not LVS-qualified: the canonical IO-cell reference fails in the KLayout deck for the PDK reasons recorded for G1.']
if fill_report: hdr.append('* IO fillers from ' + fill_report.split('/')[-1] + ': ' + json.dumps(counts, sort_keys=True))
dv = L[dv_a:]
if fill_report and any('Filler200' in l for l in fills):
    while dv and dv[-1] == '': dv.pop()
    dv += F200 + ['']
can = hdr + L[io_a:io_b+1] + L[bp_a:bp_b+1] + ['* BEGIN_TOP'] + top + ['* END_TOP', ''] + dv
open(out_can, 'w').write('\n'.join(can) + ('\n' if can[-1] != '' else ''))
# projection source: drop the dummy MP0 in the LevelDown derivative
proj = []; inside = False; dropped = 0
for l in can:
    if l.startswith('.SUBCKT ' + D + 'LevelDown '): inside = True
    if inside and l.startswith('MP0 vdd vdd vdd vdd sg13_hv_pmos'): dropped += 1; continue
    if inside and l.upper().startswith('.ENDS'): inside = False
    proj.append(l)
assert dropped == 1, dropped
proj[0] = '* r1_padring comparison-only projection source: canonical minus the dummy all-VDD PMOS MP0 of the LevelDown derivative'
open(out_proj, 'w').write('\n'.join(proj) + '\n')
if out_ring:
    # Ring-only projection: the substrate node of the explicit-VSS derivatives is a separate internal net
    # (not VSS).  In G1 the chip substrate reaches VSS through the ordinary p-taps of the core cells (deck:
    # connect(pwell, ptap), connect(ptap, cont_drw)); the IO cells' taps carry the 'sub!' label and are extracted
    # as ptap1 devices, so an empty core leaves the layout substrate net separate from VSS.
    ring = []; intop = False; n = 0
    for l in proj:
        if l.startswith('* BEGIN_TOP'): intop = True
        if l.startswith('* END_TOP'): intop = False
        if intop and l.startswith('X') and ' VSS / ' + D in l:
            l = l.replace(' VSS / ' + D, ' SUBSTRATE_NODE / ' + D); n += 1
        ring.append(l)
    assert n == 24 + n_fill_cells, n
    ring[0] = '* r1_padring ring-only comparison source: projection source with the explicit substrate node SUBSTRATE_NODE separate from VSS'
    open(out_ring, 'w').write('\n'.join(ring) + '\n')
print('ports', len(ports), ports); print('top instances', len(top) - 2)
