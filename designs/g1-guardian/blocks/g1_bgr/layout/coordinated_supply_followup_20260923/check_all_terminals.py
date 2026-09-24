#!/usr/bin/env python3
"""Fresh graph at 10222 held source terminals and 24 moved physical pad ports."""
import argparse
import collections
import json
import os
from pathlib import Path
import sys
import time
import pya
from check_full_context_flat import ROOT,sha,dump
AUDITS=ROOT/'designs/g1-guardian/review/audits'
sys.path.insert(0,str(AUDITS))
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity
from audit_native_terminal_connectivity import CUTS,LAYERS,SUPPLIES
from place_closed_analog import region

def bijective(pairs):
    forward=collections.defaultdict(set);reverse=collections.defaultdict(set)
    for left,right in pairs:forward[left].add(right);reverse[right].add(left)
    return bool(pairs) and all(len(v)==1 for v in forward.values()) and all(len(v)==1 for v in reverse.values())

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT']);old_path=bulk/'bondpad-outward-connectivity-20260923-r1/analysis.json'
    odb=bulk/'bondpad-outward-odb-20260923-r1';gds=a.candidate/'supply_context_native.gds'
    alias=old_path.with_name('source_aliases.json')
    assert sha(alias)=='7b44b2efa8bb3318c7ba28144b0d2274e00d4178e7509db577a9738a6072bf0f'
    assert sha(old_path)=='c073bf49e56003a72faee18a432b3b853e56a4bfd916cc61c3f8ec4d471bed94'
    assert sha(odb/'roundtrip.tsv')=='fb5a40ab239c756c89ffb6f339d69e3993367babe61106dd4d3b518bc365e222'
    assert sha(odb/'analysis.json')=='0e3743294e2ce42a92641d7c69fdc3a1b6ec3419c86d06dba47e0f3d2486023b'
    meta=json.loads((a.candidate/'analysis.json').read_text());assert meta['status'].startswith('passed') and sha(gds)==meta['GDS_sha256']
    old=json.loads(old_path.read_text());aliases=json.loads(alias.read_text())
    assert aliases['status'].startswith('passed') and aliases['observation_sha256']==sha(old_path)
    verilog=ROOT/'designs/g1-guardian/blocks/g1_padring/ip/sg13g2_io_padbare/verilog/sg13g2_io.v'
    assert sha(verilog)==aliases['library_Verilog_sha256']
    assert not old['errors'] and not old['split_components'] and not old['physical_port_errors']
    expected={(f[1],f[2],f[3]) for f in (l.split('\t') for l in (odb/'roundtrip.tsv').read_text().splitlines()) if f[0]=='CONN' and f[2]!='PIN'}
    assert len(expected)==10222 and expected=={(r['net'],r['instance'],r['pin']) for r in old['observations']}
    inputs={str(p):sha(p) for p in (gds,a.candidate/'analysis.json',old_path,alias,verilog,odb/'roundtrip.tsv',odb/'analysis.json',Path(__file__),AUDITS/'flat_metal_connectivity.py')}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();result=dict(status='running',inputs=inputs);dump(a.output/'analysis.json',result)
    try:
        assert bijective([('a',1),('a',1),('b',2)])
        assert not bijective([('a',1),('a',2)])
        assert not bijective([('a',1),('b',1)])
        assert not bijective([])
        result['partition_controls']=dict(positive='passed',split_rejected='passed',merge_rejected='passed',empty_rejected='passed')
        ly=pya.Layout();ly.read(str(gds));top=ly.top_cell();net,metal,held=flat_physical(ly,top)
        actual={layer:region(ly,top,pya.LayerInfo(layer,0)) for layer in LAYERS.values()}
        observations=[];old_new=collections.defaultdict(set);new_old=collections.defaultdict(set)
        by_logical=collections.defaultdict(set);by_physical=collections.defaultdict(set)
        for row in old['observations']:
            clusters=set();windows=[]
            for window in row['windows']:
                layer=window['layer'];box=pya.Box(*window['bbox']);overlap=actual[layer]&pya.Region(box);found=set()
                for polygon in overlap.each():
                    point=next(polygon.each_point_hull())
                    for probe_layer in CUTS.get(layer,(layer,)):
                        key=identity(net,metal[probe_layer],[point.x,point.y]);assert key is not None,(row['instance'],row['pin'])
                        found.add(key)
                clusters.update(found);windows.append(dict(layer=layer,bbox=window['bbox'],clusters=[list(v) for v in sorted(found)]))
            assert len(clusters)==1 and len(row['clusters'])==1,(row['instance'],row['pin'],clusters)
            new=next(iter(clusters));prior=tuple(row['clusters'][0]);old_new[prior].add(new);new_old[new].add(prior)
            by_logical[row['net']].update(clusters);by_physical[new].add(row['net'])
            observations.append(dict(instance=row['instance'],pin=row['pin'],net=row['net'],clusters=[list(new)],windows=windows))
        assert all(len(s)==1 for s in old_new.values()) and all(len(s)==1 for s in new_old.values())
        assert bijective([(left,right) for left,rights in old_new.items() for right in rights])
        assert all(len(s)==1 for s in by_logical.values())
        assert len({next(iter(by_logical[k])) for k in SUPPLIES})==5
        actual_aliases=sorted(sorted(s) for s in by_physical.values() if len(s)>1)
        expected_aliases=sorted(sorted(r['logical_nets']) for r in old['unexpected_net_merges'])
        assert actual_aliases==expected_aliases and len(actual_aliases)==8
        ports=[]
        for row in old['physical_ports']:
            box=pya.Box(*row['bbox_dbu']);assert (pya.Region(box)-actual[134]).is_empty()
            found=set()
            for polygon in (actual[134]&pya.Region(box)).each():
                point=next(polygon.each_point_hull());key=identity(net,metal[134],[point.x,point.y]);assert key is not None;found.add(key)
            expected=old_new[tuple(row['components'][0])]
            assert len(found)==1 and found==expected,row
            ports.append(dict(row,components=[list(next(iter(found)))],status='passed'))
        assert len(ports)==24 and len({r['pin'] for r in ports})==22
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed exact held terminal partition and physical ports',GDS_sha256=sha(gds),
            terminal_observations=len(observations),observations=observations,physical_ports=ports,
            old_to_new_component_bijection=True,source_connections_exact=True,all_five_supplies_distinct=True,
            source_justified_aliases=actual_aliases,errors=[],unexpected_merges=[],split_components={},
            fullchip_device_LVS='not run',current_capacity='not run',electrical_adoption='not run')
    except Exception as e:
        result.update(status='failed terminal or physical-port gate',error=repr(e));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(a.output/'analysis.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','observations','physical_ports')},indent=2))

if __name__=='__main__':main()
