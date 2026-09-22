#!/usr/bin/env python3
"""Read-only saved metadata: distinguish OP scale identity from physical-vector parity."""
import argparse
import gzip
import hashlib
import json
import math
import re
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def wave(path):
    if path.exists():return path.read_text()
    with gzip.open(str(path)+'.gz','rt') as stream:return stream.read()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('run','reference','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    state=json.loads((a.run/'run.json').read_text());assert state['status']=='completed' and state['returncode']==0
    prior=json.loads((a.run/'summary.json').read_text())
    assert prior['status']=='failed' and prior['complete_original_parameters_and_legacy_exact']
    raw=(a.run/'all_op.raw').read_text()
    assert 'No. Points: 1\n' in raw and 'Flags: real\n' in raw
    head,tail=raw.split('Values:\n',1)
    varrows=[row.split() for row in head.split('Variables:\n',1)[1].splitlines() if row.strip()]
    valrows=[row.split() for row in tail.splitlines() if row.strip()]
    assert len(varrows)==len(valrows) and valrows[0][0]=='0'
    values={row[1]:float(valrows[i][-1]) for i,row in enumerate(varrows)}
    assert len(values)==len(varrows) and all(math.isfinite(v) for v in values.values())
    waves=[]
    for name in ('op0.dat','currents.dat','monitor_voltages.dat'):
        old=[row.split() for row in wave(a.reference/name).splitlines() if row.strip()]
        new=[row.split() for row in wave(a.run/name).splitlines() if row.strip()]
        assert len(old)==len(new)==2
        assert old[0][0]=='clk' and new[0][0]=='vdda'
        assert old[0][1:]==new[0][1:] and old[1][1:]==new[1][1:]
        assert float(old[1][0])==values['v(clk)']==0 and float(new[1][0])==values['v(vdda)']==3.3
        waves.append(dict(file=name,original_scale='clk',new_scale='vdda',original_scale_value=0.,new_scale_value=3.3,
            nonscale_header_tokens_exact=True,nonscale_value_tokens_exact=True,physical_vectors=len(old[1])-1,
            full_original_byte_comparison='failed and retained',scale_reason='save all changes default OP plot scale'))
    log=(a.run/'run.log').read_text();rows=[]
    for macro in ('xota','xbuf','xref'):
        for device in ('xm1','xm2'):
            name='n.xs.'+macro+'.'+device+'.nsg13_hv_pmos'
            section,=re.findall('^DEVICE_BEGIN_'+re.escape(name)+r'\n(.*?)^DEVICE_END_'+re.escape(name)+'$',log,re.M|re.S)
            fields={m[1]:float(m[2]) for m in re.finditer(r'^\s+(\w+)\s+([-+0-9.eE]+)\s*$',section,re.M)}
            nodes={n:values['v('+name+'#'+n+')'] for n in ('bi','bp','bs','si','di','gp')}
            assert fields['ctype']==-1
            # Pinned PMOS branch evaluates Vjun_s=V(SI,BS).
            source_voltage=values['v(xs.'+macro+'.tail)']
            mapping_ok=abs(nodes['si']-source_voltage)<1e-9
            rows.append(dict(device=name,raw_named_node_candidates_V=nodes,
                external_source_voltage_V=source_voltage,
                zero_RSE_SI_equals_external_source=mapping_ok,
                candidate_SI_minus_BS_V=nodes['si']-nodes['bs'],
                candidate_SI_minus_BP_V=nodes['si']-nodes['bp'],
                metadata_limited_precision={k:fields[k] for k in ('vsb','ijs','cjs','cjsbot','cjsgat','cjssti','weff','lp_rjuns')},
                actual_junction_charge='not exposed in inspected supported output fields; not run',
                raw_node_format='15-digit ASCII raw output; no extra precision claimed'))
    pairs=[]
    for macro in ('xota','xbuf','xref'):
        pair=[r for r in rows if '.'+macro+'.' in r['device']]
        pairs.append(dict(macro=macro,named_node_mapping_status='passed' if all(r['zero_RSE_SI_equals_external_source'] for r in pair) else 'failed',
                          actual_source_junction_biases='not qualified: raw labels require physical mapping'))
    mapping_ok=all(r['zero_RSE_SI_equals_external_source'] for r in rows)
    result=dict(status='passed saved physical-vector parity but failed internal-node identity' if not mapping_ok else 'passed internal-node source identity screen; full mapping still required',
        full_original_byte_gate='failed retained; this separate audit changes no acceptance tolerance',
        run_summary_sha256=sha(a.run/'summary.json'),raw_sha256=sha(a.run/'all_op.raw'),
        script_sha256=sha(Path(__file__)),complete_original23078_parameters_exact=True,
        raw_variable_count=len(values),wave_scale_controls=waves,devices=rows,pairs=pairs,
        original_readonly_r1_interpretation='superseded: candidate raw node names were not validated against zero source resistance; raw values retained',
        actual_junction_charge='not run',hot_control='not run',equal_bias_control='not run',negative_bias_control='not run',
        shared_PSP_applicability='not qualified',scope='Read-only saved numerical result, no rerun or data rewrite')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='devices'},indent=2))


if __name__=='__main__':main()
