#!/usr/bin/env python3
"""Audit explicit comparator campaign sample identities and completed leaf evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaigns', nargs='+', required=True)
    p.add_argument('--seed-start', type=int, required=True)
    p.add_argument('--seed-stop', type=int, required=True)
    p.add_argument('--raw-source-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    samples, leaves, identities, sizes, originals = [], {}, [], [], []
    for name in a.campaigns:
        directory = SIM/'qualification'/name
        for sample in json.loads((directory/'summary.json').read_text()):
            checks = {'numerical_completed': sample['status'] == 'passed',
                      'three_temperature_cases': [r['temp_C'] for r in sample['cases']] == [25., -40., 125.],
                      'all32_frozen': sample['frozen_fingerprints'] and len(sample['fingerprints']) == 3 and
                      all(len(fp) == 32 and fp == sample['fingerprints'][0] for fp in sample['fingerprints']),
                      'all401_decisions': all(len(case['sampled_q_V']) == 401 for case in sample['cases']),
                      'case_evidence_exact': True}
            for index, evidence in enumerate(sample['case_evidence']):
                leaf = SIM/'qualification'/evidence['run']
                prov = json.loads((leaf/'provenance.json').read_text())
                raw = next(s for s in json.loads((leaf/'summary.json').read_text()) if s['seed'] == sample['seed'])
                case_index = next(i for i,c in enumerate(raw['cases']) if c['tag'] == evidence['case_tag'])
                checks['case_evidence_exact'] &= (raw['cases'][case_index] == sample['cases'][index] and
                    raw['fingerprints'][case_index] == sample['fingerprints'][index] and
                    evidence['case_completion_and_frozen_source_sample_status'] == 'passed')
                identity = {k:prov[k] for k in ['image_id','pdk_commit','ngspice','model_hashes']}
                identity['consumed_source_sha256'] = sha(leaf/'cmp.spice')
                identity['raw_source_sha256'] = sha(leaf/'raw_cell_extraction.spice')
                identities.append(identity)
                if evidence['run'] not in leaves:
                    leaves[evidence['run']] = {'summary_sha256':sha(leaf/'summary.json'),
                        'provenance_sha256':sha(leaf/'provenance.json'),'raw_attempt_status':raw['status']}
                    receipts = list(leaf.glob('*.dat.archive.json'))
                    if len(receipts) == 1 and not list(leaf.glob('*.dat')):
                        receipt = json.loads(receipts[0].read_text())
                        assert receipt['status'] == 'passed'
                        assert sha(leaf/receipt['gzip_name']) == receipt['gzip_sha256']
                        sizes.append(sum(x.stat().st_size for x in leaf.iterdir() if x.is_file()))
                        originals.append(receipt['original_bytes'])
            samples.append({'campaign':name,'seed':sample['seed'],'checks':checks})
    seeds = [s['seed'] for s in samples]
    checks = {'declared_unique_seed_coverage': sorted(seeds) == list(range(a.seed_start,a.seed_stop)) and len(set(seeds)) == len(seeds),
              'all_sample_contracts': all(all(s['checks'].values()) for s in samples),
              'source_model_runtime_exact': bool(identities) and all(x == identities[0] for x in identities),
              'declared_raw_source_exact': all(x['raw_source_sha256'] == a.raw_source_sha256 for x in identities)}
    report = {'status':'passed' if all(checks.values()) else 'failed', 'checks':checks,
              'sample_count':len(samples),'case_count':len(identities),'seed_range_half_open':[a.seed_start,a.seed_stop],
              'frozen_identity':identities[0] if identities else None,'samples':samples,'leaf_receipts':leaves,
              'storage':{'fully_archived_individual_leaf_count':len(sizes),'mean_retained_bytes':statistics.mean(sizes) if sizes else None,
                'max_retained_bytes':max(sizes) if sizes else None,'max_original_wave_bytes':max(originals) if originals else None,
                'forecast600_leaves_max_observed_GiB':max(sizes)*600/1024**3 if sizes else None},
              'scope':'Exact sample/source/runtime evidence audit; finite staircase ambiguity is not a unique offset, acceptance limit or joint-chain yield. Archived-wave compressed hashes verified; decoded-byte parity is recorded by immutable archival receipts.'}
    with a.output.open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['samples','leaf_receipts','frozen_identity']},indent=2))
    raise SystemExit(0 if report['status']=='passed' else 1)


if __name__ == '__main__':
    main()
