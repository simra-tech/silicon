#!/usr/bin/env python3
"""Build the OpenSTA inputs of the final-GDS timing run from the canonical chip CDL.

Outputs (all into --out):
  g1_chip_top_sta.v        structural top netlist of the 1414 um chip, digital-relevant part:
                           IO pads (stock sg13g2_io cell names), the g1_digital macro, the
                           por_n tie cell, the top-level antenna diodes and the analog blocks
                           that touch a digital net, as stub cells. Connectivity is the
                           CDL's .SUBCKT g1_chip_top, net names are the CDL names (= the
                           labels of the top-interconnect view of T1).
  g1_analog_stubs.lib      liberty stubs for those analog blocks: digital pins only, input
                           capacitance estimated from the gate area of the MOS devices on the
                           pin (whole sub-hierarchy of the block in the CDL), outputs without
                           timing arcs (the blocks have no timing model).
  nets.json                per top-level net: driver pin, load pins, port (for make_top_spef.py)
  stub_pin_caps.json       per stub input pin: device count, gate area, estimated C
Gate capacitance per area: thin oxide calibrated on sg13g2_inv_1 (pin A 2.867 fF typ liberty,
W 0.74+1.12 um, L 0.13 um -> 11.86 fF/um2, overlap included); thick oxide scaled by the
oxide-thickness ratio of the process spec (TGOXNW/TGOXPW 2.45/2.65 nm, TGOX1NW/1PW
7.3/7.5 nm -> x0.345, 4.09 fF/um2). Estimate, +-50 %.
Python 3.6, no dependencies."""
import argparse, json, re, collections, hashlib
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--cdl', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

C_LV = 2.86745 / ((0.74 + 1.12) * 0.13)          # fF/um2, sg13g2_inv_1 typ
C_HV = C_LV * (2.55 / 7.4)
MOSC = {'sg13_lv_nmos': C_LV, 'sg13_lv_pmos': C_LV, 'sg13_hv_nmos': C_HV, 'sg13_hv_pmos': C_HV}

# ---------------- CDL parse
lines = []
for raw in open(a.cdl):
    raw = raw.rstrip('\n')
    if raw.startswith('+') and lines: lines[-1] += ' ' + raw[1:]
    else: lines.append(raw)
subckts = {}; cur = None
for ln in lines:
    t = ln.split()
    if not t or t[0].startswith('*'): continue
    k = t[0].lower()
    if k == '.subckt': cur = t[1]; subckts[cur] = dict(ports=t[2:], items=[])
    elif k == '.ends': cur = None
    elif cur: subckts[cur]['items'].append(t)

def num(s):
    m = re.match(r'([-+0-9.eE]+)([a-zA-Z]*)', s); v = float(m.group(1)); u = m.group(2).lower()
    return v * {'': 1, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'm': 1e-3, 'f': 1e-15}.get(u[:1], 1)

def x_parse(t):
    """X line -> (name, nets, cell)."""
    toks = [x for x in t if '=' not in x]
    if '/' in toks: i = toks.index('/'); return toks[0], toks[1:i], toks[i + 1]
    return toks[0], toks[1:-1], toks[-1]

memo = {}
def gate_load(cell, port):
    """(area_um2 by model, device count) of MOS gates on port of cell, recursively."""
    key = (cell, port)
    if key in memo: return memo[key]
    sc = subckts[cell]; res = collections.Counter(); n = 0
    for t in sc['items']:
        c0 = t[0][0].upper()
        if c0 == 'M':
            d, g, s, b, model = t[1:6]
            if g != port or model not in MOSC: continue
            p = dict(x.split('=') for x in t[6:] if '=' in x)
            area = num(p['w']) * num(p['l']) * float(p.get('m', '1')) * 1e12
            res[model] += area; n += 1
        elif c0 == 'X':
            name, nets, sub = x_parse(t)
            if sub not in subckts: continue
            for i, nt in enumerate(nets):
                if nt == port and i < len(subckts[sub]['ports']):
                    r2, n2 = gate_load(sub, subckts[sub]['ports'][i]); res.update(r2); n += n2
    memo[key] = (res, n); return memo[key]

