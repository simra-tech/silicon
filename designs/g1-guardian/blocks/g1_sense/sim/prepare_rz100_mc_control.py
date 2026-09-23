#!/usr/bin/env python3
"""Prepare one original-seed MC source/observation control; no population credit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_rz100_dc_grid import queries, source_inventory, SOURCE

SIM=Path(__file__).resolve().parent
OLD='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def instrument(original, include, q):
    old,=re.findall(r'^\.include (.+)$',original,re.M)
    updated=original.replace('.include '+old,'.include '+str(include))
    blocks=[]
    for index in range(4):
        marker='echo FINGERPRINT %d\n'%index
        assert updated.count(marker)==1
        block='echo SENSE_FULL_%d_BEGIN\n'%index+''.join('print '+x+'\n' for x in q)+'echo SENSE_FULL_%d_END\n'%index
        updated=updated.replace(marker,block+marker)
        blocks.append(block)
    restored=updated
    for block in blocks:
        assert restored.count(block)==1
        restored=restored.replace(block,'')
    assert restored.replace('.include '+str(include),'.include '+old)==original
    return updated

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    assert not args.output.exists() and sha(args.candidate)==SOURCE
    folder=SIM/'qualification/mc-gm4-comp3-screen80-b1-20260922-a'
    old_source=folder/'sense_substrate_tied.spice'
    assert sha(old_source)==OLD
    original=(folder/'seed41039.cir').read_text()
    old_run=json.loads((folder/'seed41039.json').read_text())
    assert old_run['status']=='completed' and old_run['returncode']==0
    assert sha(folder/'seed41039.cir')==old_run['deck_sha256']
    before='XRZ out1 cz vss rppd w=1u l=6.2u m=1 b=0 mm_ok=1\nXCC cz out cap_cmim w=69u l=23u m=1 mm_ok=1'
    after='XRZ out1 cz vss rppd w=1u l=100u m=1 b=0 mm_ok=1\nXCC cz out cap_cmim w=45u l=23u m=1 mm_ok=1'
    assert old_source.read_text().count(before)==1
    assert old_source.read_text().replace(before,after)==args.candidate.read_text()
    inventory=source_inventory(args.candidate.read_text())
    q=queries()
    args.output.mkdir(parents=True)
    artifacts={}
    for kind,source in [('historical',old_source),('candidate',args.candidate)]:
        target=args.output/(kind+'.spice')
        target.write_bytes(source.read_bytes())
        deck=args.output/(kind+'.cir')
        deck.write_text(instrument(original,target,q))
        artifacts[kind]=dict(source_sha256=sha(target),deck_sha256=sha(deck))
    result=dict(status='prepared only; runtime controls not run',seed=41039,
        rationale='Worst original 100-seed residual; paired method control, not yield estimate.',
        original_deck_sha256=sha(folder/'seed41039.cir'), historical_source_sha256=OLD,
        candidate_source_sha256=SOURCE, artifacts=artifacts,queries=q,
        primitive_count=len(inventory), source_inverse_exact=True, observation_inverse_exact=True,
        original_run_relative=str(folder.relative_to(SIM)),
        criteria=dict(gain_min=19.9,gain_max=20.1,residual_abs_strictly_below_V=.0005),
        scope='Original SENSE-only idealVREF/PTAT/passive load; MOS/resistor mismatch protocol. cap_typ unchanged. 36 OPs25/-40/125/return25; historical SENSE_N CM grid retained with outside-range points separate. No BGR/DAC/comparator mismatch or full PEX.',
        not_run=['historical print-only parity','new-source 529-query freeze and 51 legacy controls','current-source MC population','three intrinsic OTA offset decomposition','full PEX'])
    (args.output/'contract.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],queries=len(q),primitives=len(inventory),contract_sha256=sha(args.output/'contract.json'))))

if __name__=='__main__':main()
