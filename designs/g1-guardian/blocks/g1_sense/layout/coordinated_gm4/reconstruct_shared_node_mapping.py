#!/usr/bin/env python3
"""Reconstruct output labels from pinned descriptors and zero-resistance collapse controls."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def collapse(count,pairs,flags):
    mapping=list(range(count));remaining=count;ground=2**32-1
    for pair,flag in zip(pairs,flags):
        if not flag:continue
        src,dst=pair['from_index'],pair['to_index']
        if mapping[src]<4 and (dst==ground or mapping[dst]<4 or mapping[dst]==ground):continue
        if dst!=ground and mapping[src]<mapping[dst]:src,dst=dst,src
        src=mapping[src];dst=mapping[dst] if dst!=ground else ground
        mapping=[dst if v==src else v-1 if v>src and v!=ground else v for v in mapping]
        remaining-=1
    return mapping,remaining


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','descriptor','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    run_summary=json.loads((a.run/'summary.json').read_text())
    descriptor=json.loads(a.descriptor.read_text())['descriptors'][0]
    assert descriptor['descriptor_name']=='PSP103VA'
    names=descriptor['nodes'];pairs=descriptor['collapsible']
    assert names==['D','G','S','B','NOI','GP','SI','DI','BP','BI','BS','BD','flow(NOII)']
    assert collapse(len(names),pairs,[False]*7)==(list(range(13)),13)
    assert collapse(13,pairs,[False,True,True,False,False,False,False])==([0,1,2,3,4,5,2,0,6,7,8,9,10],11)
    raw=(a.run/'all_op.raw').read_text();head,tail=raw.split('Values:\n')
    vr=[r.split() for r in head.split('Variables:\n')[1].splitlines() if r.strip()]
    vl=[r.split() for r in tail.splitlines() if r.strip()]
    assert len(vr)==len(vl) and 'No. Points: 1\n' in head
    values={r[1]:float(vl[i][-1]) for i,r in enumerate(vr)}
    assert all(math.isfinite(v) for v in values.values())
    log=(a.run/'run.log').read_text();rows=[]
    for macro in ('xota','xbuf','xref'):
        for device in ('xm1','xm2'):
            name='n.xs.'+macro+'.'+device+'.nsg13_hv_pmos'
            section,=re.findall('^DEVICE_BEGIN_'+re.escape(name)+r'\n(.*?)^DEVICE_END_'+re.escape(name)+'$',log,re.M|re.S)
            fields={m[1]:float(m[2]) for m in re.finditer(r'^\s+(\w+)\s+([-+0-9.eE]+)\s*$',section,re.M)}
            resistors=[fields['lp_'+key] for key in ('rg','rse','rde','rbulk','rjuns','rjund','rwell')]
            assert all(x>=0 for x in resistors)
            flags=[x==0 for x in resistors]
            assert flags==[False,True,True,False,False,False,False]
            mapping,count=collapse(len(names),pairs,flags)
            # External terminal identities come from immutable canonical XM1/XM2 topology.
            ext={'D':'xs.'+macro+('.fn' if device=='xm1' else '.fp'),
                 'G':{'xota':('xs.vn','xs.vp'),'xbuf':('vped','xs.vped_ref'),
                      'xref':('vref_buf','vref')}[macro][int(device[-1])-1],
                 'S':'xs.'+macro+'.tail','B':'xs.vdd_'+{'xota':'ota','xbuf':'buf','xref':'ref'}[macro]+'_monitor'}
            physical={};bindings={}
            for i,node in enumerate(names):
                j=mapping[i];label='v('+ext[names[j]]+')' if j<4 else 'v('+name+'#'+names[j].lower()+')'
                assert label in values,label
                physical[node]=values[label];bindings[node]=label
            assert physical['S']==physical['SI'] and physical['D']==physical['DI']
            assert fields['ctype']==-1 and fields['sdint']==1
            controls={'vsb':physical['BP']-physical['SI'],
                      'vds':physical['SI']-physical['DI'],
                      'vgs':physical['SI']-physical['GP']}
            # Native show prints six significant digits; this tests mapping, not numerical equivalence.
            errors={k:abs(v-fields[k]) for k,v in controls.items()}
            assert all(error<=5e-6 for error in errors.values()),errors
            rows.append(dict(device=name,resistor_metadata_6digit_ohm=resistors,collapse_flags=flags,
                             compact_node_count=count,physical_to_saved_vector=bindings,
                             mapped_voltage_V=physical,channel_identity_absolute_errors_V=errors,
                             source_junction_bias_V=physical['SI']-physical['BS'],
                             source_capacitance_6digit_F=fields['cjs'],
                             source_current_6digit_A=fields['ijs'],
                             charge='not exposed; not run'))
    pairrows=[]
    for macro in ('xota','xbuf','xref'):
        pair=[r for r in rows if '.'+macro+'.' in r['device']]
        pairrows.append(dict(macro=macro,junction_biases_V=[r['source_junction_bias_V'] for r in pair],
                             difference_V=pair[0]['source_junction_bias_V']-pair[1]['source_junction_bias_V']))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.descriptor,a.run/'all_op.raw',a.run/'run.log',Path(__file__))}
    result=dict(status='passed source-derived collapse mapping and independent channel-voltage controls',
                source='https://raw.githubusercontent.com/imr/ngspice/ngspice-46/src/osdi/osdisetup.c',
                hashes=hashes,devices=rows,pairs=pairrows,
                full_original_byte_gate='passed' if all(run_summary.get('original_wave_exact',{}).values()) and len(run_summary.get('original_wave_exact',{}))==3 else 'failed retained',
                original_room_r1_byte_gate='failed retained',raw_naive_label_identity='failed retained',
                direct_live_instance_mapping='not observed; source-derived reconstruction',
                temperature_C=float(re.search(r'^set temp=([-+0-9.]+)$',(a.run/'probe.cir').read_text(),re.M)[1]),
                junction_charge='not run',other_conditions='not evaluated by this result',
                equal_bias_control='not evaluated by this result',negative_bias_control='not evaluated by this result',
                applicability='not qualified; one representative OP only')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(pairrows,indent=2))


if __name__=='__main__':main()
