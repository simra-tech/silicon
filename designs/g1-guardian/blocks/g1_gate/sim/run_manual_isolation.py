#!/usr/bin/env python3
"""One bounded explicit-body/real-FET manual-isolation diagnostic, not safety qualification."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_manual_isolation import build,HERE,sha,TEMPLATE_SHA,PAD_SHA,CORE_SHA,FET_SHA,VECTORS
from analyze_manual_isolation import analyze,tests

sys.path.insert(0,str(HERE.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded
IMAGE='sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'
MANIFEST='sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pad-source',type=Path,required=True)
    p.add_argument('--pad-proof',type=Path,required=True)
    p.add_argument('--tap-factor',type=int,choices=[1,2])
    p.add_argument('--sensitivity-proof',type=Path)
    p.add_argument('--cpu',type=int,choices=[1,6],default=1)
    p.add_argument('--sequence',choices=['io_first','missing_core'],required=True)
    p.add_argument('--closed',action='store_true')
    p.add_argument('--bus-uf',type=float,choices=[.1,10.],default=10.)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={a.cpu} and not a.output.exists()
    root=HERE.parents[4]
    template=HERE/'campaigns/fet_20260921T151805Z_168cb700/fixture.cir'
    core=HERE/'postlayout/g1_gate_pex.spice';fet=root/'build/g1_gate/vendor/CSD16340Q3.lib'
    paths={'template':template,'pad':a.pad_source,'core':core,'fet':fet,'init':HERE/'.spiceinit'}
    bindings={n:sha(path.read_bytes()) for n,path in paths.items()}
    assert bindings['template']==TEMPLATE_SHA
    assert bindings['core']==CORE_SHA and bindings['fet']==FET_SHA
    proof=json.loads(a.pad_proof.read_text())
    assert proof['status'].startswith('passed source-only') and proof['candidate_sha256']==PAD_SHA
    assert proof['original_parameter_and_tap_R_preservation'] and proof['exact_original_library_prefix']
    assert all(r['wrong_bulk_rejected'] and r['missing_bulk_terminal_rejected'] for r in proof['flattened_controls'])
    conditional=None
    if a.tap_factor:
        assert a.sensitivity_proof
        from audit_manual_pad_variant import audit
        conditional=audit(a.pad_source,a.sensitivity_proof,a.pad_proof,a.tap_factor)
    else:assert bindings['pad']==PAD_SHA and not a.sensitivity_proof
    a.output.mkdir(parents=True)
    (a.output/'.spiceinit').write_bytes(paths['init'].read_bytes())
    deck,contract=build(template.read_bytes(),a.pad_source.resolve(),core.resolve(),fet.resolve(),
        a.output,a.sequence,a.closed,{.1:.1e-6,10.:10e-6}[a.bus_uf])
    contract.update(source_hashes=bindings,pad_proof_sha256=sha(a.pad_proof.read_bytes()),
                    conditional_tap_R=conditional,requested_cpu=a.cpu,
                    preparation_controls=tests(),deck_sha256=sha(deck.encode()))
    (a.output/'fixture.cir').write_text(deck)
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    for name in ['run_manual_isolation.py','prepare_manual_isolation.py','analyze_manual_isolation.py']:
        (a.output/name).write_bytes((HERE/name).read_bytes())
    if conditional:(a.output/'audit_manual_pad_variant.py').write_bytes((HERE/'audit_manual_pad_variant.py').read_bytes())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f.read_bytes()) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    expected=json.loads((HERE.parents[1]/'g1_trip/sim/qualification/joint586-mm-tranqual-20260922-a-enabled/preparation.json').read_text())['expected_runtime_identity']
    assert runtime==expected
    # Exact library view is still installed; design clones do not edit the PDK.
    assert sha((pd/'libs.ref/sg13g2_io/spice/sg13g2_io.spi').read_bytes())==proof['spi_sha256']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,
        OCI_config_digest=IMAGE,OCI_manifest_digest=MANIFEST,runtime_exact=True,
        stochastic_scope='Original deterministic gate fixture corners; no new mismatch population or inherited SENSE realization'),indent=2)+'\n')
    with (a.output/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str(a.output/'fixture.cir')],stream,a.output/'run.json',120,cwd=a.output,interval_s=1)
    log=(a.output/'run.log').read_text()
    failures=[line for line in log.splitlines() if re.search(r'(?i)^\s*(?:error|fatal)\b|timestep too small|simulation aborted|doAnalyses:|no such vector|no such parameter|cannot parse',line)]
    result=dict(status='failed',runtime=state,errors=failures,
        warnings=[line for line in log.splitlines() if re.search(r'(?i)warning|limit|nan',line)])
    try:
        assert state['status']=='completed' and state['returncode']==0
        assert not failures and 'MANUAL_ISOLATION_END' in log
        assert all(sha(path.read_bytes())==bindings[n] for n,path in paths.items())
        assert sha((a.output/'fixture.cir').read_bytes())==contract['deck_sha256']
        lines=(a.output/'wave.tsv').read_text().splitlines()
        assert lines[0].split()==['time']+VECTORS
        wave=np.array([list(map(float,line.split())) for line in lines[1:] if line.strip()])
        report=analyze(wave,contract)
        (a.output/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
        result.update(status='passed source/numerical diagnostic; inspect independent electrical dispositions',
                      rows=len(wave),endpoint_s=float(wave[-1,0]),
                      conditional_manual_isolation=report['conditional_manual_isolation'],
                      historical_gate_voltage=report['historical_gate_voltage'])
        if a.closed:
            result['negative_control_exercised']=report['negative_control_exercised']
            assert report['negative_control_exercised']
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:
        result['analysis_error']=repr(exc);result['status']='failed'
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()
