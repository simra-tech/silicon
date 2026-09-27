#!/usr/bin/env python3
"""Gate 3: non-overlap window measured on the extracted candidate (g1_trip_nf4_novclk_pex.spice), full macro with
DAC codes soft 153 / hard 200, ISENSE at 1.5 V (fixed), VREF 1.04 V, clock 212 ns period with 0.2 ns edges on the
cmp_clk pin (as the kick bench). At the 2nd clock period (VDD/2 crossings, internal nets x1.cmp_clk_s / x1.cmp_clk_n):
  W_fall = t(cmp_clk_s falls) - t(cmp_clk_n rises)   (hard evaluates, soft resets later)
  W_rise = t(cmp_clk_n falls) - t(cmp_clk_s rises)   (soft evaluates, hard resets later)
plus the evaluate-edge delays from cmp_clk, 10-90 % edge times and swing of both comparator clocks.
  python3 win_pex.py <outdir> <net> <mos> <vdd> <temp>  -> deck; run with ngspice -b in blocks/g1_trip/sim"""
import os, sys
out, net, mos, vdd, temp = sys.argv[1:6]
name = 'win_%s_%sV_%sC' % (mos, vdd, temp)
v = float(vdd)
bits = '\n'.join('Vs%d s%d 0 dc %s\nVh%d h%d 0 dc %s' % (b, b, vdd if (153 >> b) & 1 else '0', b, b, vdd if (200 >> b) & 1 else '0') for b in range(8))
deck = f"""* {name}
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib {mos}
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib {mos}
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib cap_typ
.temp {temp}
.option rshunt=1e12 gmin=1e-13
.include {net}
Vdd vdd 0 dc {vdd}
Vdda vdda 0 dc 3.3
Vref vref 0 dc 1.04
Visense isense 0 dc 1.5
Vclk cmp_clk 0 pulse(0 {vdd} 20n 0.2n 0.2n 105.8n 212n)
{bits}
X1 isense vref cmp_clk s0 s1 s2 s3 s4 s5 s6 s7 h0 h1 h2 h3 h4 h5 h6 h7 cmp_soft cmp_hard vdd vdda 0 g1_trip
Cq cmp_soft 0 10f
Cqh cmp_hard 0 10f
.control
tran 0.02n 460n
let h = {v / 2}
meas tran tclk_r when v(cmp_clk)=h rise=2
meas tran tclk_f when v(cmp_clk)=h fall=2
meas tran ts_r when v(x1.cmp_clk_s)=h rise=2
meas tran ts_f when v(x1.cmp_clk_s)=h fall=2
meas tran th_r when v(x1.cmp_clk_n)=h rise=2
meas tran th_f when v(x1.cmp_clk_n)=h fall=2
meas tran s_tr trig v(x1.cmp_clk_s) val={v*0.1} rise=2 targ v(x1.cmp_clk_s) val={v*0.9} rise=2
meas tran s_tf trig v(x1.cmp_clk_s) val={v*0.9} fall=2 targ v(x1.cmp_clk_s) val={v*0.1} fall=2
meas tran h_tr trig v(x1.cmp_clk_n) val={v*0.1} rise=2 targ v(x1.cmp_clk_n) val={v*0.9} rise=2
meas tran h_tf trig v(x1.cmp_clk_n) val={v*0.9} fall=2 targ v(x1.cmp_clk_n) val={v*0.1} fall=2
meas tran s_min min v(x1.cmp_clk_s) from=200n to=460n
meas tran s_max max v(x1.cmp_clk_s) from=200n to=460n
meas tran h_min min v(x1.cmp_clk_n) from=200n to=460n
meas tran h_max max v(x1.cmp_clk_n) from=200n to=460n
let w_fall = ts_f - th_r
let w_rise = th_f - ts_r
let ev_s = ts_r - tclk_r
let ev_h = th_r - tclk_f
echo "WIN {name} w_fall=$&w_fall w_rise=$&w_rise ev_soft=$&ev_s ev_hard=$&ev_h s_tr=$&s_tr s_tf=$&s_tf h_tr=$&h_tr h_tf=$&h_tf s_min=$&s_min s_max=$&s_max h_min=$&h_min h_max=$&h_max"
wrdata {out}/{name}.dat v(cmp_clk) v(x1.cmp_clk_s) v(x1.cmp_clk_n)
.endc
.end
"""
open(os.path.join(out, name + '.cir'), 'w').write(deck)
print(os.path.join(out, name + '.cir'))
