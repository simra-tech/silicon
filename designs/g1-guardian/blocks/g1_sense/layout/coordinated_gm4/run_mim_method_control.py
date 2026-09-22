#!/usr/bin/env python3
"""One bounded stock-supported 3D MIM coverage control; no electrical adoption."""
import argparse
import datetime
import importlib.metadata
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import klayout_pex
from export_sense_kpex_api import sha
from klayout_pex.fastercap.fastercap_runner import fastercap_parse_capacitance_matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('coupon','output','resource-gate','original-pilot'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    assert os.sched_getaffinity(0)=={7} and importlib.metadata.version('klayout-pex')=='0.3.12'
    gate=json.loads(args.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['external_allocation']['expected_growth_gib']>=.125
    meta=json.loads((args.coupon/'manifest.json').read_text())
    assert meta['status']=='passed native coupon geometry preparation'
    gds=args.coupon/'sense_mim_method_control.gds';cdl=args.coupon/'sense_mim_method_control.cdl'
    assert sha(gds)==meta['GDS_sha256'] and sha(cdl)==meta['CDL_sha256']
    prior=json.loads((args.original_pilot/'summary.json').read_text())
    package=Path(klayout_pex.__file__).parent;pdk=Path('/foss/pdks/ihp-sg13g2')
    assert all(sha(package/name)==value for name,value in prior['tool_hashes'].items())
    assert all(sha(pdk/name)==value for name,value in prior['card_hashes'].items())
    args.output.mkdir(parents=True,exist_ok=False)
    for path in (Path(__file__),Path(__file__).with_name('MIM_METHOD_CONTROL_20260922.md')):
        (args.output/path.name).write_bytes(path.read_bytes())
    command=['kpex','--pdk','ihp-sg13g2','--threads','1','--fastercap','--blackbox','false','--cache-lvs','false',
             '--geo_check','true','--gds',str(gds),'--cell','sense_mim_method_control','--schematic',str(cdl),
             '--out_dir',str(args.output/'engine')]
    result=dict(status='running',command=command,GDS_sha256=sha(gds),CDL_sha256=sha(cdl),
                script_sha256=sha(Path(__file__)),resource_gate_sha256=sha(args.resource_gate),
                timeout_s=120,max_output_bytes=128*2**20,threads=1,blackbox=False,
                method='supported native FasterCap3D, default settings, all dielectrics',
                matrix_precision='stock FasterCap console print precision; not arbitrary precision',
                completeness='not qualified',electrical_adoption='not run')
    def save(): (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    save();start=time.monotonic();reason=None;interrupts=[]
    old={sig:signal.signal(sig,lambda num,frame:interrupts.append(num))for sig in(signal.SIGINT,signal.SIGTERM)}
    with(args.output/'kpex.log').open('x')as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while child.poll()is None:
                elapsed=time.monotonic()-start;size=sum(p.stat().st_size for p in args.output.rglob('*')if p.is_file())
                result.update(wall_s=elapsed,output_bytes=size);save()
                if interrupts or elapsed>=120 or size>128*2**20:
                    reason='external_interrupt'if interrupts else('timeout'if elapsed>=120 else'output_limit')
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                    break
                try:child.wait(timeout=1)
                except subprocess.TimeoutExpired:pass
        finally:
            if child.poll()is None:os.killpg(child.pid,signal.SIGKILL);child.wait()
            for sig,handler in old.items():signal.signal(sig,handler)
    result.update(returncode=child.returncode,termination_reason=reason,wall_s=time.monotonic()-start,
                  status='failed bounded 3D control')
    matrices=list(args.output.rglob('*_FasterCap_Output.txt'))
    if child.returncode==0 and reason is None and len(matrices)==1:
        try:
            matrix=fastercap_parse_capacitance_matrix(matrices[0])
            rows=matrix.rows;names=matrix.conductor_names
            assert all(math.isfinite(value)for row in rows for value in row)
            result.update(status='passed 3D solver execution; physical coverage audit pending',
                          conductor_names=names,matrix_F=rows)
        except Exception as error:result['matrix_error']=repr(error)
    unchanged=sha(gds)==meta['GDS_sha256'] and sha(cdl)==meta['CDL_sha256']
    unchanged &= all(sha(package/name)==value for name,value in prior['tool_hashes'].items())
    unchanged &= all(sha(pdk/name)==value for name,value in prior['card_hashes'].items())
    result.update(all_inputs_tools_cards_unchanged=unchanged,
                  output_bytes=sum(p.stat().st_size for p in args.output.rglob('*')if p.is_file()))
    if not unchanged:result['status']='failed changed inputs'
    save();print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('passed')else 1)


if __name__=='__main__':main()
