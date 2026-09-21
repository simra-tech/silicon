#!/usr/bin/env python3
"""G1_DOSE pre-irradiation off-current baseline from the LVS-extracted netlist.

For each MOS corner (mos_tt, mos_ss, mos_ff) and temperature (-40, 27, 85, 125,
150, 175 C; -196 C model extrapolated) one deck: VGS = 0, source and body at 0,
ID of the standard device (D_STD) and of the ELT (D_ELT) at VDS = 0.1 V and 1.2 V,
plus an ID(VGS) sweep -0.3 .. 1.2 V at both VDS written to .dat.

Netlist: g1_dose_pair_extracted.cir = reports/lvs_pair/g1_dose_extracted.cir
with the KLayout device names M$1/M$2 renamed XMELT/XMSTD (sg13_lv_nmos is a subcircuit), pins re-ordered from KLayout S G D B to SPICE D G S B ("$" is a comment
character for ngspice). The PSP model is a planar-device model: it has no
STI-edge (parasitic sidewall) transistor, so both devices are modelled as
identical planar channels of the extracted W/L; the ELT's freedom from STI-edge
leakage is NOT represented here.

Model library in the pinned container (PDK_ROOT=/foss/pdks, commit 8437402):
  .lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib <corner>
  pre_osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi   (PSP 103.6 compiled model)
Run: python3 gen_offcurrent.py && bash run_offcurrent.sh   (inside flow/run.sh)
"""
import os
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'decks'); os.makedirs(out, exist_ok=True)
LIB = '/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib'
corners = ['mos_tt', 'mos_ss', 'mos_ff']
temps = [-40, 27, 85, 125, 150, 175, -196]
deck = """* G1_DOSE off-current baseline: corner {corner}, T = {T} C{tag}
.lib {lib} {corner}
.include ../g1_dose_pair_extracted.cir
.option gmin=1e-16 abstol=1e-16 reltol=1e-4
.temp {T}
X1 D_ELT D_STD G_SHARED VSS g1_dose_pair
Vg G_SHARED 0 dc 0
Vs VSS 0 dc 0
Vdstd D_STD 0 dc 0.1
Vdelt D_ELT 0 dc 0.1
.control
* PSP 103.6 is a Verilog-A model: load the PDK's compiled OSDI object before the circuit is parsed
pre_osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
set filetype=ascii
set wr_singlescale
set wr_vecnames
op
let id_std_v01 = -i(vdstd)
let id_elt_v01 = -i(vdelt)
let ratio_v01 = id_std_v01/id_elt_v01
print id_std_v01 id_elt_v01 ratio_v01
alter vdstd dc = 1.2
alter vdelt dc = 1.2
op
let id_std_v12 = -i(vdstd)
let id_elt_v12 = -i(vdelt)
let ratio_v12 = id_std_v12/id_elt_v12
print id_std_v12 id_elt_v12 ratio_v12
dc Vg -0.3 1.2 0.01
let id_std = -i(vdstd)
let id_elt = -i(vdelt)
wrdata {stem}_idvg_v12.dat id_std id_elt
alter vdstd dc = 0.1
alter vdelt dc = 0.1
dc Vg -0.3 1.2 0.01
let id_std = -i(vdstd)
let id_elt = -i(vdelt)
wrdata {stem}_idvg_v01.dat id_std id_elt
.endc
.end
"""
runs = []
for c in corners:
    for T in temps:
        tag = '  (MODEL EXTRAPOLATED: outside the characterised temperature range)' if (T < -40 or T > 125) else ''
        stem = f'{c}_T{T:+d}C'.replace('+', 'p').replace('-', 'm')
        open(os.path.join(out, stem + '_off.cir'), 'w').write(deck.format(corner=c, T=T, lib=LIB, tag=tag, stem=stem))
        runs.append(f'ngspice -b {stem}_off.cir > ../logs/{stem}_off.log 2>&1')
open(os.path.join(here, 'run_offcurrent.sh'), 'w').write(
    '#!/usr/bin/env bash\n# Run from this directory inside the pinned container (flow/run.sh).\nset -e\ncd "$(dirname "$0")/decks"\nmkdir -p ../logs\n'
    'ngspice -v | head -3 > ../logs/ngspice_banner.txt\ncat /foss/pdks/ihp-sg13g2/COMMIT > ../logs/pdk_commit.txt\n' + '\n'.join(runs) + '\n')
print(len(runs), 'runs written')
