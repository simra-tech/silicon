#!/usr/bin/env python3
"""Source-held CTS clustering experiment; never updates the adopted macro."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment_text(original, output, cluster):
    """Change only five output paths and the declared clustering option."""
    assert cluster in (0, 8)
    assert not re.search(r'CTS_SINK_CLUSTERING_SIZE', original)
    replacements = []
    for kind, suffix in [('ODB', 'odb'), ('DEF', 'def'), ('SDC', 'sdc'),
                         ('NL', 'nl.v'), ('PNL', 'pnl.v')]:
        pattern = r'^set ::env\(SAVE_' + kind + r'\) (.+)$'
        hits = re.findall(pattern, original, re.M)
        assert len(hits) == 1
        old = 'set ::env(SAVE_' + kind + ') ' + hits[0]
        new = 'set ::env(SAVE_' + kind + ') {' + str(output / ('g1_digital.' + suffix)) + '}'
        replacements.append((old, new))
    result = original
    for old, new in replacements:
        result = result.replace(old, new)
    addition = 'set ::env(CTS_SINK_CLUSTERING_SIZE) 8\n' if cluster else ''
    result += addition
    restored = result[:-len(addition)] if addition else result
    for old, new in replacements:
        restored = restored.replace(new, old)
    assert restored == original
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--cluster', required=True, type=int, choices=(0, 8))
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    root = Path('/work')
    flow = root / 'designs/g1-guardian/blocks/g1_ctrl/flow'
    old = flow / 'runs/run7/35-openroad-cts/_env.tcl'
    odb = flow / 'runs/run7/34-openroad-detailedplacement/g1_digital.odb'
    sdc = flow / 'g1_digital.sdc'
    assert sha(old) == 'cb4c7d0f37320acff4072a347aff1446084c1e279a4882a8da49abad503335e1'
    assert sha(odb) == 'fb92d5d466f4d841324082476ef3bf6f88bbd1838ca6a8d23dab9c198a426876'
    assert sha(sdc) == 'c36bf03041045f951179e22970de05bcdcae2dd66374f175a9da8e91a2b84673'
    import librelane
    scripts = Path(librelane.__file__).parent / 'scripts'
    tool = Path(shutil.which('openroad')).resolve()
    inputs = [old, odb, sdc, tool] + sorted((scripts / 'openroad').rglob('*.tcl'))
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    for lib in ('sg13g2_stdcell', 'sg13g2_io'):
        inputs += sorted((pdk / 'libs.ref' / lib / 'lib').glob('*.lib'))
    hashes = {str(x): sha(x) for x in inputs}
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    envfile = a.output / '_env.tcl'
    envfile.write_text(environment_text(old.read_text(), a.output, a.cluster))
    wrapper = a.output / 'run.tcl'
    wrapper.write_text('\n'.join([
        'set_thread_count 1',
        'source {' + str(scripts / 'openroad/cts.tcl') + '}',
        # Report both unchanged macro constraints and the integrated fanout
        # constraint. The second report does not alter the CTS algorithm.
        'report_check_types -max_slew -max_capacitance -max_fanout -violators > {' + str(a.output / 'macro_violators.rpt') + '}',
        'set_max_fanout 8 [current_design]',
        'report_check_types -max_fanout -violators > {' + str(a.output / 'integrated_fanout.rpt') + '}',
        'set fp [open {' + str(a.output / 'counts.tsv') + '} w]',
        'foreach name {sclk osc_clk} {puts $fp "$name\\t[llength [all_registers -clock $name]]"}',
        'close $fp',
        'puts CTS_FANOUT_EXPERIMENT_COMPLETE',
    ]) + '\n')
    env = os.environ.copy()
    env.update(SCRIPTS_DIR=str(scripts), STEP_DIR=str(a.output),
               _TCL_ENV_IN=str(envfile), _SDC_IN=str(sdc), OMP_NUM_THREADS='1')
    command = ['timeout', '--kill-after=5', '240', str(tool), '-exit', '-no_splash', str(wrapper)]
    result = dict(status='running', cluster=a.cluster, inputs=hashes, command=command,
                  tool_version=subprocess.check_output([str(tool), '-version'], universal_newlines=True).strip(),
                  not_run=['Routed timing', 'Functional equivalence', 'TMR separation',
                           'Pin geometry preservation', 'DRC/LVS/antenna/density',
                           'Integrated adoption'])
    start = time.monotonic()
    try:
        with (a.output / 'tool.log').open('x') as log:
            child = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        result.update(returncode=child.returncode, wall_s=time.monotonic()-start)
        text = (a.output / 'tool.log').read_text()
        assert child.returncode == 0 and 'CTS_FANOUT_EXPERIMENT_COMPLETE' in text
        assert not re.search(r'(^|\n)(Error:|\[ERROR)', text)
        assert all(sha(Path(x)) == h for x, h in hashes.items())
        counts = dict(line.split('\t') for line in (a.output / 'counts.tsv').read_text().splitlines())
        assert {k: int(v) for k, v in counts.items()} == {'sclk': 52, 'osc_clk': 1148}
        report = (a.output / 'integrated_fanout.rpt').read_text()
        result.update(status='passed CTS execution and clock register counts', counts=counts,
                      integrated_fanout_status='failed' if '(VIOLATED)' in report else 'passed',
                      outputs={x.name: sha(x) for x in a.output.iterdir() if x.is_file()})
    except Exception as exc:
        result.update(status='failed CTS execution or source/count contract', error=repr(exc))
        raise
    finally:
        (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
