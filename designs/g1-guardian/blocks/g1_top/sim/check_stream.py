#!/usr/bin/env python3
"""Saved-vector electrical acceptance for two pinned c_mid streaming fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
from check_campaign import read_wave
from run_bounded import atomic_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = 'c_mid_pex_tl_tt_27C_clockfix_compact_threads2_functional_20260921T153913Z_6b398c8f.cir'
SOURCE_SHA256 = '506df5bf09fa11eff7dfc1cc80b5e62ee02b757b25cc0ca4b2771b6226a54a29'
CONTRACTS = {
    SOURCE_SHA256: dict(source=SOURCE,event=16e-6,end=28e-6),
    '001e608cb3018553d48542d951bfe22a20d7c970c34376cb3553d5404bd96b36': dict(
        source='c_mid_pex_tl_tt_27C_clockfix_threads2_functional_20260921T222659Z_db3a4818.cir',event=30e-6,end=42e-6),
}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def evaluate(cols, rows, completion, event=16e-6, end=28e-6):
    idx = {c:i for i,c in enumerate(cols)}
    def val(row, name):
        return row[idx[name]]
    checks = dict(solver_and_raw_complete=completion=='passed', endpoint=abs(rows[-1][0]-end)<1e-12)
    before = [r for r in rows if event-1e-6<=r[0]<event]
    after = [r for r in rows if r[0]>=event]
    checks['pre_event_armed'] = bool(before) and all(val(r,'v(gate)')>2.5 and val(r,'v(inrush_active)')<.2 and val(r,'v(dig_trip)')<.2 and val(r,'v(en_core)')>1 for r in before)
    def code(row, prefix):
        bits = [val(row, f'v({prefix}{i})') for i in range(8)]
        if any(.2<x<1 for x in bits):
            return None
        return sum(1<<i for i,x in enumerate(bits) if x>=1)
    checks['configured_thresholds'] = bool(before) and all(code(r,'soft')==153 and code(r,'hard')==200 for r in before)
    low = next((i for i,r in enumerate(after) if val(r,'v(gate)')<1),None)
    values = dict(event_s=event, observed_end_s=rows[-1][0], model='Behavioral external switch and fitted pad, ideal oscillator, block C-PEX; not real FET or full assembled RC.')
    checks['gate_low_reached'] = low is not None
    if low is not None:
        values['gate_low_delay_s'] = after[low][0]-event
        checks['latency_under_10us'] = 0<=values['gate_low_delay_s']<10e-6
        checks['stays_low'] = all(val(r,'v(gate)')<1 for r in after[low:])
    last = rows[-1]
    checks['digital_trip_latched'] = val(last,'v(dig_trip)')>1
    checks['analog_trip_latched'] = val(last,'v(tripped)')>1
    checks['hard_cause'] = val(last,'v(cause1)')>1 and val(last,'v(cause0)')<.2
    checks['fault_asserted'] = val(last,'v(fault_n)')<.33
    values.update(gate_end_V=val(last,'v(gate)'),current_end_A=val(last,'i(vim)'))
    checks['current_below_1pct_nominal_1A'] = abs(values['current_end_A'])<.01
    checks['requested_fault_present'] = bool(after) and abs(max(val(r,'v(iprof)') for r in after)-1.8)<1e-6
    return dict(status='not run to completion' if completion!='passed' else 'passed' if all(checks.values()) else 'failed', checks=checks, values=values,
        limitations='No comparator accuracy, full serial counter readback, real FET, physical RC, alternate clocks, or SEU fill qualification. Partial observations cannot establish whole-fixture acceptance.')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('campaign', type=Path)
    a = ap.parse_args()
    out = a.campaign.resolve()
    dest = out/'electrical_acceptance.json'
    if dest.exists():
        ap.error('electrical acceptance exists; preserve prior evidence')
    manifest = json.loads((out/'run.json').read_text())
    assessment = json.loads((out/'assessment.json').read_text())
    contract=CONTRACTS.get(manifest['source_deck_sha256'])
    if contract is None or Path(manifest['source_deck']).name!=contract['source']:
        ap.error('fixture has no qualified acceptance contract in this checker')
    p = out/'observations.tsv'
    if sha(p)!=assessment['observation_sha256']:
        ap.error('observation hash changed')
    cols, rows = read_wave(p)
    r = evaluate(cols, rows, assessment['completion'],event=contract['event'],end=contract['end'])
    r.update(checker_sha256=sha(Path(__file__)), waveform_sha256=sha(p), manifest_sha256=sha(out/'run.json'), completion_assessment_sha256=sha(out/'assessment.json'), source_deck_sha256=manifest['source_deck_sha256'])
    atomic_json(dest,r)
    print(json.dumps(r,indent=2))
    if r['status']!='passed':
        raise SystemExit(1)

if __name__=='__main__':
    main()