# ---------------- stub definitions: cell -> list of (cdl_port, stub_pin, direction)
STUB = collections.OrderedDict([
    ('g1_osc',  [('en', 'en', 'input')] + [('trim[%d]' % i, 'trim_%d' % i, 'input') for i in range(4)] + [('osc_clk', 'osc_clk', 'output')]),
    ('g1_trip', [('clk', 'clk', 'input')] + [('dac_soft[%d]' % i, 'dac_soft_%d' % i, 'input') for i in range(8)]
                + [('dac_hard[%d]' % i, 'dac_hard_%d' % i, 'input') for i in range(8)] + [('cmp_soft', 'cmp_soft', 'output'), ('cmp_hard', 'cmp_hard', 'output')]),
    ('g1_gate', [(p, p, 'input') for p in ('trip_d', 'clr_d', 'fast_en', 'hard_cmp', 'en_core')] + [(p, p, 'output') for p in ('gate_core', 'fault_core', 'tripped')]),
    ('g1_ls_up', [('in', 'in', 'input'), ('out', 'out', 'output')]),
    ('g1_t2f', [('en', 'en', 'input'), ('mode', 'mode', 'input'), ('fout', 'fout', 'output')]),
    ('g1_bgr', [('r4', 'r4', 'input')]),
])
IOMAP = {  # CDL IO derivative -> (stock cell, [(cdl port, liberty pin, dir)])
    'G1_VSS_DERIVATIVE__sg13g2_IOPadIn': ('sg13g2_IOPadIn', [('pad', 'pad', 'port'), ('p2c', 'p2c', 'output')]),
    'G1_VSS_DERIVATIVE__sg13g2_IOPadOut4mA': ('sg13g2_IOPadOut4mA', [('pad', 'pad', 'port'), ('c2p', 'c2p', 'input')]),
    'G1_VSS_DERIVATIVE__sg13g2_IOPadOut16mA': ('sg13g2_IOPadOut16mA', [('pad', 'pad', 'port'), ('c2p', 'c2p', 'input')]),
    'G1_VSS_DERIVATIVE__sg13g2_IOPadOut30mA': ('sg13g2_IOPadOut30mA', [('pad', 'pad', 'port'), ('c2p', 'c2p', 'input')]),
    'G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog': ('sg13g2_IOPadAnalog', [('pad', 'pad', 'port'), ('padres', 'padres', 'inout')]),
}
SUPPLY = {'VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS'}

stubcaps = collections.OrderedDict()
for cell, pins in STUB.items():
    for cp, sp, d in pins:
        if d != 'input': continue
        r, n = gate_load(cell, cp)
        c = sum(area * MOSC[m] for m, area in r.items())
        stubcaps['%s/%s' % (cell, sp)] = dict(cdl_port=cp, devices=n, gate_area_um2={m: round(v, 4) for m, v in r.items()}, C_fF=round(c, 3))

# ---------------- digital macro port directions (ECO gate netlist interface, CDL port order)
MACRO_OUT = set('bgr_r4 clk_div_out clr_d cmp_clk fast_en fault_n gate_en osc_en sdo t2f_en t2f_mode trip trip_d trip_set_sel'.split()) \
    | {'dac_hard[%d]' % i for i in range(8)} | {'dac_soft[%d]' % i for i in range(8)} | {'osc_trim[%d]' % i for i in range(4)} | {'trip_cause[%d]' % i for i in range(2)}

top = subckts['g1_chip_top']
esc = lambda s: '\\' + s + ' '
v = ['// Generated by make_sta_inputs.py from the canonical chip CDL (.SUBCKT g1_chip_top). STA view: digital-relevant',
     '// instances only; decap/fill/tap cells, supply pads, corner and filler IO cells, bondpads, SENSE/DOSE/DUT omitted.',
     'module g1_chip_top (%s);' % ', '.join(p for p in top['ports'] if p not in SUPPLY)]
for p in top['ports']:
    if p not in SUPPLY: v.append('  inout %s;' % p)
nets = collections.defaultdict(lambda: dict(driver=None, loads=[], port=None))
wires = set(); body = []
def conn(net, inst, pin, d):
    if net in SUPPLY: return
    wires.add(net)
    if d == 'output':
        assert nets[net]['driver'] is None, (net, inst, pin); nets[net]['driver'] = [inst, pin]
    else: nets[net]['loads'].append([inst, pin, d])
for p in top['ports']:
    if p not in SUPPLY: nets[p]['port'] = p
