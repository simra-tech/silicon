"""Prospective combined R100/area4 own calibration; no R62 code inheritance."""
import json
import hashlib
import re
import sys
from pathlib import Path
import run_regenpair4_roomcal as base

NAME='joint586-regenpair4-r100-roomcal-s78101-20260923-a'
CANONICAL_SHA='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
OLD_CANDIDATE=base.candidate_source
OLD_REPLAY=base.replay


def sense_r100(original):
    r62=OLD_CANDIDATE(original)
    line='XRZ out1 cz vss rppd w=1u l=62u m=1 b=0 mm_ok=1\n'
    replacement=line.replace('l=62u','l=100u')
    block,=re.findall(r'(?m)^\.subckt g1_ota_main_candidate .*?^\.ends\n',r62,re.S)
    assert block.count(line)==r62.count(line)==1
    result=r62.replace(line,replacement)
    assert result.replace(replacement,line)==r62
    assert hashlib.sha256(result.encode()).hexdigest()==CANONICAL_SHA
    return result


def serialized_replay(records):
    tree=OLD_REPLAY(records)
    for field in ['brackets','current_brackets']:
        if field in tree:
            assert set(tree[field])=={'soft','hard'} and all(type(v) is tuple and len(v)==2 and all(type(i) is int for i in v) for v in tree[field].values())
            tree[field]={k:list(v) for k,v in tree[field].items()}
    return tree


def prepare():
    original=base.SIM/'qualification'/base.NAME/'contract.json'
    assert base.sha(original)=='8df5d57cc2d8a829241a2a504e62bba68ea6f5a65c1ce24dd9392a28ad90dba0'
    packet=json.loads(original.read_text());parent=base.SIM/'qualification'/base.PARENT
    assert all(base.sha(base.ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    out=base.allocate_run(base.SIM,NAME)
    for name in ['bgr.spice','population_inventory.json']:(out/name).write_bytes((parent/name).read_bytes())
    (out/'sense.spice').write_text(sense_r100((parent/'sense.spice').read_text()))
    (out/'trip.spice').write_text(base.trip_transform((parent/'trip.spice').read_text()))
    for path in [Path(__file__).resolve(),base.SIM/'test_regenpair4_r100_roomcal.py',original]:packet['bindings_sha256'][str(path.relative_to(base.ROOT))]=base.sha(path)
    packet.update(run_id=NAME,source_hashes={n:base.sha(out/n) for n in ['sense.spice','trip.spice','bgr.spice']},inventory_sha256=base.sha(out/'population_inventory.json'),
        scope='PREPARED combined C45/R100 SENSE plus hardXM3/4 W6/L.26; own78101 room binary endpoints/midpoints/rounding, no inherited R62 codes. OriginalSPARSE/0.2ns/1200s/full11512+27 reset/observations. Three own-new-code heldouts p57/p59/p61 only after independent calibration audit. No population/source adoption.',
        deterministic_geometry_changes=dict(sense_main_XCC_w_um=[69,45],sense_main_XRZ_l_um=[6.2,100],hard_XM3_XM4_w_um=[3,6],hard_XM3_XM4_l_um=[.13,.26]),
        parameter_scope='11503 original rows exact; same9 declared native draw changes as R62-area4. RZ deterministic length/resistance/parasitics intentionally differ although its random rsh/w/l fingerprints remain identical; query inventory is not geometry. Fullcandidate11512 own-before/after and cross-phase equality required.',
        source_dependency='Requires ROOT actual R100 partial-field/source disposition plus native f43->1c953318 hard-only proof. No electrical equivalence to R62, no inherited codes, no field completeness claim.',
        representation='Only binary replay tuple bracket pairs normalized to JSON arrays before exact receipt comparison; tested separately; no numerical value/order/status changes.')
    with (out/'contract.json').open('x') as stream:json.dump(packet,stream,indent=2)
    print(str((out/'contract.json').relative_to(base.ROOT)),base.sha(out/'contract.json'))


def main():
    if len(sys.argv)>1 and sys.argv[1]=='prepare':prepare();return
    # Process-local specialization: original frozen helper/source stays untouched.
    base.NAME=NAME;base.candidate_source=sense_r100;base.replay=serialized_replay
    base.main()


if __name__=='__main__':main()
