"""Independent saved-source/runtime/parameter/wave reconstruction in the pinned runtime."""
import argparse
import json
from pathlib import Path
from run_joint586_c45rz62_knownfailures import ROOT,SIM,sha,bindings,inspect_case,resolve_wave


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True);p.add_argument('--execution-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    d=bindings(a.execution,a.execution_sha256);records=[]
    for case in d['controls']:
        out=SIM/'qualification'/case['run_id'];r=dict(run_id=case['run_id'],status='not run')
        if (out/'run.json').exists():
            r['status']='failed'
            try:
                assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text())
                provenance=json.loads((out/'provenance.json').read_text());assert provenance['runtime_identity']==prep['expected_runtime_identity'] and provenance['execution_sha256']==a.execution_sha256
                result=inspect_case(out,prep,json.loads((out/'run.json').read_text()),(out/'run.log').read_text())
                summary=json.loads((out/'summary.json').read_text());assert all(summary[k]==v for k,v in result.items())
                r.update(status='passed independent reconstruction',result=result,receipts_sha256={n:sha(out/n) for n in ['preparation.json','probe.cir','sense.spice','provenance.json','run.json','run.log','summary.json',resolve_wave(out/'phase0.dat').name]})
            except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:r['audit_error']=repr(error)
        records.append(r)
    result=dict(status='completed candidate diagnostics only',execution_sha256=a.execution_sha256,auditor_sha256=sha(Path(__file__)),records=records,
        numerical_passed=sum(r['status']=='passed independent reconstruction' for r in records),not_run=sum(r['status']=='not run' for r in records),
        source_adoption='not run',population_qualification='not run',new_source_calibration='not run')
    out=ROOT/a.output;assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(result['numerical_passed']);raise SystemExit(0 if result['numerical_passed']==4 else 1)


if __name__=='__main__':main()
