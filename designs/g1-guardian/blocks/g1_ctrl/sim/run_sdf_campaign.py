#!/usr/bin/env python3
"""Pilot SDF annotation of the matching run7 netlist with stock PDK cells."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded,atomic_json

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--corner',choices=['nom_typ_1p20V_25C','nom_slow_1p08V_125C','nom_fast_1p32V_m40C'],default='nom_typ_1p20V_25C')
    ap.add_argument('--image-id',required=True)
    ap.add_argument('--annotation-only',action='store_true',help='stop after 1us; qualify annotation, not functionality')
    a=ap.parse_args()
    run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=HERE/'campaigns'/('sdf_'+run_id);out.mkdir(parents=True,exist_ok=False)
    build=ROOT/'build/g1_sdf'/run_id;build.mkdir(parents=True,exist_ok=False)
    nl=HERE.parent/'layout/g1_digital.nl.v';built=ROOT/'build/g1_digital/final_run7/nl/g1_digital.nl.v'
    if sha(nl)!=sha(built):raise SystemExit('SDF netlist provenance mismatch')
    sdf=ROOT/'build/g1_digital/final_run7/sdf'/a.corner/('g1_digital__'+a.corner+'.sdf')
    shutil.copyfile(sdf,out/'input.sdf')
    pdk=Path('/foss/pdks/ihp-sg13g2');models=pdk/'libs.ref/sg13g2_stdcell/verilog'
    fixture=(HERE/'tb_g1_digital.v').read_text().replace('module tb_g1_digital;',
        'module tb_g1_digital;\ninitial begin $sdf_annotate("'+str(out/'input.sdf')+'",dut); $display("SDF_ANNOTATION_RETURNED"); end')
    if a.annotation_only:
        fixture=fixture.replace('module tb_g1_digital;', 'module tb_g1_digital;\ninitial begin #1000; $display("ANNOTATION_PILOT_END"); $finish; end')
    tb=out/'testbench.v';tb.write_text(fixture)
    sources=[models/'sg13g2_udp.v',models/'sg13g2_stdcell.v',nl,tb]
    meta=dict(options=vars(a),image_id=a.image_id,pdk_commit=(pdk/'COMMIT').read_text().strip(),
        sdf_sha256=sha(sdf),netlist_sha256=sha(nl),runner_sha256=sha(Path(__file__)),
        source_sha256={str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p.relative_to(pdk)):sha(p) for p in sources},
        version=subprocess.run(['iverilog','-V'],capture_output=True,text=True).stdout.splitlines()[0],
        timing_checks='not established; Icarus does not implement full setup/hold checking')
    env=dict(os.environ);env['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib:'+env.get('LD_LIBRARY_PATH','')
    with (out/'compile.log').open('x') as log:
        r=run_bounded(['iverilog','-g2012','-gspecify','-ginterconnect','-Tmax','-DGLS','-Wno-timescale','-o',str(build/'test.vvp')]+list(map(str,sources)),log,out/'compile.json',120,env=env,metadata=meta)
    if r['status']!='completed':print(out.relative_to(ROOT),'compile failed');raise SystemExit(1)
    with (out/'simulation.log').open('x') as log:
        r=run_bounded(['vvp','-n',str(build/'test.vvp')],log,out/'simulation.json',300,cwd=build,env=env,metadata=meta)
    text=(out/'simulation.log').read_text()
    r['functional_acceptance']='not run' if a.annotation_only else 'passed' if r['status']=='completed' and 'ALL TESTS PASSED' in text else 'failed' if r['status'] in ('completed','failed') else 'not run to completion'
    warnings=[l for l in text.splitlines() if re.search('warning|error|unable|cannot|unsupported',l,re.I)]
    r['annotation_warnings']=warnings[:100];r['annotation_warning_count']=len(warnings)
    r['annotation_status']='failed' if warnings or 'SDF_ANNOTATION_RETURNED' not in text else 'completed with simulator limitations'
    atomic_json(out/'simulation.json',r)
    print(out.relative_to(ROOT),r['status'],r['functional_acceptance'],r['annotation_status'],'warnings',len(warnings))
    print(text[-2500:])
if __name__=='__main__':main()
