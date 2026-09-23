#!/usr/bin/env python3
"""Isolated signal-route guide probe with actual core obstacles; no PDN claim."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
from check_closed_macro_odb import sha,quote
from check_fullchip_def_odb import observation,OPENROAD,PDK,DESIGN


def obstacle_observation(path):
    return ['set fp [open '+quote(path)+' w]',
            'foreach o [[ord::get_db_block] getObstructions] {',
            'set b [$o getBBox]',
            'puts $fp "[[$b getTechLayer] getName]\t[$b xMin]\t[$b yMin]\t[$b xMax]\t[$b yMax]"',
            '}', 'close $fp']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--odb-check',type=Path,required=True)
    p.add_argument('--obstacles',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.odb_check/'analysis.json').read_text())
    obs=json.loads((a.obstacles/'analysis.json').read_text())
    source=a.odb_check/'unrouted_fullchip.odb';obs_script=a.obstacles/'core_obstacles.tcl'
    assert meta['status'].startswith('passed') and sha(source)==meta['ODB_sha256']
    assert sha(OPENROAD)==meta['OpenROAD_sha256'] and sha(obs_script)==obs['Tcl_sha256']
    assert obs['status'].startswith('passed') and meta['instances']==4904
    # Only the historical, unchanged constraint variables are reused. Never
    # source the old flow environment, output paths, LEFs, floorplan or database.
    previous=DESIGN/'blocks/g1_padring/flow/runs/assembly-1350/38-openroad-globalrouting/_env.tcl'
    keys=['DESIGN_NAME','CLOCK_PORT','CLOCK_NET','CLOCK_PERIOD','IO_DELAY_CONSTRAINT',
          'MAX_FANOUT_CONSTRAINT','OUTPUT_CAP_LOAD','CLOCK_UNCERTAINTY_CONSTRAINT',
          'CLOCK_TRANSITION_CONSTRAINT','TIME_DERATING_CONSTRAINT']
    constraints=[]
    for key in keys:
        found=re.findall(r'^set ::env\('+key+r'\) (.*)$',previous.read_text(),re.M)
        assert len(found)==1
        constraints.append('set ::env('+key+') '+found[0])
    sdc=DESIGN/'blocks/g1_padring/flow/g1_chip_top.sdc'
    child_sdc=DESIGN/'blocks/g1_ctrl/layout/g1_digital_top.sdc'
    libs=[PDK/'libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib',
          DESIGN/'blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_typ_1p2V_3p3V_25C.lib',
          DESIGN/'blocks/g1_ctrl/layout/lib/g1_digital__nom_typ_1p20V_25C.lib']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    inputs={str(q):sha(q)for q in [source,obs_script,previous,sdc,child_sdc,OPENROAD]+libs}
    result=dict(status='running',inputs=inputs,script_sha256=sha(Path(__file__)),
                routing_scope='signal guide probe, unchanged libraries/constraints, strict no-overflow; no detailed metal/PDN adoption',
                not_run=['detailed routing','full new PDN/powerfeed connectivity','fullchip DRC/LVS/PEX/density/antenna/STA/currentIR','electrical adoption'])
    receipt=a.output/'analysis.json';receipt.write_text(json.dumps(result,indent=2)+'\n')
    lines=['set_thread_count 1']+['read_liberty '+quote(q)for q in libs]+['read_db '+quote(source)]
    lines+=constraints+['read_sdc '+quote(sdc),'source '+quote(obs_script)]
    lines+=observation(a.output/'before.tsv')+obstacle_observation(a.output/'obstacles.tsv')
    lines+=['write_db '+quote(a.output/'obstructed.odb'),
            'set_routing_layers -signal Metal2-TopMetal2 -clock Metal2-TopMetal2',
            'set_global_routing_layer_adjustment Metal2-TopMetal2 0.3',
            'global_route -congestion_iterations 50 -verbose',
            'write_guides '+quote(a.output/'global.guide'),
            'write_db '+quote(a.output/'global.odb')]
    lines+=observation(a.output/'after.tsv')
    script=a.output/'route.tcl';script.write_text('\n'.join(lines)+'\n')
    command=['timeout','--kill-after=5','300',str(OPENROAD),'-exit',str(script)]
    start=time.monotonic()
    with(a.output/'route.log').open('x')as log:
        run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result.update(command=command,returncode=run.returncode,wall_s=time.monotonic()-start)
    original=sorted((a.odb_check/'roundtrip.tsv').read_text().splitlines())
    if(a.output/'before.tsv').exists():
        assert sorted((a.output/'before.tsv').read_text().splitlines())==original
        result['pre_route_instance_connectivity_held']='passed'
    if(a.output/'obstacles.tsv').exists():
        observed=sorted((a.output/'obstacles.tsv').read_text().splitlines())
        expected=sorted('\t'.join([r['layer']]+list(map(str,r['bbox_dbu'])))for r in obs['obstacles'])
        assert observed==expected
        result['all_native_obstacle_rectangles_held']='passed'
    result['inputs_unchanged']=all(sha(Path(q))==value for q,value in inputs.items())
    assert result['inputs_unchanged']
    if run.returncode==0:
        assert sorted((a.output/'after.tsv').read_text().splitlines())==original
        assert (a.output/'global.guide').stat().st_size>0
        result.update(status='passed isolated strict global-route guide probe',
                      post_route_instance_connectivity_held='passed',guide_sha256=sha(a.output/'global.guide'),
                      global_ODB_sha256=sha(a.output/'global.odb'))
    else:
        result['status']='failed isolated global-route guide probe'
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if run.returncode==0 else 1)


if __name__=='__main__':
    main()
