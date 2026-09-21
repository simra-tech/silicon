#!/usr/bin/env python3
"""Off-current baseline decks for the PCell-only G1_DOSE variants, from their LVS-extracted netlists.

  pcell : g1_dose_pair_pcell  -- sg13_hv_nmos drain on D_ELT (VDS 0.1, 1.2, 3.3 V; VGS sweep to 3.3 V),
                                 sg13_lv_nmos drain on D_STD (VDS 0.1, 1.2 V)
  nw    : g1_dose_pair_nw     -- narrow LV on D_ELT, wide LV on D_STD (VDS 0.1, 1.2 V)

VGS = 0, source and body 0 V; corners mos_tt/ss/ff of BOTH cornerMOSlv.lib and cornerMOShv.lib (same
corner names); temperatures -40, 27, 85, 125, 150, 175 C (150/175 model extrapolated).
Model lines exactly as used (PDK_ROOT=/foss/pdks in the pinned container, commit 8437402):
  .lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib <corner>
  .lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib <corner>
  pre_osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
The PSP model has no STI-edge transistor: this is the pre-irradiation baseline only.
Run: python3 gen_offcurrent_variants.py && bash run_offcurrent_variants.sh   (inside flow/run.sh)
"""
import os
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'decks'); os.makedirs(out, exist_ok=True)
M = '/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models'
corners = ['mos_tt', 'mos_ss', 'mos_ff']
temps = [-40, 27, 85, 125, 150, 175]
variants = {
    'pcell': dict(sub='g1_dose_pair_pcell', a='hv', b='lv', vds_a=[0.1, 1.2, 3.3], vgs_max_a=3.3),
    'nw':    dict(sub='g1_dose_pair_nw', a='narrow', b='wide', vds_a=[0.1, 1.2], vgs_max_a=1.2),
}
head = """* G1_DOSE {sub} off-current baseline: corner {corner}, T = {T} C{tag}
.lib {M}/cornerMOSlv.lib {corner}
.lib {M}/cornerMOShv.lib {corner}
.include ../g1_dose_pair_{v}_extracted.cir
.option gmin=1e-16 abstol=1e-16 reltol=1e-4
.temp {T}
X1 D_ELT D_STD G_SHARED VSS {sub}
Vg G_SHARED 0 dc 0
Vs VSS 0 dc 0
Vda D_ELT 0 dc 0.1
Vdb D_STD 0 dc 0.1
.control
pre_osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
set filetype=ascii
set wr_singlescale
set wr_vecnames
"""
runs = []
for v, cfg in variants.items():
    for c in corners:
        for T in temps:
            tag = '  (MODEL EXTRAPOLATED)' if T > 125 else ''
            stem = f'{v}_{c}_T{T:+d}C'.replace('+', 'p').replace('-', 'm')
            d = head.format(sub=cfg['sub'], corner=c, T=T, tag=tag, M=M, v=v)
            a, b = cfg['a'], cfg['b']
            for vds in (0.1, 1.2):
                t = str(vds).replace('.', '')
                d += f"alter vda dc = {vds}\nalter vdb dc = {vds}\nop\nlet id_{a}_v{t} = -i(vda)\nlet id_{b}_v{t} = -i(vdb)\nlet ratio_v{t} = id_{b}_v{t}/id_{a}_v{t}\nprint id_{a}_v{t} id_{b}_v{t} ratio_v{t}\n"
            for vds in cfg['vds_a'][2:]:
                t = str(vds).replace('.', '')
                d += f"alter vda dc = {vds}\nop\nlet id_{a}_v{t} = -i(vda)\nprint id_{a}_v{t}\n"
            d += f"alter vda dc = 0.1\nalter vdb dc = 0.1\ndc Vg -0.3 {cfg['vgs_max_a']} 0.01\nlet id_{a} = -i(vda)\nlet id_{b} = -i(vdb)\nwrdata {stem}_idvg_v01.dat id_{a} id_{b}\n.endc\n.end\n"
            open(os.path.join(out, stem + '_off.cir'), 'w').write(d)
            runs.append(f'ngspice -b {stem}_off.cir > ../logs/{stem}_off.log 2>&1')
open(os.path.join(here, 'run_offcurrent_variants.sh'), 'w').write(
    '#!/usr/bin/env bash\n# Run from this directory inside the pinned container (flow/run.sh).\nset -e\ncd "$(dirname "$0")/decks"\nmkdir -p ../logs\n' + '\n'.join(runs) + '\n')
print(len(runs), 'runs written')
