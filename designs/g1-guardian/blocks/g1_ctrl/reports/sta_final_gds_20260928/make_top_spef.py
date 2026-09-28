#!/usr/bin/env python3
"""Write the top-level route parasitics of the chip as a SPEF for OpenSTA.

Inputs: nets.json of make_sta_inputs.py (driver and load pins of every top-level net), the per-net
R/C of the top-interconnect view (--rc; T1's top_rc_nets.json: kpex 2.5D CC C_total = ground +
coupling to the other routed nets, R_series_upper_bound_ohm, R_pin_to_pin from the reference pin),
and the view summary (--aux; make_top_interconnect_spice.py: C_pin_only_fragments_fF of IO-cell pin
stacks, C_bondpad_fF, and the pad-side port nets, which have no route).
Models (--model):
  p2p  star: the reference pin of the extraction (the pin without an R_pin_to_pin entry, normally
       the macro pin) is the centre node; every other pin hangs on it through its R_pin_to_pin;
       pins without an entry (a second antenna diode) take the largest R of the net. Half of the
       net C sits on the centre, the other half is split evenly over the other pins. Nets without
       R_pin_to_pin fall back to ub.
  ub   pi: the series upper bound R between the driver and one far node, C/2 at each end, every
       load on the far node through 1 mOhm (pessimistic).
Coupling C is grounded (Miller factor 1, no signal-integrity analysis). Fragment C is added to the
routed nets, bondpad + fragment C to the pad-side port nets, unless disabled.
Python 3.6, no dependencies."""
import argparse, json, hashlib, datetime, re
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--nets', required=True); ap.add_argument('--rc', required=True); ap.add_argument('--aux', required=True)
ap.add_argument('--out', required=True); ap.add_argument('--report', required=True)
ap.add_argument('--model', choices=('p2p', 'ub'), default='p2p')
ap.add_argument('--no-fragments', action='store_true'); ap.add_argument('--no-bondpad', action='store_true')
ap.add_argument('--cscale', type=float, default=1.0, help='multiply the route C (sensitivity runs)')
a = ap.parse_args()
N = json.load(open(a.nets))['nets']
RCJ = json.load(open(a.rc)); RC = RCJ['nets']
AUX = json.load(open(a.aux))['nets']

ANT = {}   # antenna instance by x position (CDL order = x order on the chip, checked against the net)
def t1pin(key, net):
    inst, pin = key.rsplit(':', 1)
    m = re.match(r'retained_fullchip_sg13g2_antennanp@([\d.]+),', inst)
    if m: return ('ANTENNA', float(m.group(1)), pin)
    inst = inst[1:] if inst.startswith('X') else inst
    inst = inst.replace('i_core_u_', 'i_core.u_')
    pin = re.sub(r'\[(\d+)\]$', r'_\1', pin) if inst in ('i_core.u_trip', 'i_core.u_osc') else pin
    return (inst, pin)

OUTPORTS = {'SDO', 'FAULT_N', 'GATE', 'TEMP_OUT'}; INPORTS = {'EN', 'SCLK', 'SDI'}
esc = lambda s: s.replace('.', '\\.')
pin = lambda inst, p: '%s:%s' % (esc(inst), p)
L = ['*SPEF "ieee 1481-1999"', '*DESIGN "g1_chip_top"', '*DATE "%s"' % datetime.date.today().isoformat(),
     '*VENDOR "G1"', '*PROGRAM "make_top_spef.py"', '*VERSION "2"', '*DESIGN_FLOW "PIN_CAP NONE"',
     '*DIVIDER /', '*DELIMITER :', '*BUS_DELIMITER []', '*T_UNIT 1 NS', '*C_UNIT 1 PF', '*R_UNIT 1 OHM', '*L_UNIT 1 HENRY', '',
     '*PORTS'] + ['%s %s' % (p, 'O' if p in OUTPORTS else 'I' if p in INPORTS else 'B') for p in sorted(n for n in N if N[n]['port'])] + ['']
