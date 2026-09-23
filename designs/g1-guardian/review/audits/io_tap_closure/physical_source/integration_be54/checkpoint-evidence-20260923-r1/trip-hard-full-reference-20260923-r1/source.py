#!/usr/bin/env python3
"""Source-faithful R100 full-reference successor with the isolated hard clone."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/explicit_vss_interface'))
from prepare_r5 import parse,flattened,TOP


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT']);folder=bulk/'trip-regenpair4-native-20260923-r1'
    candidate=folder/'candidate.gds';analysis=folder/'analysis.json';trip=folder/'g1_trip_regenpair4_lvs.cdl'
    proof=folder/'trip_reference_proof.json';original=ROOT/'designs/g1-guardian/blocks/g1_trip/layout/g1_trip_lvs.cdl'
    expected={candidate:'1c9533180ec3d45265f3617298310a31aa01bb515fee6178a939ee6364502f22',
        analysis:'3321c5e3fbb194af4262b0648f2a282781623db045ebd32bc3c5451fa8cf963f',
        trip:'dcc3880685da6f62003f105f7f1d108cf31814659d9cbc7b3f7b780296211d9a',
        proof:'43676683e4e7015374a9ffd824a353a1f86e68ec87d433390f113e307c382488',
        original:'60a9ad6e3744ff0b3dcd407a78febcb49315840a65fdf8ef851032d6e88bfd76'}
    assert all(sha(p)==h for p,h in expected.items())
    assert json.loads(proof.read_text())['status']=='passed exact candidate wholeTRIP reference conversion and inverse'
    base=bulk/'sense-r100-full-reference-20260923-r1'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes());arms=[]
    for filename,beforehash in [('physical_taps.cdl','5b0b4a2b284c7ee2578d0ae55cf8f9fe0646b2a4739f24d1f1edd9e7ab4320c4'),
            ('physical_taps_reader.cdl','6dceb11fbea85e5020b434fd027a306e506a4130daa44613b483b63b70d2830f')]:
        source=base/filename;assert sha(source)==beforehash;expected[source]=beforehash
        raw=source.read_text();begin='* BEGIN_SOURCE g1_trip\n';end='* END_SOURCE g1_trip'
        assert raw.count(begin)==raw.count(end)==1
        start=raw.index(begin)+len(begin);stop=raw.index(end,start);old=raw[start:stop]
        assert old.rstrip('\n')==original.read_text().rstrip('\n')
        new=trip.read_text().rstrip('\n')+'\n\n';changed=raw[:start]+new+raw[stop:]
        assert changed[:start]+old+changed[start+len(new):]==raw
        _,oldcells=parse(raw.encode());_,newcells=parse(changed.encode())
        assert set(newcells)-set(oldcells)=={'G1_CMP_REGENPAIR4'} and not set(oldcells)-set(newcells)
        before,_=flattened(oldcells);after,_=flattened(newcells)
        assert set(before)==set(after) and oldcells[TOP]['pins']==newcells[TOP]['pins']
        differences=[]
        for path,oldrecord in before.items():
            record=after[path]
            if record==oldrecord:continue
            assert path.endswith(('/XCH/MM3','/XCH/MM4')),path
            assert oldrecord['nodes']==record['nodes'] and oldrecord['model']==record['model']=='SG13_LV_NMOS'
            op=dict(p.split('=',1) for p in oldrecord['params']);np=dict(p.split('=',1) for p in record['params'])
            assert set(op)==set(np)
            delta={k:(op[k],np[k]) for k in op if op[k]!=np[k]}
            assert delta=={'w':('3u','6u'),'l':('0.13u','0.26u')},(path,delta)
            differences.append(dict(path=path,nodes=record['nodes'],model=record['model'],delta=delta))
        assert len(differences)==2
        taps={p:r for p,r in before.items() if r['model'] in ('PTAP1','NTAP1')}
        assert len(taps)==386 and all(after[p]==r for p,r in taps.items())
        # Intent is the isolated XCH clone, not a shared soft/hard mutation.
        assert changed.count('XCS icmp vth_soft clk cmp_soft cmp_soft_n VDD VSS g1_cmp\n')==1
        assert changed.count('XCH icmp vth_hard cmp_clk_n cmp_hard cmp_hard_n VDD VSS g1_cmp_regenpair4\n')==1
        wrong=changed.replace('MM3 xn yn xp vss sg13_lv_nmos w=6u l=0.26u','MM3 xn yn xp vss sg13_lv_nmos w=5u l=0.26u')
        assert wrong!=changed and trip.read_text().strip() not in wrong
        destination=a.output/filename;destination.write_text(changed)
        arms.append(dict(file=filename,input_sha256=beforehash,output_sha256=sha(destination),
            reverse_bytes_exact=True,standalone_wholeTRIP_body_exact=True,flattened_differences=differences,
            all386taps_other_source_blocks_and_pins_exact=True,shared_soft_source_held=True,wrong_clone_negative_rejected=True))
    assert all(sha(p)==h for p,h in expected.items())
    (a.output/'summary.json').write_text(json.dumps(dict(status='passed exact hard-only current fullchip reference splice',
        inputs={str(p):h for p,h in expected.items()},arms=arms,GDS_sha256=sha(candidate),
        native_LVS='not run',adoption='not run',rule_or_model_changes='not applicable'),indent=2)+'\n')


if __name__=='__main__':main()
