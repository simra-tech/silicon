#!/usr/bin/env python3
"""Compare unchanged stock-written MOS junction attribution to frozen source defaults."""
import argparse,hashlib,json,re
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(value):
    match=re.fullmatch(r'([-+\d.eE]+)([up]?)',value);assert match,value
    return float(match.group(1))*{'':1,'u':1e-6,'p':1e-12}[match.group(2)]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prototype',type=Path,required=True);p.add_argument('--stock',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();m=json.loads((a.prototype/'manifest.json').read_text());stock=json.loads((a.stock/'summary.json').read_text());assert stock['status']=='passed'
    rows=[]
    for cell in m['cells']:
        name=cell['cell'];path=a.stock/(name+'-lvs/native_prototypes_extracted.cir');text=path.read_text();lines=[]
        for line in text.splitlines():
            if line.startswith('+'):lines[-1]+=' '+line[1:].strip()
            else:lines.append(line)
        devices=[line for line in lines if line.startswith('M')];assert len(devices)==(2 if name.startswith('pair') else 1)
        expected=cell['expected_model_junction']
        for line in devices:
            words=line.split();d,g,s,b=words[1:5];params={k.lower():v for k,v in re.findall(r'(\w+)=([^\s]+)',line)}
            target_s='tail' if name.startswith('pair') else ('vss' if name=='bias_n2' else 'vdd')
            target_d=('fn' if g=='inn' else 'fp') if name.startswith('pair') else 'd'
            nodes={s:{'area_um2':number(params['as'])*1e12,'perimeter_um':number(params['ps'])*1e6},d:{'area_um2':number(params['ad'])*1e12,'perimeter_um':number(params['pd'])*1e6}}
            assert set(nodes)=={target_s,target_d}
            actual=dict(as_um2=nodes[target_s]['area_um2'],ad_um2=nodes[target_d]['area_um2'],ps_um=nodes[target_s]['perimeter_um'],pd_um=nodes[target_d]['perimeter_um'])
            delta={k:actual[k]-expected[k] for k in actual}
            rows.append(dict(cell=name,gate=g,source_net=target_s,drain_net=target_d,stock_line=line,extracted_file_sha256=sha(path),
                             actual_stock_node_junction=actual,source_default_node_junction=expected,delta_stock_minus_source_default=delta,
                             status='passed' if all(abs(v)<1e-8 for v in delta.values()) else 'failed',
                             aggregate_area_delta_um2=delta['as_um2']+delta['ad_um2'],aggregate_perimeter_delta_um=delta['ps_um']+delta['pd_um']))
    controls=[]
    for ng in (16,64):
        for gate in ('inn','inp'):
            left=next(r for r in rows if r['cell']=='pair_split'+str(ng) and r['gate']==gate)
            right=next(r for r in rows if r['cell']=='pair_control'+str(ng) and r['gate']==gate)
            controls.append(dict(ng=ng,gate=gate,stock_parameters_identical=left['actual_stock_node_junction']==right['actual_stock_node_junction']))
    assert all(r['stock_parameters_identical'] for r in controls)
    result={'status':'failed stock-written per-node junction fidelity despite strict LVS match','prototype_manifest_sha256':sha(a.prototype/'manifest.json'),
            'stock_summary_sha256':sha(a.stock/'summary.json'),'script_sha256':sha(Path(__file__)),'rows':rows,'split_control_comparisons':controls,
            'scope':'Stock text SPICE attribution only, correctly accounting D/S reversal. Independent-array control has the same averaged A/P, so this is not evidence against split-specific geometry. No extracted-to-golden or deck/model edits. Device geometry and topology checks remain independently passed; actual PSP model/junction applicability is not established by strict LVS.',
            'not_run':['modified extraction or golden reference','electrical significance of per-node attribution','routed SENSE macro fit','new broad PEX']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'devices':len(rows),'all_split_controls_identical':all(r['stock_parameters_identical'] for r in controls)},indent=2))
if __name__=='__main__':main()
