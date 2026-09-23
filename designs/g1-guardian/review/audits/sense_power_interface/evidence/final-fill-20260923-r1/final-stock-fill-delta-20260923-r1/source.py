#!/usr/bin/env python3
"""Export the exact additive filler polygon delta from a fixed sealed source."""
import argparse
import collections
import json
import os
from pathlib import Path
import sys
import pya
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from place_closed_analog import region,text_records,sha

FILL={(layer,22)for layer in(1,5,8,10,30,50,67,126,134)}


def instances(layout):
    return collections.Counter((cell.name,i.cell.name,str(i.cell_inst),i.prop_id)
        for cell in layout.each_cell()for i in cell.each_inst())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('base','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    before_path=a.base/'sealed_native.gds';after_path=a.candidate/'filled_native.gds'
    before_meta=json.loads((a.base/'analysis.json').read_text());after_meta=json.loads((a.candidate/'analysis.json').read_text())
    assert before_meta['status'].startswith('passed')and after_meta['status'].startswith('passed')
    assert sha(before_path)==before_meta['GDS_sha256']=='3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9'
    assert sha(after_path)==after_meta['GDS_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(before_path),candidate_GDS_sha256=sha(after_path),
        script_sha256=sha(Path(__file__)),source_metadata_sha256=sha(a.base/'analysis.json'),
        candidate_metadata_sha256=sha(a.candidate/'analysis.json'),
        not_run=['stock DRC/density/antenna in this invocation','fill-sensitive PEX/electrical acceptance','adoption'])
    try:
        before=pya.Layout();before.read(str(before_path));bt=before.top_cell()
        after=pya.Layout();after.read(str(after_path));at=after.top_cell()
        assert before.dbu==after.dbu==.001 and bt.name==at.name
        assert bt.bbox()==at.bbox()==pya.Box(0,0,1414000,1414000)
        old_instances=instances(before);new_instances=instances(after)
        assert not old_instances-new_instances,'An original hierarchical instance changed or disappeared'
        assert text_records(before,bt)==text_records(after,at)
        overlay=pya.Layout();overlay.dbu=.001;ot=overlay.create_cell('final_added_filler_NOT_ADOPTED')
        keys={(i.layer,i.datatype)for i in before.layer_infos()+after.layer_infos()}
        rows=[];added_regions={}
        for key in sorted(keys):
            info=pya.LayerInfo(*key);old=region(before,bt,info);new=region(after,at,info)
            removed=old-new;added=new-old
            assert removed.is_empty(),('removed',key)
            assert key in FILL or added.is_empty(),('functional addition',key)
            if key in FILL:added_regions[key]=added
            if not added.is_empty():
                for poly in added.each():ot.shapes(overlay.layer(info)).insert(poly)
            rows.append(dict(layer=list(key),old_area_dbu2=old.area(),new_area_dbu2=new.area(),
                removed_area_dbu2=0,added_area_dbu2=added.area(),added_polygon_count=added.count()))
        path=a.output/'added_filler_only.gds';overlay.write(str(path))
        saved=pya.Layout();saved.read(str(path));st=saved.top_cell()
        for key in sorted(FILL):
            info=pya.LayerInfo(*key)
            assert(region(saved,st,info)^added_regions.get(key,pya.Region())).is_empty()
        assert sha(before_path)==result['source_GDS_sha256']and sha(after_path)==result['candidate_GDS_sha256']
        result.update(status='passed exact additive datatype22 ledger and source reconstruction',
            original_hierarchical_instances_retained=sum(old_instances.values()),
            added_hierarchical_instances=sum((new_instances-old_instances).values()),
            all_non22_polygons_and_all_texts='passed exact preservation',
            old_fill_removed='none',saved_overlay_XOR='passed all nine filler layers',
            overlay_sha256=sha(path),layers=rows)
    except Exception as exc:
        result.update(status='failed exact filler ledger',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k!='layers'},indent=2))


if __name__=='__main__':main()
