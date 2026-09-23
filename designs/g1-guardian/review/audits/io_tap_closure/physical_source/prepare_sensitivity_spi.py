#!/usr/bin/env python3
"""Two explicitly conditional tap-R views, not validated physical bounds."""
import argparse
import collections
from decimal import Decimal,localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(HERE.parents[1]/'fullchip_reference_closure/physical_lvs/explicit_vss_interface'))
from prepare import parse,flattened,TOP
PREFIX='G1_VSS_DERIVATIVE__'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--parent-spi',type=Path,required=True)
    ap.add_argument('--parent-summary',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    proof=bulk/'io-physical-ap-source-20260923-r2/summary.json'
    physical=proof.parent/'physical_taps.cdl'
    j=json.loads(proof.read_text());pj=json.loads(a.parent_summary.read_text())
    raw=a.parent_spi.read_bytes()
    assert digest(raw)==pj['candidate_sha256']=='c46e32249a04ed75d25d5f2b4f0b79304c25f7d85ce7628ee5a65b1734f43256'
    assert sha(physical)==j['source_sha256']=='796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf'
    assert pj['status'].startswith('passed') and j['status'].startswith('passed')
    lines,cells=parse(raw);_,full=parse(physical.read_bytes())
    affected={PREFIX+n for n in pj['affected_cells']};assert len(affected)==30
    assert affected<=set(cells) and affected<=set(full)
    composed=dict(full);composed.update({n:cells[n] for n in affected})
    before,reached=flattened(composed)
    assert len([r for r in before.values() if r['model'] in ('PTAP1','NTAP1')])==386
    # Match original CDL-to-SPI instance identities using the already verified
    # ordered-terminal mapping, not coincidental names (IOVdd swaps XR0/XR1).
    cross={(PREFIX+r['cell'],r['cdl_instance'].upper()):r for r in pj['complete_local_crossview_mapping']}
    declared={};rows=[]
    for row in j['changed_records']:
        key=(row['cell'],row['instance'].upper());link=cross[key]
        assert link['model'].upper()=='PTAP1'
        inst,=[i for i in cells[key[0]]['instances'] if i['name'].upper()==link['spice_instance'].upper()]
        target,=[i for i in full[key[0]]['instances'] if i['name'].upper()==key[1]]
        assert [n.upper() for n in inst['nodes']]==[n.upper() for n in target['nodes']]
        assert inst['model'].upper()==target['model'].upper()=='PTAP1'
        assert len(inst['record']['indices'])==1
        index,=inst['record']['indices']
        assert index not in declared
        old=lines[index];token,=[p for p in inst['params'] if p.upper().startswith('R=')]
        assert token.split('=',1)[1]==row['original_SPI_R']
        with localcontext() as ctx:
            ctx.prec=50
            area=Decimal(row['A_um2']);perimeter=Decimal(row['P_um'])
            values={k:format(Decimal(980)/(area+k*perimeter),'.18E') for k in (1,2)}
        declared[index]=dict(row=row,inst=inst,values=values,old=old)
        rows.append(dict(cell=key[0],cdl_instance=key[1],SPI_instance=inst['name'],
            ordered_terminals=inst['nodes'],old_R=token,source_line=index+1,
            A_um2=str(area),P_um=str(perimeter),R_ohm={str(k):v for k,v in values.items()},
            shape_classes=sorted({p['classification'] for p in row['owned_geometry']['polygons']}),
            geometry_owner=key,parameter_scope='only explicit instance R; no model card edit'))
    assert len(declared)==42
    # Record the complete actual fullchip occurrence mapping to local records.
    bylocal={(r['cell'],r['SPI_instance'].upper()):r for r in rows}
    occurrence=[]
    def walk(name,path,stack):
        assert name not in stack
        for inst in composed[name]['instances']:
            child=inst['model'].upper();ipath=path+'/'+inst['name'].upper()
            if child in composed:walk(child,ipath,stack+[name])
            elif child in ('PTAP1','NTAP1'):
                row=bylocal[(name,inst['name'].upper())]
                occurrence.append(dict(path=ipath,local_cell=name,SPI_instance=inst['name'],
                    CDL_instance=row['cdl_instance'],nodes=before[ipath]['nodes'],
                    A_um2=row['A_um2'],P_um=row['P_um'],R_ohm=row['R_ohm']))
    walk(TOP,TOP,[]);assert len(occurrence)==386 and len({r['path'] for r in occurrence})==386
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    results=[]
    for k in (1,2):
        changed=list(lines);edits=[]
        for index,d in sorted(declared.items()):
            new,n=re.subn(r'(?i)\bR=\S+','R='+d['values'][k],d['old']);assert n==1
            changed[index]=new;edits.append(dict(line=index+1,before=d['old'],after=new))
        candidate=''.join(changed).encode();_,cc=parse(candidate)
        combined=dict(full);combined.update({n:cc[n] for n in affected});after,_=flattened(combined)
        expected={p:dict(r,params=list(r['params'])) for p,r in before.items()}
        for row in occurrence:
            params=expected[row['path']]['params']
            indexes=[i for i,v in enumerate(params) if v.upper().startswith('R=')];assert len(indexes)==1
            params[indexes[0]]='R='+row['R_ohm'][str(k)]
        assert after==expected and set(after)==set(before)
        restored=candidate.decode().splitlines(True)
        for e in edits:
            assert restored[e['line']-1]==e['after'];restored[e['line']-1]=e['before']
        assert ''.join(restored).encode()==raw
        assert all(cells[n]['pins']==cc[n]['pins'] for n in cells)
        wrong={p:dict(r,params=list(r['params'])) for p,r in after.items()}
        first=occurrence[0]['path'];wrong[first]['params'].append('G1_UNAUTHORIZED=1')
        missing=dict(after);missing.pop(first)
        bulkwrong={p:dict(r,nodes=list(r['nodes'])) for p,r in after.items()};bulkwrong[first]['nodes'][1]='IOVSS'
        omitted_edit={p:dict(r,params=list(r['params'])) for p,r in after.items()};omitted_edit[first]=before[first]
        controls=dict(positive_exact_graph=after==expected,wrong_parameter_rejected=wrong!=expected,
            omitted_device_rejected=missing!=expected,wrong_bulk_rejected=bulkwrong!=expected,
            omitted_R_edit_rejected=omitted_edit!=expected,reverse_bytes_exact=True)
        assert all(controls.values())
        dest=a.output/('physical_AP_conditional_P%d.spi'%k);dest.write_bytes(candidate)
        results.append(dict(perimeter_factor=k,file=dest.name,sha256=sha(dest),local_edits=edits,
            expanded_tap_edits=386,controls=controls,all_non_tap_params_nodes_models_held=True,
            original_library_prefix_held=candidate[:raw.index(b'\n* Design-local explicit substrate')]==raw[:raw.index(b'\n* Design-local explicit substrate')]))
    report=dict(status='passed exact conditional electrical derivatives; simulation and physical applicability not run',
        inputs={str(p):sha(p) for p in (a.parent_spi,a.parent_summary,proof,physical,Path(__file__))},
        parent_SPI_sha256=digest(raw),physical_CDL_sha256=sha(physical),local_mapping=rows,
        fullchip386_occurrence_mapping=occurrence,variants=results,
        model_cards='unchanged',signal_bulk_pin_interfaces='unchanged explicit VSS',
        classification='conditional arithmetic sensitivities; neither a validated physical bound nor qualified arbitrary-shape substrate spreading',
        not_run=['Power sequencing','ESD qualification','Physical R applicability','Adoption'])
    (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
