#!/usr/bin/env python3
"""Report every unchanged relative-context gate, including undefined zero cases."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def entries(narrow, wide):
    for matrix in (narrow, wide):
        assert len(matrix) == 2 and all(len(row) == 2 for row in matrix)
        assert all(math.isfinite(v) for row in matrix for v in row)
    result = []
    for i in range(2):
        for j in range(2):
            a, b = narrow[i][j], wide[i][j]
            delta = abs(a-b)
            relative = delta/abs(b) if b != 0 else None
            result.append(dict(row=i, column=j, narrow_fF=a, wide_fF=b,
                absolute_difference_fF=delta, relative_difference=relative,
                status=('failed undefined relative denominator' if relative is None else
                        'passed' if relative <= .01 else 'failed greater than original 1%'),
                exact_equal=a == b))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    values, identities, hashes = {}, [], {}
    expected = {f'{v}_{m}_{d}.cir' for v in ('no_fill','actual_fill')
                for m in ('grounded','floating') for d in ('P','N')}
    for width in (12,24,48):
        base = args.pair/('width%d'%width)
        data = {}
        for name in ('manifest.json','clip/provenance.json','analysis/summary.json','analysis/ac_checks.json'):
            raw = (base/name).read_bytes(); data[name] = json.loads(raw)
            hashes[str(width)+'/'+name] = hashlib.sha256(raw).hexdigest()
        run, clip, analysis, ac = [data[n] for n in data]
        assert run['status'].startswith('passed') and len(run['steps']) == 4
        assert all(r['returncode']==0 for r in run['steps'])
        assert clip['status'].startswith('passed') and clip['context_um']==width
        assert len(ac)==8 and {r['deck'] for r in ac}==expected
        assert all(r['status']=='passed' and r['returncode']==0 and
                   r['tolerance_F']==1e-25 and r['max_abs_error_F']<1e-25 for r in ac)
        identities.append({k:clip[k]for k in ('source_gds_sha256','inventory_sha256',
                           'geometry_audit_sha256','script_sha256','pair','length_um')})
        values[width] = {v+'_'+m:r['modes'][m]['matrix_fF']
                         for v,r in analysis['results'].items() for m in ('grounded','floating')}
        assert set(values[width])=={v+'_'+m for v in ('no_fill','actual_fill') for m in ('grounded','floating')}
    assert identities[0]==identities[1]==identities[2]
    checks = {key:entries(values[24][key],values[48][key])for key in values[48]}
    rows = [r for group in checks.values()for r in group]
    output = dict(status='passed' if all(r['status']=='passed'for r in rows) else 'failed',
        criterion='Unchanged every-entry abs(C24-C48)/abs(C48)<=0.01; zero denominator remains failed/undefined, no absolute tolerance substituted',
        checks=checks, identity=identities[0], input_sha256=hashes,
        observed_matrices_fF=values, original_relative_gate_unchanged=True,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        numerical_graph_AC='passed all24',
        not_run=['Whole route and longitudinal convergence','Actual-source electrical acceptance'],
        not_applicable=['Stochastic seed for deterministic capacitor-network checks'])
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items()if k not in ('observed_matrices_fF','input_sha256')},indent=2))
    raise SystemExit(0 if output['status']=='passed' else 1)


if __name__=='__main__': main()
