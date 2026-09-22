#!/usr/bin/env python3
"""Prepare only: canonical single-PMOS repeated-bias and changed-body diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
FIELDS=('w','l','delvto','factuo','ctype','sdint','vsb','vds','vgs','ijs','cjs','cjsbot','cjsgat','cjssti',
        'lp_rg','lp_rse','lp_rde','lp_rbulk','lp_rjuns','lp_rjund','lp_rwell')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    native='XM1 fn inn tail vdd sg13_hv_pmos w=384u l=2u ng=64 m=1 mm_ok=1'
    assert source.read_text().splitlines().count(native)==1
    a.output.mkdir(parents=True)
    deck='''* Canonical-device conditional bias diagnostic; not the SENSE design.
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib mos_tt_mismatch
.temp 25
.option rshunt=1e12 gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7 method=gear
VD fn 0 .157014036212935
VG inn 0 .071652077882563
VS tail 0 1.503158591455624
VB vdd 0 3.3
'''+native+'''
.save all
.control
set num_threads=1
set numdgt=17
set filetype=ascii
setseed 73001
reset
set temp=25
'''
    for label,body in [('equal_a',3.3),('equal_b',3.3),('negative_body',3.0)]:
        deck+=f'alter VB = {body}\nop\necho BIAS_BEGIN_{label}\n'
        for field in FIELDS:deck+='print @n.xm1.nsg13_hv_pmos['+field+']\n'
        deck+='write '+label+'.raw all\necho BIAS_END_'+label+'\n'
    deck+='quit\n.endc\n.end\n'
    (a.output/'probe.cir').write_text(deck)
    (a.output/'.spiceinit').write_bytes((HERE.parents[2]/'g1_trip/sim/.spiceinit').read_bytes())
    (a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    contract=dict(status='prepared only; not run',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  canonical_device=native,deck_sha256=hashlib.sha256(deck.encode()).hexdigest(),
                  model_binding='Same compiled canonical PSP/card, canonical W/L/ng/m/mm_ok; separate tiny-circuit realization, not original full-population draw',
                  cases=['equal_a','equal_b','negative_body'],changed_parameter='external ideal body source only:3.3→3.0V',
                  model_parameter_gate='all four realized W/L/DELVTO/FACTUO exactly identical across three OP points',
                  mapping_gate='pinned descriptor/source collapse plus independent channel-voltage identities',
                  equal_bias_gate={'junction_voltage_abs_delta_V':1e-9,'junction_capacitance_relative_delta':1e-6},
                  negative_bias_gate={'junction_voltage_abs_delta_V_min':.29,'junction_capacitance_relative_delta_min':.01},
                  bound={'child_seconds':30,'CPU':6,'new_output_MiB':8},
                  charge='not exposed; not run; cjs is not charge',
                  applicability='not qualified; this checks necessary bias conditions and mapping, not shared-geometry electrical equivalence',
                  non_changes=['canonical design source','GDS','model cards','compiled OSDI','rule decks','internal electrical node connections'])
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n');print(json.dumps(contract,indent=2))


if __name__=='__main__':main()
