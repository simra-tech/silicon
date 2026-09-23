#!/usr/bin/env python3
"""Prepare once-only exact-input900s attempts; original600s population failures stay."""
import gzip
import json
from pathlib import Path
import re
from run_586_calibration_sample import HERE,ROOT,REFERENCE,sample_deck,sha
from run_bgr_substitution_draw_audit import read_group
from result_directory import allocate_run

CASES=[(74140,0),(74144,3),(74145,3),(74149,3),(74150,1)]

def main():
    output=HERE/'t2f586-nearendpoint-recovery-contract-20260923-b.json';assert not output.exists()
    refprep=json.loads((REFERENCE/'preparation.json').read_text());records=[]
    for seed,index in CASES:
        parent=HERE/'runs'/('t2f586-calibration-s%d-20260922-a'%seed);old=parent/('p%02d'%index)
        row,=json.loads((old/'summary.json').read_text());prov=json.loads((parent/'provenance.json').read_text())
        assert row['status']=='failed' and row['runtime']['status']=='timeout' and row['runtime']['timeout_s']==600 and not row['errors']
        assert prov['runtime_identity']==refprep['runtime']
        assert (old/'probe.cir').read_text()==sample_deck((REFERENCE/'probe.cir').read_text(),seed,row['temperature_C'])
        assert sha(old/'probe.cir')==row['deck_sha256']
        assert all(sha(old/n)==sha(parent/n)==v for n,v in refprep['source_hashes'].items())
        log=(old/'run.log').read_text();assert 'Initial Transient Solution' in log
        assert not re.search('warning',log.split('Initial Transient Solution',1)[1],re.I)
        assert 'Using SPARSE 1.3 as Direct Linear Solver' in log
        expected={tag:read_group(log,'P0_'+tag+'_BEFORE',keys) for tag,keys in refprep['groups'].items()}
        assert sum(map(len,expected.values()))==3180
        siblings=[];header=None
        for sibling in sorted(parent.glob('p??')):
            siblingrow,=json.loads((sibling/'summary.json').read_text())
            if sibling==old:continue
            assert siblingrow['status']=='passed' and siblingrow['full3180_status']=='passed'
            assert siblingrow['parameters_before']==siblingrow['parameters_after']==expected
            files=['summary.json','run.json','run.log','probe.cir','phase0.dat.gz','phase0.dat.archive.json']
            siblings.append(dict(leaf=sibling.name,receipts_sha256={n:sha(sibling/n) for n in files}))
            with gzip.open(str(sibling/'phase0.dat.gz'),'rb') as stream:local=stream.readline().decode().split()
            assert len(local)==13
            if header is None:header=local
            assert header==local
        assert len(siblings)==3
        progress=HERE/('t2f586-s%d-p%02d-timeout-progress-20260923.json'%(seed,index))
        evidence=json.loads(progress.read_text());slope=evidence['last60s']
        assert evidence['receipts_sha256']['run.json']==sha(old/'run.json')
        assert slope['classification']=='advancing in final telemetry window' and slope['process_cpu_to_wall_ratio']>.9
        assert 0<slope['linear_remaining_wall_s_at_observed_slope']<=120
        run='t2f586-s%d-p%02d-recovery900-20260923-b'%(seed,index)
        out=allocate_run(HERE.parent,run,relative_parent='qualification/runs')
        files=['bgr.spice','t2f.spice','.spiceinit','probe.cir','population_inventory.json']
        for n in files:
            original=parent/n if n=='population_inventory.json' else old/n
            (out/n).write_bytes(original.read_bytes());assert sha(out/n)==sha(original)
        recipe=dict(status='prepared only; no launch lease or runner implementation qualified',run_id=run,
            original_parent=parent.name,original_leaf=old.name,seed=seed,temperature_C=row['temperature_C'],watchdog_s=900,
            expected_runtime_identity=prov['runtime_identity'],groups=refprep['groups'],expected_full3180=expected,
            expected_header_tokens=header,source_hashes={n:sha(out/n) for n in files},
            exact_deck_inverse='Byte identity; only host watchdog600→900 and fresh working directory. Relative output basename unchanged.',
            original_failure=dict(summary_sha256=sha(old/'summary.json'),run_sha256=sha(old/'run.json'),log_sha256=sha(old/'run.log'),watchdog_s=600),
            progress_hypothesis=dict(report_sha256=sha(progress),last60s=slope),successful_original_leaf_reuse=siblings,
            bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in [old/'summary.json',old/'run.json',old/'run.log',old/'run.progress.jsonl',old/'probe.cir',parent/'summary.json',parent/'provenance.json',progress,REFERENCE/'preparation.json',REFERENCE/'probe.cir',Path(__file__).resolve()]},
            mandatory_checks=['Exactruntime/cards/source/SPARSEseed/timing/options; all3180beforeafter==originalsame-seed fullvector and1129primitive inventory',
                'Exact13header names/order,finite32usendpoint,positiveoriginalfrequency/scalars,HBTexternalVCE<=1.6',
                'No originalwaveprefix comparison: original failedleaf has no exportedwaveform',
                'Separate recoveryreceipt; original600failure and originalfixed300 denominator never rewritten/aliased',
                'Any recovered calibration/heldout result is separate derivation from exacthashbound3originalpassedleaves+1recovery; original25/100linear±2C unchanged',
                'No automaticretry, seedreplacement,KLU,watchdogextensionbeyond900, source/tolerance/refit change'])
        (out/'preparation.json').write_text(json.dumps(recipe,indent=2)+'\n')
        records.append(dict(seed=seed,index=index,run_id=run,preparation_sha256=sha(out/'preparation.json'),exact_deck_sha256=sha(out/'probe.cir'),original_failure_retained=True))
    payload=dict(status='prepared five once-only900s exact-input recoveries; not run and no lease',cases=records,
        expected_external_growth_GiB=.20,max_total_CPU_s=4500,
        prior_preparation_failure='a stopped before simulator/packet: population_inventory lives at originalparent, not leaf. Partial74140-a copiedinputs retained, no run.log or simulation.',
        explicit_exclusions='74128/74143 far-from-endpoint failures not authorized; no other seeds included',
        preparer_sha256=sha(Path(__file__)))
    output.write_text(json.dumps(payload,indent=2)+'\n');print(output.relative_to(ROOT),sha(output))

if __name__=='__main__':main()
