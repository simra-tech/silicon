#!/usr/bin/env python3
"""Separate extraction-only exclusion of exactly three proven purged dummies."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bulk',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    proof=a.bulk/'io-three-dummy-proof-20260923-r2/proof/summary.json'
    assert sha(proof)=='b74ba62651dcd1350d1457e79f297bc6f42637d42fd1499b02a6b9b344c7db7f'
    p=json.loads(proof.read_text());assert p['status']=='passed independent three-dummy source/native-terminal proof'
    assert len(p['source_occurrences'])==len(p['physical_instances'])==3
    assert len({q['cluster'] for q in p['local_terminal_probes'].values()})==1
    a.output.mkdir(parents=True);(a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    inputs=[('original',a.bulk/'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl',
             'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'),
            ('tap_prefix',a.bulk/'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl',
             '7395c32d170a787dbc81fd10c67148301d168e51f5ac38de3f0866efe5894006')]
    results=[]
    for label,source,expected in inputs:
        assert sha(source)==expected
        raw=source.read_bytes()
        match=re.search(rb'(?m)^\.SUBCKT sg13g2_LevelDown .*?^\.ENDS',raw,re.S);assert match
        record=p['source_occurrences'][0]['source_record'].encode()+b'\n'
        assert match.group(0).count(record)==1
        offset=match.start()+match.group(0).index(record)
        altered=raw[:offset]+raw[offset+len(record):]
        assert altered[:offset]+record+altered[offset:]==raw
        assert len(raw)-len(altered)==len(record)
        output=a.output/(label+'_three_dummy_extraction_only.cdl');output.write_bytes(altered)
        results.append(dict(variant=label,input_sha256=sha(source),output_sha256=sha(output),
                            output_name=output.name,removed_definition_line=record.decode().rstrip('\n'),
                            byte_offset=offset,reverse_exact=True,
                            source_occurrences=p['source_occurrences'],
                            difference='One definition record / exactly three reachable all-VDD occurrences; no other byte changed.'))
    summary=dict(status='passed separate extraction-reference preparation; comparison not run',
                 proof_sha256=sha(proof),references=results,script_sha256=sha(Path(__file__)),
                 canonical_source_and_all_device_geometry='unchanged',
                 coverage='Three source-declared dummies independently physically proved; not three extracted devices.',
                 not_run=['comparison with derived references','combined marker/fullchip integration','adoption'],
                 original_strict_LVS='failed retained')
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary['status'])


if __name__=='__main__':main()
