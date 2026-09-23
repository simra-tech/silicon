#!/usr/bin/env python3
"""One waveform-only 2us diagnostic of the preserved failed 76002 draw."""
import difflib
import json
from pathlib import Path
import re
from prepare_586_adverse_population import HERE, ROOT, sha
from result_directory import allocate_run

ORIGINAL = HERE/'runs/t2f586-fast-population-controls-20260923-a-changed'
MEASUREMENTS = '''meas tran t_a when v(fout)=0.6 rise=8
meas tran t_b when v(fout)=0.6 rise=24
let freq = (24-8)/(t_b-t_a)
print freq
meas tran i33_avg avg i(vdd) from=t_a to=t_b
meas tran i12_avg avg i(vdd12) from=t_a to=t_b
meas tran vref_avg avg v(vref) from=t_a to=t_b
meas tran vth_avg avg v(xt2f.vth) from=t_a to=t_b
meas tran cap1_max max v(xt2f.cap1) from=t_a to=t_b
meas tran fout_hi max v(fout) from=t_a to=t_b
meas tran fout_lo min v(fout) from=t_a to=t_b
meas tran t_half_a trig v(fout) val=0.6 rise=8 targ v(fout) val=0.6 fall=8

'''


def make_prefix(original):
    assert original.count('tran 5n 32u\n') == 1 and original.count(MEASUREMENTS) == 1
    assert original.count('setseed 76002\n') == original.count('\nreset\n') == 1
    assert 'echo P0_T2F_AFTER_END\n'+MEASUREMENTS+'wrdata phase0.dat ' in original
    deck = original.replace('tran 5n 32u\n', 'tran 5n 2u\n').replace(MEASUREMENTS, '')
    assert not re.search(r'(?mi)^\s*(?:meas(?:ure)?\s|let\s+freq\b|print\s+freq\b)', deck)
    restored = deck.replace('tran 5n 2u\n', 'tran 5n 32u\n').replace('wrdata phase0.dat ', MEASUREMENTS+'wrdata phase0.dat ')
    assert restored == original
    assert deck.split('.control\n')[0] == original.split('.control\n')[0]
    return deck


def main():
    run_id = 't2f586-fast76002-prefix2us-20260923-a'
    packet_path = HERE/(run_id+'.json')
    assert not packet_path.exists()
    failure, = json.loads((ORIGINAL/'summary.json').read_text())
    audit_path = HERE/'t2f586-fast76002-failure-analysis-20260923-r2.json'
    audit = json.loads(audit_path.read_text())
    assert failure['control_status'] == 'failed' and failure['runtime']['status'] == 'timeout'
    assert audit['full3180_before_status'] == 'passed complete declared query inventory'
    prep = json.loads((ORIGINAL/'preparation.json').read_text())
    out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
    for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'population_inventory.json']:
        (out/name).write_bytes((ORIGINAL/name).read_bytes())
        assert sha(out/name) == sha(ORIGINAL/name)
    original = (ORIGINAL/'probe.cir').read_text()
    deck = make_prefix(original)
    (out/'probe.cir').write_text(deck)
    (out/'declared_prefix_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), deck.splitlines(True),
        fromfile='preservedFailed32us76002', tofile='separateWaveformOnly2us76002')))
    prep.update(run_id=run_id, status='not run; separately approved waveform-only prefix', watchdog_s=600,
        endpoint_s=2e-6, original_run=ORIGINAL.name, original_deck_sha256=sha(ORIGINAL/'probe.cir'),
        deck_sha256=sha(out/'probe.cir'), required_before3180=audit['full3180_before'],
        removed_future_commands=MEASUREMENTS.strip().splitlines(),
        scope='ONE waveform-only2us prefix of preservedfast76002 failure. Body/source/card/seed/OP/reset/tolerances/5nsstep/rails/load/13vectorsunchanged; endpoint32us->2us and explicitremovalof10meas+letfreq+printfreq commands only. Full3180 beforeaftermustexactoriginalBEFORE. No originalwaveprefixparity (noneexported), no frequency/accuracy/fullqualification/adoption/fast30release. Original600sfullfailure remainsfailed; no automaticretry.')
    for p in [ORIGINAL/'probe.cir', ORIGINAL/'summary.json', ORIGINAL/'preparation.json', ORIGINAL/'run.log',
              audit_path, HERE/'run_586_fast76002_prefix.py', Path(__file__).resolve()]:
        prep['live_bindings_sha256'][str(p.relative_to(ROOT))] = sha(p)
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    payload = dict(status='not run; one separately approved diagnostic', run_id=run_id,
        preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'),
        original_deck_sha256=sha(ORIGINAL/'probe.cir'), watchdog_s=600, endpoint_s=2e-6,
        expected_external_growth_GiB=.05, no_fast30_release=True)
    packet_path.write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps(dict(packet=str(packet_path.relative_to(ROOT)), sha256=sha(packet_path),
                         removed_commands=prep['removed_future_commands']), indent=2))


if __name__ == '__main__':
    main()
