#!/usr/bin/env python3
"""Audit completed imposed-charge runs, recording even briefly wrong decisions."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results-root',type=Path,required=True)
    p.add_argument('--runs',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    records=[];fingerprints=[];controls={}
    for run in a.runs.split(','):
        assert '/' not in run
        root=a.results_root/run
        contract=json.loads((root/'contract.json').read_text())
        rows=json.loads((root/'manifest.json').read_text())
        assert len(rows)==2*(1+len(contract['nodes']))
        source=root/'cmp.spice';assert sha(source)==contract['source_sha256']
        for row in rows:
            assert row['status']=='passed characterization'
            leaf=root/row['name']
            assert json.loads((leaf/'analysis.json').read_text())==row
            assert sha(leaf/'fixture.cir')==row['deck_sha256']
            assert sha(leaf/'tool.log')==row['log_sha256']
            path=leaf/'wave.tsv';assert sha(path)==row['metrics']['wave_sha256']
            fp=row['fingerprints'];assert len(fp['BEFORE'])==120 and fp['BEFORE']==fp['AFTER'];fingerprints.append(fp['BEFORE'])
            data=[list(map(float,line.split())) for line in path.read_text().splitlines()[1:] if line.strip()]
            assert len(data)==row['metrics']['rows']
            inj=contract['phase_ns']*1e-9
            held=[r for r in data if inj<=r[0]<=320e-9]
            wrong=[r for r in held if (r[1]<.6 if row['differential_V']>0 else r[1]>.6)]
            delivered=sum((b[0]-c[0])*(c[10]+b[10])/2 for c,b in zip(data,data[1:]))
            assert abs(delivered-row['polarity']*row['charge_fC']*1e-15)<=max(1e-20,row['charge_fC']*1e-20)
            record=dict(run=run,name=row['name'],contract_sha256=sha(root/'contract.json'),analysis_sha256=sha(leaf/'analysis.json'),
                        differential_V=row['differential_V'],node=row['node'],charge_fC=row['charge_fC'],polarity=row['polarity'],phase_ns=contract['phase_ns'],
                        metrics=row['metrics'],held_window_q_min_V=min(r[1] for r in held),held_window_q_max_V=max(r[1] for r in held),
                        any_wrong_logic_observed=bool(wrong),wrong_logic_first_last_s=[wrong[0][0],wrong[-1][0]] if wrong else None,
                        delivered_charge_C=delivered,simulation_wall_s=row['wall_s'])
            records.append(record)
            if row['charge_fC']==0:
                controls.setdefault((contract['phase_ns'],row['differential_V']),[]).append(row['metrics']['wave_sha256'])
    assert all(fp==fingerprints[0] for fp in fingerprints)
    assert all(len(values)==2 and len(set(values))==1 for values in controls.values())
    result=dict(status='passed imposed-charge characterization audit',transients=len(records),
                full120_parameter_freeze='passed',matched_zero_charge_waveforms='passed',charge_area_check='passed',
                changed_held_samples=sum(r['metrics']['changed_held_decision'] for r in records),
                any_wrong_logic_observed_cases=sum(r['any_wrong_logic_observed'] for r in records),
                failed_next_decision_recovery=sum(not r['metrics']['recovered_next_decision'] for r in records),
                failed_late_decision_recovery=sum(not r['metrics']['recovered_late_decisions'] for r in records),
                min_observed_node_V=min(r['metrics']['min_observed_node_V'] for r in records),
                max_observed_node_V=max(r['metrics']['max_observed_node_V'] for r in records),
                reliability_validity='not run: observed voltages include outside-rail excursions; no survival/model-validity claim',
                physical_radiation_measurement='not applicable',full_chain_feedback_recovery='not run',
                scope='One62001draw,revision1standalonecellCPEX,inheritednative/AP convention. Charge is electrical fixture input, not LET or radiation rate. Nominalrails/temperature only. Wrong-logic observation is a hazard, not safety acceptance.',
                cases=records)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))


if __name__=='__main__':
    main()
