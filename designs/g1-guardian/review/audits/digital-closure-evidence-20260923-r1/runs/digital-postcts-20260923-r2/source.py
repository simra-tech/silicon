#!/usr/bin/env python3
"""Resume a hash-held CTS candidate through the unchanged downstream flow."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initial_views(old, candidate):
    # Only source headers survive. Old SDF, placement and timing metrics do not.
    result = {key: old[key] for key in ('json_h', 'vh')}
    for key, suffix in [('odb', 'odb'), ('def', 'def'), ('nl', 'nl.v'),
                        ('pnl', 'pnl.v'), ('sdc', 'sdc')]:
        result[key] = str(candidate / ('g1_digital.' + suffix))
    result['metrics'] = {key: value for key, value in old['metrics'].items()
                         if key.startswith(('design__lint_', 'synthesis__'))
                         or key in ('design__inferred_latch__count',
                                    'design__instance_unmapped__count')}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and not a.output.exists()
    a.candidate = a.candidate.resolve()
    a.output = a.output.resolve()
    assert a.candidate != a.output and a.candidate not in a.output.parents
    os.environ['_LLN_OVERRIDE_OPENROAD'] = '/foss/tools/openroad-librelane/bin/openroad'
    os.environ['_OPENLANE_MAX_CORES'] = '1'
    from librelane.common import set_tpe, _get_process_limit
    from librelane.config import Config
    from librelane.flows import Flow
    from librelane.state import State
    set_tpe(ThreadPoolExecutor(max_workers=1))
    assert _get_process_limit() == 1
    flow_dir = Path('${REPOSITORY}/designs/g1-guardian/blocks/g1_ctrl/flow')
    config = flow_dir / 'config_tmr_spread.yaml'
    old_state = flow_dir / 'runs/run7/35-openroad-cts/state_in.json'
    candidate_hashes = {
        'g1_digital.odb': '24d4207bcdc507b114f9237d004872155d32756f888b1e23d0c63668cc961c6b',
        'g1_digital.def': 'c49dd1b75bed7fba3eefc229fc7642887acf4ebffc92061e40371ce4c20bd140',
        'g1_digital.nl.v': 'f991e5af3fa1a5ad1b0178de8287c1dc4519269f1c645a9a914a2bad430f8ad7',
    }
    assert all(sha(a.candidate / name) == value for name, value in candidate_hashes.items())
    old = json.loads(old_state.read_text())
    views = initial_views(old, a.candidate)
    state = State.load(views)
    inputs = [config, old_state, flow_dir / 'g1_digital.sdc', Path(__file__),
              Path(os.environ['_LLN_OVERRIDE_OPENROAD'])]
    inputs += [Path(value) for key, value in views.items() if key != 'metrics']
    held = {str(path): sha(path) for path in inputs}
    meta = Config.get_meta(str(config))
    assert meta.flow == 'Classic' and meta.substituting_steps is not None
    cls = Flow.factory.get(meta.flow).Substitute(meta.substituting_steps)
    flow = cls(str(config), pdk='ihp-sg13g2', pdk_root='/foss/pdks')
    ids = [step.id for step in flow.Steps]
    assert ids.count('OpenROAD.CTS') == 1
    start_step = ids[ids.index('OpenROAD.CTS') + 1]
    assert start_step == 'OpenROAD.STAMidPNR-1'
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'initial_state.json').write_text(json.dumps(views, indent=2) + '\n')
    record = dict(status='running', inputs_sha256=held, start_step=start_step,
                  steps=ids, affinity=sorted(os.sched_getaffinity(0)), threads=1,
                  not_run=['Full-chip integration and adoption',
                           'Independent affected-view audits'],
                  not_applicable=['Statistical seed'])
    def save():
        (a.output / 'summary.json').write_text(json.dumps(record, indent=2) + '\n')
    save()
    started = time.monotonic()
    try:
        final = flow.start(with_initial_state=state,
                           _force_run_dir=str(a.output / 'flow'), frm=start_step)
        (a.output / 'final_state.json').write_text(final.dumps())
        assert all(sha(Path(path)) == value for path, value in held.items())
        record['status'] = 'passed downstream flow execution; independent audits pending'
    except Exception as exc:
        record.update(status='failed downstream flow', error=repr(exc))
        raise
    finally:
        record['wall_s'] = time.monotonic() - started
        save()


if __name__ == '__main__':
    main()
