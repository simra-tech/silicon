#!/usr/bin/env python3
"""Prepare three completed32us corner replays and exact KLU repeats; no launch."""
import difflib,json
from pathlib import Path
from prepare_586_fast76002_solver import HERE,ROOT,sha
from result_directory import allocate_run

REFERENCES=dict(typical='t2f586-population-controls-20260922-a-enabled',slow='t2f586-slow-population-controls-20260923-a-enabled',fast='t2f586-fast-population-controls-20260923-a-enabled')


def make_full(original):
    assert original.count('\n.control\n')==1 and original.count('tran 5n 32u\n')==1
    assert original.count('method=gear')==1 and '.options klu' not in original
    trial=original.replace('\n.control\n','\n.options klu\n.control\n')
    assert trial.replace('.options klu\n','')==original
    return trial


def main():
    packet=HERE/'t2f586-klu-matched-controls-20260923-a.json';assert not packet.exists()
    cases=[]
    for corner,name in REFERENCES.items():
        old=HERE/'runs'/name;baseline,=json.loads((old/'summary.json').read_text())
        assert baseline['control_status']=='passed' and baseline['full3180_status']=='passed' and len(baseline['phases'])==1
        phase=baseline['phases'][0];assert phase['parameters_before']==phase['parameters_after']
        assert sum(map(len,phase['parameters_before'].values()))==3180
        for label in ['replay','repeat']:
            run_id='t2f586-klu-'+corner+'-'+label+'-20260923-a'
            out=allocate_run(HERE.parent,run_id,relative_parent='qualification/runs')
            prep=json.loads((old/'preparation.json').read_text())
            for n in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json']:(out/n).write_bytes((old/n).read_bytes())
            original=(old/'probe.cir').read_text();trial=make_full(original);(out/'probe.cir').write_text(trial)
            (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),trial.splitlines(True),fromfile='completedSparse'+corner,tofile='matchedKlu'+corner)))
            prep.update(run_id=run_id,status='prepared only; no launch',original_run=name,original_deck_sha256=sha(old/'probe.cir'),
                deck_sha256=sha(out/'probe.cir'),required_before3180=phase['parameters_before'],endpoint_s=32e-6,watchdog_s=600,
                scope='Matched completed32us '+corner+' SPARSE-to-KLU control and exact independent KLU repeat. Sole algorithm change .options klu. Same source/draw/model/reset/OP/options/5ns/32us/13vectors/original measurements/600s. Exact SPARSE-vs-KLU wave/grid failures separate; full3180 and KLUrepeat exactwave mandatory for prospective review. No solver adoption, source acceptance, new sample count or population release.')
            for p in [old/n for n in ['probe.cir','summary.json','run.log','provenance.json','phase0.dat.gz','preparation.json']]+[Path(__file__).resolve(),HERE/'run_586_klu_control.py',HERE/'analyze_586_klu_controls.py']:
                prep['live_bindings_sha256'][str(p.relative_to(ROOT))]=sha(p)
            (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
            case=dict(corner=corner,label=label,run_id=run_id,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir'))
            (HERE/(run_id+'.json')).write_text(json.dumps(case,indent=2)+'\n');cases.append(case)
    packet.write_text(json.dumps(dict(status='prepared only; six matched full32us controls not run',cases=cases,watchdog_s=600,
        prospective_checks=['All3180 exact original/before/after individually','Original finite13vectors32us/HBTVCE<=1.6/positive frequency','SPARSE/KLU exactwave/grid status separately retained','Same-KLU independentrepeat full decoded waveform exact, no tolerance substitution','Frequency/endpoint/allvector differences descriptive, no adoption bound'],expected_external_growth_GiB=.30),indent=2)+'\n')
    print(packet.relative_to(ROOT),sha(packet))


if __name__=='__main__':main()
