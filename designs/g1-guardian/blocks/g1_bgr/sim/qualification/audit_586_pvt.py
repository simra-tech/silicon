#!/usr/bin/env python3
"""Audit all81 attempted fixedprocess/supply conditions; retain incomplete leaves."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import numpy as np
from run_586_pvt import transform

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    ref = HERE/'runs/bgr_one_draw_20260922_r1'
    qm = json.loads((ref/'manifest.json').read_text())
    template = ref/'disabled'
    original = (template/'nominal.cir').read_text()
    records = []
    for hbt, mos, res, vdd in itertools.product(['typ', 'bcs', 'wcs'], ['tt', 'ff', 'ss'], ['typ', 'bcs', 'wcs'], [3.0, 3.3, 3.6]):
        condition = {'hbt': hbt, 'mos': mos, 'res': res, 'vdd_V': vdd}
        if (hbt, mos, res, vdd) == ('typ', 'tt', 'typ', 3.3):
            run = template
            original_row, = [r for r in qm['cases'] if r['name'] == 'disabled']
            assert original_row['status'] == 'passed'
            record = {'condition': condition, 'run': str(run.relative_to(HERE)), 'status': 'passed',
                      'reuse': 'literal qualifiednominal condition, not rerun', 'manifest_sha256': sha(ref/'manifest.json'),
                      'wall_s': original_row['wall_seconds'] if 'wall_seconds' in original_row else original_row.get('wall_s')}
        else:
            name = 'bgr586-pvt-%s-%s-%s-v%d-20260922-a' % (hbt, mos, res, round(vdd*10))
            run = HERE/'runs'/name
            if not (run/'summary.json').exists():
                records.append({'condition': condition, 'run': str(run.relative_to(HERE)), 'status': 'not run to completion'})
                continue
            row, = json.loads((run/'summary.json').read_text())
            prov = json.loads((run/'provenance.json').read_text())
            assert row['condition'] == prov['declared_changes'] == condition
            assert prov['source_sha256'] == qm['source_sha256'] and prov['runtime'] == qm['runtime']
            assert prov['reference_deck_sha256'] == sha(template/'nominal.cir')
            assert prov['reference_manifest_sha256'] == sha(ref/'manifest.json')
            assert (run/'nominal.cir').read_text() == transform(original, hbt, mos, res, vdd)
            assert sha(run/'nominal.cir') == prov['deck_sha256']
            assert sha(run/'pex_nominal.spice') == qm['source_sha256']
            assert prov['parameter_order'] == qm['parameters'] and not prov['mismatch_enabled']
            record = {'condition': condition, 'run': str(run.relative_to(HERE)), 'status': row['status'],
                      'watchdog_status': row['watchdog_status'], 'wall_s': row['wall_s'], 'errors': row['errors'],
                      'summary_sha256': sha(run/'summary.json'), 'provenance_sha256': sha(run/'provenance.json')}
            if row['status'] != 'passed':
                record['tc_status'] = 'not run'
                records.append(record)
                continue
        logpath = run/'run.log'
        log = logpath.read_text()
        observed = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
        assert [key for key, value in observed] == qm['parameters']+qm['parameters']
        assert observed[:2842] == observed[2842:] and all(np.isfinite(float(v)) for k, v in observed)
        data = np.loadtxt(str(run/'nominal.dat'), skiprows=1)
        assert data.shape == (34, 12) and np.isfinite(data).all() and np.array_equal(data[:, 0], np.arange(-40, 126, 5))
        tc = float(np.ptp(data[:, 1])/data[13, 1]/165*1e6)
        if run != template:
            assert tc == row['tc_ppm_C'] and observed[:2842] == [tuple(p) for p in row['parameters_before']]
            assert row['tc_status'] == ('passed' if tc <= 50 else 'failed')
        record.update(tc_ppm_C=tc, tc_status='passed' if tc <= 50 else 'failed', vref25_V=float(data[13, 1]),
                      wave_sha256=sha(run/'nominal.dat'), deck_sha256=sha(run/'nominal.cir'), log_sha256=sha(logpath),
                      parameters_before_after_exact=True)
        records.append(record)
    result = {'attempted_grid_conditions': 81, 'completed_conditions': sum(r['status'] == 'passed' for r in records),
              'numerically_failed_conditions': sum(r['status'] == 'failed' for r in records),
              'not_run_to_completion_conditions': sum(r['status'] == 'not run to completion' for r in records),
              'tc_failed_completed_conditions': sum(r.get('tc_status') == 'failed' for r in records),
              'maximum_completed_tc_ppm_C': max((r['tc_ppm_C'] for r in records if 'tc_ppm_C' in r), default=None),
              'source_sha256': qm['source_sha256'], 'runtime_identity': qm['runtime'], 'records': records,
              'scope': 'All3HBT×3MOS×3R×3supply conditions, each34 temperatures-40..125C, unchanged586/nominalmismatchdisabled/full2842beforeafter. Nominal condition reusedliterally. Original50ppm/C criterion; incomplete failures have no invented TC and no survivor-yield claim. Standalone1pF/ideal1VIPTAT, futurephysicalCC not covered.'}
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['records', 'runtime_identity']}, indent=2))


if __name__ == '__main__':
    main()
