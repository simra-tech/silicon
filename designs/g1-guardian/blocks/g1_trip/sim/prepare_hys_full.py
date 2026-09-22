#!/usr/bin/env python3
"""Prepare only the reviewed3-us HYS full leaf from the passed direct prefix."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import difflib

SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
REFERENCE='hys-feedback-direct-prefix-20260922-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):
    with p.open('x') as f:f.write(json.dumps(d,indent=2)+'\n')

def prepare(run_id):
    ref=SIM/'qualification'/REFERENCE
    check=json.loads((ref/'prefix_check.json').read_text())
    assert check['status']=='passed' and all(check['checks'].values())
    assert len(check['parameters']['after'])==27 and check['parameters']['before']==[]
    att=json.loads((ref/'digital_attestation.json').read_text())
    assert att['status']=='passed' and all(att['checks'].values())
    original=(ref/'prefix.cir').read_text()
    assert original.count('tran .2n 0.9u 0 .2n\n')==1
    assert 'v(xt.cmp_clk_n)' not in original
    changed=original.replace('tran .2n 0.9u 0 .2n\n','tran .2n 3u 0 .2n\n')
    old_output='qualification/'+REFERENCE+'/prefix.dat'
    new_output='qualification/'+run_id+'/full.dat'
    assert changed.count(old_output)==1
    changed=changed.replace(old_output,new_output)
    lines=changed.splitlines(True)
    for i,line in enumerate(lines):
        if line.startswith('.save ') or line.startswith('wrdata '):
            lines[i]=line.rstrip('\n')+' v(xt.cmp_clk_n)\n'
    changed=''.join(lines)
    assert changed.count(' v(xt.cmp_clk_n)\n')==2
    reverse=changed.replace(' v(xt.cmp_clk_n)\n','\n').replace(new_output,old_output).replace('tran .2n 3u 0 .2n\n','tran .2n 0.9u 0 .2n\n')
    assert reverse==original
    out=SIM/'qualification'/run_id
    out.mkdir()
    (out/'full.cir').write_text(changed)
    (out/'deck.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile=REFERENCE+'/prefix.cir',tofile=run_id+'/full.cir')))
    frozen=json.loads((ref/'frozen_inputs.json').read_text())
    for n,v in frozen.items():assert sha(ref/n)==v
    bound=set(frozen)|{'prefix.dat','prefix_check.json','digital_attestation.json','digital.dat','digital_check.json','g1_hys_diagnostic.vvp'}
    expected={str((ref/n).relative_to(ROOT)):sha(ref/n) for n in sorted(bound)}
    expected[str((SIM/'.spiceinit').relative_to(ROOT))]=sha(SIM/'.spiceinit')
    assert sha(SIM/'.spiceinit')==sha(ref/'.spiceinit')
    dump(out/'preparation.json',dict(status='prepared; simulation not run',reference=REFERENCE,
        deck_sha256=sha(out/'full.cir'),reference_inputs=expected,
        contract_sha256=sha(SIM/'HYS_FULL_FEEDBACK_CONTRACT_20260922.md'),
        reference_prefix_parity_window_s=[0,.85e-6],original_vector_count=60,new_vector_count=61,
        endpoint_us=3,watchdog_s=900,expected_growth_gib=.15,
        actual_full_run='not run',parameter_contract='27 exact post; same-instance pre-query not run',
        deck_changes=['endpoint .9 to3us','output filename','save/export actual hard clock xt.cmp_clk_n'],
        reverse_diff_exact=True))
    print(json.dumps(dict(output=str(out.relative_to(ROOT)),deck_sha256=sha(out/'full.cir'),status='prepared only'),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args()
    assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    prepare(a.run_id)