for t in top['items']:
    if t[0][0].upper() != 'X': continue
    name, nl, cell = x_parse(t); iname = name[1:]
    if cell in IOMAP:
        stock, pm = IOMAP[cell]; ports = subckts[cell]['ports']; cs = []
        if nl[ports.index('pad')] in SUPPLY: continue          # pad07_vdda: supply, not timed
        for cp, lp, d in pm:
            n = nl[ports.index(cp)]
            if n.startswith('_nc'): continue
            cs.append('.%s(%s)' % (lp, n)); conn(n, iname, lp, 'input' if d == 'port' else d)
        body.append('  %s %s (%s);' % (stock, iname, ', '.join(cs)))
    elif cell == 'g1_digital':
        ports = subckts[cell]['ports']; buses = collections.OrderedDict(); cs = []
        for cp, n in zip(ports, nl):
            if cp in ('VDD', 'VSS'): continue
            conn(n, 'i_core.u_digital', cp, 'output' if cp in MACRO_OUT else 'input')
            m = re.match(r'(\w+)\[(\d+)\]$', cp)
            if m: buses.setdefault(m.group(1), {})[int(m.group(2))] = n
            else: cs.append('.%s(%s)' % (cp, n))
        for b, bits in buses.items():
            cs.append('.%s({%s})' % (b, ', '.join(bits[i] for i in sorted(bits, reverse=True))))
        body.append('  g1_digital %s(%s);' % (esc('i_core.u_digital'), ', '.join(cs)))
    elif cell == 'sg13g2_tiehi':
        body.append('  sg13g2_tiehi %s(.L_HI(%s));' % (esc('i_core.u_digital_1'), nl[0])); conn(nl[0], 'i_core.u_digital_1', 'L_HI', 'output')
    elif cell == 'sg13g2_antennanp':
        body.append('  sg13g2_antennanp %s (.A(%s));' % (iname, nl[0])); conn(nl[0], iname, 'A', 'input')
    elif cell in STUB:
        ports = subckts[cell]['ports']; cs = []; inst = iname.replace('i_core_u_', 'i_core.u_')
        for cp, sp, d in STUB[cell]:
            n = nl[ports.index(cp)]; cs.append('.%s(%s)' % (sp, n)); conn(n, inst, sp, d)
        body.append('  %s %s(%s);' % (cell, esc(inst), ', '.join(cs)))
v += ['  wire %s;' % w for w in sorted(wires - set(top['ports']))] + body + ['endmodule', '']
(out / 'g1_chip_top_sta.v').write_text('\n'.join(v))

# ---------------- liberty stubs
L = ['/* Generated by make_sta_inputs.py: interface stubs of G1 analog blocks for STA. Digital pins only.',
     '   Input capacitance estimated from MOS gate area (see stub_pin_caps.json); outputs have no timing arcs. */',
     'library (g1_analog_stubs) {', '  delay_model : table_lookup;', '  time_unit : "1ns";', '  voltage_unit : "1V";',
     '  current_unit : "1mA";', '  pulling_resistance_unit : "1kohm";', '  leakage_power_unit : "1nW";',
     '  capacitive_load_unit (1,pf);', '  nom_process : 1;', '  nom_voltage : 1.2;', '  nom_temperature : 25;',
     '  default_input_pin_cap : 0;', '  default_output_pin_cap : 0;']
for cell, pins in STUB.items():
    L += ['  cell (%s) {' % cell, '    area : 0;', '    dont_touch : true;', '    dont_use : true;']
    for cp, sp, d in pins:
        L.append('    pin (%s) { direction : %s; capacitance : %s; }' % (sp, d, ('%.6f' % (stubcaps['%s/%s' % (cell, sp)]['C_fF'] / 1000.0)) if d == 'input' else '0'))
    L.append('  }')
L += ['}', '']
(out / 'g1_analog_stubs.lib').write_text('\n'.join(L))
sha = hashlib.sha256(open(a.cdl, 'rb').read()).hexdigest()
(out / 'nets.json').write_text(json.dumps(dict(cdl=a.cdl, cdl_sha256=sha, nets=nets), indent=1, sort_keys=True) + '\n')
(out / 'stub_pin_caps.json').write_text(json.dumps(dict(cdl_sha256=sha, C_LV_fF_per_um2=round(C_LV, 4), C_HV_fF_per_um2=round(C_HV, 4), pins=stubcaps), indent=1) + '\n')
nodrv = sorted(k for k, n in nets.items() if n['driver'] is None and not n['port'])
print('nets', len(nets), 'no-driver internal nets', nodrv)
for k, s in stubcaps.items(): print('%-22s %3d dev %7.2f fF %s' % (k, s['devices'], s['C_fF'], s['gate_area_um2']))
