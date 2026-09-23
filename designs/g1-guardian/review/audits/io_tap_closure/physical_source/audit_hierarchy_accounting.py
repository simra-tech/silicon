#!/usr/bin/env python3
"""Trace direct-active source ownership and compare—not fit—saved totals."""
import argparse
import collections
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'fullchip_reference_closure/physical_lvs/explicit_vss_interface'))
from prepare import parse,flattened,TOP


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    source=bulk/'fullchip-current-digital-reference-20260923-r2/current_digital_explicit_vss.cdl'
    old=bulk/'io-tap-physical-ownership-20260923-r1/analysis.json'
    direct=bulk/'io-direct-ownership-20260923-r1/analysis.json'
    assert sha(source)=='febefea51c08ee2432aac512b251aee990f4812dbaee59d9acdc879b18429e74'
    proofs=[json.loads(p.read_text()) for p in (old,direct)]
    assert proofs[1]['status']=='passed per-tap local native ownership' and not proofs[1]['failures']
    _,cells=parse(source.read_bytes());flat,reached=flattened(cells)
    databases=[{(row['cell'].upper(),tap['source']['instance'].upper()):tap for row in proof['cells'] for tap in row['taps']} for proof in proofs]
    rows=[]
    def walk(cell,path):
        for inst in cells[cell]['instances']:
            ipath=path+'/'+inst['name'].upper();model=inst['model'].upper()
            if model in cells:
                walk(model,ipath)
            elif model in ('PTAP1','NTAP1'):
                key=(cell.removeprefix('G1_VSS_DERIVATIVE__'),inst['name'].upper())
                vals=[db[key] for db in databases]
                rows.append(dict(path=ipath,cell=cell,instance=inst['name'],nodes=flat[ipath]['nodes'],
                    original_subtracted_geometry=vals[0],direct_active_geometry=vals[1]))
    walk(TOP,TOP)
    assert len(rows)==386
    totals=[]
    for name in ('original_subtracted_geometry','direct_active_geometry'):
        sums=collections.defaultdict(lambda:[Decimal(0),Decimal(0),0])
        for row in rows:
            val=row[name];key=tuple(row['nodes'])
            sums[key][0]+=Decimal(val['area_um2']);sums[key][1]+=Decimal(val['perimeter_um']);sums[key][2]+=1
        totals.append(dict(method=name,totals=[dict(nodes=list(k),A_um2=str(v[0]),P_um=str(v[1]),count=v[2]) for k,v in sums.items()]))
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed source-traced accounting diagnostic; not adopted',
        inputs={str(p):sha(p) for p in (source,old,direct,Path(__file__).resolve())},
        occurrences=rows,totals=totals,affected_instances=sum(r['original_subtracted_geometry']['area_um2']!=r['direct_active_geometry']['area_um2'] for r in rows),
        source_or_geometry_mutation='not applicable; none',comparison_acceptance='not run',
        physical_overlap_ownership='not run; direct parent shapes can overlap child shapes and need explicit independent partition proof',
        electrical_R='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(totals,indent=2))


if __name__=='__main__':main()
