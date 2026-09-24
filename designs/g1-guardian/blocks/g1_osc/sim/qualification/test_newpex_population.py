#!/usr/bin/env python3
"""Pure admission and saved-audit controls; launches no simulation."""
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+'.py'))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def main():
    runner = module('run_mc_newpex_population')
    audit = module('audit_newpex_population')
    ok = runner.allowed_case
    assert ok('qualify', 63401, 'nominal', '0,15', 'osc_r095_newpex_qual_20260924_r1')
    assert ok('qualify', 63411, 'slowhot', '0,15', 'osc_r095_newpex_slowhot_qual_20260924_r1')
    assert ok('screen', 63101, 'nominal', '0,15', 'osc_r095_newpex_nominal100_20260924_r1_s63101')
    assert ok('screen', 63200, 'nominal', '0,15', 'osc_r095_newpex_nominal100_20260924_r1_s63200')
    assert ok('screen', 63301, 'nominal', ','.join(map(str, range(16))), 'osc_r095_newpex_all16_20260924_r1_s63301')
    assert ok('screen', 63320, 'nominal', ','.join(map(str, range(16))), 'osc_r095_newpex_all16_20260924_r1_s63320')
    assert ok('screen', 62001, 'slowhot', '0,15', 'osc_r095_newpex_adverse100_20260924_r1_s62001')
    assert ok('screen', 62100, 'slowhot', '0,15', 'osc_r095_newpex_adverse100_20260924_r1_s62100')
    assert not ok('screen', 63100, 'nominal', '0,15', 'osc_r095_newpex_nominal100_20260924_r1_s63100')
    assert not ok('screen', 63101, 'nominal', '0,15', 'wrong-run-id')
    assert not ok('screen', 63101, 'nominal', '0,1', 'osc_r095_newpex_nominal100_20260924_r1_s63101')
    assert not ok('screen', 63301, 'nominal', '0,15', 'osc_r095_newpex_all16_20260924_r1_s63301')
    assert not ok('screen', 62001, 'nominal', '0,15', 'osc_r095_newpex_adverse100_20260924_r1_s62001')
    assert not ok('qualify', 63401, 'slowhot', '0,15', 'osc_r095_newpex_qual_20260924_r1')
    assert not ok('screen', 62101, 'slowhot', '0,15', 'osc_r095_newpex_adverse100_20260924_r1_s62101')
    assert runner.attempt_classification(True)['status'] == 'failed'
    qualification = HERE/'runs/osc_r095_newpex_qual_20260924_r1'
    manifest = json.loads((qualification/'manifest.json').read_text())
    row = next(item for item in manifest['cases'] if item['name'] == 'transient')
    assert audit.expected_deck(row, manifest['fingerprint_parameters']) == (qualification/'transient.cir').read_text()
    assert audit.wave_complete(qualification/'transient.dat')
    assert audit.log_matches(qualification/'transient.log', qualification/'transient.stderr', row)
    with tempfile.TemporaryDirectory(prefix='osc-newpex-audit-') as dirname:
        tmp = Path(dirname)
        wave = tmp/'wave.dat'
        header = ' time v(osc_clk) i(vdd) v(x1.va) v(x1.vb)\n'
        good = header+''.join('%0.9e 1 0 0 0\n' % (i*6e-9) for i in range(1001))
        wave.write_text(good)
        assert audit.wave_complete(wave)
        wave.write_text(good.replace('3.000000000e-06 1 0 0 0', '3.000000000e-06 nan 0 0 0'))
        assert not audit.wave_complete(wave)
        wave.write_text(good.replace('3.000000000e-06 1 0 0 0', '2.000000000e-06 1 0 0 0'))
        assert not audit.wave_complete(wave)
        wave.write_text('\n'.join(good.splitlines()[:500])+'\n')
        assert not audit.wave_complete(wave)
        log = tmp/'sample.log'
        stderr = tmp/'sample.stderr'
        stderr.write_text((qualification/'transient.stderr').read_text())
        text = (qualification/'transient.log').read_text()
        log.write_text(text.replace(row['fingerprints'][0], '9.999e-06', 1))
        assert not audit.log_matches(log, stderr, row)
        log.write_text(text+'\nError: corrupted after result\n')
        assert not audit.log_matches(log, stderr, row)
    assert audit.CAMPAIGNS['nominal100'][:3] == (63101, 63200, (0, 15))
    assert audit.CAMPAIGNS['all16'][:3] == (63301, 63320, tuple(range(16)))
    assert audit.CAMPAIGNS['adverse100'][:3] == (62001, 62100, (0, 15))
    with tempfile.TemporaryDirectory(prefix='osc-newpex-missing-qual-') as dirname:
        saved_here = audit.HERE
        audit.HERE = Path(dirname)
        try:
            for campaign in audit.CAMPAIGNS:
                try:
                    audit.audit(campaign)
                except ValueError as exc:
                    assert 'not run' in str(exc)
                else:
                    raise AssertionError('Missing qualification must fail closed')
        finally:
            audit.HERE = saved_here
    print('31 pure controls PASS; no population simulation or credit')


if __name__ == '__main__':
    main()
