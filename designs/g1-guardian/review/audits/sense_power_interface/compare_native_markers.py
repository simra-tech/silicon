#!/usr/bin/env python3
"""Compare exact unchanged-stock main markers; inherited failures remain failures."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    receipt=json.loads((path/'summary.json').read_text())
    assert receipt['inputs_rules_unchanged'] and len(receipt['decks'])==1
    deck=receipt['decks'][0]
    assert deck['name']=='main' and deck['returncode']==0 and len(deck['reports'])==1
    report=deck['reports'][0];rdb=path/report['path'];assert sha(rdb)==report['sha256']
    markers=collections.Counter()
    for item in ET.parse(rdb).findall('.//items/item'):
        key=(item.findtext('category'),item.findtext('cell'),tuple(v.text for v in item.findall('values/value')))
        markers[key]+=1
    assert sum(markers.values())==report['markers']
    return receipt,markers


def rows(counter):
    return [dict(category=key[0],cell=key[1],values=key[2],count=count)for key,count in sorted(counter.items())]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    before,old=load(a.baseline);after,new=load(a.candidate)
    assert before['GDS_sha256']=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    assert after['GDS_sha256']=='7f79e3d1fe9fda97c943e3045c6c3e08ef209c488dd1943c41e82070599540b2'
    assert before['stock_rule_hashes']==after['stock_rule_hashes']
    added=new-old;removed=old-new
    result=dict(status='passed exact marker preservation'if not added and not removed else'failed exact marker preservation',
                baseline_summary_sha256=sha(a.baseline/'summary.json'),candidate_summary_sha256=sha(a.candidate/'summary.json'),
                baseline_markers=sum(old.values()),candidate_markers=sum(new.values()),added=rows(added),removed=rows(removed),
                inherited_failures=rows(old&new),absolute_stock_acceptance='failed'if new else'passed',
                scope='Exact category/cell/value multiset comparison, no tolerance or inherited-rule waiver',
                not_run=['maximal DRC','routed-signal/root-PDN interactions','density/antenna/fullchipLVS/PEX/EM','adoption'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='inherited_failures'},indent=2))
    raise SystemExit(0 if not added and not removed else 1)


if __name__=='__main__':main()
