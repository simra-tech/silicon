#!/usr/bin/env python3
"""Independent six-condition fixture audit; no cohort dispatch."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_joint586_adverse_fixture_controls import fixture, SIM, ROOT, REFERENCE, sha
from run_joint586_adverse_fixture_control import qualification
from run_joint586_transients import phase_parameters
from audit_joint586_adverse_transients import wave_check, decoded


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--transient-audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    packet=json.loads(a.packet.read_text());records=[];errors=[]
    assert len(packet['cases'])==6 and len({r['label'] for r in packet['cases']})==6
    original=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
    for case in packet['cases']:
        run=SIM/'qualification'/case['run'];entry=dict(run=case['run'],status='not run');records.append(entry)
        if not (run/'summary.json').exists():continue
        try:
            prep=json.loads((run/'preparation.json').read_text());qualification(a.transient_audit,prep)
            row,=json.loads((run/'summary.json').read_text());prov=json.loads((run/'provenance.json').read_text())
            entry['status']=row['status']
            assert sha(run/'preparation.json')==case['preparation_sha256']==prov['preparation_sha256']
            assert sha(run/'population_transient.cir')==case['deck_sha256']==prep['deck_sha256']
            assert (run/'population_transient.cir').read_text()==fixture(original,case['run'],prep['corner'],prep['seed'],prep['condition'])
            assert prov['runtime_identity']==prep['expected_runtime_identity'] and all(prov['input_checks'].values())
            assert sha(run/'runner.py')==prov['runner_sha256'] and prov['qualified_audit_sha256']==sha(a.transient_audit)
            assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
            assert all(sha(run/n)==v for n,v in prep['source_hashes'].items())
            assert sha(run/'population_inventory.json')==prep['inventory_sha256']
            names=['preparation.json','population_transient.cir','population_inventory.json','runner.py','provenance.json','summary.json','run.json','run.log']
            entry['receipts_sha256']={n:sha(run/n) for n in names}
            if row['status']!='passed required fixture control':continue
            assert row['runtime']==json.loads((run/'run.json').read_text()) and row['runtime']['status']=='completed'
            assert row['runtime']['returncode']==0 and not row['errors']
            log=(run/'run.log').read_text();section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
            assert phase_parameters(section,prep['groups'],prep['expected_vector'])==row['parameters']
            blob=decoded(run/'phase0.dat');assert hashlib.sha256(blob).hexdigest()==row['decoded_wave_sha256']
            data,analysis=wave_check(blob,19,prep['prospective_sampling'])
            assert len(data)==row['wave_rows'] and analysis==row['wave_analysis'] and analysis['sampling_status']=='passed'
            cm=prep['condition'][4];mean=[(r[17]+r[18])/2 for r in data];diff=[r[17]-r[18] for r in data]
            assert max(abs(v-cm) for v in mean)<1e-12 and max(abs(v-.025) for v in diff)<1e-12
            actual=dict(mean_common_mode_minmax_V=[min(mean),max(mean)],differential_minmax_V=[min(diff),max(diff)],
                shn_minmax_V=[min(r[18] for r in data),max(r[18] for r in data)])
            assert row['actual_input_observation']==actual
            entry.update(full11512_legacy27_status='passed',actual_input_observation=actual,
                decoded_wave_sha256=row['decoded_wave_sha256'],decisions=row['decisions'])
        except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
            entry['evidence_status']='failed';errors.append(dict(run=case['run'],error=repr(error)))
    result=dict(status='passed six required owncorner fixture controls' if not errors and all(r['status']=='passed required fixture control' for r in records)
        else 'failed or incomplete required fixture gate',corner=packet['corner'],records=records,audit_errors=errors,
        packet_sha256=sha(a.packet),transient_audit_sha256=sha(a.transient_audit),auditor_sha256=sha(Path(__file__)),
        scope='Exact source/draw/11512/27/finite19vectors/actualinput/originalsampling. No accuracy or population result inferred from fixed-code controls. All failures and notrun retained; no physicalsource adoption.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
    raise SystemExit(0 if result['status']=='passed six required owncorner fixture controls' else 1)


if __name__=='__main__':main()
