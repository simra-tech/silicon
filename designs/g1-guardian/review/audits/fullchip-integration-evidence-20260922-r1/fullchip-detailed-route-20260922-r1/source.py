#!/usr/bin/env python3
"""Bounded one-thread detailed signal-route candidate; preserve all instances."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
from check_closed_macro_odb import sha,quote
from check_fullchip_def_odb import observation,OPENROAD


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--global-route',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    parent=json.loads((a.global_route/'analysis.json').read_text())
    assert parent['status']=='passed isolated strict global-route guide probe'
    for q,value in parent['inputs'].items():
        assert sha(Path(q))==value,q
    odb=a.global_route/'global.odb';guide=a.global_route/'global.guide'
    assert sha(odb)==parent['global_ODB_sha256'] and sha(guide)==parent['guide_sha256']
    # Reuse only exact qualified library/constraint setup; the derived database
    # already holds every audited native obstacle. No repeated obstruction add.
    original=(a.global_route/'route.tcl').read_text()
    prefix=original.split('\nsource ',1)[0]
    assert prefix.startswith('set_thread_count 1\n') and prefix.count('read_db ')==1
    prefix=re.sub(r'^read_db .*$', 'read_db '+quote(odb),prefix,flags=re.M)
    assert 'global_route' not in prefix and 'dbObstruction' not in prefix
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    output_drc=a.output/'detailed.drc'
    lines=[prefix,'read_guides '+quote(guide),
           'detailed_route -droute_end_iter 64 -or_seed 42 -verbose 1 -output_drc '+quote(output_drc),
           'write_db '+quote(a.output/'detailed.odb'),
           'write_def '+quote(a.output/'detailed.def')]
    lines+=observation(a.output/'after.tsv')
    script=a.output/'route.tcl';script.write_text('\n'.join(lines)+'\n')
    command=['timeout','--kill-after=5','600',str(OPENROAD),'-exit',str(script)]
    result=dict(status='running',global_ODB_sha256=sha(odb),guide_sha256=sha(guide),
                parent_metadata_sha256=sha(a.global_route/'analysis.json'),script_sha256=sha(Path(__file__)),
                original_setup_sha256=sha(a.global_route/'route.tcl'),OpenROAD_sha256=sha(OPENROAD),
                seed=42,threads=1,command=command,
                not_run=['new full PDN/feeds','native route GDS streamout and polygon proof','stock fullchip DRC/LVS/PEX/density/antenna/STA/currentIR','electrical adoption'])
    receipt=a.output/'analysis.json';receipt.write_text(json.dumps(result,indent=2)+'\n')
    start=time.monotonic()
    with(a.output/'route.log').open('x')as log:
        run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result.update(returncode=run.returncode,wall_s=time.monotonic()-start)
    if(a.output/'after.tsv').exists():
        assert sorted((a.output/'after.tsv').read_text().splitlines())==sorted((a.global_route/'after.tsv').read_text().splitlines())
        result['instances_and_terminal_connectivity_held']='passed'
    passed=run.returncode==0 and output_drc.is_file() and not output_drc.read_text().strip()
    result['status']='passed isolated detailed-route candidate with zero router markers'if passed else'failed isolated detailed-route candidate'
    if output_drc.exists():
        result.update(router_DRC_sha256=sha(output_drc),router_DRC_bytes=output_drc.stat().st_size,
                      router_markers=len(re.findall(r'^violation type:',output_drc.read_text(),re.M)))
    for name in ['detailed.odb','detailed.def']:
        if(a.output/name).exists():result[name+'_sha256']=sha(a.output/name)
    assert sha(odb)==parent['global_ODB_sha256'] and sha(guide)==parent['guide_sha256']
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
