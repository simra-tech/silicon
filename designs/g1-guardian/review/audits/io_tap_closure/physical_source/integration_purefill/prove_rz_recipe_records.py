#!/usr/bin/env python3
"""Verify repeated GDS serialization differs only in BGNLIB/BGNSTR dates."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def nextrec(stream):
    head=stream.read(4)
    if not head:return None
    assert len(head)==4
    length,kind,dtype=struct.unpack('>HBB',head)
    assert length>=4 and length%2==0
    body=stream.read(length-4);assert len(body)==length-4
    return kind,dtype,body
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--expected-sha',required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    reference=a.reference
    assert sha(reference)==a.expected_sha and len(a.expected_sha)==64
    counts={};timestamps=0;records=0
    with reference.open('rb') as src,a.candidate.open('rb') as dst:
        while True:
            x=nextrec(src);y=nextrec(dst)
            assert (x is None)==(y is None),('record count',records)
            if x is None:break
            assert x[:2]==y[:2],('record type',records,x[:2],y[:2])
            kind,dtype,body=x;assert len(body)==len(y[2]),('record length',records)
            if kind in (1,5):
                assert dtype==2 and len(body)==24,('date record',records)
                timestamps+=body!=y[2]
            else:assert body==y[2],('nondate record byte mismatch',records,kind)
            counts[kind]=counts.get(kind,0)+1;records+=1
    result=dict(status='passed exact GDS record identity except timestamp payloads',
                reference_gds_sha256=a.expected_sha,reproduced_gds_sha256=sha(a.candidate),
                total_records=records,date_records=counts.get(1,0)+counts.get(5,0),
                date_payloads_different=timestamps,all_nondate_records_byte_exact=True,
                other_record_differences=0)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
