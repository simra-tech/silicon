#!/usr/bin/env python3
"""Static separate-layout XOR for the exact RZ-column spacing-only revision."""
import argparse,json,os
from pathlib import Path
from build_native_prototypes import pya,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    parentscript=(a.parent/'builder_snapshot.py').read_text();newscript=(a.candidate/'builder_snapshot.py').read_text()
    old="[(-.3,ry-.28,'out1'),(.3,ry+6.48,'cz')]";new="[(-.32,ry-.28,'out1'),(.32,ry+6.48,'cz')]"
    assert parentscript.count(old)==1 and parentscript.replace(old,new)==newscript
    paths=[a.parent/'g1_ota_main_physical.gds',a.candidate/'g1_ota_main_physical.gds'];layouts=[];tops=[]
    for path in paths:
        ly=pya.Layout();ly.read(str(path));layouts.append(ly);tops.append(ly.cell('g1_ota_main_physical'))
    assert sha(paths[0])=='3d60787621c5f23128643c640cdac7d8ec9d7185e921ddc9b2760037f69dd108' and sha(paths[1])=='970b6b572f8637a5e56ad2d695e925f7e938ae28136a0e0015b256b77f6ae701'
    keys=sorted({(info.layer,info.datatype)for ly in layouts for info in ly.layer_infos()});rows=[];window=pya.Region(pya.DBox(118.9,127.7,120.4,154.7).to_itype(.001))
    for layer,datatype in keys:
        regions=[pya.Region(top.begin_shapes_rec(ly.layer(layer,datatype))).merged()for top,ly in zip(tops,layouts)]
        delta=regions[0]^regions[1];assert(delta-window).is_empty()
        if not delta.is_empty():assert datatype==0 and layer in(8,19,10,29,30,49,50)
        rows.append(dict(layer=layer,datatype=datatype,xor_um2=delta.area()*1e-6))
    result=dict(status='passed exact RZ-column-only source and saved-layout XOR',parent_GDS_sha256=sha(paths[0]),candidate_GDS_sha256=sha(paths[1]),script_sha256=sha(Path(__file__)),
                derived_builder_change='Only two RZ head-access offsets +/-0.30 to +/-0.32um',window_um=[118.9,127.7,120.4,154.7],layers=rows,
                native_layers_exact=True,original_DRC_failure='retained three M3.b markers',stock_revision_checks='separate run',source_parameters_changed=False)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
