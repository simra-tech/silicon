#!/usr/bin/env python3
"""Resume canonical routed views at RC extraction with matching pinned tools."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('state', 'database', 'netlist', 'powered-netlist', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and not a.output.exists()
    bindir = Path('/foss/tools/openroad-librelane/bin')
    os.environ['PATH'] = str(bindir)+os.pathsep+os.environ['PATH']
    os.environ['_LLN_OVERRIDE_OPENROAD'] = str(bindir/'openroad')
    os.environ['_OPENLANE_MAX_CORES'] = '1'
    from librelane.common import set_tpe, _get_process_limit
    from librelane.config import Config
    from librelane.flows import Flow
    from librelane.state import State
    set_tpe(ThreadPoolExecutor(max_workers=1))
    assert _get_process_limit() == 1
    views = json.loads(a.state.read_text())
    assert set(views) == {'odb', 'def', 'nl', 'pnl', 'sdc', 'json_h', 'vh', 'metrics'}
    original_views = dict(views)
    views.update(odb=str(a.database), **{'def': str(a.database.with_suffix('.def'))},
                 nl=str(a.netlist), pnl=str(a.powered_netlist))
    # Geometry metrics survive the exact inverse DEF proof. Timing is recomputed.
    stale = ('timing__', 'clock__', 'power__', 'design__max_slew_',
             'design__max_cap_', 'design__max_fanout_')
    views['metrics'] = {k:v for k,v in views['metrics'].items() if not k.startswith(stale)}
    proofs = [a.database.parent/'summary.json', a.netlist.parent/'summary.json',
              a.powered_netlist.parent/'summary.json']
    db_proof, nl_proof, pnl_proof = [json.loads(x.read_text()) for x in proofs]
    assert db_proof['status'] == 'passed exact inverse DEF and saved OpenDB roundtrip'
    assert db_proof['input_sha256'] == sha(Path(original_views['odb']))
    assert db_proof['outputs_sha256']['g1_digital.odb'] == sha(a.database)
    assert db_proof['outputs_sha256']['g1_digital.def'] == sha(a.database.with_suffix('.def'))
    for key, proof, path in [('nl', nl_proof, a.netlist), ('pnl', pnl_proof, a.powered_netlist)]:
        assert proof['status'] == 'passed exact reversible two-instance rename'
        assert proof['input_sha256'] == sha(Path(original_views[key]))
        assert proof['output_sha256'] == sha(path)
        assert proof['mapping'] == db_proof['mapping']
    config = Path('/work/designs/g1-guardian/blocks/g1_ctrl/flow/config_tmr_spread.yaml')
    inputs = [a.state, config, Path(__file__), bindir/'sta', bindir/'openroad'] + proofs
    inputs += [Path(v) for k,v in views.items() if k != 'metrics']
    held = {str(path): sha(path) for path in inputs}
    meta = Config.get_meta(str(config))
    cls = Flow.factory.get(meta.flow).Substitute(meta.substituting_steps)
    flow = cls(str(config), pdk='ihp-sg13g2', pdk_root='/foss/pdks')
    ids = [step.id for step in flow.Steps]
    assert ids.count('OpenROAD.RCX') == 1
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'initial_state.json').write_text(json.dumps(views, indent=2)+'\n')
    record = dict(status='running', inputs_sha256=held, start_step='OpenROAD.RCX',
                  steps=ids, affinity=sorted(os.sched_getaffinity(0)), threads=1,
                  sta_version=subprocess.check_output([str(bindir/'sta'), '-version'], text=True),
                  not_run=['Full-chip integration/adoption', 'Independent final-view audits'],
                  not_applicable=['Statistical seed'])
    def save():
        (a.output/'summary.json').write_text(json.dumps(record, indent=2)+'\n')
    save()
    started = time.monotonic()
    try:
        final = flow.start(with_initial_state=State.load(views),
                           _force_run_dir=str(a.output/'flow'), frm='OpenROAD.RCX')
        (a.output/'final_state.json').write_text(final.dumps())
        assert all(sha(Path(path)) == value for path,value in held.items())
        record['status'] = 'passed downstream flow execution; independent audits pending'
    except Exception as exc:
        record.update(status='failed downstream flow', error=repr(exc))
        raise
    finally:
        record['wall_s'] = time.monotonic()-started
        save()


if __name__ == '__main__':
    main()
