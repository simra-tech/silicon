#!/usr/bin/env python3
"""Exact source-deck controls and repeat inserted-zero-source cases for five nonexact corners."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[4]
SENSE=ROOT/'designs/g1-guardian/blocks/g1_sense/sim'
BASE=SENSE/'qualification/corners-20260921-a'
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--shards',nargs='+',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert len(os.sched_getaffinity(0))==1
a.output.mkdir(exist_ok=False);out=a.output.resolve()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
shutil.copyfile(Path(__file__),out/Path(__file__).name)
baseline={row['name']:row for row in json.loads((BASE/'summary.json').read_text())}
cases=[(path.resolve(),row) for path in a.shards for row in json.loads((path/'summary.json').read_text()) if row['scale']==0 and not row['baseline_printed_vectors_exact']]
assert len(cases)==5
(out/'plan.json').write_text(json.dumps({'status':'prospective exact-control investigation, no acceptance tolerance change',
    'corners':[row['name'] for path,row in cases],'comparisons':['exact unmodified source deck versus historical baseline','repeat inserted-zero-source deck versus its completed PVT result','unmodified source versus inserted-zero-source'],
    'timeout_s_per_leaf':120,'gain_criterion_unchanged':[19.9,20.1],
    'source_netlist_sha256':sha(BASE/'sense_substrate_tied.spice'),'baseline_summary_sha256':sha(BASE/'summary.json'),
    'equivalence_with_nonzero_tolerance':'not run; no tolerance defined by this diagnostic'},indent=2)+'\n')
results=[]
for shard,old in cases:
    name=old['name'];row={'name':name,'original_PVT_max_abs_delta':old['baseline_printed_vector_max_abs_delta_by_column'],'runs':{}}
    for kind,deck,cwd,reference in (
        ('unmodified_source',BASE/(name+'.cir'),SENSE,baseline[name]['rows']),
        ('inserted_zero_source_repeat',shard/name/'r0/fixture.cir',shard/name/'r0',old['rows'])):
        leaf=out/name/kind;leaf.mkdir(parents=True)
        with (leaf/'tool.log').open('x') as stream:
            state=run_bounded(['ngspice','-b',str(deck)],stream,leaf/'run.json',120,cwd=cwd,
                env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),metadata={'deck_sha256':sha(deck),'source_deck_unchanged':True},interval_s=1)
        log=(leaf/'tool.log').read_text();data={};duplicates=[]
        for line in log.splitlines():
            if line.startswith('ROW '):
                tokens=line.split()
                if tokens[1] in data:duplicates.append(tokens[1])
                data[tokens[1]]=list(map(float,tokens[2:]))
        errors=[line for line in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',line)]
        complete=state['status']=='completed' and state['returncode']==0 and not errors and not duplicates and set(data)==set(reference) and 'QUALIFICATION_END' in log and all(len(values)==(7 if kind=='unmodified_source' else 11) and all(map(math.isfinite,values)) for values in data.values())
        result={'status':'passed' if complete else 'failed','rows':data,'errors':errors,'duplicates':duplicates,'deck_sha256':sha(deck)}
        if complete:
            delta=[max(abs(data[key][column]-reference[key][column]) for key in data) for column in range(7)]
            result.update(exact_seven_vector_parity=all(value==0 for value in delta),max_abs_delta_by_column=delta)
        row['runs'][kind]=result
        print(name,kind,result['status'],result.get('exact_seven_vector_parity'),flush=True)
    if all(item['status']=='passed' for item in row['runs'].values()):
        left=row['runs']['unmodified_source']['rows'];right=row['runs']['inserted_zero_source_repeat']['rows']
        row['unmodified_vs_zero_source_max_abs_delta_by_column']=[max(abs(left[key][column]-right[key][column]) for key in left) for column in range(7)]
    results.append(row)
    (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
