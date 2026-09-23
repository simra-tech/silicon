#!/usr/bin/env python3
"""Read-only hierarchy-size and pinned mapping-code audit after bounded LVS failure."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import pya


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    ly=pya.Layout();ly.read(str(path));top=ly.cell('placed_core_NOT_CONNECTED_FULLCHIP');assert top
    memo={};active=set();rows=[]
    def walk(cell):
        index=cell.cell_index()
        if index in memo:return memo[index]
        assert index not in active;active.add(index)
        direct=Counter();children=[]
        for li in ly.layer_indexes():
            count=cell.shapes(li).size()
            if count:direct[str(ly.get_info(li))]=count
        total=sum(direct.values());instances=0;depth=0
        for inst in cell.each_inst():
            multiplier=inst.cell_inst.size()
            child=ly.cell(inst.cell_index);sub=walk(child)
            total+=multiplier*sub['expanded_shapes'];instances+=multiplier*(1+sub['expanded_instances'])
            depth=max(depth,1+sub['depth'])
            children.append(dict(cell=child.name,count=multiplier,transform=str(inst.cplx_trans)))
        row=dict(cell=cell.name,direct_layers=dict(direct),children=children,expanded_shapes=total,
            expanded_instances=instances,depth=depth)
        active.remove(index);memo[index]=row;rows.append(row);return row
    topinfo=walk(top)
    return dict(sha256=sha(path),DBU=ly.dbu,all_cells=ly.cells(),reachable_cells=len(memo),
        top=topinfo,cells=sorted(rows,key=lambda r:r['cell']))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    current=bulk/'analog-pair-integration-20260923-r1/analog_pair_native.gds'
    old=bulk/'gshared-fill-20260923-r4/route_fill_pruned.gds'
    assert sha(current)=='be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'
    assert sha(old)=='4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2'
    a.output.mkdir(parents=True)
    result=dict(status='running read-only hierarchy diagnosis',inventories={})
    for name,path in [('old',old),('current',current)]:
        data=inventory(path);result['inventories'][name]={k:v for k,v in data.items() if k!='cells'}
        (a.output/(name+'_hierarchy.json')).write_text(json.dumps(data,indent=2)+'\n')
    pdk=Path('/foss/pdks/ihp-sg13g2');assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    files=[]
    for path in sorted((pdk/'libs.tech/klayout/tech/lvs').rglob('*')):
        if not path.is_file() or path.suffix not in ('.lvs','.rb'):continue
        text=path.read_text()
        if 'Apply RF MOS model mapping' in text or 'rfmos_model_mapping' in text.lower():
            dest=a.output/('rule_'+path.name);dest.write_text(text)
            files.append(dict(relative_path=str(path.relative_to(pdk)),sha256=sha(path),copy=dest.name))
    assert files
    for arm,directory,filename in [('old','io-physical-ap-native-lvs-20260923-r1','route_fill_pruned.log'),
            ('current','analog-pair-native-lvs-20260923-r1','analog_pair_native.log')]:
        log=bulk/directory/'reports'/filename
        text=log.read_text();(a.output/(arm+'_engine.log')).write_text(text)
        result.setdefault('logs',{})[arm]=dict(sha256=sha(log),last_lines=text.splitlines()[-12:])
    result.update(status='passed read-only hierarchy/log inventory; cause inference separate',
        pinned_mapping_files=files,rule_model_geometry_changes='not applicable',native_rerun='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())


if __name__=='__main__':main()
