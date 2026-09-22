#!/usr/bin/env python3
"""Exact-current conditional metallic comparison, not circuit qualification."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    for name in ('baseline','candidate','output'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    paths=[p/n for p in (a.baseline,a.candidate) for n in ('result/summary.json','result/solution.json','independent_audit.json')]
    inputs={str(p):sha(p) for p in paths+[Path(__file__)]}
    for base in (a.baseline,a.candidate):
        assert json.loads((base/'independent_audit.json').read_text())['status'].startswith('passed independent')
        assert json.loads((base/'result/summary.json').read_text())['status']=='passed conditional fixed-current metallic solve'
    x,y=[json.loads((p/'result/solution.json').read_text()) for p in (a.baseline,a.candidate)]
    sx,sy=[json.loads((p/'result/summary.json').read_text()) for p in (a.baseline,a.candidate)]
    assert sx['resistance_values']==sy['resistance_values'] and sx['worker_sha256']==sy['worker_sha256']
    assert sx['native_engine_sha256']==sy['native_engine_sha256']
    strip=lambda p:{k:v for k,v in p.items() if k not in ('component','extracted_node','reduced_node','delta_V')}
    assert [strip(p) for p in x['points']]==[strip(p) for p in y['points']]
    assert x['references']==y['references'] and len(x['points'])==3355 and x['components']==y['components']==55
    rows=[]
    for ref in x['references']:
        before=[p for p in x['points'] if p['source_net']==ref['source_net']]
        after=[p for p in y['points'] if p['source_net']==ref['source_net']]
        stats=lambda p:dict(minimum_V=min(v['delta_V'] for v in p),maximum_V=max(v['delta_V'] for v in p),
            span_V=max(v['delta_V'] for v in p)-min(v['delta_V'] for v in p),maximum_absolute_V=max(abs(v['delta_V']) for v in p))
        rows.append(dict(source_net=ref['source_net'],reference_kind=ref['reference_kind'],baseline=stats(before),candidate=stats(after),
            maximum_terminal_voltage_change_V=max(abs(u['delta_V']-v['delta_V']) for u,v in zip(before,after))))
    report=dict(status='passed exact-input conditional metallic comparison',scenario=sx['scenario'],inputs=inputs,
        exact_3355_point_current_source_mapping=True,exact_55_reference_contract=True,engine_solver_tables_unchanged=True,
        baseline_power_W=x['power_W'],candidate_power_W=y['power_W'],nets=rows,
        physical_contact_model_boundaries='not qualified',nonlinear_circuit='not run',adoption='not run')
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('inputs','nets')},indent=2))


if __name__=='__main__':main()
