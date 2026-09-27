#!/usr/bin/env python3
"""r4 candidate nf4_novclk: schematic-level design sweep of the non-overlap clock generator.
Writes one ngspice deck per (corner, variant) with the generator driving a lumped copy of the two comparator
clock loads (tail NMOS 4 x 4/0.13 with S/D at vss, precharge PMOS 6+6+3+3 / 0.13 with S/D at vdd, per comparator,
plus 15 fF wiring) and the r3 clock inverter XCLKI (P 1/0.13, N 0.5/0.13) on a separate copy of the load as the
edge-time reference.  Measures, per corner: the delayed-copy delay, the two non-overlap windows
  W_fall = t(cks falls) - t(ckh rises)  after the cmp_clk falling edge (hard evaluates, soft resets later)
  W_rise = t(ckh falls) - t(cks rises)  after the cmp_clk rising edge (soft evaluates, hard resets later)
at VDD/2 crossings, and 10-90 % edge times of cks, ckh and the reference inverter output.
  python3 gen_sweep.py <outdir> <variant> <mos> <vdd> <temp>   -> <outdir>/<name>.cir (run with ngspice -b)"""
import os, sys
out, var, mos, vdd, temp = sys.argv[1:6]
GEN = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(('..', 'g1_novclk.spice') if var == 'final' else ('variants', 'g1_novclk_%s.spice' % var)))).read()
name = 'gen_%s_%s_%sV_%sC' % (var, mos, vdd, temp)
LOAD = """
.subckt ckload ck vdd vss
XMT1 vss ck vss vss sg13_lv_nmos w=16u l=0.13u
XMP1 vdd ck vdd vdd sg13_lv_pmos w=18u l=0.13u
C1 ck vss 15f
.ends
"""
deck = f"""* {name}
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib {mos}
.temp {temp}
.option rshunt=1e12 gmin=1e-13
{GEN}
{LOAD}
Vdd vdd 0 dc {vdd}
Vclk clk 0 pulse(0 {vdd} 20n 0.2n 0.2n 99.8n 200n)
XG clk cks ckh vdd 0 g1_novclk
XLS cks vdd 0 ckload
XLH ckh vdd 0 ckload
XMRP ckr clk vdd vdd sg13_lv_pmos w=1u l=0.13u
XMRN ckr clk 0 0 sg13_lv_nmos w=0.5u l=0.13u
XLR ckr vdd 0 ckload
.control
tran 0.01n 460n
let h = {vdd}/2
meas tran tclk_r when v(clk)=h rise=2
meas tran tclk_f when v(clk)=h fall=2
meas tran tcks_r when v(cks)=h rise=2
meas tran tcks_f when v(cks)=h fall=2
meas tran tckh_r when v(ckh)=h rise=2
meas tran tckh_f when v(ckh)=h fall=2
meas tran tdl_r when v(xg.dly)=h rise=2
meas tran tdl_f when v(xg.dly)=h fall=2
let w_fall = tcks_f - tckh_r
let w_rise = tckh_f - tcks_r
let d_rise = tdl_r - tclk_r
let d_fall = tdl_f - tclk_f
let ev_soft = tcks_r - tclk_r
let ev_hard = tckh_r - tclk_f
meas tran cks_tr trig v(cks) val={{{vdd}*0.1}} rise=2 targ v(cks) val={{{vdd}*0.9}} rise=2
meas tran cks_tf trig v(cks) val={{{vdd}*0.9}} fall=2 targ v(cks) val={{{vdd}*0.1}} fall=2
meas tran ckh_tr trig v(ckh) val={{{vdd}*0.1}} rise=2 targ v(ckh) val={{{vdd}*0.9}} rise=2
meas tran ckh_tf trig v(ckh) val={{{vdd}*0.9}} fall=2 targ v(ckh) val={{{vdd}*0.1}} fall=2
meas tran ref_tr trig v(ckr) val={{{vdd}*0.1}} rise=2 targ v(ckr) val={{{vdd}*0.9}} rise=2
meas tran ref_tf trig v(ckr) val={{{vdd}*0.9}} fall=2 targ v(ckr) val={{{vdd}*0.1}} fall=2
meas tran cks_min min v(cks) from=150n to=460n
meas tran cks_max max v(cks) from=150n to=460n
meas tran ckh_min min v(ckh) from=150n to=460n
meas tran ckh_max max v(ckh) from=150n to=460n
meas tran idd avg i(Vdd) from=220n to=420n
print w_fall w_rise d_rise d_fall ev_soft ev_hard
echo "RESULT {name} w_fall=$&w_fall w_rise=$&w_rise d_rise=$&d_rise d_fall=$&d_fall ev_soft=$&ev_soft ev_hard=$&ev_hard cks_tr=$&cks_tr cks_tf=$&cks_tf ckh_tr=$&ckh_tr ckh_tf=$&ckh_tf ref_tr=$&ref_tr ref_tf=$&ref_tf cks_min=$&cks_min cks_max=$&cks_max ckh_min=$&ckh_min ckh_max=$&ckh_max idd=$&idd"
wrdata {out}/{name}.dat v(clk) v(xg.dly) v(cks) v(ckh) v(ckr)
.endc
.end
"""
open(os.path.join(out, name + '.cir'), 'w').write(deck)
print(os.path.join(out, name + '.cir'))
