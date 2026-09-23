#!/usr/bin/env python3
"""Exact unchanged native blackbox CC API; incomplete fields are NOT qualified."""
import argparse,importlib.metadata,json,math,os,time
from pathlib import Path
import klayout.db as kdb
import klayout_pex
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from inspect_passive_sites import sha

def materialize(region):
    return kdb.Region([kdb.Polygon(p) for p in region.each()]).merged()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['view','reference','source','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={0} and not a.output.exists()
    assert kdb.__version__=='0.30.9' and importlib.metadata.version('klayout-pex')=='0.3.12'
    m=json.loads((a.view/'manifest.json').read_text());ref=json.loads((a.reference/'manifest.json').read_text())
    assert m['status']=='passed source134 native-polygon-preserving diagnostic view'
    assert ref['status']=='passed saved-polygon and exact source reference gate'
    assert sha(a.source)==m['source_sha256']==ref['source_sha256']
    assert m['parent_GDS_sha256']==ref['GDS_sha256']
    gds=a.view/'g1_sense_pex_view.gds';cdl=a.reference/'g1_sense_physical.cdl'
    assert sha(gds)==m['GDS_sha256'] and sha(cdl)==ref['CDL_sha256']
    pkg=Path(klayout_pex.__file__).parent;pdk=Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    tools={q:sha(q) for q in pkg.rglob('*') if q.is_file() and q.suffix in ['.py','.json','.lvs','.lylvs','.rb']}
    cards={q:sha(q) for q in (pdk/'libs.tech/ngspice/models').rglob('*.lib')}
    inputs={q:sha(q) for q in [gds,cdl,a.source,a.view/'manifest.json',a.reference/'manifest.json']}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_sha256=sha(a.source),view_GDS_sha256=sha(gds),
        native_GDS_sha256=m['parent_GDS_sha256'],CDL_sha256=sha(cdl),
        tool_hashes={str(q.relative_to(pkg)):h for q,h in tools.items()},
        model_hashes={str(q.relative_to(pdk)):h for q,h in cards.items()},
        complete_field_coverage='FAILED: native blackbox MIM/tap omissions retained',
        model_composition='not qualified',electrical='not run',adoption='not run',
        VSUBS='unbound extractor substrate; no implicit0/VSS assignment',
        numerical_engine='unchanged native2.5D CC, original reporter; no SPICE/CSV writer')
    save=lambda:(a.output/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    start=time.monotonic();save()
    try:
        args=KpexCLI.parse_args(['--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','CC',
            '--blackbox','true','--cache-lvs','false','--gds',str(gds),'--cell','g1_sense_physical',
            '--schematic',str(cdl),'--out_dir',str(a.output/'engine')],Env.from_os_environ())
        KpexCLI.validate_args(args);cli=KpexCLI()
        tech=TechInfo.from_json(args.tech_pbjson_path,dielectric_filter=args.dielectric_filter)
        db=cli.create_lvsdb(args)
        context=KLayoutExtractionContext.prepare_extraction(db,args.effective_cell_name,tech,True)
        inventory=[]
        for pair,layers in context.extracted_layers.items():
            for layer in layers.source_layers:
                r=materialize(layer.region);inventory.append(dict(name=layer.lvs_layer_name,pair=list(pair),area_um2=r.area()*context.dbu**2,polygons=r.count()))
        unknown=[dict(name=q.lvs_layer_name,area_um2=materialize(q.region).area()*context.dbu**2) for q in context.unnamed_layers]
        circuit=db.netlist().circuit_by_name(args.effective_cell_name)
        native_names=sorted(n.expanded_name() for n in circuit.each_net())
        expected={q['pex_label'] for q in m['labels']}
        assert len(expected)==134
        result.update(technology_sha256=sha(Path(args.tech_pbjson_path)),layer_inventory=inventory,
            unknown_layers=unknown,native_net_names=native_names,expected_source_labels=sorted(expected))
        save()
        extraction=cli.run_kpex_2_5d_engine(args,context,tech,str(a.output/'native_report.rdb.gz'),None,None)
        summary=extraction.summarize();rows=[]
        for key,value in sorted(summary.capacitances.items()):
            value=float(value);assert math.isfinite(value) and value>=0 and key.net1!=key.net2
            rows.append(dict(net1=key.net1,net2=key.net2,capacitance_fF=value,capacitance_fF_hex=value.hex()))
        assert rows and not summary.resistances
        path=a.output/'exact_capacitances.json';path.write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')
        reread=json.loads(path.read_text());assert all(float.fromhex(r['capacitance_fF_hex'])==r['capacitance_fF'] for r in reread)
        raw_nodes={r[k] for r in rows for k in ['net1','net2']}
        unknown_nodes=sorted(raw_nodes-expected-{'VSUBS'})
        result.update(status='passed raw native CC only; completefield FAILED',capacitor_count=len(rows),
            capacitor_sha256=sha(path),unknown_capacitor_nodes=unknown_nodes,
            exact_source_node_mapping='passed' if not unknown_nodes else 'failed; annotation forbidden',
            binary64_roundtrip=True)
    except Exception as exc:
        result.update(status='failed raw CC diagnostic',error=repr(exc));raise
    finally:
        unchanged=all(sha(q)==h for q,h in {**inputs,**tools,**cards}.items())
        result.update(inputs_tools_cards_unchanged=unchanged,wall_s=time.monotonic()-start)
        if not unchanged:result['status']='failed changed input/tool/card'
        save()

if __name__=='__main__':main()