rep = {}; notes = []
for net in sorted(N):
    n = N[net]
    allp = ([] if not n['driver'] else [tuple(n['driver'])]) + [(l[0], l[1]) for l in n['loads']]
    if n['port']:
        drv = n['port']; dconn = '*P %s %s' % (drv, 'O' if drv in OUTPORTS else 'I' if drv in INPORTS else 'B')
    elif n['driver']: drv = pin(*n['driver']); dconn = '*I %s O' % drv
    else: drv = pin(*allp[0]); dconn = '*I %s B' % drv
    others = [pin(*p) for p in allp if pin(*p) != drv]
    conns = [dconn] + ['*I %s I' % l for l in others]
    ax = AUX.get(net, {}); frag = 0.0 if a.no_fragments else (ax.get('C_pin_only_fragments_fF') or 0.0)
    if net in RC:
        d = RC[net]; C = d['C_total_fF'] * a.cscale + frag; Rub = d['R_series_upper_bound_ohm']; src = 'rc'
    elif n['port'] and ax:
        C = frag + (0.0 if a.no_bondpad else ax.get('C_bondpad_fF', 0.0)); Rub = 0.0; src = 'aux_port'   # pad-side: pin stack + bondpad
    elif not n['loads'] and not n['port']:
        L += ['*D_NET %s 0' % net, '*CONN'] + conns + ['*END', '']
        rep[net] = dict(src='open', model='none', C_total_fF=0, R={}); continue
    else:
        notes.append('%s: no R/C, not annotated' % net); continue
    caps = []; res = []; model = a.model; Rmap = {}
    p2p = RC.get(net, {}).get('R_pin_to_pin') or {}
    refs = []
    if model == 'p2p' and p2p:
        keyed = {}
        ants = sorted(p for p in allp if p[0].startswith('ANTENNA'))
        antx = sorted(t1pin(k, net)[1] for k in p2p if t1pin(k, net)[0] == 'ANTENNA')
        for k, r in p2p.items():
            t = t1pin(k, net)
            if t[0] == 'ANTENNA': t = ants[antx.index(t[1])]
            keyed[t] = r
        refs = [p for p in allp if p not in keyed and not p[0].startswith('ANTENNA')]
        if len(refs) != 1: notes.append('%s: reference pin not in the STA view (%s), ub model' % (net, refs))
    if model == 'p2p' and len(refs) == 1:
        centre = pin(*refs[0]); rmax = max(keyed.values())
        leaves = [p for p in allp if p != refs[0]]
        caps.append((centre, C / 2.0))
        for p in leaves:
            r = keyed.get(p, rmax); Rmap[pin(*p)] = r
            caps.append((pin(*p), C / 2.0 / len(leaves))); res.append((centre, pin(*p), r))
        if n['port']: res.append((drv, centre, 0.001))
    else:
        model = 'ub'; far = '%s:1' % net
        caps += [(drv, C / 2.0), (far, C / 2.0)]; res.append((drv, far, max(Rub, 0.001)))
        for l in others: res.append((far, l, 0.001)); Rmap[l] = Rub
    L += ['*D_NET %s %.6g' % (net, C / 1000.0), '*CONN'] + conns + ['*CAP'] + ['%d %s %.6g' % (i + 1, nd, c / 1000.0) for i, (nd, c) in enumerate(caps)] \
         + ['*RES'] + ['%d %s %s %.6g' % (i + 1, x, y, r) for i, (x, y, r) in enumerate(res)] + ['*END', '']
    rep[net] = dict(src=src, model=model, C_total_fF=round(C, 3), C_fragments_fF=frag, R_series_upper_bound_ohm=Rub, R_to_pin_ohm=Rmap, driver=drv)
open(a.out, 'w').write('\n'.join(L) + '\n')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
json.dump(dict(nets_json_sha256=sha(a.nets), rc_sha256=sha(a.rc), aux_sha256=sha(a.aux), spef_sha256=sha(a.out), model=a.model, cscale=a.cscale,
               fragments=not a.no_fragments, bondpad=not a.no_bondpad, notes=notes, nets=rep), open(a.report, 'w'), indent=1, sort_keys=True)
print('nets written', len(rep), 'notes', notes)
