"""Freeze only three original0.2ns arms; six-arm preparation remains unchanged."""
import json
from prepare_joint586_c45rz62_anchors import ROOT,SIM,CANDIDATE_SHA
from prepare_joint586_tmax_probe import sha


def main():
    packet=SIM/'qualification/joint586-c45rz62-calibration-anchors-20260923-a.json'
    assert sha(packet)=='d2e0bcdbe79588f512c25b17849940e95ae22504b46ce2954e64d14bf0336ac9'
    data=json.loads(packet.read_text());assert data['candidate_source_sha256']==CANDIDATE_SHA
    controls=[c for c in data['controls'] if c['tmax']=='0.2n'];assert [c['leaf'] for c in controls]==['p00','p08','p09']
    files=[packet]+[SIM/n for n in ['freeze_joint586_c45rz62_anchors.py','run_joint586_c45rz62_anchors.py','audit_joint586_c45rz62_anchors.py',
        'test_joint586_c45rz62_runtime.py','prepare_joint586_c45rz62_anchors.py','test_joint586_c45rz62_anchors.py','c45rz62_native_scale.py',
        'run_joint586_tmax_probe.py','run_joint586_transients.py','run_nominal_clock_probe.py','compare_joint586_tmax_probe.py',
        'run_bgr_substitution_draw_audit.py','analyze_bgr_substitution_outcomes.py','prepare_joint586_tmax_probe.py',
        'prepare_joint586_klu_replay.py','wave_archive.py','result_directory.py','.spiceinit']]
    physical=ROOT/'designs/g1-guardian/blocks/g1_sense/sim/run_loaded_compensation_candidate.py';files.append(physical)
    for c in controls:
        out=SIM/'qualification'/c['run_id'];assert sha(out/'preparation.json')==c['preparation_sha256']
        assert not (out/'run.json').exists();files.append(out/'preparation.json')
    execution=dict(status='authorized three source diagnostics at original0.2ns only; no adoption',controls=controls,
        packet=str(packet.relative_to(ROOT)),packet_sha256=sha(packet),bindings_sha256={str(f.relative_to(ROOT)):sha(f) for f in files},
        expected_bulk_GiB=.15,watchdog_s=1200,scope='No candidate1ns launch. Native area law/full11512+27 precede output observations. Intentional cross-source differences never inherit old calibration or population qualification.')
    path=SIM/'qualification/joint586-c45rz62-original-step-execution-20260923-a.json';assert not path.exists();path.write_text(json.dumps(execution,indent=2)+'\n');print(sha(path))


if __name__=='__main__':main()
