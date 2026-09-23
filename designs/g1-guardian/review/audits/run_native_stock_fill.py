#!/usr/bin/env python3
"""Run unmodified pinned fill macros and prove only additive filler changed."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import subprocess
import sys
import pya
from place_closed_analog import region, sha
from streamout_native_signal_routes import text_records

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
PDK = Path('/foss/pdks/ihp-sg13g2')
FILL = {(layer, 22) for layer in (1, 5, 8, 10, 30, 50, 67, 126, 134)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--gds-name', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--watchdog', type=int, default=600)
    a = p.parse_args()
    assert not a.output.exists() and 60 <= a.watchdog <= 1800
    assert Path(a.gds_name).name == a.gds_name and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    pin = (PDK/'COMMIT').read_text().strip()
    assert pin == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    source = a.candidate/a.gds_name; meta = json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source) == meta['GDS_sha256']
    before = pya.Layout(); before.read(str(source)); bt = before.top_cell()
    assert before.dbu == .001 and bt.bbox() == pya.Box(0, 0, 1414000, 1414000)
    boundary = region(before, bt, pya.LayerInfo(39, 4))
    assert (boundary ^ pya.Region(bt.bbox())).is_empty()
    tech = PDK/'libs.tech/klayout/tech'
    driver = tech/'scripts/filler.py'
    paths = [driver]+[tech/'macros'/('sg13g2_filler_'+name+'.lym') for name in ('ActGatP', 'Metal', 'TopMetal')]
    bindings = {str(f.relative_to(PDK)): sha(f) for f in paths}
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    output = a.output/'filled_native.gds'
    command = ['klayout', '-b', '-zz', '-r', str(driver), '-rd', 'output_file='+str(output), str(source)]
    result = dict(status='running', source_GDS_sha256=sha(source), source_metadata_sha256=sha(a.candidate/'analysis.json'),
        PDK_commit=pin, stock_filler_hashes=bindings, script_sha256=sha(Path(__file__)), command=command,
        not_run=['filled stock DRC/density/antenna', 'fill-sensitive extraction/electrical checks', 'adoption'])
    receipt = a.output/'analysis.json'; receipt.write_text(json.dumps(result, indent=2)+'\n')
    with (a.output/'tool.log').open('x') as stream:
        state = run_bounded(command, stream, a.output/'run.json', a.watchdog, cwd=ROOT,
            env=dict(os.environ, PDK_ROOT=str(PDK.parent), PDK=PDK.name, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'), interval_s=1)
    result.update(status='failed stock fill or geometry preservation', runtime=state,
        inputs_macros_unchanged=sha(source) == result['source_GDS_sha256'] and all(sha(PDK/f) == value for f, value in bindings.items()))
    receipt.write_text(json.dumps(result, indent=2)+'\n')
    assert state['status'] == 'completed' and state['returncode'] == 0 and output.is_file()
    assert result['inputs_macros_unchanged']
    faulthandler.dump_traceback_later(60, repeat=True)
    after = pya.Layout(); after.read(str(output)); at = after.top_cell()
    assert after.dbu == before.dbu and at.name == bt.name and at.bbox() == bt.bbox()
    before_instances = collections.Counter((i.cell.name, str(i.trans)) for i in bt.each_inst())
    after_instances = collections.Counter((i.cell.name, str(i.trans)) for i in at.each_inst())
    assert not before_instances-after_instances
    assert text_records(before, bt) == text_records(after, at)
    layers = {(i.layer, i.datatype) for i in before.layer_infos()+after.layer_infos()}
    checks = []; errors = []
    for key in sorted(layers):
        old = region(before, bt, pya.LayerInfo(*key)); new = region(after, at, pya.LayerInfo(*key))
        removed = old-new; added = new-old
        checks.append(dict(layer=list(key), old_area_dbu2=old.area(), new_area_dbu2=new.area(),
                           removed_area_dbu2=removed.area(), added_area_dbu2=added.area()))
        if not removed.is_empty() or (key not in FILL and not added.is_empty()):
            errors.append(checks[-1])
    (a.output/'geometry_gate.json').write_text(json.dumps(dict(status='failed' if errors else 'passed', errors=errors, layers=checks), indent=2)+'\n')
    assert not errors, errors
    assert any(r['added_area_dbu2'] > 0 for r in checks if tuple(r['layer']) in FILL)
    result.update(status='passed stock additive fill with functional geometry held', GDS_sha256=sha(output),
        topcell=at.name, old_instances_retained=sum(before_instances.values()),
        new_fill_instances=sum((after_instances-before_instances).values()),
        functional_polygons_texts_instances_held='passed', existing_filler_not_removed='passed',
        geometry_gate_sha256=sha(a.output/'geometry_gate.json'), layers=checks)
    receipt.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2)); faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
