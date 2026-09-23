#!/usr/bin/env python3
"""Generate an isolated R0.95 OSC candidate, never the production macro.

Run with pinned KLayout: klayout -b -r gen_osc_r095_candidate.py
  -rd out=<new-directory>/osc_r095.gds

Only the four RA/RB segment lengths change (58.5 -> 55.575 um).
Connections follow their generated heads; unchanged external pins/boundary and
stock DRC/LVS must be checked after generation. Existing candidate simulations
reuse baseline parasitics; this generator does not qualify those parasitics.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_SHA = '3559b7ce9173cca2fd6ccc74aa13d3017c3abe2ce853593b6071aed514095c1b'
LIB_SHA = 'fdfb517ce53885b26305d8769cc972c6b1c6bc6323d29d89841f8b8f325c29c4'
OLD = "L = {'RA': 58.5, 'RB': 58.5, 'RT1': 64.05, 'RT2': 64.05, 'RBIAS': 67.15, 'dum': 64.05}"
NEW = OLD.replace("'RA': 58.5, 'RB': 58.5", "'RA': 55.575, 'RB': 55.575")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def transformed_source(source):
    if sha(source) != BASE_SHA:
        raise ValueError('Baseline generator changed; independently review before use')
    text = source.decode()
    if text.count(OLD) != 1:
        raise ValueError('Expected exactly one resistor-length definition')
    return text.replace(OLD, NEW)


def generate(output):
    output = Path(output).resolve()
    if output.name != 'osc_r095.gds':
        raise ValueError('Use isolated output basename osc_r095.gds')
    # The retained generator replaces this substring in the entire path.
    # Reject ambiguous parents before it can write a companion outside here.
    if str(output).count('.gds') != 1:
        raise ValueError('Output parents must not contain .gds')
    targets = [output, output.with_suffix('.lef'),
               output.with_name('osc_r095_pexlabels.txt'),
               output.with_name('osc_r095_generation.json')]
    if any(p.exists() for p in targets):
        raise FileExistsError('Refusing to overwrite candidate artifacts')
    if not output.parent.is_dir():
        raise ValueError('Create a dedicated output directory first')
    if sha((HERE/'g1_layout_lib.py').read_bytes()) != LIB_SHA:
        raise ValueError('Layout helper changed; independently review before use')
    source = transformed_source((HERE/'gen_osc_layout.py').read_bytes())
    namespace = {'__name__': '__main__', '__file__': str(HERE/'gen_osc_layout.py'),
                 'out': str(output)}
    exec(compile(source, str(HERE/'gen_osc_layout.py'), 'exec'), namespace)
    if not all(p.is_file() for p in targets[:3]):
        raise RuntimeError('Missing generated geometry/interface artifacts')
    report = dict(status='generated only; physical qualification not run',
                  baseline_generator_sha256=BASE_SHA, layout_helper_sha256=LIB_SHA,
                  transformed_generator_sha256=sha(source.encode()),
                  candidate_wrapper_sha256=sha(Path(__file__).read_bytes()),
                  segment_names=['RA1', 'RA2', 'RB1', 'RB2'],
                  old_length_um=58.5, new_length_um=55.575,
                  outputs_sha256={p.name: sha(p.read_bytes()) for p in targets[:3]},
                  stock_drc='not run', stock_lvs='not run', new_pex='not run',
                  production_adoption='not run', silicon_measurement='not run')
    targets[3].write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    generate(globals().get('out', ''))
