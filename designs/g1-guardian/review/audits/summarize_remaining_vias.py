#!/usr/bin/env python3
"""One compact receipt for newly completed cohorts; bulk artifacts stay in place."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    cohorts=[];stages=[]
    for n in (2,3,4):
        source=a.results_root/('priority-via-local-cohort%d-20260922-r1'%n)
        summary=json.loads((source/'summary.json').read_text());contract=json.loads((source/'contract.json').read_text());checks=json.loads((source/'AC_checks.json').read_text());phases=json.loads((source/'phases.json').read_text())
        assert summary['status']=='passed cohort%d four pairedsites and32ACcomparisons plus2syntheticcontrols'%n
        assert sha(source/'contract.json')==summary['contract_sha256']
        assert len(checks)==34 and all(r['status']=='passed' and r['abs_error_F']<=1e-25 for r in checks)
        assert all(r['status']=='completed' and r['returncode']==0 for r in phases)
        assert contract['parent_sha256']=='af9ac30034c8c11e09d1f24f732f3476c5653fb95eaa0b67f214c2e14c56f76d'
        assert contract['candidate_sha256']=='04fb6443010bed31595974cca636a9dbd292fda47f0cd45507688f05b1c9a7d8'
        target=a.output/('cohort%d'%n);target.mkdir()
        compact=[]
        for name in ('summary.json','contract.json','AC_checks.json','phases.json','derived_runner.py','runner.py'):
            data=(source/name).read_bytes()
            assert all(v not in data for v in (b'/home/',b'/opt/sim/',b'.private/'))
            shutil.copyfile(source/name,target/name)
            assert sha(source/name)==sha(target/name)
            compact.append(dict(path='cohort%d/'%n+name,sha256=sha(target/name),bytes=len(data)))
        inventory=[dict(path=str(f.relative_to(source)),sha256=sha(f),bytes=f.stat().st_size) for f in sorted(source.rglob('*')) if f.is_file()]
        assert sum(r['bytes'] for r in inventory)<contract['max_output_bytes']
        cohorts.append(dict(cohort=n,stages=contract['stage_ids'],actual_AC=32,synthetic_AC=2,
                            compact_artifacts=compact,bulk_artifacts=inventory,deltas_fF=summary['deltas_fF']))
        stages.extend(contract['stage_ids'])
    assert sorted(stages)==[7,8,9,11,12,13,14,15,16,17,18,20] and len(stages)==len(set(stages))
    result=dict(status='passed remaining12 local stages',cohorts=cohorts,
                previously_covered_stages=[0,1,2,3,4,5,6,10,19],covered_stages=list(range(21)),
                actual_AC=96,synthetic_AC=6,script_sha256=sha(Path(__file__)),
                full_route_RC='not run',operating_source_transients='not run',current_IR='not run',
                geometry_adoption='not run',physical_measurement='not applicable',seed='not applicable')
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],actual_AC=96,synthetic_AC=6,local_stages_covered=21,manifest_sha256=sha(a.output/'manifest.json')),indent=2))

if __name__=='__main__':main()
