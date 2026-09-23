#!/usr/bin/env python3
"""Read-only source/ODB/native-window binding for remaining macro and pad rails."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[2]
RAILS={'VDD','VDDA','VSS','IOVDD','IOVSS'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('prepared','odb','observations','final-core','bgr-ledger','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    pnl=DESIGN/'blocks/g1_padring/netlist/g1_chip_top.pnl.v'
    sources={}
    for master,name,body in re.findall(r'^\s*(\w+)\s+(\\?\S+)\s+\((.*?)\);',pnl.read_text(),re.M|re.S):
        name=name.lstrip('\\')
        pins={pin:net.strip().lstrip('\\')for pin,net in re.findall(r'\.(\w+)\(([^()]*)\)',body)}
        if pins:
            assert name not in sources,name
            sources[name]=dict(master=master,pins=pins)
    prepared=json.loads((a.prepared/'analysis.json').read_text())
    odb=json.loads((a.odb/'analysis.json').read_text())
    obs=json.loads(a.observations.read_text())
    core=json.loads((a.final_core/'analysis.json').read_text())
    assert prepared['DEF_sha256']==odb['source_DEF_sha256']
    assert odb['status'].startswith('passed') and core['status'].startswith('passed')
    assert obs['GDS_sha256']=='301cb530b14dd7e36c8a30b7f840aac62295f95642ed9264423de2b455bfc6f7'
    assert core['BGR_source_GDS_sha256']=='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
    logical={}
    for line in (a.odb/'roundtrip.tsv').read_text().splitlines():
        fields=line.split('\t')
        if fields[0]=='CONN':
            _,net,instance,pin=fields
            key=(instance,pin);assert key not in logical
            logical[key]=net
    components={r['instance']:r for r in prepared['changes']}
    legacy_path=DESIGN/'review/audits/current-envelopes-20260922-r1/summary.json'
    legacy=json.loads(legacy_path.read_text())
    currents={(r['macro'],r['rail']):r for r in legacy['branches']}
    bgr=json.loads(a.bgr_ledger.read_text())
    bgr_i={r['source_net']:r['net_injection_A']for r in bgr['references']if r['source_net']in('vdd','vss')}
    osc_path=DESIGN/'blocks/g1_osc/sim/qualification/actual_receiver_current_20260922.json'
    osc=json.loads(osc_path.read_text())
    osc_run=osc_path.parent/'runs/osc_actual_receiver_nominal_20260922_01'
    osc_manifest=json.loads((osc_run/'manifest.json').read_text())
    assert sha(osc_run/'osc.spice')==osc_manifest['source_sha256']['osc.spice']==osc_manifest['source_sha256']['baseline.spice']
    t2f_path=DESIGN/'blocks/g1_t2f/sim/qualification/transition_current_selected.json'
    t2f=json.loads(t2f_path.read_text())
    selected=[];excluded=collections.Counter();counts=collections.Counter()
    for row in obs['observations']:
        net,instance,pin=row['net'],row['instance'],row['pin']
        if net not in RAILS:continue
        counts[net]+=1
        assert logical[instance,pin]==net
        if not (instance.startswith('i_core.')or instance.startswith('pad')or instance.startswith('IO_BOND_')):
            excluded['decap'if instance.startswith('DECAP_')else'other_instance']+=1
            continue
        assert instance in sources and sources[instance]['pins'][pin]==net,(instance,pin,net)
        assert components[instance]['master']==sources[instance]['master']
        record=dict(net=net,instance=instance,master=sources[instance]['master'],pin=pin,
                    source_binding='passed PNL port == resolved OpenDB net == recorded native-window logical owner',
                    windows=row['windows'],recorded_physical_components=row['clusters'],
                    current_status='not run',current_scope='No current inferred from a voltage label or pin rectangle')
        if instance=='i_core.u_bgr':
            final=core['BGR_chip_ports'][pin]
            record['final_source_GDS_sha256']=core['BGR_source_GDS_sha256']
            record['final_core_native_pin_probe']=final
            record['old_LEF_window_status']='historical r2 abstraction; final native pin probe supersedes connectivity identity'
            record['current_status']='available conditional fixed-current nominal injection, not worst-case envelope'
            record['current_A']=abs(bgr_i[pin]);record['current_ledger_sha256']=sha(a.bgr_ledger)
        macro={'i_core.u_trip':'TRIP','i_core.u_gate':'GATE'}.get(instance)
        if (macro,net)in currents:
            record['current_status']='available historical representative simulated waveform; final/PVT envelope not qualified'
            record['current_windows']=currents[macro,net]['windows']
            record['current_provenance']=dict(summary_sha256=sha(legacy_path),waveform_sha256=legacy['waveform_sha256'],
                                             temperature_C=legacy['temperature_C'],probe=currents[macro,net]['probe'])
        if instance=='i_core.u_sense':
            record['feed_status']='independent source-held overlay implemented; separate committed evidence'
            record['exploratory_branch_envelope_A']=.002
        if instance=='i_core.u_osc' and pin=='VDD':
            record['current_status']='available baseline OSC representative simulated mean/peak; RMS/full PVT not run'
            record['current_window']=osc['windows']['steady']['supplies']['i(vdd)']
            record['current_provenance']=dict(summary_sha256=sha(osc_path),vector_sha256=osc['vector_sha256'],
                                             source_sha256=sha(osc_run/'osc.spice'),scope=osc['scope'])
        if instance=='i_core.u_t2f':
            record['historical_combined_current_not_individual']=dict(summary_sha256=sha(t2f_path),scope=t2f['scope'],
                maximum_vdda_sampled_A=max(w['vdda_max_sampled_A']for c in t2f['cases']for w in c['windows'].values()),
                maximum_vdd_sampled_A=max(w['vdd_max_sampled_A']for c in t2f['cases']for w in c['windows'].values()))
        selected.append(record)
    expected={('i_core.u_bgr','vdd'):'VDDA',('i_core.u_trip','IOVDD'):'VDDA',('i_core.u_trip','VDD'):'VDD',
              ('i_core.u_t2f','vdd'):'VDDA',('i_core.u_t2f','vdd12'):'VDD',('i_core.u_osc','VDD'):'VDD'}
    for key,net in expected.items():assert logical[key]==net and sources[key[0]]['pins'][key[1]]==net
    result=dict(status='passed source-bound remaining supply inventory; route/current qualification not run',
                script_sha256=sha(Path(__file__)),source_PNL_sha256=sha(pnl),prepared_sha256=sha(a.prepared/'analysis.json'),
                ODB_sha256=odb['ODB_sha256'],observations_sha256=sha(a.observations),
                final_core_GDS_sha256=core['GDS_sha256'],final_BGR_source_GDS_sha256=core['BGR_source_GDS_sha256'],
                separate_clock_receiver_current=dict(source_sha256=sha(osc_path),scope=osc['scope'],
                    current_window=osc['windows']['steady']['supplies']['i(vddclk)'],
                    allocation='Separate immediate receiver VDD fixture, not OSC macro current; full digital load not covered'),
                exact_domain_mapping=[dict(instance=k[0],pin=k[1],net=n)for k,n in expected.items()],
                all_recorded_power_terminal_counts=dict(counts),selected_macro_pad_terminals=len(selected),
                other_terminals_counted_but_not_reaudited=dict(excluded),terminals=selected,
                inherited_observation_failure=obs['status'],inherited_nonpower_alias_merges=obs['unexpected_net_merges'],
                geometry_mutated=False,not_run=['remaining supply routing/clearance','actual internal supply current partition',
                                              'full PVT current envelope/current sharing/EM','root final PDN merge','fullchip LVS/PEX/adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('terminals','inherited_nonpower_alias_merges')},indent=2))


if __name__=='__main__':main()
