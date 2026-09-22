#!/usr/bin/env python3
"""Observe native coupon conductor/dielectric domain construction, stopping before meshing."""
import argparse
import json
import os
from pathlib import Path
import klayout.db as kdb
import klayout_pex.fastercap.fastercap_input_builder as module
from klayout_pex.fastercap.fastercap_model_generator import FasterCapModelBuilder
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from computed_layer_geometry_adapter import ExactComputedLayerBuilder
from export_sense_kpex_api import materialize,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('lvsdb','gds','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={7}
    assert sha(a.lvsdb)=='f258e4251106158456335eb899ae511c7f56c4cf258c1bb4c23ffc4f187fb05b'
    assert sha(a.gds)=='546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20'
    a.output.mkdir(parents=True);(a.output/'audit_snapshot.py').write_bytes(Path(__file__).read_bytes())
    args=KpexCLI.parse_args(['--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','CC','--lvsdb',str(a.lvsdb),
                            '--out_dir',str(a.output/'context')],Env.from_os_environ())
    KpexCLI.validate_args(args);tech=TechInfo.from_json(args.tech_pbjson_path,dielectric_filter=args.dielectric_filter)
    tech_hash=sha(Path(args.tech_pbjson_path));db=KpexCLI().create_lvsdb(args)
    context=KLayoutExtractionContext.prepare_extraction(db,args.effective_cell_name,tech,False)
    ly=kdb.Layout();ly.read(str(a.gds));top=ly.top_cell();query={};runs=[]
    class RecordingBuilder(FasterCapModelBuilder):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.events=[]
        def add_conductor(self,net_name,layer,z,height):
            self.events.append(dict(kind='conductor',name=net_name,source_layer='VSUBS' if net_name=='VSUBS' else query['layer'],
                                    area_um2=materialize(layer).area()*1e-6,z_um=z,height_um=height,region=materialize(layer)))
            return super().add_conductor(net_name,layer,z,height)
        def add_dielectric(self,material_name,layer,z,height):
            self.events.append(dict(kind='dielectric',name=material_name,area_um2=materialize(layer).area()*1e-6,
                                    z_um=z,height_um=height,region=materialize(layer)))
            return super().add_dielectric(material_name,layer,z,height)
        def generate(self):return self  # Observation boundary: native mesh generation deliberately not called.
    original=module.FasterCapModelBuilder
    try:
        module.FasterCapModelBuilder=RecordingBuilder
        for label,base in [('stock',module.FasterCapInputBuilder),('exact_computed',ExactComputedLayerBuilder)]:
            class Tracked(base):
                def shapes_of_net(self,layer_name,net):
                    query['layer']=layer_name
                    return super().shapes_of_net(layer_name,net)
            built=Tracked(context,tech).build();controls=[]
            for canonical,pair,layers in [('Metal5',(67,0),('metal5_cap','metal5_n_cap')),
                                           ('MIM',(36,0),('cmim_top',)),('TopMetal1',(126,0),('topmetal1',)),
                                           ('TopVia1',(125,0),('topvia1_n_cap',)),
                                           ('Vmim',(129,0),('mim_via',))]:
                native=materialize(kdb.Region(top.begin_shapes_rec(ly.layer(*pair))))
                supplied=kdb.Region()
                for event in built.events:
                    if event['kind']=='conductor' and event['source_layer'].lower() in layers:supplied+=event['region']
                xor=materialize(supplied^native).area()*1e-6
                controls.append(dict(layer=canonical,native_area_um2=native.area()*1e-6,supplied_union_area_um2=materialize(supplied).area()*1e-6,XOR_um2=xor))
                assert xor==0,(label,canonical,xor)
            if label=='exact_computed':
                for event in built.events:
                    if event.get('source_layer')=='metal5_cap':assert event['area_um2']==49.
                    if event.get('source_layer')=='metal5_n_cap':assert abs(event['area_um2']-18.24)<1e-8
            owned=[]
            for circuit in db.netlist().each_circuit():
                for device in circuit.each_device():
                    if device.device_class().name!='cap_cmim':continue
                    for terminal,computed in [('mim_top','cmim_top'),('mim_btm','metal5_cap')]:
                        terminal_shapes=db.shapes_of_terminal(device.terminal_ref(terminal))
                        assert len(terminal_shapes)==1
                        region=materialize(next(iter(terminal_shapes.values())))
                        net=device.net_for_terminal(terminal).expanded_name()
                        events=[e for e in built.events if e['kind']=='conductor' and e.get('source_layer')==computed and e['name']==net]
                        assert len(events)==1
                        delta=materialize(events[0]['region']^region).area()*1e-6
                        if label=='exact_computed':assert delta==0
                        owned.append(dict(device_id=device.id(),terminal=terminal,computed_layer=computed,net=net,
                                          native_area_um2=region.area()*1e-6,domain_native_XOR_um2=delta,
                                          model_W_um=device.parameter('w'),model_L_um=device.parameter('l')))
            assert len(owned)==2
            runs.append(dict(case=label,domains=[{k:v for k,v in e.items() if k!='region'} for e in built.events],
                             materials=built.materials,native_conductor_union_controls=controls,primitive_owned_domain_controls=owned))
    finally:module.FasterCapModelBuilder=original
    assert sha(Path(args.tech_pbjson_path))==tech_hash
    result=dict(status='passed pre-mesh native domain observation; complete field/model composition not qualified',
                runs=runs,technology_sha256=tech_hash,LVSDB_sha256=sha(a.lvsdb),GDS_sha256=sha(a.gds),
                script_sha256=sha(Path(__file__)),adapter_sha256=sha(Path(__file__).with_name('computed_layer_geometry_adapter.py')),
                ownership='native plates are present as physical conductor domains; no primitive-owned field decomposition added',
                native_Vmim_to_computed_identity=dict(native_GDS=[129,0],computed_name='mim_via',computed_GDS=list(tech.gds_pair('mim_via'))),
                thin_MIM_25D_table_scope=dict(canonical_name=tech.computed_layer_info_by_name['cmim_top'].original_layer_name,
                    substrate_names=list(tech.substrate_cap_by_layer_name),
                    overlap_names={k:list(v) for k,v in tech.overlap_cap_by_layer_names.items()},
                    fringe_names={k:list(v) for k,v in tech.side_overlap_cap_by_layer_names.items()},
                    status='MIM thin-plate canonical name is TODO and absent from conventional-metal coefficient tables; complete2.5D not qualified'),
                observation_adapter='in-memory native builder subclass records domain input then stops at generate; no installed package edits',
                meshing='not run',solver='not run',model_intrinsic_subtraction='not run',r8_fullmacro='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
