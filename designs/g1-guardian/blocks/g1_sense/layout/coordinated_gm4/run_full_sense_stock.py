#!/usr/bin/env python3
"""Bounded full-SENSE stock DRC and conditional strict hierarchical LVS."""
import argparse,datetime,json,os
from pathlib import Path
from run_stock_native_prototypes import sha

HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('candidate','reference','output','resource-gate'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={7}
    gate=json.loads(a.resource_gate.read_text());assert gate['status']=='passed' and gate['expected_growth_gib']>=.1 and 0<=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()<1800
    m=json.loads((a.candidate/'manifest.json').read_text());ref=json.loads((a.reference/'manifest.json').read_text());assert ref['status']=='passed saved-polygon and exact source reference gate' and sha(a.candidate/'g1_sense_physical.gds')==m['GDS_sha256']==ref['GDS_sha256']
    original=HERE/'run_stacked_stock.py';assert sha(original)=='1204ff3fc810a50e5c34418283e8934c50f15cf52017c5b11d82e3fc6b39b53e';text=original.read_text()
    patches=[("base = here / 'stacked-pair-20260922-r2'",'base = Path('+repr(str(a.candidate.resolve()))+')'),("reference = here / 'stacked-pair-reference-20260922-r1'",'reference = Path('+repr(str(a.reference.resolve()))+')'),("out = here / 'stacked-pair-stock-20260922-r1'",'out = Path('+repr(str(a.output.resolve()))+')'),
             ('8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3',m['GDS_sha256']),('STACKED_STOCK_CONTRACT_20260922.md','FULL_SENSE_CONTRACT_20260922.md'),("['--layout=' + str(gds), '--netlist=' + str(cdl)]","['--layout=' + str(gds), '--netlist=' + str(cdl), '--no_series_res']"),("full_main='not run'","fullchip_fit='not run'")]
    for old,new in patches:assert text.count(old)==1,old;text=text.replace(old,new)
    assert text.count('g1_main_pair_stacked64')==3;text=text.replace('g1_main_pair_stacked64','g1_sense_physical')
    hook="        row['output_bytes'] = output_bytes(out)"
    gate="        if kind == 'lvs':\n            tops = [c for r in xrefs for c in r['xref']['circuits'] if c['first'] == 'g1_sense_physical']\n            row['nine_source_pin_gate'] = len(tops) == 1 and tops[0]['children']['pin'] == {'Match': 9}\n            passed = passed and row['nine_source_pin_gate']\n"
    assert text.count(hook)==1;text=text.replace(hook,gate+hook)
    prep=a.output.with_name(a.output.name+'-preparation');prep.mkdir(parents=True);(prep/'derived_runner.py').write_text(text);(prep/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes());(prep/'contract.md').write_bytes((HERE/'FULL_SENSE_CONTRACT_20260922.md').read_bytes())
    ns=dict(__file__=str(original),__name__='full_sense_stock_derivative');exec(compile(text,str(original),'exec'),ns);ns['main']()
if __name__=='__main__':main()
