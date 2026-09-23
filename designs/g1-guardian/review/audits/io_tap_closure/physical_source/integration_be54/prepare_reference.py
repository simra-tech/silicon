#!/usr/bin/env python3
"""Only the two source-authorized SENSE passive edits in the current AP view."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/explicit_vss_interface'))
from prepare_r5 import parse,flattened,TOP


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    candidate=bulk/'analog-pair-integration-20260923-r1/analog_pair_native.gds'
    analysis=candidate.parent/'analysis.json'
    sense=bulk/'sense-comp45-native-reference-20260923-r3/g1_sense_physical.cdl'
    senseproof=sense.parent/'manifest.json'
    assert sha(candidate)=='be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'
    assert sha(analysis)=='80575bbd6a51044a287bb091c6888a02acdb4fb096d95dc201278dcc7e74fab3'
    assert json.loads(analysis.read_text())['status']=='passed isolated analog-pair hierarchy replacement'
    assert sha(sense)=='8a9c92bd68f75d94fb3a08b95d7082d2a24e2dfd0827e9ba06e1ee84637cef5c'
    sj=json.loads(senseproof.read_text());assert sj['status'].startswith('passed') and sj['CDL_sha256']==sha(sense)
    normalized=sense.read_text().replace('.subckt g1_sense_physical ','.subckt g1_sense ')
    assert normalized!=sense.read_text()
    expected=[('RRZ out1 cz vss rppd w=1u l=6.2u m=1 b=0\n','RRZ out1 cz vss rppd w=1u l=62u m=1 b=0\n'),
        ('CCC cz out cap_cmim w=69u l=23u m=1\n','CCC cz out cap_cmim w=45u l=23u m=1\n')]
    sourcefolder=bulk/'io-physical-ap-source-20260923-r2'
    inputs={str(p):sha(p) for p in (candidate,analysis,sense,senseproof,Path(__file__))}
    a.output.mkdir(parents=True);arms=[]
    for filename,originalsha in [('physical_taps.cdl','796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf'),
            ('physical_taps_reader.cdl','d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4')]:
        source=sourcefolder/filename;assert sha(source)==originalsha;inputs[str(source)]=sha(source)
        raw=source.read_text();begin='* BEGIN_SOURCE g1_sense\n';end='* END_SOURCE g1_sense'
        assert raw.count(begin)==raw.count(end)==1
        start=raw.index(begin)+len(begin);stop=raw.index(end,start);old=raw[start:stop]
        new=old
        # RZ also occurs in the unchanged reference/buffer OTA. Restrict to
        # the independently named main OTA, not an indiscriminate text replace.
        pivot=new.index('.subckt g1_ota_main_candidate ')
        prefix,mainpart=new[:pivot],new[pivot:]
        for before,after in expected:
            assert mainpart.count(before)==1;mainpart=mainpart.replace(before,after)
        new=prefix+mainpart
        assert new.rstrip('\n')==normalized.rstrip('\n')
        changed=raw[:start]+new+raw[stop:]
        assert changed[:start]+old+changed[start+len(new):]==raw
        _,beforecells=parse(raw.encode());_,aftercells=parse(changed.encode())
        before,_=flattened(beforecells);after,_=flattened(aftercells)
        assert set(before)==set(after) and beforecells[TOP]['pins']==aftercells[TOP]['pins']
        differences=[]
        for path,record in before.items():
            current=after[path]
            if record==current:continue
            assert record['nodes']==current['nodes'] and record['model']==current['model']
            oldparams=dict(p.split('=',1) for p in record['params']);newparams=dict(p.split('=',1) for p in current['params'])
            delta={k:(oldparams[k],newparams[k]) for k in oldparams if oldparams[k]!=newparams[k]}
            assert set(oldparams)==set(newparams)
            assert (path.endswith('/XOTA/RRZ') and delta=={'l':('6.2u','62u')}) or (path.endswith('/XOTA/CCC') and delta=={'w':('69u','45u')}),(path,delta)
            differences.append(dict(path=path,model=record['model'],parameter_delta=delta))
        assert len(differences)==2
        taps_before={p:r for p,r in before.items() if r['model'] in ('PTAP1','NTAP1')}
        assert len(taps_before)==386 and all(after[p]==r for p,r in taps_before.items())
        dest=a.output/filename;dest.write_text(changed)
        # Wrong edited value, extra source deletion, and altered terminal all
        # differ from the literal independently qualified SENSE reference.
        negative=dict(wrong_R_rejected=new.replace('l=62u','l=61u')!=normalized+'\n',
            wrong_C_rejected=new.replace('w=45u','w=44u')!=normalized+'\n',
            omitted_device_rejected=new.replace(expected[1][1],'')!=normalized+'\n')
        assert all(negative.values())
        arms.append(dict(file=filename,input_sha256=originalsha,output_sha256=sha(dest),
            byte_edit_region=[start,stop],old_region=old,new_region=new,reverse_bytes_exact=True,
            exact_standalone_SENSE_body_after_top_name_projection=True,flattened_differences=differences,
            all386tap_records_and_nodes_exact=True,all_other_blocks_and_source_bytes_exact=True,negative_controls=negative))
    assert all(sha(Path(p))==h for p,h in inputs.items())
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(dict(status='passed exact two-passive current-fullchip source update; native LVS not run',
        inputs=inputs,arms=arms,GDS_sha256=sha(candidate),SENSE_CDL_sha256=sha(sense),
        native_LVS='not run',adoption='not run',rule_model_changes='not applicable'),indent=2)+'\n')


if __name__=='__main__':main()
