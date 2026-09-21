#!/usr/bin/env python3
"""Generate the ngspice decks for the G1_DUT npn13G2 characterisation.

One deck per (HBT corner, temperature). Each deck runs:
  * forward Gummel at VCB = 0 (VBE 0.30 .. 1.00 V, 1 mV): IC, IB, beta
  * output curves IC(VCE) for IB = 1, 2, 4, 8 uA
and extracts VBE at IC = 1 uA, 8 uA, 10 uA, beta at IC = 1 uA and 10 uA and
peak beta into a .meas summary.

Model library inside the pinned container (PDK_ROOT=/foss/pdks, commit 8437402):
  .lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib <corner>
Corners: hbt_typ, hbt_bcs, hbt_wcs.  Temperatures: -40 27 85 125 150 175 C and
-196 C (model extrapolated: the card is characterised -40..125 C only).
Run: python3 gen_decks.py && bash run_all.sh   (inside flow/run.sh)
"""
import os
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'decks')
os.makedirs(out, exist_ok=True)
LIB = '/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib'
corners = ['hbt_typ', 'hbt_bcs', 'hbt_wcs']
temps = [-40, 27, 85, 125, 150, 175, -196]

deck = """* G1_DUT npn13G2 characterisation: corner {corner}, T = {T} C{tag}
* device: npn13G2, Nx=1 (default emitter 0.07 x 0.90 um^2), substrate node to 0
.lib {lib} {corner}
.option gmin=1e-15 abstol=1e-15 reltol=1e-4
.temp {T}

Vbe b 0 dc 0.8
Vc  b c dc 0
XQ1 c b e 0 npn13G2 Nx=1
Ve e 0 dc 0

.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
* ---- forward Gummel, VCB = 0 ----
dc Vbe 0.30 1.00 0.001
let ic = i(vc)
let ib = -i(vbe) - i(vc)
let beta = ic/ib
wrdata {stem}_gummel.dat ic ib beta
meas dc vbe_1u  find v(b) when ic=1e-6
meas dc vbe_8u  find v(b) when ic=8e-6
meas dc vbe_10u find v(b) when ic=1e-5
meas dc vbe_100n find v(b) when ic=1e-7
meas dc ib_1u   find ib when ic=1e-6
meas dc ib_10u  find ib when ic=1e-5
meas dc beta_1u  find beta when ic=1e-6
meas dc beta_10u find beta when ic=1e-5
meas dc beta_100u find beta when ic=1e-4
meas dc beta_max max beta from=0.5 to=1.0
let dvbe_8 = vbe_8u - vbe_1u
print vbe_1u vbe_8u vbe_10u vbe_100n dvbe_8 ib_1u ib_10u beta_1u beta_10u beta_100u beta_max
.endc

.end
"""

deck_out = """* G1_DUT npn13G2 output curves: corner {corner}, T = {T} C{tag}
.lib {lib} {corner}
.option gmin=1e-15 abstol=1e-15 reltol=1e-4
.temp {T}

Ib 0 b dc 1u
Vce c 0 dc 1.0
XQ1 c b e 0 npn13G2 Nx=1
Ve e 0 dc 0

.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
dc Vce 0 1.6 0.01 Ib 1u 8u 1u
let ic = -i(vce)
wrdata {stem}_output.dat ic
.endc
.end
"""

runlines = []
for c in corners:
    for T in temps:
        tag = '  (MODEL EXTRAPOLATED: outside the -40..125 C card range)' if (T < -40 or T > 125) else ''
        stem = f'{c}_T{T:+d}C'.replace('+', 'p').replace('-', 'm')
        with open(os.path.join(out, stem + '_gummel.cir'), 'w') as f:
            f.write(deck.format(corner=c, T=T, lib=LIB, tag=tag, stem=stem))
        with open(os.path.join(out, stem + '_output.cir'), 'w') as f:
            f.write(deck_out.format(corner=c, T=T, lib=LIB, tag=tag, stem=stem))
        runlines.append(f'ngspice -b {stem}_gummel.cir > ../logs/{stem}_gummel.log 2>&1')
        runlines.append(f'ngspice -b {stem}_output.cir > ../logs/{stem}_output.log 2>&1')
with open(os.path.join(here, 'run_all.sh'), 'w') as f:
    f.write('#!/usr/bin/env bash\n# Run from this directory inside the pinned container (flow/run.sh).\n'
            'set -e\ncd "$(dirname "$0")/decks"\nmkdir -p ../logs\nngspice -v | head -3 > ../logs/ngspice_banner.txt\n'
            'cat /foss/pdks/ihp-sg13g2/COMMIT > ../logs/pdk_commit.txt\n' + '\n'.join(runlines) + '\n')
print(len(runlines), 'runs written')
