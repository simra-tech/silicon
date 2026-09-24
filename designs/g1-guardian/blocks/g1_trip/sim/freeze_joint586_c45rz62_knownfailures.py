"""Prepare exact original-method four-case execution, with all source/card identities held."""
import json
from pathlib import Path
from prepare_joint586_c45rz62_anchors import ROOT,SIM,CANDIDATE_SHA
from prepare_joint586_tmax_probe import sha
from result_directory import allocate_run


def main():
    reference=SIM/'qualification/joint586-c45rz62-knownfailures-prepared-20260923-a/contract.json'
    assert sha(reference)=='1f54ccc8d2f55b24f162b5e8cec36d5b504a11a9dc3e2ebcd74b7bb4401364be';d=json.loads(reference.read_text())
    source=ROOT/d['candidate_source_repository_path'];assert sha(source)==CANDIDATE_SHA
    template=SIM/'qualification/joint586-c45rz62-s73001-p00-original-step-20260923-a/preparation.json';pilot=json.loads(template.read_text())
    files=[reference,source,template]+[SIM/n for n in ['freeze_joint586_c45rz62_knownfailures.py','run_joint586_c45rz62_knownfailures.py','audit_joint586_c45rz62_knownfailures.py',
        'test_joint586_c45rz62_knownfailures.py','prepare_joint586_c45rz62_known_failures.py','run_joint586_c45rz62_anchors.py',
        'prepare_joint586_c45rz62_anchors.py','c45rz62_native_scale.py','run_joint586_tmax_probe.py','run_joint586_transients.py',
        'run_nominal_clock_probe.py','compare_joint586_tmax_probe.py','run_bgr_substitution_draw_audit.py','analyze_bgr_substitution_outcomes.py','wave_archive.py','result_directory.py','.spiceinit']]
    bindings={str(f.relative_to(ROOT)):sha(f) for f in files};controls=[]
    for record in d['records']:
        run=record['run_id'];out=allocate_run(SIM,run);original=SIM/'qualification'/record['original_run'];parent=original.parent
        provenance=json.loads((parent/'provenance.json').read_text())
        for name in ['trip.spice','bgr.spice','population_inventory.json']:(out/name).write_bytes((parent/name).read_bytes())
        (out/'sense.spice').write_bytes(source.read_bytes());(out/'probe.cir').write_bytes((reference.parent/(run+'.cir')).read_bytes())
        (out/'declared_source_replay_difference.diff').write_bytes((reference.parent/(run+'.diff')).read_bytes())
        prep=dict(record,source_hashes=dict(provenance['source_hashes'],**{'sense.spice':CANDIDATE_SHA}),inventory_sha256=provenance['inventory_sha256'],
            expected_runtime_identity=provenance['runtime_identity'],groups=pilot['groups'],prospective_sampling=pilot['prospective_sampling'],
            comparison_bounds=pilot['method_comparison_bounds'],tmax='0.2ns')
        prep['bindings_sha256'].update(bindings);assert sha(out/'probe.cir')==prep['deck_sha256']
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n');controls.append(dict(run_id=run,preparation_sha256=sha(out/'preparation.json'),watchdog_s=1200))
    packet=dict(status='authorized four original-step source diagnostics only',controls=controls,bindings_sha256=bindings,original_reference_sha256=sha(reference),scope='Keep all four original failures; no recalibration, source adoption or population release.')
    path=SIM/'qualification/joint586-c45rz62-knownfailures-execution-20260923-a.json';assert not path.exists();path.write_text(json.dumps(packet,indent=2)+'\n');print(sha(path))


if __name__=='__main__':main()
