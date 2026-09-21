#!/usr/bin/env python3
"""Bounded LVS of an exact scratch candidate, preserving all comparison failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parents[4]
BLOCK=ROOT/'designs/g1-guardian/blocks/g1_padring'
PDK=Path('/foss/pdks/ihp-sg13g2')
LVS=PDK/'libs.tech/klayout/tech/lvs'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--work',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
if a.work.exists() or a.report.exists():raise FileExistsError('Preserve existing evidence')
a.work.mkdir(parents=True);a.report.mkdir(parents=True)
work,report,candidate=a.work.resolve(),a.report.resolve(),a.candidate.resolve()
os.environ['KLAYOUT_PATH']=str(PDK/'libs.tech/klayout')
base=BLOCK/'layout/g1_chip_top.gds';cdl=BLOCK/'netlist/g1_chip_top.cdl'
# Intent is specified from stock schematic MP0 (W4.65/L0.45, all VDD), not
# inferred by copying the extracted candidate netlist into a reference.
intent=cdl.read_text();start=intent.index('.SUBCKT sg13g2_IOPadIn ');end=intent.index('.ENDS',start)
line='MP_G1_VDD_ANT vdd vdd vdd vdd sg13_hv_pmos m=1 w=4.65u l=450n ng=1\n'
intent=intent[:end]+line+intent[end:]
intent_path=work/'g1_chip_top_intentional_dummy.cdl';intent_path.write_text(intent)
manifest={'candidate':str(a.candidate),'candidate_sha256':sha(candidate),'baseline_sha256':sha(base),
          'stock_chip_cdl_sha256':sha(cdl),'intentional_reference_sha256':sha(intent_path),
          'intentional_reference_delta':{'cell':'sg13g2_IOPadIn','added_device':line.strip(),
                                        'source':'Independent parallel all-VDD dummy design intent; no extracted netlist used as reference'},
          'pdk_commit':(PDK/'COMMIT').read_text().strip(),'script_sha256':sha(Path(__file__)),
          'scope':'Non-production exact-candidate comparisons; no waived rules/devices','checks':[]}
def save():
    (report/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
save()
shutil.copyfile(Path(__file__),report/'runner.py')
(report/'intentional_cdl_delta.txt').write_text('.SUBCKT sg13g2_IOPadIn pad p2c vdd vss iovdd iovss\n'+line+'* All original devices and connections retained.\n')
def run(name,cmd,timeout=3600):
    log=report/(name+'.log');start=time.monotonic();timeout_hit=False
    with log.open('w') as f:
        proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timeout_hit=True;os.killpg(proc.pid,signal.SIGTERM)
            try:code=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
    txt=log.read_text()
    row={'name':name,'command':cmd,'exit_code':code,'timed_out':timeout_hit,'wall_seconds':time.monotonic()-start,
         'status':'not run' if timeout_hit else ('passed' if code==0 and 'Comparison mode: PASS (netlists match).' in txt else 'failed')}
    manifest['checks'].append(row);save();print(json.dumps(row),flush=True)
# The core helper sees precisely the candidate GDS and original routing DEF.
runview=work/'candidate_run'
for suffix,target in [('gds/g1_chip_top.gds',candidate),('def/g1_chip_top.def',BLOCK/'flow/runs/assembly-1350/final/def/g1_chip_top.def')]:
    link=runview/'final'/suffix;link.parent.mkdir(parents=True,exist_ok=True);link.symlink_to(target)
for name,layout,reference,top in [
    ('input_pad_baseline',base,cdl,'sg13g2_IOPadIn'),
    ('input_pad_candidate_stock_reference',candidate,cdl,'sg13g2_IOPadIn'),
    ('input_pad_candidate_intentional_reference',candidate,intent_path,'sg13g2_IOPadIn'),
    ('full_chip_candidate_stock_reference',candidate,cdl,'g1_chip_top'),
    ('full_chip_candidate_intentional_reference',candidate,intent_path,'g1_chip_top'),
]:
    if name=='full_chip_candidate_stock_reference':
        run('core_lvs',['bash',str(BLOCK/'flow/lvs/run_core_lvs.sh'),str(runview),str(work/'core')])
    output=report/name
    run(name,['python3',str(LVS/'run_lvs.py'),'--layout',str(layout),'--netlist',str(reference),
              '--topcell',top,'--run_mode','deep','--run_dir',str(output),'--top_lvl_pins','--spice_comments'])
    dbs=list(output.glob('*.lvsdb'))
    if dbs:
        with (output/'xref.txt').open('w') as f:
            subprocess.run(['klayout','-b','-rd','db='+str(dbs[0]),'-r',str(BLOCK/'flow/lvs/xref_summary.py')],stdout=f,stderr=subprocess.STDOUT,timeout=120)
assert sha(candidate)==manifest['candidate_sha256']
