#!/usr/bin/env python3
"""Hash-bound reuse of strict stock runner for the eight-device core only."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource-gate',type=Path,required=True)
    args=parser.parse_args()
    gate=json.loads(args.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['expected_growth_gib']>=.1
    assert gate['ram_available_bytes']>=4*2**30 and gate['project_cpu_budget']>=1
    original=HERE/'run_stacked_stock.py'
    assert sha(original)=='1204ff3fc810a50e5c34418283e8934c50f15cf52017c5b11d82e3fc6b39b53e'
    reference=ROOT/'build/scratch/sense-core8-reference-20260922-r1'
    assert sha(reference/'manifest.json')=='3311ec4c72310a8057a0504b68c4405d52d57562f96c41780e924f61177c5149'
    assert sha(reference/'g1_main_core8.cdl')=='fb5326d73b1f05543781f4f21c818a6823e0a879a7098389d1bfc560a2b9e8b8'
    text=original.read_text()
    patches=[
        ("base = here / 'stacked-pair-20260922-r2'", "base = here.parents[5] / 'build/scratch/sense-core8-20260922-r1'"),
        ("reference = here / 'stacked-pair-reference-20260922-r1'", "reference = here.parents[5] / 'build/scratch/sense-core8-reference-20260922-r1'"),
        ("out = here / 'stacked-pair-stock-20260922-r1'", "out = here.parents[5] / 'build/scratch/sense-core8-stock-20260922-r1'"),
        ('passed saved-polygon and exact source reference gate','passed independent saved-polygon and exact source reference gate'),
        ('8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3','b7f1e3c68b18e81617c992ee3f1001c309070e5b50fb20c96cd80ce4dc0b90db'),
        ('STACKED_STOCK_CONTRACT_20260922.md','CORE8_STOCK_CONTRACT_20260922.md')]
    for old,new in patches:
        assert text.count(old)==1,old
        text=text.replace(old,new)
    assert text.count('g1_main_pair_stacked64')==3
    text=text.replace('g1_main_pair_stacked64','g1_main_core8')
    # Preserve the tested strict parser, 180s watchdog, 50MiB gate and stop-on-failure policy.
    bindings={p:sha(p) for p in (Path(__file__),HERE/'CORE8_STOCK_CONTRACT_20260922.md',original)}
    receipt=ROOT/'build/scratch/sense-core8-stock-preparation-20260922-r1'
    receipt.mkdir(exist_ok=False)
    (receipt/'derived_stock_runner.py').write_text(text)
    for p in bindings: (receipt/p.name).write_bytes(p.read_bytes())
    record=dict(resource_gate_sha256=sha(args.resource_gate),bindings={p.name:h for p,h in bindings.items()},
                derived_runner_sha256=hashlib.sha256(text.encode()).hexdigest(),status='running')
    (receipt/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    namespace=dict(__file__=str(original),__name__='core8_strict_stock_derivative')
    exec(compile(text,str(original),'exec'),namespace)
    try:
        namespace['main']()
    except SystemExit as exc:
        code=exc.code
    else:
        code=0
    record['bindings_unchanged']=all(sha(p)==h for p,h in bindings.items())
    record['status']='passed' if code==0 and record['bindings_unchanged'] else 'failed'
    record['returncode']=code
    (receipt/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(0 if record['status']=='passed' else 1)


if __name__=='__main__': main()
