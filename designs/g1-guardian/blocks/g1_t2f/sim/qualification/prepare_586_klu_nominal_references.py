#!/usr/bin/env python3
"""Three source-held nominal KLU references for original disabled-wave criterion."""
import difflib,json
from pathlib import Path
from prepare_586_klu_controls import HERE,ROOT,sha
from result_directory import allocate_run

def transform(original):
    assert original.count('\n.control\n')==1 and '.options klu' not in original
    assert original.count('tran 5n 32u\n')==1
    trial=original.replace('\n.control\n','\n.options klu\n.control\n')
    assert trial.replace('.options klu\n','')==original
    return trial

def main():
    packet=HERE/'t2f586-klu-nominal-references-20260923-b.json';assert not packet.exists()
    refs=dict(typical='t2f586-source-controls-20260922-a-new-t25',slow='t2f586-adverse-controls-20260922-a-slow-cal25',fast='t2f586-adverse-controls-20260922-a-fast-cal25')
    cases=[]
    for corner,name in refs.items():
        old=HERE/'runs'/name;row,=json.loads((old/'summary.json').read_text());prep=json.loads((old/'preparation.json').read_text())
        assert row['control_status']=='passed' and row['runtime']['status']=='completed' and row['runtime']['returncode']==0 and not row['errors']
        assert row['parameters_before']==row['parameters_after']
        assert sum(map(len,row['parameters_before'].values()))==3180
        source_names=['bgr.spice','t2f.spice','.spiceinit'];run='t2f586-klu-nominal-'+corner+'-20260923-b'
        out=allocate_run(HERE.parent,run,relative_parent='qualification/runs')
        for n in source_names:(out/n).write_bytes((old/n).read_bytes())
        original=(old/'probe.cir').read_text();trial=transform(original)
        (out/'probe.cir').write_text(trial)
        (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),trial.splitlines(True),fromfile='originalNominal'+corner,tofile='sameNominalKlu'+corner)))
        recipe=dict(status='prepared only; runner and launch not qualified',corner=corner,run_id=run,original_run=name,watchdog_s=600,
            source_hashes={n:sha(out/n) for n in source_names},groups=prep['query_groups'] if corner=='typical' else prep['groups'],expected_full3180=row['parameters_before'],
            original_deck_sha256=sha(old/'probe.cir'),deck_sha256=sha(out/'probe.cir'),
            original_preparation_sha256=sha(old/'preparation.json'),original_provenance_sha256=sha(old/'provenance.json'),
            bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in [old/'summary.json',old/'probe.cir',old/'preparation.json',old/'provenance.json',Path(__file__).resolve()]},
            scope='Only.optionsklu selector. Original nominal source/no mismatch enable/reset/options/load/temp25/rails/timing/32us/13vectors/measurements/outputbasename remain exact. Full3180 exactnominal/BFOREAFTER required. Same-KLU disablednominal exactwave criterion, not cross-SPARSE equality waiver. No population launch, source adoption or refit.')
        (out/'preparation.json').write_text(json.dumps(recipe,indent=2)+'\n')
        cases.append(dict(corner=corner,run_id=run,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir')))
    packet.write_text(json.dumps(dict(status='prepared only; three same-KLU nominal references not run',cases=cases,watchdog_s=600,expected_external_growth_GiB=.15,
        prior_preparation_failure='typical-a copiedinputs retained, no simulation: historicalnominal schema uses query_groups, corner schema groups; b explicitly selects original schemas without query omission.',
        reason='Original disabled-to-nominal exact waveform criterion needs same-solver nominal references, in addition to sixcontrol disabledchanged equality.',preparer_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(packet.relative_to(ROOT),sha(packet))

if __name__=='__main__':main()
