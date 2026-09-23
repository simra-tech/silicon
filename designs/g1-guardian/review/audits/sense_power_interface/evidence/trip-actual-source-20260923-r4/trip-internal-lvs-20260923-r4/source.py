#!/usr/bin/env python3
"""Compare additive TRIP access geometry with the unchanged source reference."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pya
from build_ls_interface import sha

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'))
from run_stock_native_prototypes import strict_xref


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--native-source',type=Path)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    meta=json.loads((a.candidate/'analysis.json').read_text());assert meta['status'].startswith('passed')
    gds=a.candidate/'g1_trip.gds';ref=a.candidate/'g1_trip_lvs.cdl'
    assert sha(gds)==meta['GDS_sha256']
    assert sha(ref)==meta['source_reference_sha256']=='60a9ad6e3744ff0b3dcd407a78febcb49315840a65fdf8ef851032d6e88bfd76'
    source=HERE.parents[2]/'blocks/g1_trip/layout'
    assert sha(source/'g1_trip_lvs.cdl')==sha(ref)
    if a.native_source:
        assert sha(a.native_source)==meta['source_GDS_sha256']
        assert sha(source/'g1_trip.gds')==meta['actual_native_source_binding']['canonical_functional_source_GDS_sha256']
    else:assert sha(source/'g1_trip.gds')==meta['source_GDS_sha256']
    pdk=Path('/foss/pdks/ihp-sg13g2');assert(pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    rules={str(q.relative_to(pdk)):sha(q)for q in(pdk/'libs.tech/klayout/tech/lvs').rglob('*')if q.is_file()}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    cmd=['timeout','--kill-after=5','180','python3',str(pdk/'libs.tech/klayout/tech/lvs/run_lvs.py'),
         '--layout='+str(gds.resolve()),'--netlist='+str(ref.resolve()),'--topcell=g1_trip','--run_mode=deep',
         '--run_dir='+str(a.output.resolve()/'reports')]
    result=dict(status='running',GDS_sha256=sha(gds),reference_sha256=sha(ref),command=cmd,
                script_sha256=sha(Path(__file__)),strict_xref_helper_sha256=sha(Path(sys.modules['run_stock_native_prototypes'].__file__)),
                stock_rule_hashes=rules,not_run=['MOS ng/junction model applicability beyond stock comparison',
                    'fullnative placement/context','current partition/contact capacity/IR/EM/PVT','PEX','adoption'])
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    started=time.monotonic()
    with(a.output/'stock.log').open('x')as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    logs='\n'.join(q.read_text(errors='replace')for q in a.output.rglob('*.log'))
    explicit='Congratulations! Netlists match.'in logs and"Netlists don't match"not in logs
    databases=[dict(path=str(q.relative_to(a.output)),sha256=sha(q),xref=strict_xref(q))for q in a.output.rglob('*.lvsdb')]
    unchanged=sha(gds)==result['GDS_sha256']and sha(ref)==result['reference_sha256']and all(sha(pdk/q)==h for q,h in rules.items())
    passed=run.returncode==0 and explicit and bool(databases)and all(r['xref']['status']=='passed'for r in databases)and unchanged
    result.update(status='passed strict source LVS'if passed else'failed strict source LVS',returncode=run.returncode,
                  wall_s=time.monotonic()-started,explicit_match=explicit,databases=databases,inputs_rules_unchanged=unchanged)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='stock_rule_hashes'},indent=2));raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
