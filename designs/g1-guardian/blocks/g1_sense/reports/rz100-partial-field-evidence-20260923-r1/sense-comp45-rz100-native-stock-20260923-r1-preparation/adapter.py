#!/usr/bin/env python3
"""Unchanged stock full DRC/strict LVS, source-bound isolated C45/R62 candidate."""
import argparse,json,os
from pathlib import Path
from inspect_passive_sites import sha,SOURCE

def main():
    p=argparse.ArgumentParser()
    for name in ['candidate','reference','source','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={1} and not a.output.exists() and sha(a.source)==SOURCE
    m=json.loads((a.candidate/'manifest.json').read_text());r=json.loads((a.reference/'manifest.json').read_text())
    assert m['status']=='passed isolated two-passive geometry/connectivity'
    assert r['status']=='passed saved-polygon and exact source reference gate'
    assert m['source_sha256']==r['source_sha256']==SOURCE
    here=Path(__file__).resolve().parent.parent/'coordinated_gm4';old=here/'run_stacked_stock.py'
    assert sha(old)=='1204ff3fc810a50e5c34418283e8934c50f15cf52017c5b11d82e3fc6b39b53e'
    text=old.read_text()
    replacements=[("base = here / 'stacked-pair-20260922-r2'",'base = Path('+repr(str(a.candidate))+')'),
        ("reference = here / 'stacked-pair-reference-20260922-r1'",'reference = Path('+repr(str(a.reference))+')'),
        ("out = here / 'stacked-pair-stock-20260922-r1'",'out = Path('+repr(str(a.output))+')'),
        ('os.sched_getaffinity(0) == {7}','os.sched_getaffinity(0) == {1}'),
        ("source = here.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'",'source = Path('+repr(str(a.source))+')'),
        ('baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877',SOURCE),
        ('8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3',m['GDS_sha256']),
        ('STACKED_STOCK_CONTRACT_20260922.md','FULL_SENSE_CONTRACT_20260922.md'),
        ("['--layout=' + str(gds), '--netlist=' + str(cdl)]","['--layout=' + str(gds), '--netlist=' + str(cdl), '--no_series_res']")]
    for x,y in replacements:assert text.count(x)==1,x;text=text.replace(x,y)
    assert text.count('g1_main_pair_stacked64')==3;text=text.replace('g1_main_pair_stacked64','g1_sense_physical')
    hook="        row['output_bytes'] = output_bytes(out)"
    gate="        if kind == 'lvs':\n            tops = [c for q in xrefs for c in q['xref']['circuits'] if c['first'] == 'g1_sense_physical']\n            row['nine_source_pin_gate'] = len(tops) == 1 and tops[0]['children']['pin'] == {'Match': 9}\n            passed = passed and row['nine_source_pin_gate']\n"
    assert text.count(hook)==1;text=text.replace(hook,gate+hook)
    prep=a.output.with_name(a.output.name+'-preparation');assert not prep.exists();prep.mkdir(parents=True)
    (prep/'derived_runner.py').write_text(text);(prep/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (prep/'contract.json').write_text(json.dumps(dict(source_sha256=SOURCE,candidate_manifest_sha256=sha(a.candidate/'manifest.json'),
        reference_manifest_sha256=sha(a.reference/'manifest.json'),derived_runner_sha256=sha(prep/'derived_runner.py'),
        runtime_scope='Original180s stock children and50MiB guard; full DRC excluding density, strict LVS with no_series_res and9pinmatch; no deck/card edits.',
        unchanged_failures='Prior51 stockA/P annotations, fullfield/modelplane applicability unresolved. No current/PEX/fullchip/adoption waiver.'),indent=2)+'\n')
    ns=dict(__file__=str(old),__name__='candidate_stock');exec(compile(text,str(prep/'derived_runner.py'),'exec'),ns);ns['main']()
if __name__=='__main__':main()
