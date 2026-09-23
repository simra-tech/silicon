"""Freeze own-six/nominal implementation; no launches or statistical adoption."""
import json
from pathlib import Path
from prepare_586_klu_population_qualification import HERE,ROOT,sha

def main():
    own=HERE/'t2f586-klu-own6-preparation-20260923-a.json';nominal=HERE/'t2f586-klu-nominal-references-20260923-b.json'
    new=HERE/'t2f586-klu-own6-new-controls-20260923-a.json';out=HERE/'t2f586-klu-own6-implementation-20260923-a.json'
    assert not new.exists() and not out.exists()
    cases=[]
    for case in json.loads(own.read_text())['cases']:
        if case['scheduling']!='new control not run':continue
        cases.append(dict(case,label=case['corner']+'-'+case['label']))
    assert len(cases)==8
    new.write_text(json.dumps(dict(status='prepared eight missing full32us KLU controls only; existing ten inputs reused',cases=cases,original_own6_packet_sha256=sha(own)),indent=2)+'\n')
    import run_586_population_control,run_586_source_control,run_nominal_clock_probe,run_bgr_substitution_draw_audit,analyze_bgr_substitution_outcomes,wave_archive,run_586_calibration_sample,analyze_586_population
    files=[Path(m.__file__).resolve() for m in [run_586_population_control,run_586_source_control,run_nominal_clock_probe,run_bgr_substitution_draw_audit,analyze_bgr_substitution_outcomes,wave_archive,run_586_calibration_sample,analyze_586_population]]
    files += [HERE/n for n in ['run_586_klu_temperature.py','prepare_586_klu_temperature_coverage.py','prepare_586_klu_controls.py','prepare_586_klu_population_qualification.py','prepare_586_klu_nominal_references.py','run_586_klu_nominal_reference.py','run_586_nearendpoint_recovery.py','audit_586_klu_population_qualification.py','test_586_klu_population_qualification.py']]+[Path(__file__).resolve()]
    payload=dict(status='implementation prepared and source-bound; no launch lease or population release',
        preparation_packet=str(new.relative_to(ROOT)),preparation_packet_sha256=sha(new),
        own6_packet=str(own.relative_to(ROOT)),own6_packet_sha256=sha(own),nominal_packet=str(nominal.relative_to(ROOT)),nominal_packet_sha256=sha(nominal),
        implementation_bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
        runners=dict(new8='run_586_klu_temperature.py',nominal3='run_586_klu_nominal_reference.py',independent_per_corner_audit='audit_586_klu_population_qualification.py'),
        new_watchdog_CPU_s=6600,new_external_growth_GiB=.55,
        authority='Preparation only. Explicit lease/resource and coordinator review before11new600scontrols. Exact ten existing inputs are reused only after independent complete audit. All6+sameKLU nominalgate/1129variation/exactreturn required percorner; no solveradoption/population launch from this receipt.')
    out.write_text(json.dumps(payload,indent=2)+'\n');print(out.relative_to(ROOT),sha(out))

if __name__=='__main__':main()
