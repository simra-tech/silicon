#!/usr/bin/env python3
"""Exact one-record syntax adapter; every parameter/node byte held."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    original=json.loads((a.candidate/'summary.json').read_text())
    assert original['status']=='passed isolated preparation'
    old=next(c for c in original['cells'] if c['kind']=='secondary')
    gds,source=Path(old['gds']),Path(old['reference'])
    assert sha(gds)==old['GDS_sha256'] and sha(source)==old['CDL_sha256']
    raw=source.read_bytes()
    pattern=rb'(?m)^(X\S+)([ \t]+[^\r\n]*\bptap1\b[^\r\n]*)$'
    matches=list(re.finditer(pattern,raw));assert len(matches)==1
    target=matches[0];newname=b'R_G1_TAP_SYNTAX_'+target.group(1)
    assert newname not in raw
    new=raw[:target.start(1)]+newname+raw[target.end(1):]
    assert new.replace(newname,target.group(1),1)==raw
    a.output.mkdir(parents=True)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    newg=a.output/'secondary.gds';newg.write_bytes(gds.read_bytes())
    newc=a.output/'secondary.cdl';newc.write_bytes(new)
    row=copy.deepcopy(old);row.update(gds=str(newg),reference=str(newc),CDL_sha256=sha(newc))
    result=copy.deepcopy(original)
    result.update(cells=[row],source_view='one original tap X-prefix changed to pinned reader R-prefix only',
                  script_sha256=sha(Path(__file__)),original_preparation_sha256=sha(a.candidate/'summary.json'),
                  original_reference_sha256=sha(source),geometry_byte_identity=sha(newg)==sha(gds),
                  source_reverse_byte_identity=True,
                  adapter_record=dict(original_name=target.group(1).decode(),adapted_name=newname.decode(),
                                      unchanged_suffix=target.group(2).decode()))
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['adapter_record'],indent=2))


if __name__=='__main__':main()
