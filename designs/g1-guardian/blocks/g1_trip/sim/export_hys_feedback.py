#!/usr/bin/env python3
"""Export compact HYS evidence without host-resource or machine-path metadata."""
import hashlib
import json
from pathlib import Path

SIM=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def export():
    target=SIM.parent/'reports/hys-feedback-20260922'
    target.mkdir()
    manifest={}
    runs=['hys-feedback-prefix-20260922-r1','hys-feedback-direct-prefix-20260922-r2','hys-feedback-full-20260922-r3']
    for run in runs:
        source=SIM/'qualification'/run
        out=target/run;out.mkdir()
        files=['full_check.json','full_launch_prospective_addendum.json'] if run==runs[-1] else ['prefix_check.json','digital_samples.json']
        for name in files:
            p=source/name
            obj=json.loads(p.read_text())
            if isinstance(obj,dict):
                state=obj.pop('runtime_state',None)
                if state:
                    obj['simulation_execution']={k:state[k] for k in ['status','returncode','wall_s','timeout_s','started_utc','finished_utc']}
            (out/name).write_text(json.dumps(obj,indent=2)+'\n')
            manifest[run+'/'+name]=dict(source_sha256=sha(p),export_sha256=sha(out/name),transform='Only runtime_state replaced by portable execution status/timing; otherwise exact JSON content')
        if run!=runs[-1]:
            d=json.loads((source/'digital_check.json').read_text())
            portable={k:v for k,v in d.items() if k!='commands'}
            portable['execution']=[{k:r[k] for k in ['stage','returncode','wall_s']} for r in d['commands']]
            (out/'digital_check.json').write_text(json.dumps(portable,indent=2)+'\n')
            manifest[run+'/digital_check.json']=dict(source_sha256=sha(source/'digital_check.json'),export_sha256=sha(out/'digital_check.json'),transform='Exact checks and portable command status/timing; machine-path command arrays omitted')
    source=SIM/'qualification'/runs[-1]
    prep=json.loads((source/'preparation.json').read_text())
    bindings=dict(preparation=prep,launch_contract=json.loads((source/'launch_contract.json').read_text()),
        full_waveform_sha256=sha(source/'full.dat'),full_log_sha256=sha(source/'full.log'),
        public_checker_sha256=sha(SIM/'check_hys_full.py'),public_launcher_sha256=sha(SIM/'run_hys_full.py'),
        export_script_sha256=sha(Path(__file__).resolve()))
    (target/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
    (target/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(str(target))

if __name__=='__main__':export()
