#!/usr/bin/env python3
"""Add source-native IO/glue to a qualified core without reusing old routes."""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import pya
from place_closed_analog import region, text_records, sha

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[1]
PDK=Path('/foss/pdks/ihp-sg13g2')
ORIENT=dict(N=pya.Trans.R0,W=pya.Trans.R90,S=pya.Trans.R180,E=pya.Trans.R270,
            FS=pya.Trans.M0,FN=pya.Trans.M90,FW=pya.Trans.M45,FE=pya.Trans.M135)


def transform(xy,orient,size):
    linear=pya.Trans(ORIENT[orient])
    box=linear*pya.Box(0,0,*size)
    return pya.Trans(xy[0]-box.left,xy[1]-box.bottom)*linear


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--odb-check',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    coremeta=json.loads((a.core/'analysis.json').read_text())
    prepared=json.loads((a.prepared/'analysis.json').read_text())
    odb=json.loads((a.odb_check/'analysis.json').read_text())
    core=a.core/'refreshed_core.gds'
    assert coremeta['status'].startswith('passed') and sha(core)==coremeta['GDS_sha256']
    assert prepared['DEF_sha256']==odb['source_DEF_sha256']
    assert odb['status'].startswith('passed') and odb['instances']==4904
    baseline=DESIGN/'blocks/g1_padring/layout/g1_chip_top.gds'
    assert sha(baseline)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    lefs=[PDK/'libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef',
          DESIGN/'blocks/g1_padring/ip/sg13g2_io_padbare/lef/sg13g2_io.lef',
          DESIGN/'blocks/g1_padring/ip/bondpad_70x70_tm1/lef/bondpad_70x70_tm1.lef']
    sizes={}
    for path in lefs:
        for name,body in re.findall(r'^MACRO (\S+)\n(.*?)^END \1$',path.read_text(),re.M|re.S):
            match=re.search(r'\bSIZE ([\d.]+) BY ([\d.]+) ;',body)
            if match:
                assert name not in sizes
                sizes[name]=[round(float(v)*1000)for v in match.groups()]
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    old=pya.Layout();old.read(str(baseline));ot=old.cell('g1_chip_top')
    new=pya.Layout();new.read(str(core));nt=new.top_cell()
    assert old.dbu==new.dbu==.001
    assert sum(1 for _ in nt.each_inst())==4674
    rows=[r for r in prepared['changes']if r['kind']in('retained_IO','retained_glue')]
    assert len(rows)==210
    required_masters={r['master']for r in rows}
    lookup={}
    for instance in ot.each_inst():
        if instance.cell.name not in required_masters:
            continue
        key=(instance.cell.name,str(instance.trans))
        assert key not in lookup,key
        lookup[key]=instance
    before={str(info):region(new,nt,info)for info in new.layer_infos()}
    additions=collections.defaultdict(pya.Region)
    copies={};placed=[]
    def add(name,master,xy,orient,source_instance=None):
        cell=old.cell(master)
        assert cell is not None and master in sizes
        if master not in copies:
            copied=new.create_cell('retained_fullchip_'+master);copied.copy_tree(cell)
            assert text_records(old,cell)==text_records(new,copied)
            for info in old.layer_infos():
                assert (region(old,cell,info)^region(new,copied,info)).is_empty()
            copies[master]=copied
        t=transform(xy,orient,sizes[master])
        newinst=nt.insert(pya.CellInstArray(copies[master].cell_index(),t))
        for info in old.layer_infos():
            additions[str(info)]+=region(old,cell,info).transformed(t)
        placed.append(dict(instance=name,master=master,transform=str(t),
                           native_bbox_dbu=[newinst.bbox().left,newinst.bbox().bottom,newinst.bbox().right,newinst.bbox().top],
                           source_transform=str(source_instance.trans)if source_instance else None))
    for row in rows:
        oldxy=row['old'][:2];oldorient=row['old'][2]
        expected=transform(oldxy,oldorient,sizes[row['master']])
        instance=lookup[(row['master'],str(expected))]
        add(row['instance'],row['master'],row['new'][:2],row['new'][2],instance)
    for row in prepared['added_native_IO_fillers']:
        add(row['instance'],row['master'],row['xy'],row['orient'])
    assert len(placed)==230 and sum(1 for _ in nt.each_inst())==4904
    assert len(new.top_cells())==1
    for info in new.layer_infos():
        expected=before.get(str(info),pya.Region())+additions[str(info)]
        assert (region(new,nt,info)^expected).is_empty(),str(info)
    # Every copied cell's text was proven above; saved whole-layout roundtrip
    # also checks transformed texts. Top package pin labels/sealring are a
    # separate unfinished interface stage, not silently invented here.
    texts=text_records(new,nt)
    output=a.output/'fullchip_instances_unrouted.gds';new.write(str(output))
    saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
    assert text_records(saved,st)==texts
    for info in new.layer_infos():
        assert (region(new,nt,info)^region(saved,st,info)).is_empty()
    result=dict(status='passed full native instance integration; unrouted',GDS_sha256=sha(output),
                core_GDS_sha256=sha(core),source_GDS_sha256=sha(baseline),DEF_sha256=prepared['DEF_sha256'],
                ODB_sha256=odb['ODB_sha256'],script_sha256=sha(Path(__file__)),instances=4904,
                native_added_instances=placed,retained_core_instances=4674,LEFs=[dict(path=str(q),sha256=sha(q))for q in lefs],
                exact_native_geometry_and_texts='passed',source_DEF_to_native_instance_binding='passed',saved_roundtrip='passed',
                not_run=['full assembly connectivity','stock DRC/LVS/density/antenna/PEX','PDN and signal routes',
                         'package labels and new sealring','STA/currentIR/EM','electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='native_added_instances'},indent=2))


if __name__=='__main__':
    main()
