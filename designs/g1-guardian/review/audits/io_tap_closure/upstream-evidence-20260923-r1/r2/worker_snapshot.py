#!/usr/bin/env python3
"""Read-only source provenance; never execute downloaded generator code."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(text, name):
    found = re.search(r'^\.subckt\s+' + re.escape(name) + r'\s.*?^\.ends[^\n]*', text, re.M | re.I | re.S)
    assert found
    return found.group(0)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and not a.output.exists()
    pinned = Path('/foss/pdks/ihp-sg13g2')
    assert (pinned / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    versions = {'': '03db2a692d3969b29128c15b0ec02c6ff605087f',
                'deps/c4m-flexio': '1072d3240273f8ef43486a40712ca264687bb05b',
                'deps/PDKMaster': '06f01e66f5cb5bfa61770f8b713814537ed91e33'}
    for rel, commit in versions.items():
        assert subprocess.check_output(['git', '-C', str(a.upstream / rel), 'rev-parse', 'HEAD'], text=True).strip() == commit
        subprocess.run(['git', '-C', str(a.upstream / rel), 'diff', '--exit-code', '--quiet'], check=True)
    factory = a.upstream / 'deps/c4m-flexio/c4m/flexio/factory.py'
    tree = ast.parse(factory.read_text())
    cell = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == '_LevelUpInv')
    method = next(n for n in cell.body if isinstance(n, ast.FunctionDef) and n.name == '_create_circuit')
    calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
    instantiations = []
    nets = []
    for call in calls:
        if isinstance(call.func, ast.Attribute) and call.func.attr == 'instantiate':
            instantiations.append(dict(line=call.lineno, primitive=ast.unparse(call.args[0]),
                                       name=next(ast.literal_eval(k.value) for k in call.keywords if k.arg == 'name')))
        if isinstance(call.func, ast.Attribute) and call.func.attr == 'new_net':
            nets.append(dict(line=call.lineno, arguments={k.arg: ast.unparse(k.value) for k in call.keywords}))
    assert len(instantiations) == 8
    assert all(row['primitive'] in ('spec.nmos', 'spec.pmos', 'spec.ionmos', 'spec.iopmos') for row in instantiations)
    vss = next(row for row in nets if row['arguments']['name'] == "'vss'")
    bulk_names = re.findall(r'(\w+)\.ports\.bulk', vss['arguments']['childports'])
    assert sorted(bulk_names) == ['n_i_inv', 'n_lvld', 'n_lvld_n', 'n_lvld_n_inv']
    io = pinned / 'libs.ref/sg13g2_io'
    cdl = io / 'cdl/sg13g2_io.cdl'
    spice = io / 'spice/sg13g2_io.spice'
    spi = io / 'spice/sg13g2_io.spi'
    vacask = io / 'vacask/sg13g2_io.inc'
    assert sha(cdl) == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
    assert sha(spice) == '1d53ab7df431b717ef5aff43e1117c0224681d5cc84886da37a319280ee958d6'
    assert spi.read_bytes() == spice.read_bytes()
    cb = block(cdl.read_text(), 'sg13g2_LevelUpInv')
    sb = block(spice.read_text(), 'sg13g2_LevelUpInv')
    current_devices = [line for line in cb.splitlines() if re.match(r'^[MXR]', line, re.I)]
    assert len(current_devices) == 9
    tap = [line for line in current_devices if ' ptap1 ' in line]
    assert tap == ['XR0 vss sub! ptap1 A=1.051p P=4.1u']
    nmos = [line for line in current_devices if 'nmos ' in line]
    assert len(nmos) == 4 and all(line.split()[4] == 'sub!' for line in nmos)
    vt = vacask.read_text()
    assert vt.startswith('// Converted from IHP SG13G2 PDK for Ngspice')
    vacask_taps = [dict(line=i, text=line.strip()) for i, line in enumerate(vt.splitlines(), 1)
                   if re.search(r'\)\s+[pn]tap1\s+', line)]
    assert len(vacask_taps) == 65
    assert all(not re.search(r'\b(?:a|p|perim)\s*=', row['text'], re.I) for row in vacask_taps)
    old_paths = ['.gitmodules', 'pdm.lock', 'pyproject.toml', 'scripts/gen_spice.py',
                 'c4m/pdk/ihpsg13g2/pyspice.py', 'c4m/pdk/ihpsg13g2/pdkmaster.py',
                 'c4m/pdk/ihpsg13g2/io.py', 'c4m/pdk/ihpsg13g2/_io_compliance.py',
                 'deps/c4m-flexio/c4m/flexio/factory.py', 'deps/PDKMaster/pdkmaster/design/cell.py',
                 'deps/PDKMaster/pdkmaster/design/circuit.py', 'deps/PDKMaster/pdkmaster/io/spice/pyspice.py']
    source_hashes = {rel: sha(a.upstream / rel) for rel in old_paths}
    summary = dict(status='passed read-only alternative-source audit; strict IO LVS applicability remains unresolved',
                   pdk_commit=(pinned / 'COMMIT').read_text().strip(), upstream_commits=versions,
                   upstream_url='https://gitlab.com/Chips4Makers/c4m-pdk-ihpsg13g2/-/tree/v0.0.4',
                   source_hashes=source_hashes,
                   pinned_hashes={str(path.relative_to(pinned)): sha(path) for path in [cdl, spice, spi, vacask, io / 'doc/README.md']},
                   generator_LevelUpInv=dict(method_lines=[method.lineno, method.end_lineno], instantiations=instantiations,
                                              vss=vss, direct_vss_body_instances=bulk_names, explicit_tap_instances=0),
                   current_LevelUpInv=dict(cdl_block=cb, spice_block=sb, devices=len(current_devices), explicit_taps=tap,
                                           nmos_body_node='sub!'), vacask_taps=vacask_taps,
                   checks=dict(exact_upstream_and_dependency_commits='passed', pinned_spice_spi_byte_identity='passed',
                               explicit_generator_eight_MOS_body_connections='passed', current_nine_device_source='passed',
                               VACASK_independent_physical_AP_source='failed: converted electrical R-only view',
                               old_generator_drop_in_reference_equivalence='failed: removes explicit substrate resistor',
                               independently_source_consistent_current_native_IO_reference='not run: none established',
                               generator_execution_or_repin='not run', new_LVS='not run', geometry_source_model_deck_changes='not run',
                               analog_seed='not applicable'),
                   scope='AST inspection only; no downloaded Python import or execution, no reference rewrite or extraction-derived parameters.',
                   worker_sha256=sha(Path(__file__)))
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('vacask_taps', 'source_hashes', 'pinned_hashes', 'current_LevelUpInv')}, indent=2))


if __name__ == '__main__':
    main()
