#!/usr/bin/env python3
"""Exact input rebinding of prior controlled saved-netlist diagnostics."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
PRIOR=HERE.parents[1]/'fullchip_reference_closure/physical_lvs'
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
GDS='4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2'
DB='1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT']);candidate=bulk/'gshared-fill-20260923-r4'
    database=bulk/'io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb'
    source=bulk/'io-physical-ap-source-20260923-r2/physical_taps_reader.cdl'
    bond=ROOT/'designs/g1-guardian/padframe/bondmap_candidate_20260923.csv'
    assert sha(database)==DB and sha(candidate/'route_fill_pruned.gds')==GDS
    assert sha(bond)=='73ed1fc85aaea04b4c975d799dc5843c28f2762c2d33a54c5df0d771bacf3521'
    a.output.mkdir(parents=True);manifest=[]
    def rebind(name,expected,edits):
        original=PRIOR/name;assert sha(original)==expected
        old=original.read_text();new=old
        for before,after in edits:
            assert new.count(before)==1,(name,before,new.count(before));new=new.replace(before,after)
        path=a.output/Path(name).name;path.write_text(new)
        (a.output/(path.name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
        manifest.append(dict(original=str(original),original_sha256=sha(original),prepared=path.name,prepared_sha256=sha(path),edits=edits))
        return path
    flatten=rebind('audit_api_flatten.py','c464d7fb87a2a2e375f43e00e7d437248e6a9b4f05f858cf5d151f83e84d7415',[
        ('set(os.sched_getaffinity(0)) == {1}','len(os.sched_getaffinity(0)) == 1'),
        ('1c8f3f91b8be00e0fbbdf4c2a40734fb5f8fe8b0388b1780768699e1a2afcbcf',DB)])
    material=rebind('full_marker_candidate/audit_saved_material.py','4a6096101e2fc5ae84709cc3e1a1196701206f1c4eaf2b0d5f5691b9eac23c76',[
        ("a.candidate / 'io_marker_native.gds'","a.candidate / 'route_fill_pruned.gds'"),
        ('ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca',GDS),
        ('3ed5cd2b78b3d4f4ed724730fcba2388148340d6442249e143c17a9f7ac99f04',DB),
        ("'passed exact drawn TM2 coverage; all 7058 floating fill polygons absent from saved layer'","'passed exact drawn TM2 coverage; current floating fill count separately recorded'"),
        ('    assert filler.count() == 7058 and filler.area() == 352900000000','    assert filler.count() > 0 and filler.area() > 0 # Current held GDS, not old-parent count.')])
    ports=rebind('full_marker_candidate/probe_current_ports.py','f1d991c0f9d96170efaed69d2e97f1d07e009d4c0877d5c1499dc72520fa5264',[
        ("a.candidate / 'io_marker_native.gds'","a.candidate / 'route_fill_pruned.gds'"),
        (" and meta['parent_GDS_sha256'] == PARENT",''),
        ('ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca',GDS),
        ('f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9','d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4'),
        ("assert material['native_filler_polygons'] == 7058","assert material['native_filler_polygons'] > 0 # Exact current material proof, not old-parent count.")])
    report=dict(status='prepared exact current saved-data controls',workers=manifest,database_sha256=DB,GDS_sha256=GDS,
        source_sha256=sha(source),bondmap_sha256=sha(bond),native_LVS='failed original deep comparison preserved',
        comparison='not run',runs=[])
    def save():(a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    commands=[('flatten',[str(flatten),'--database',str(database)]),
        ('material',[str(material),'--candidate',str(candidate),'--database',str(database)]),
        ('ports',[str(ports),'--candidate',str(candidate),'--database',str(database),'--database-sha256',DB,
            '--bondmap',str(bond),'--source',str(source),'--material-proof',str(a.output/'material/summary.json')])]
    env=dict(os.environ,PYTHONPATH=str(PRIOR/'full_marker_candidate'))
    for name,args in commands:
        cmd=['python3']+args+['--output',str(a.output/name)]
        with (a.output/(name+'.log')).open('x') as log:
            run=run_bounded(cmd,log,a.output/(name+'_run.json'),120,env=env,cwd=ROOT,interval_s=3)
        report['runs'].append(dict(stage=name,run=run));save()
        assert run['status']=='completed' and run['returncode']==0,(name,run)
    assert all(sha(PRIOR/r['original'].split(str(PRIOR)+'/')[1])==r['original_sha256'] and sha(a.output/r['prepared'])==r['prepared_sha256'] for r in manifest)
    report['status']='passed current exact flatten/material/physical22pin controls; comparison not run';save()


if __name__=='__main__':main()
