#!/usr/bin/env python3
"""Frozen strict stock runner reuse with explicit fresh fullmain input bindings."""
import argparse,datetime,hashlib,json,os
from pathlib import Path
from run_stock_native_prototypes import sha

HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--resource-gate',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and os.sched_getaffinity(0)=={7}
    gate=json.loads(a.resource_gate.read_text());assert gate['status']=='passed' and gate['expected_growth_gib']>=.1
    assert 0<=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()<1800
    candidate=a.candidate.resolve();reference=a.reference.resolve();output=a.output.resolve()
    m=json.loads((candidate/'manifest.json').read_text());ref=json.loads((reference/'manifest.json').read_text())
    assert m['status']=='passed fullmain scoped geometry/terminal preparation' and ref['status']=='passed complete saved-polygon and exact source reference gate'
    assert sha(candidate/'g1_ota_main_physical.gds')==m['GDS_sha256']==ref['GDS_sha256']
    original=HERE/'run_stacked_stock.py';assert sha(original)=='1204ff3fc810a50e5c34418283e8934c50f15cf52017c5b11d82e3fc6b39b53e'
    text=original.read_text();patches=[
        ("base = here / 'stacked-pair-20260922-r2'",'base = Path('+repr(str(candidate))+')'),
        ("reference = here / 'stacked-pair-reference-20260922-r1'",'reference = Path('+repr(str(reference))+')'),
        ("out = here / 'stacked-pair-stock-20260922-r1'",'out = Path('+repr(str(output))+')'),
        ('passed saved-polygon and exact source reference gate','passed complete saved-polygon and exact source reference gate'),
        ('8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3',m['GDS_sha256']),
        ('STACKED_STOCK_CONTRACT_20260922.md','FULLMAIN_CONTRACT_20260922.md')]
    for old,new in patches:assert text.count(old)==1,old;text=text.replace(old,new)
    assert text.count('g1_main_pair_stacked64')==3;text=text.replace('g1_main_pair_stacked64','g1_ota_main_physical')
    prep=output.with_name(output.name+'-preparation');prep.mkdir(parents=True,exist_ok=False)
    (prep/'derived_stock_runner.py').write_text(text);(prep/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes());(prep/'contract.md').write_bytes((HERE/'FULLMAIN_CONTRACT_20260922.md').read_bytes())
    record=dict(status='running',resource_gate_sha256=sha(a.resource_gate),derived_sha256=hashlib.sha256(text.encode()).hexdigest(),candidate_manifest_sha256=sha(candidate/'manifest.json'),reference_manifest_sha256=sha(reference/'manifest.json'))
    (prep/'run.json').write_text(json.dumps(record,indent=2)+'\n');ns=dict(__file__=str(original),__name__='fullmain_stock_derivative');exec(compile(text,str(original),'exec'),ns)
    try:ns['main']()
    except SystemExit as exc:code=exc.code
    else:code=0
    record.update(status='passed' if code==0 else 'failed',returncode=code);(prep/'run.json').write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(code)
if __name__=='__main__':main()
