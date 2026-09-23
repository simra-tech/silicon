#!/usr/bin/env python3
"""Run unchanged stock main/maximal DRC for one hash-bound derived core."""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import pya
from run_core_maximal_only import PDK, DRC, sha, switches


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--gds-name',required=True)
    p.add_argument('--topcell',default='placed_core_NOT_CONNECTED_FULLCHIP')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',choices=['main','maximal'])
    p.add_argument('--only',choices=['main','maximal'])
    p.add_argument('--main-watchdog',type=int,default=180)
    p.add_argument('--maximal-watchdog',type=int,default=600)
    a=p.parse_args()
    assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert a.main_watchdog==120 and a.maximal_watchdog==120
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert Path(a.gds_name).name==a.gds_name
    source=a.candidate/a.gds_name
    metadata=json.loads((a.candidate/'analysis.json').read_text())
    assert metadata['status'].startswith('passed') and sha(source)==metadata['GDS_sha256']
    layout=pya.Layout();layout.read(str(source))
    assert layout.cell(a.topcell) is not None, 'Requested DRC topcell absent from hash-bound GDS'
    sys.path.insert(0,str(DRC))
    spec=importlib.util.spec_from_file_location('pinned_stock_drc',DRC/'run_drc.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sw=switches(module,source,a.topcell)
    if a.execute:
        deck=DRC/'ihp-sg13g2.drc' if a.execute=='main' else DRC/'rule_decks/sg13g2_maximal.drc'
        table='main' if a.execute=='main' else 'sg13g2_maximal'
        module.run_check(deck,[table],str(source),a.output/'reports',sw)
        return
    assert not a.output.exists()
    (a.output/'reports').mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    rules={str(q.relative_to(PDK)):sha(q) for q in (PDK/'libs.tech/klayout/tech').rglob('*')if q.is_file()}
    result=dict(status='running',GDS_sha256=sha(source),candidate_metadata_sha256=sha(a.candidate/'analysis.json'),
                script_sha256=sha(Path(__file__)),switch_helper_sha256=sha(Path(__file__).with_name('run_core_maximal_only.py')),
                stock_rule_hashes=rules,switches={k:str(v)for k,v in sw.items()},decks=[],
                not_run=['density/fill','antenna','connected fullchip LVS/PEX/currentIR/EM','electrical adoption'])
    receipt=a.output/'summary.json';receipt.write_text(json.dumps(result,indent=2)+'\n')
    planned=[(kind,bound)for kind,bound in [('main',a.main_watchdog),('maximal',a.maximal_watchdog)]if not a.only or kind==a.only]
    if a.only:
        result['not_run'].append('other stock deck in this independent invocation')
    for kind,bound in planned:
        command=['timeout','--kill-after=5',str(bound),'python3',str(Path(__file__).resolve())]+sys.argv[1:]+['--execute',kind]
        start=time.monotonic()
        with (a.output/(kind+'.log')).open('x')as log:
            run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        reports=[]
        suffix='_main.lyrdb'if kind=='main'else'_sg13g2_maximal.lyrdb'
        for q in (a.output/'reports').glob('*'+suffix):
            categories=collections.Counter(i.findtext('category')for i in ET.parse(q).findall('.//items/item'))
            reports.append(dict(path=str(q.relative_to(a.output)),sha256=sha(q),markers=sum(categories.values()),categories=dict(categories)))
        passed=run.returncode==0 and len(reports)==1 and reports[0]['markers']==0
        result['decks'].append(dict(name=kind,returncode=run.returncode,wall_s=time.monotonic()-start,
                                   command=command,watchdog_s=bound,reports=reports,status='passed'if passed else'failed'))
        receipt.write_text(json.dumps(result,indent=2)+'\n')
        if not passed:
            break
    unchanged=sha(source)==result['GDS_sha256'] and all(sha(PDK/q)==v for q,v in rules.items())
    passed=unchanged and len(result['decks'])==len(planned) and all(d['status']=='passed'for d in result['decks'])
    result.update(status=('passed scoped '+(a.only or 'main and maximal')+' DRC')if passed else'failed scoped candidate DRC',
                  inputs_rules_unchanged=unchanged)
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='stock_rule_hashes'},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
