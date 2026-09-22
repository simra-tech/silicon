#!/usr/bin/env python3
"""Bounded unchanged-PSP charge-difference observation fixture; no adoption."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'g1_trip/sim'))
from run_nominal_clock_probe import run_bounded


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--step-ns',type=float,required=True)
    p.add_argument('--amplitude',type=float,required=True);p.add_argument('--cpu',type=int,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={a.cpu} and a.cpu in (6,7)
    assert (a.amplitude,a.step_ns) in ((0.,.1),(.3,.1),(.3,.05))
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    native='XM1 fn inn tail vdd sg13_hv_pmos w=384u l=2u ng=64 m=1 mm_ok=1'
    assert source.read_text().splitlines().count(native)==1
    pd=Path('/foss/pdks/ihp-sg13g2');assert (pd/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    expected=json.loads((HERE/'psp-junction-source-equations-20260922-r1.json').read_text())['file_hashes']
    assert all(sha(pd/n)==h for n,h in expected.items())
    fields=('w','l','delvto','factuo','ctype','sdint','ijs','cjs','lp_rjuns','lp_rg','lp_rse','lp_rde','lp_rbulk','lp_rjund','lp_rwell')
    saved=' '.join('@n.xm1.nsg13_hv_pmos['+f+']' for f in fields)
    low=3.3-a.amplitude
    deck='''* Native PSP source-junction DeltaQ observation; ideal-bias diagnostic only.
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib mos_tt_mismatch
.temp 25
.option rshunt=1e12 gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7 method=gear
VD fn 0 .157014036212935
VG inn 0 .071652077882563
VS tail 0 1.503158591455624
'''+f'VB vdd 0 PWL(0 3.3 10n 3.3 30n {low:.17g} 50n {low:.17g} 70n 3.3 100n 3.3)\n'+native+'\n.save all '+saved+'''
.control
set num_threads=1
set numdgt=17
set filetype=ascii
setseed 73001
reset
set temp=25
op
write initial.raw all
'''+f'tran {a.step_ns:.17g}n 100n 0 {a.step_ns:.17g}n\n'+'''write transient.raw all
echo CHARGE_CONTROL_COMPLETE
quit
.endc
.end
'''
    a.output.mkdir(parents=True);(a.output/'probe.cir').write_text(deck)
    (a.output/'.spiceinit').write_bytes((HERE.parents[2]/'g1_trip/sim/.spiceinit').read_bytes())
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    contract=dict(source_sha256=sha(source),deck_sha256=sha(a.output/'probe.cir'),files=expected,
                  source_instance=native,amplitude_V=a.amplitude,maxstep_ns=a.step_ns,
                  ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
                  declared_gates=dict(static_BS_KCL_abs_A=1e-15,zero_charge_abs_C=1e-20,
                                      return_cycle_relative=.001,timestep_relative=.001,integral_CdV_relative=.001,
                                      charge_absolute_floor_C=1e-20),
                  observation='signed BS-side DeltaQ from native resistor, rshunt and static ijs; not absolute Q',
                  scope='single ideal-biased canonical PMOS, separate draw; no shared-layout or full-SENSE applicability claim')
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:
        result=run_bounded(['ngspice','-b','probe.cir'],log,a.output/'run.json',30,cwd=a.output,interval_s=.5)
    assert all(sha(pd/n)==h for n,h in expected.items()) and sha(source)==contract['source_sha256']
    assert sum(f.stat().st_size for f in a.output.iterdir() if f.is_file())<8*2**20
    print(json.dumps(result,indent=2));assert result['status']=='completed' and result['returncode']==0


if __name__=='__main__':main()
