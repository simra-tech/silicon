#!/usr/bin/env python3
"""Conditional DC bounds and explicitly incomplete power accounting from retained evidence."""
import argparse,collections,hashlib,json,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[4];B=R/'designs/g1-guardian/blocks';A=R/'designs/g1-guardian/review/audits'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mesh',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),args.output/'runner.py');inputs={}
def read(path):
    inputs[str(path.relative_to(R)) if path.is_absolute() else str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return json.loads(path.read_text())
mesh=read(args.mesh);sense=read(B/'g1_sense/sim/qualification/corners-20260921-a/summary.json');power=read(A/'power-evidence-20260921.json');joint=read(B/'g1_t2f/sim/qualification/transition_current_selected.json');thermal=read(B/'g1_t2f/sim/qualification/runs/t2f_joint_temp7_20260921_01/manifest.json')
osc=[]
for f in sorted((B/'g1_osc/sim/qualification/runs').glob('osc_trim80_shard*20260921_01/manifest.json')):
    for case in read(f)['cases']:
        if case['status']=='passed':osc.append(case)
log=B/'g1_padring/flow/runs/assembly-1350/22-openroad-generatepdn/analog_straps.log';inputs[str(log.relative_to(R))]=hashlib.sha256(log.read_bytes()).hexdigest()
sense_rows=[{'case':c['name'],'corner':c['corner'],'point':key,'draw_A':-v[-1]} for c in sense for key,v in c['rows'].items()]
nom_sense=max((c for c in sense_rows if c['corner']==['tt','typ',3.3,27] and '_c0.0_' in c['point']),key=lambda c:c['draw_A'],default=None)
if nom_sense is None:nom_sense=max((c for c in sense_rows if c['corner']==['tt','typ',3.3,27] and re.search(r'_c0(?:\.0)?_',c['point'])),key=lambda c:c['draw_A'])
max_sense=max(sense_rows,key=lambda c:c['draw_A']);min_sense=min(sense_rows,key=lambda c:c['draw_A'])
nom_osc=next(c for c in osc if c['name']=='tt_typ_typ_1.2_27_c0');max_osc=max(osc,key=lambda c:c['vdd']*c['measurements']['iua']*1e-6);fast_osc=max(osc,key=lambda c:c['measurements']['fmhz'])
nom_joint=next(c for c in joint['cases'] if c['conditions']['temperature_C']==27)['windows']['initial_ptat'];max_thermal=max(thermal['cases'],key=lambda c:-c['measurements']['i33_avg'])
ctrl=next(x for x in power['runs'] if x['block']=='g1_ctrl')['power_W'];tt=ctrl['nom_typ_1p20V_25C']['Total'];ff=ctrl['nom_fast_1p32V_m40C']['Total']
clock_ratio=nom_osc['measurements']['fmhz']/10
ctrl_scaled=(tt['internal']+tt['switching'])*clock_ratio+tt['leakage']
feed_parts={'M4_parallel_M5_85p48um_by_5p10um':mesh['sheet_ohm_per_square']['Metal4']*85.48/5.10/2,'six_TopVia1_cuts':mesh['via_ohm_per_cut']['TopVia1']/6,'four_hundred_Via3_cuts':mesh['via_ohm_per_cut']['Via3']/400,'four_hundred_Via4_cuts':mesh['via_ohm_per_cut']['Via4']/400};feed_R=sum(feed_parts.values())
network=mesh['networks'];groups={net:collections.defaultdict(list) for net in network}
for net,rec in network.items():
    for t in rec['terminals']:groups[net][t['name'].split('/')[0]].append(t)
    assert rec['full_width_GDS_coverage_passed'] and all(t['status']=='passed' and t['linear_residual_max']<1e-9 for t in rec['terminals'])
loop_rows=[]
for net in ['VDDA','VDD']:
    for inst,terms in groups[net].items():
        ret=groups['VSS'][inst]
        for mode in ['mesh_parallel','single_path']:
            key='mesh_effective_R_ohm' if mode=='mesh_parallel' else 'mesh_shortest_path_R_ohm'
            forward=[t[key]+t['access_R_ohm']+(feed_R if net=='VDDA' else 0) for t in terms];back=[t[key]+t['access_R_ohm'] for t in ret]
            loop_rows.append({'instance':inst,'supply':net,'mode':mode,'supply_R_range_ohm':[min(forward),max(forward)],'return_R_range_ohm':[min(back),max(back)],'single_access_loop_R_range_ohm':[min(forward)+min(back),max(forward)+max(back)]})
near={'VDDA':nom_sense['draw_A']+nom_joint['vdda_mean_A'],'VDD':tt['total']/1.2+nom_osc['measurements']['iua']*1e-6+nom_joint['vdd_mean_A']}
near_scaled=near|{'VDD':ctrl_scaled/1.2+nom_osc['measurements']['iua']*1e-6+nom_joint['vdd_mean_A']}
# A passive resistor graph's reciprocal transfer R to any injection point is
# at most its self R. Use that inequality rather than inventing missing load locations.
bounds=[]
for frequency_case,total in [('CTRL_at_10MHz',near),('CTRL_all_dynamic_scaled_to_OSC',near_scaled)]:
    for metal_scale in [1,2]:
        for external_R in [0,1,5]:
            for inst,ts in groups['VDDA'].items():
                # The whole combined group's current is conservatively available to
                # each observed member, because currents were not saved separately.
                own=nom_sense['draw_A'] if inst=='i_core.u_sense' else nom_joint['vdda_mean_A']
                own_return=own if inst=='i_core.u_sense' else own+nom_joint['vdd_mean_A']
                forward=max(t['mesh_effective_R_ohm']*total['VDDA']+t['access_R_ohm']*own for t in ts)+feed_R*total['VDDA']
                ret=max(t['mesh_effective_R_ohm']*(total['VDDA']+total['VDD'])+t['access_R_ohm']*own_return for t in groups['VSS'][inst])
                # Unknown GATE/TRIP currents are excluded, never set to zero as a claim.
                if inst in ['i_core.u_gate','i_core.u_trip']:continue
                drop=metal_scale*(forward+ret)+external_R*(total['VDDA']+total['VDD'])
                bounds.append({'case':frequency_case,'instance':inst,'resistance_scale_assumed':metal_scale,'additional_loop_R_assumed_ohm':external_R,'known_load_only_drop_bound_V':drop,'conditional_voltage_at_3p3V':3.3-drop,'qualification_floor_used_V':3.0,'missing_loads_included':False})
partial_power=near['VDDA']*3.3+near['VDD']*1.2
mixed=max_sense['draw_A']*3.6+max_osc['measurements']['iua']*1e-6*max_osc['vdd']-max_thermal['measurements']['i33_avg']*max_thermal['vdd']-max_thermal['measurements']['i12_avg']*max_thermal['vdd12']+ff['total']
capacity=[]
for resistance in [20,40,80]:
    for vsource,vfloor in [(3.3,3.0),(3.0,3.0),(1.2,1.08),(1.08,1.08)]:capacity.append({'loop_R_assumed_ohm':resistance,'source_V':vsource,'qualification_floor_V':vfloor,'Imax_from_headroom_A':max(0,(vsource-vfloor)/resistance),'scope':'Only Ohms-law sensitivity; not measured/extracted complete loop and not a functional limit'})
result={'scope':'Conditional analytical budget; not joint electrical simulation or whole-chip power/IR acceptance','inputs':inputs,'mesh_validation':{'connected_terminal_count':sum(len(x['terminals']) for x in network.values()),'max_linear_residual':max(t['linear_residual_max'] for n in network.values() for t in n['terminals']),'max_reciprocity_residual':max(n['reciprocity_residual_max'] for n in network.values())},'feed_approximation_ohm':feed_parts,'feed_sum_ohm':feed_R,'feed_exclusions':['M3 patch spreading','pad metal and Via2','bondpad/package/board/regulator'],'loop_R_estimates':loop_rows,'current_evidence':{'sense_near_room':nom_sense,'sense_screen_max':max_sense,'sense_screen_min':min_sense,'joint_near_room':nom_joint,'joint_scope':joint['scope'],'osc_near_room':nom_osc,'osc_max_power_case':max_osc,'osc_fastest_case':fast_osc,'ctrl_TT_10MHz_W':tt['total'],'ctrl_TT_all_dynamic_scaled_to_OSC_W':ctrl_scaled,'ctrl_frequency_scale':clock_ratio},'near_room_known_rail_currents_A':near,'partial_accounting':{'near_room_known_only_power_W':partial_power,'near_room_all_dynamic_scaled_power_W':near_scaled['VDDA']*3.3+near_scaled['VDD']*1.2,'mixed_screen_maxima_partial_power_W':mixed,'near_room_unallocated_10mW_remainder_W':.010-partial_power,'mixed_unallocated_10mW_remainder_W':.010-mixed,'qualification':'not run: these are incomplete sums from different fixtures/temperatures, not coherent whole-chip corners'},'conditional_DC_bounds':bounds,'headroom_current_sensitivity':capacity,'missing':['Active GATE and TRIP power','Actual pad/IO load and workload activity','Transient SENSE current and actual reference-bias interaction','Coherent PVT/workload assignment','Whole-system substrate/ground/package impedance','IR-aware functional block validation'],'whole_chip_below_10mW':'not run','loaded_whole_chip_IR':'not run'}
(args.output/'budget.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'feed_R_ohm':feed_R,'partial_accounting':result['partial_accounting'],'mesh_validation':result['mesh_validation'],'near_room_currents_A':near,'max_nominal_known_load_bound_V':max(x['known_load_only_drop_bound_V'] for x in bounds if x['resistance_scale_assumed']==1 and x['additional_loop_R_assumed_ohm']==0)},indent=2))
