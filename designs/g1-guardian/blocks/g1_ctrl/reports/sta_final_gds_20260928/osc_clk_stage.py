#!/usr/bin/env python3
"""osc_clk insertion upstream of the macro's clock root, by ngspice (the oscillator has no liberty).
Circuit: the two output inverters of g1_osc as in the canonical CDL (XB1 q->qn_b, XB2 qn_b->osc_clk;
g1_osc_inv: lv PMOS 1/0.13 um, lv NMOS 0.5/0.13 um), the top-level osc_clk route as a pi
(C/2 - R - C/2, R = series upper bound, C = route total incl. coupling grounded), the macro-internal
part of the net (series R sum and total C of the port net in the macro SPEF) as a second pi, and the macro's root clock buffer
clkbuf_0_osc_clk (sg13g2_buf_16, PDK stdcell SPICE) with its 38 fF routed load. Stimulus: ideal
pulse on q with 0.2 ns edges, 100 ns period. Measured: delay q->A and qn_b->A (50 %), 20-80 %
transition at A (the liberty's slew thresholds). One run per corner, and one with R=0,C=0 (no route).
Usage: osc_clk_stage.py <R_ohm> <C_route_fF> <R_macro_internal_ohm> <C_macro_internal_fF> <outdir>   (runs inside the container)"""
import sys, subprocess, json, re, os
R, C, Rin, Cin, outd = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
M = '/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models'; SC = '/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice'
CORNERS = dict(fast=('mos_ff', 1.32, -40), typ=('mos_tt', 1.20, 25), slow=('mos_ss', 1.08, 125))
res = {}
OSDI = '/foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi'
open(os.path.join(outd, '.spiceinit'), 'w').write(''.join('osdi %s/%s.osdi\n' % (OSDI, n) for n in ('psp103', 'psp103_nqs', 'r3_cmc', 'mosvar')))
for route in ('route', 'noroute'):
    for k, (mos, v, t) in CORNERS.items():
        r, c, ri, ci = (R, C, Rin, Cin) if route == 'route' else (0.001, 0.0, 0.001, 0.0)   # noroute: osc output straight on the buffer pin
        name = '%s_%s' % (k, route)
        deck = """* osc_clk output stage + top route + macro root buffer, %s
.lib %s/cornerMOSlv.lib %s
.include %s
.temp %g
.option klu
.subckt g1_osc_inv a y vdd vss
XMP y a vdd vdd sg13_lv_pmos w=1u l=0.13u m=1
XMN y a vss vss sg13_lv_nmos w=0.5u l=0.13u m=1
.ends
VDD vdd 0 %g
VQ q 0 PULSE(0 %g 10n 0.2n 0.2n 49.8n 100n)
XB1 q qn_b vdd 0 g1_osc_inv
XB2 qn_b osc vdd 0 g1_osc_inv
C1 osc 0 %gf
R1 osc mid %g
C2 mid 0 %gf
C3 mid 0 %gf
R2 mid far %g
C4 far 0 %gf
XBUF x far vdd 0 sg13g2_buf_16
CL x 0 38f
.tran 1p 130n
.control
run
meas tran dq_r trig v(q) val=%g rise=1 targ v(far) val=%g rise=1
meas tran dq_f trig v(q) val=%g fall=1 targ v(far) val=%g fall=1
meas tran dn_r trig v(qn_b) val=%g fall=1 targ v(far) val=%g rise=1
meas tran dn_f trig v(qn_b) val=%g rise=1 targ v(far) val=%g fall=1
meas tran tr trig v(far) val=%g rise=1 targ v(far) val=%g rise=1
meas tran tf trig v(far) val=%g fall=1 targ v(far) val=%g fall=1
meas tran tr_osc trig v(osc) val=%g rise=1 targ v(osc) val=%g rise=1
meas tran tf_osc trig v(osc) val=%g fall=1 targ v(osc) val=%g fall=1
.endc
.end
""" % (name, M, mos, SC, t, v, v, c / 2, max(r, 0.001), c / 2, ci / 2, max(ri, 0.001), ci / 2,
       v / 2, v / 2, v / 2, v / 2, v / 2, v / 2, v / 2, v / 2, .2 * v, .8 * v, .8 * v, .2 * v, .2 * v, .8 * v, .8 * v, .2 * v)
        dp = os.path.join(outd, name + '.cir'); open(dp, 'w').write(deck)
        p = subprocess.Popen(['ngspice', '-b', dp], cwd=outd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        o = p.communicate()[0].decode(errors='replace'); open(os.path.join(outd, name + '.log'), 'w').write(o)
        m = {kk: float(vv) * 1e9 for kk, vv in re.findall(r'^(\w+)\s*=\s*([-+0-9.eE]+)', o, re.M) if kk in ('dq_r', 'dq_f', 'dn_r', 'dn_f', 'tr', 'tf', 'tr_osc', 'tf_osc')}
        res[name] = dict(corner=k, route=route, models=mos, vdd=v, temp=t, R_ohm=r, C_route_fF=c, R_macro_ohm=ri, C_macro_fF=ci, rc=p.returncode, ns=m)
        print(name, p.returncode, m)
json.dump(res, open(os.path.join(outd, 'osc_clk_stage.json'), 'w'), indent=1, sort_keys=True)
