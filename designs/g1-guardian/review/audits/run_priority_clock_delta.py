#!/usr/bin/env python3
"""Bounded paired24um clock endpoint clip delta; no convergence/full-route claim."""
import argparse,hashlib,json,os,shutil,sys
from pathlib import Path
import pya
ROOT=Path(__file__).resolve().parents[4];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-manifest',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();load=lambda path:json.loads(path.read_text())
candidate=load(a.manifest);parent=load(a.parent_manifest);assert candidate['parent_candidate_sha256']==parent['candidate_sha256']
assert load(BASE/'priority-via-core-lvs-20260922-r1/summary.json')['status']=='passed'
assert load(BASE/'priority-via-connectivity-20260922-r2.json')['status']=='passed'
for name in ('drc','antenna','density'):assert load(BASE/('priority-via-stock-'+name+'-20260922-r1/summary.json'))['status']=='passed'
helpers=['prepare_interface_clip.py','run_fill_clip_pex.py','export_clip_lvsdb.lvs','analyze_interface_clip.py','clip_cap_graph.py','check_fill_clip_ac.py'];helperhash={name:sha(BASE/name) for name in helpers}
a.output.mkdir(parents=True);out=a.output.resolve();shutil.copyfile(__file__,out/'runner.py')
contract={'parent_sha256':parent['candidate_sha256'],'candidate_sha256':candidate['candidate_sha256'],'pair':'isense_clock','context_um':24,'end_margin_um':20,'length_inside_overlap_default_um':20,
    'helper_hashes':helperhash,'allocation_cpus':1,'max_batch_output_bytes':268435456,'KPEX_and_extract_timeout_s_each':120,'parser_or_numerical_failure_stops_batch':True,
    'captured_changed_stage_ids':[2,3,10],'remaining_changed_stage_ids':sorted(set(range(21))-{2,3,10}),
    'scope':'Prospectivepairedlocaldelta only; rootlongIPTATwide48timeout andfullmatrixcontextfailure retained. Nominal rootclockmutual circuitresult is parent/deliveredsource only, not candidate electrical acceptance.'}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
inventory=load(BASE/'route-via-inventory-20260922-r2.json');metals=(8,10,30,50,67,126,134);cuts={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
phases=[];summaries={}
for view,manifest in [('parent',a.parent_manifest),('candidate',a.manifest)]:
    gds=(manifest.parent/'g1_chip_top.gds').resolve();expected=load(manifest)['candidate_sha256'];assert sha(gds)==expected
    leaf=out/view;leaf.mkdir();ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_chip_top');network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]));layers={}
    for layer in metals:layers[layer]=network.make_layer(ly.layer(layer,0),'M'+str(layer));network.connect(layers[layer])
    for cut,(lower,upper) in cuts.items():
        region=network.make_layer(ly.layer(cut,0),'V'+str(cut));network.connect(region);network.connect(region,layers[lower]);network.connect(region,layers[upper])
    network.extract_netlist()
    def identity(layer,point):
        net=network.probe_net(layers[layer],pya.DPoint(*point).to_itype(ly.dbu));assert net is not None
        return (net.circuit().name,net.cluster_id)
    targets=[]
    for name,point in [('i_core.isense',(733.92,615.72)),('i_core.cmp_clk',(734.4,615.72))]:
        physical=identity(50,point);anchors=[]
        for net in inventory['nets']:
            if net['net']!=name:continue
            for via in net['vias']:
                for stage in via['cut_stages']:
                    anchor=identity(stage['lower_layer'],via['point_um']);assert anchor==physical
                    anchors.append({'point_um':via['point_um'],'layer':stage['lower_layer'],'physical_net':anchor})
        assert anchors;targets.append({'name':name,'point_um':point,'physical_net':physical,'all_recorded_route_anchors_match':anchors})
    assert targets[0]['physical_net']!=targets[1]['physical_net']
    (leaf/'physical_target_identity.json').write_text(json.dumps({'status':'passed','GDS_sha256':expected,'targets':targets,'scope':'Allsevenactualdrawingmetals andvias, no labels/virtualmerge; targetmidpoints match every recordedroute-via anchor.'},indent=2)+'\n')
    del network,ly
    commands=[('prepare',['python3',str(BASE/'prepare_interface_clip.py'),'--pair','isense_clock','--gds',str(gds),'--expected-sha256',expected,'--context-um','24','--end-margin-um','20','--output',str(leaf/'clip')],120),
        ('pex',['python3',str(BASE/'run_fill_clip_pex.py'),'--clip',str(leaf/'clip'),'--output',str(leaf/'pex')],500),
        ('analyze',['python3',str(BASE/'analyze_interface_clip.py'),'--input',str(leaf/'pex'),'--output',str(leaf/'analysis')],120),
        ('AC_check',['python3',str(BASE/'check_fill_clip_ac.py'),str(leaf/'analysis')],300)]
    for phase,command,limit in commands:
        assert all(sha(BASE/name)==value for name,value in helperhash.items())
        with (leaf/(phase+'.log')).open('x') as stream:state=run_bounded(command,stream,leaf/(phase+'.json'),limit,cwd=ROOT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),interval_s=1)
        phases.append({'view':view,'phase':phase,'status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s']})
        (out/'phases.json').write_text(json.dumps(phases,indent=2)+'\n');assert state['status']=='completed' and state['returncode']==0
        if phase=='pex':
            records=load(leaf/'pex/manifest.json');assert len(records)==2 and all(row['extract_status']=='completed' and row['extract_returncode']==0 and row['kpex_status']=='completed' and row['kpex_returncode']==0 for row in records)
        assert sum(path.stat().st_size for path in out.rglob('*') if path.is_file())<=contract['max_batch_output_bytes']
    checks=load(leaf/'analysis/ac_checks.json');assert len(checks)==8 and all(row['status']=='passed' for row in checks)
    summaries[view]=load(leaf/'analysis/summary.json');assert sha(gds)==expected
deltas={}
for variant in ('no_fill','actual_fill'):
    deltas[variant]={}
    for mode in ('grounded','floating'):
        left=summaries['parent']['results'][variant]['modes'][mode];right=summaries['candidate']['results'][variant]['modes'][mode]
        deltas[variant][mode]={key:right[key]-left[key] for key in ('P_ground_equivalent_fF','N_ground_equivalent_fF','mutual_fF')}
result={'status':'passed pairedlocalextraction and16capacitorgraphACchecks; electricalacceptance notrun','contract_sha256':sha(out/'contract.json'),'source_identities':[parent['candidate_sha256'],candidate['candidate_sha256']],
    'deltas_fF':deltas,'summaries':summaries,'coverage_stage_ids':[2,3,10],'other18_changed_stage_RC':'not run','fullmatrix_context_convergence':'failed inpriorrootbaseline andretained, nottestedhere','candidate_dynamic_circuit_effect':'not run'}
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:value for key,value in result.items() if key!='summaries'},indent=2))
