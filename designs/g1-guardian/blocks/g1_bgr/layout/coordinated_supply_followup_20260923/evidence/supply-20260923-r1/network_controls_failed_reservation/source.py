#!/usr/bin/env python3
"""Sequential source/AP/metal controls; prepares but never runs analog."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('--resource-gate',type=Path,required=True)
    a=ap.parse_args();assert not a.receipt.exists() and set(os.sched_getaffinity(0))=={0}
    gate=json.loads(a.resource_gate.read_text())
    assert gate['status']=='passed' and gate['project_cpu_budget']>=41 and gate['ram_available_bytes']>=16*1024**3
    bulk=Path(os.environ['G1_RESULTS_ROOT']);layout=HERE.parent
    candidate=bulk/'bgr-supply-candidate-20260923-r1'
    drc=bulk/'bgr-supply-drc-20260923-r1';lvs=bulk/'bgr-supply-lvs-20260923-r1'
    preparation=bulk/'bgr-supply-metal-prepare-20260923-r1'
    fixture=bulk/'bgr-supply-fixture-20260923-r1'
    source=layout.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    base_fixture=layout.parent/'sim/qualification/runs/bgr586-raw-current-ledger-20260922-a/nominal.cir'
    baseline=bulk/'bgr-external-pin-metal-prepare-20260923-r3'
    scripts=[layout/'coordinated_full_closure/audit_junctions.py',
             layout/'coordinated_dvbe_remedy_20260923/prepare_metal.py',
             layout/'coordinated_return_remedy/run_candidate_metal.py',
             layout/'coordinated_return_remedy/extract_metal_r.py',
             layout/'coordinated_return_remedy/audit_metal_r_solution.py',
             HERE/'prepare_fixture.py',layout/'coordinated_model_boundary/audit_external_pin_source.py']
    physical=[bulk/('bgr-supply-context-'+k+'-20260923-r1')/'summary.json' for k in ('main','maximal','antenna','density')]
    physical += [bulk/'bgr-supply-pruned-context-20260923-r3/analysis.json',bulk/'bgr-supply-context-terminals-20260923-r1/analysis.json']
    assert all(json.loads(p.read_text())['status'].startswith('passed') for p in physical)
    context=bulk/'bgr-supply-context-candidate-20260923-r1'
    context_meta=json.loads((context/'analysis.json').read_text())
    context_gds=context/'supply_context_native.gds';context_sha=sha(context_gds)
    assert context_meta['status'].startswith('passed') and context_meta['GDS_sha256']==context_sha
    assert context_meta['source_BRG_geometry_sha256']==sha(candidate/'bank.gds')
    assert context_meta['original_parent_sha256']=='ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
    for path in physical[:4]+physical[5:]:
        assert json.loads(path.read_text())['GDS_sha256']==context_sha,path
    clearance=json.loads(physical[4].read_text())
    assert clearance['inputs'][str(context_gds)]==context_sha
    assert clearance['inputs'][str(candidate/'bank.gds')]==sha(candidate/'bank.gds')
    for path in (drc/'summary.json',lvs/'summary.json'):
        observed=json.loads(path.read_text())
        assert observed['status']=='passed' and observed['inputs'][str(candidate/'bank.gds')]==sha(candidate/'bank.gds')
        assert observed['inputs'][str(candidate/'bank.cdl')]==sha(candidate/'bank.cdl')
    initial=[Path(__file__),a.resource_gate,source,base_fixture,candidate/'preparation.json',candidate/'bank.gds',
             drc/'summary.json',lvs/'summary.json',baseline/'summary.json',baseline/'points.json',
             context/'analysis.json',context_gds]+scripts+physical
    bindings={str(p):sha(p) for p in initial}
    a.receipt.mkdir(parents=True);(a.receipt/'source.py').write_bytes(Path(__file__).read_bytes())
    report=dict(status='running',inputs=bindings,stages=[],analog='not run',adoption='not run',reservation_GiB=16,memory_enforced=False)
    def save(): (a.receipt/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    def run(name,args):
        command=['python3']+[str(s) for s in args]
        start=time.monotonic()
        with (a.receipt/(name+'.log')).open('x') as log:
            r=subprocess.run(['timeout','-k','5','90']+command,stdout=log,stderr=subprocess.STDOUT)
        report['stages'].append(dict(name=name,command=command,returncode=r.returncode,wall_s=time.monotonic()-start,watchdog_s=90))
        save();assert r.returncode==0,name
    save()
    try:
        run('source336AP',[scripts[0],'--stock',lvs,'--output',lvs/'junction_audit.json'])
        run('metal_preparation',[scripts[1],'--candidate',candidate,'--baseline-preparation',baseline,
            '--output',preparation,'--resource-gate',a.resource_gate,'--drc',drc,'--lvs',lvs])
        networks={}
        for scenario,control in [('KPEX','bgr-metal-r-controls-kpex-20260922-r4'),('LEF','bgr-metal-r-controls-lef-20260922-r2')]:
            name='bgr-metal-r-supply-'+scenario.lower()+'-20260923-r1';networks[scenario]=bulk/name
            run('metal_'+scenario,[scripts[2],'--run-id',name,'--preparation',preparation,'--resource-gate',a.resource_gate,
                '--mode','full','--scenario',scenario,'--control',bulk/control/'result/summary.json'])
            run('independent_'+scenario,[scripts[4],'--result',networks[scenario]/'result','--output',networks[scenario]/'independent_audit.json'])
        run('fixture_preparation',[scripts[5],'--source',source,'--fixture',base_fixture,'--preparation',preparation,
            '--kpex-network',networks['KPEX'],'--lef-network',networks['LEF'],'--baseline-points',baseline/'points.json',
            '--output',fixture,'--resource-gate',a.resource_gate])
        run('independent_source',[scripts[6],'--prepared',fixture,'--source',source])
        assert all(sha(Path(p))==h for p,h in bindings.items())
        report.update(status='passed source/AP/complete-positive-network controls; analog not run',inputs_unchanged=True,
                      prepared_fixture=str(fixture))
    except Exception as error:
        report.update(status='failed',error=repr(error));raise
    finally:save()
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
