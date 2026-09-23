#!/usr/bin/env python3
"""Conservative mapped-netlist Boolean equivalence; no timing/CDC claim."""
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


def commands(reference, candidate, library):
    # The library contains an unsupported clock-gating cell. Skip whole cells
    # with absent functions, but require every instantiated cell to resolve:
    # hierarchy -check, check -assert and zero blackboxes remain mandatory.
    # Runtime negative control proves an instantiated omitted cell is rejected.
    lines = []
    for source, name in [(reference, 'gold'), (candidate, 'gate')]:
        lines += ['read_liberty -ignore_miss_func ' + str(library), 'read_verilog ' + str(source),
                  'hierarchy -check -top g1_digital', 'proc', 'flatten',
                  'clk2fflogic', 'opt_clean', 'check -assert', 'select -assert-none a:blackbox',
                  'rename g1_digital ' + name, 'design -stash ' + name]
    lines += ['design -copy-from gold -as gold gold',
              'design -copy-from gate -as gate gate',
              'equiv_make gold gate equiv', 'hierarchy -check -top equiv',
              'equiv_struct -icells -fwd', 'equiv_simple -seq 3', 'equiv_status -assert']
    return '\n'.join(lines) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', required=True, type=Path)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    for path in (a.reference, a.candidate, a.output):
        assert re.fullmatch(r'[A-Za-z0-9_./-]+', str(path)), 'Unsafe Yosys path'
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    lib = pdk/'libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib'
    tool = Path(shutil.which('yosys')).resolve()
    held = {str(path): sha(path) for path in (a.reference, a.candidate, lib, tool)}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    script = a.output/'proof.ys'
    script.write_text(commands(a.reference, a.candidate, lib))
    cmd = ['timeout', '--kill-after=5', '180', str(tool), '-Q', '-T', '-s', str(script)]
    result = dict(status='running', inputs_sha256=held, command=cmd,
                  scope='Mapped netlist Boolean equivalence under unchanged functional Liberty and clk2fflogic global-step/negative-async-hold semantics; not timing, reset analog behavior or CDC proof',
                  not_run=['Post-route timing equivalence', 'Silicon measurement'],
                  not_applicable=['Statistical seed'])
    started = time.monotonic()
    with (a.output/'tool.log').open('x') as log:
        child = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    result.update(returncode=child.returncode, wall_s=time.monotonic()-started)
    log = (a.output/'tool.log').read_text()
    passed = child.returncode == 0 and 'Equivalence successfully proven!' in log
    held_ok = all(sha(Path(path)) == value for path, value in held.items())
    result.update(status='passed Boolean equivalence' if passed and held_ok else 'failed Boolean equivalence attempt',
                  source_held=held_ok, log_sha256=sha(a.output/'tool.log'))
    (a.output/'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if passed and held_ok else 1)


if __name__ == '__main__':
    main()
