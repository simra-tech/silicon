#!/usr/bin/env python3
"""Audit nine literal historical load fixtures with unchanged nominal586 source."""
import argparse
import json
from pathlib import Path
import numpy as np
from run_586_pvt import sha

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    qualified = HERE/'runs/bgr_one_draw_20260922_r1'
    qm = json.loads((qualified/'manifest.json').read_text())
    historical = HERE/'runs/bgr_capload9_20260921_01'
    rows = []
    for corner in ['nominal', 'slow', 'fast']:
        for cap in ['1e-13', '1e-11', '1e-10']:
            run = HERE/'runs'/('bgr586-capload-'+corner+'-'+cap+'-20260922-a')
            record = {'run': str(run.relative_to(HERE)), 'corner': corner, 'capacitance_F': float(cap), 'status': 'not run to completion'}
            if not (run/'summary.json').exists():
                rows.append(record)
                continue
            row, = json.loads((run/'summary.json').read_text())
            prov = json.loads((run/'provenance.json').read_text())
            assert prov['source_sha256'] == qm['source_sha256'] == sha(run/'pex_nominal.spice')
            assert prov['runtime'] == qm['runtime'] and prov['ngspice'] == qm['ngspice']
            assert prov['reference_manifest_sha256'] == sha(qualified/'manifest.json')
            tag = row['case']
            assert sha(run/(tag+'.cir')) == prov['historical_deck_sha256'] == sha(historical/(tag+'.cir'))
            assert sha(run/'.spiceinit') == prov['spiceinit_sha256'] == sha(historical/'.spiceinit')
            assert prov['historical_deck_exact']
            record.update(status=row['status'], wall_s=row['wall_s'], watchdog_status=row['watchdog_status'],
                          summary_sha256=sha(run/'summary.json'), provenance_sha256=sha(run/'provenance.json'), deck_sha256=sha(run/(tag+'.cir')),
                          recovery_acceptance=row['recovery_acceptance'], warnings_retained=True)
            if row['status'] == 'passed':
                data = np.loadtxt(str(run/(tag+'.dat')), skiprows=1)
                assert data.shape == (20020, 12) and np.isfinite(data).all() and abs(data[-1, 0]-40e-6) < 1e-12
                assert sha(run/(tag+'.dat')) == row['waveform_sha256']
                assert float(data[0, 1]) == row['vref_initial_V'] and float(data[-1, 1]) == row['vref_final_V']
                assert float(data[:, 1].min()) == row['vref_min_V'] and float(data[:, 1].max()) == row['vref_max_V']
                record.update(rows=len(data), endpoint_s=float(data[-1, 0]), waveform_sha256=row['waveform_sha256'],
                              vref_initial_V=row['vref_initial_V'], vref_final_V=row['vref_final_V'], vref_min_V=row['vref_min_V'],
                              peak_vref_drop_V=float(data[0, 1]-data[:, 1].min()), final_return_delta_V=float(data[-1, 1]-data[0, 1]))
            rows.append(record)
    result = {'status': 'completed read-only audit; numerical outcomes separate from unallocated recovery criteria',
              'required_conditions': 9, 'numerically_passed': sum(r['status'] == 'passed' for r in rows),
              'numerically_failed': sum(r['status'] == 'failed' for r in rows), 'not_run_to_completion': sum(r['status'] == 'not run to completion' for r in rows),
              'records': rows, 'source_sha256': qm['source_sha256'], 'runtime': qm['runtime'],
              'scope': 'Canonical586 nominal/slow/fast ×0.1/10/100pF, literalhistorical40us100nAstepfixtures. No adopted recoveryerror/stability budget. Full2842queries not run inside these literal loadfixtures; separatePVT/model qualification does not turn this into mismatch/physicalCC/globalstability qualification.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['records', 'runtime']}, indent=2))


if __name__ == '__main__':
    main()
