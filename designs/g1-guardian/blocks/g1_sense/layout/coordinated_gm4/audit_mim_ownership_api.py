#!/usr/bin/env python3
"""Read-only native MIM ownership and installed extraction API boundary; no solver."""
import argparse,hashlib,inspect,json,os
from pathlib import Path
import pya,klayout_pex
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.fastercap.fastercap_model_generator import FasterCapModelBuilder

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def materialize(region):return pya.Region([pya.Polygon(q)for q in region.each()]).merged()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('lvsdb','gds','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={7}and not a.output.exists()and pya.__version__=='0.30.9'
    binds={path:sha(path)for path in(a.lvsdb,a.gds)}
    assert binds[a.lvsdb]=='95e8683146bc38ecf9a78e3fde3fe8541c9a888707a77c378b816c9136a1af67'
    db=pya.LayoutVsSchematic();db.read(str(a.lvsdb));ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_sense_physical')
    native_mim=materialize(pya.Region(top.begin_shapes_rec(ly.layer(36,0))))
    native_m5=materialize(pya.Region(top.begin_shapes_rec(ly.layer(67,0))))
    owners=[];unions={'mim_top':pya.Region(),'mim_btm':pya.Region()}
    for circuit in db.netlist().each_circuit():
        for device in circuit.each_device():
            if device.device_class().name!='cap_cmim':continue
            terms={};shapes={}
            for terminal in device.device_class().terminal_definitions():
                # This API returns layer-index -> Region, not a layer argument.
                raw=db.shapes_of_terminal(device.terminal_ref(terminal.name))
                assert len(raw)==1
                li,region=next(iter(raw.items()));region=materialize(region);b=region.bbox()
                assert region.count()==1 and region.area()==b.area()
                assert(db.layer_name(li),terminal.name)in(('cmim_top','mim_top'),('cmim_btm','mim_btm'))
                assert (unions[terminal.name]&region).is_empty()
                unions[terminal.name]+=region;shapes[terminal.name]=region
                terms[terminal.name]=dict(layer_name=db.layer_name(li),net=device.net_for_terminal(terminal.name).expanded_name(),
                    area_um2=region.area()*1e-6,perimeter_um=region.perimeter()*.001,
                    bbox_um=[q*.001 for q in(b.left,b.bottom,b.right,b.top)])
            assert(shapes['mim_top']^shapes['mim_btm']).is_empty()
            w=device.parameter('w');length=device.parameter('l')
            assert abs(terms['mim_top']['area_um2']-w*length)<1e-8
            assert abs(terms['mim_top']['perimeter_um']-2*(w+length))<1e-8
            owners.append(dict(stock_device_id=device.id(),native_W_um=w,native_L_um=length,terminals=terms,
                analytic_nominal_27C_area_fF=1.5*w*length,analytic_nominal_27C_perimeter_fF=.04*2*(w+length)))
    assert len(owners)==3
    for region in unions.values():assert(materialize(region)^native_mim).is_empty()
    layers={db.layer_name(i):i for i in db.layer_indexes()}
    bottom=materialize(db.layer_by_index(layers['metal5_cap']));noncap=materialize(db.layer_by_index(layers['metal5_n_cap']))
    assert(bottom^unions['mim_btm']).is_empty()and(bottom&noncap).is_empty()
    assert((bottom+noncap)^native_m5).is_empty()
    package=Path(klayout_pex.__file__).parent
    paths=['fastercap/fastercap_input_builder.py','fastercap/fastercap_model_generator.py','fastercap/fastercap_runner.py',
           'rcx25/c/overlap_extractor.py','rcx25/c/sidewall_and_fringe_extractor.py']
    sources={name:sha(package/name)for name in paths}
    signature=str(inspect.signature(FasterCapModelBuilder.add_conductor))
    assert set(inspect.signature(FasterCapModelBuilder.add_conductor).parameters)=={'self','net_name','layer','z','height'}
    args=KpexCLI.parse_args(['--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','CC','--lvsdb',str(a.lvsdb)],Env.from_os_environ())
    tech=Path(args.pdk.config.tech_pb_json_path);tech_lines=tech.read_text().splitlines()
    matching=[dict(line=i+1,text=line.strip())for i,line in enumerate(tech_lines)if any(key in line.lower()for key in('mim','<todo>','metal5_cap','metal5_n_cap'))]
    pdk=Path('/foss/pdks/ihp-sg13g2');model_files=['libs.tech/ngspice/models/capacitors_mod.lib','libs.tech/ngspice/models/capacitors_mod_mismatch.lib',
        'libs.tech/ngspice/models/cornerCAP.lib','libs.tech/klayout/python/sg13g2_pycell_lib/ihp/cmim_code.py']
    result=dict(status='passed native primitive-ownership recovery; complete extraction boundary not qualified',
        script_sha256=sha(Path(__file__)),LVSDB_sha256=binds[a.lvsdb],GDS_sha256=binds[a.gds],owners=owners,
        same_device_top_bottom_mask_XOR_um2=0.,between_device_mask_overlap_um2=0.,native_MIM_union_XOR_um2=0.,
        owned_bottom_M5_area_um2=bottom.area()*1e-6,remaining_M5_area_um2=noncap.area()*1e-6,
        M5_owned_remaining_partition_XOR_um2=0.,M5_owned_remaining_overlap_um2=0.,
        installed_source_sha256=sources,model_PCell_sha256={name:sha(pdk/name)for name in model_files},
        model_formula='[CJ*L_um*W_um + 2*CJSW*(L_um+W_um)] * instance_scale * [1+TC1*(T-27)+TC2*(T-27)^2], with source cmim_core CJ=cap_carea, CJSW=40e-18F and mm scaling unchanged',
        model_formula_reference='ngspice-46 manual section3.3.8 equations3.10-3.13, https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf#page=83',
        model_internal_series_resistance_ohm=.055,
        conductor_API_signature=signature,tech_json_sha256=sha(tech),tech_MIM_rows=matching,
        supported_primitive_pair_deembedding=False,
        limitation='Stock3D builder merges geometry by electrical net before surface generation; output matrix has net-conductor indices, no primitive-owned field terms. Stock2.5D visitors retain geometry before summation but fringe shielding recreates properties with net only and groups by net; owner-aware masking would require a new validated extraction path.',
        no_new_extraction=True,no_meshing=True,no_solver=True,no_source_card_deck_or_geometry_mutation=True)
    assert all(sha(path)==value for path,value in binds.items())
    a.output.mkdir(parents=True);(a.output/'script_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
