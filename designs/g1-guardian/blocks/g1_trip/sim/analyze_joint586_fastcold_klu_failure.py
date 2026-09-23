#!/usr/bin/env python3
"""Read-only failed KLU initialization evidence; never infer missing waveforms."""
import argparse,json,re
from pathlib import Path
from prepare_joint586_fastcold_klu import SIM,ROOT,ORIGINAL,sha,transform
from run_joint586_transients import phase_parameters


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    out=SIM/'qualification/joint586-fast-lowcold-klu-20260923-a';prep=json.loads((out/'preparation.json').read_text());row,=json.loads((out/'summary.json').read_text())
    assert row['status']=='failed separate KLU fixture diagnostic' and row['runtime']['status']=='completed' and row['runtime']['returncode']==0
    assert (out/'population_transient.cir').read_text()==transform((ORIGINAL/'population_transient.cir').read_text(),out.name)
    assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    log=(out/'run.log').read_text();assert 'Using KLU as Direct Linear Solver' in log
    assert not (out/'phase0.dat').exists() and not (out/'phase0.dat.gz').exists()
    result=dict(status='completed read-only failed-initialization audit; original failure retained',run=out.name,
        original_sparse_status='failed original1200s timeout; no alias',runtime=row['runtime'],errors=row['errors'],
        wave_and_decision_status='not run; initialization failed, no waveform',full_parameter_status='not run to completion',
        explicit_failure_scope='OP and transient initial-timepoint TimestepTooSmall, q.xbgr.xq55.qnpn13g2 reported trouble instance; not demonstrated root cause',
        solver_adoption_and_fast30='not run; not released',receipts_sha256={n:sha(out/n) for n in ['summary.json','run.log','run.json','preparation.json','population_transient.cir','provenance.json']},analyzer_sha256=sha(Path(__file__)))
    try:
        section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        params=phase_parameters(section,prep['groups'],prep['expected_vector'])
        result.update(full_parameter_status='passed11512beforeafter+27 exact despite failed OP; no valid operating-point inference',parameters=params)
    except (AssertionError,ValueError,KeyError) as error:result['parameter_audit_failure']=repr(error)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['parameters','receipts_sha256','errors']},indent=2))


if __name__=='__main__':main()
