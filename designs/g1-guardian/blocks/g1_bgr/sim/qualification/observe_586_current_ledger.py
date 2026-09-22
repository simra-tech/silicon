#!/usr/bin/env python3
"""Full source-device raw current ledger; external-port mapping is a separate gate."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from run_586_pvt import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def inventory(source):
    rows = []
    for line in source.splitlines():
        if not line.startswith(('XM', 'XR', 'XQ')):
            continue
        words = line.split()
        name = words[0].lower()
        if line.startswith('XM'):
            model = words[5]
            assert model in ['sg13_hv_pmos', 'sg13_hv_nmos']
            queries = ['@n.xbgr.'+name+'.n'+model+'['+field+']' for field in ['ide', 'ige', 'ise', 'ibe', 'ctype']]
            terminals = ['D', 'G', 'S', 'B']
            status = 'raw total-current fields; external polarity mapping requires independent KCL/control'
        elif line.startswith('XQ'):
            model = words[5]
            assert model == 'npn13G2'
            queries = ['@q.xbgr.'+name+'.qnpn13g2['+field+']' for field in ['ic', 'ib', 'ie', 'is']]+['@r.xbgr.'+name+'.rsub[i]', '@c.xbgr.'+name+'.csub[i]']
            terminals = ['C', 'B', 'E', 'BN']
            status = 'raw intrinsic C/B/E/S plus explicit Rsub/Csub branches; thermal current excluded; external BN mapping separately audited'
        else:
            model = words[4]
            assert model in ['rhigh', 'rppd']
            queries = ['@n.xbgr.'+name+'.nr1[ibody]']
            terminals = ['1', '2', 'BN']
            status = 'internal body current only; external end and substrate currents not directly available, not silently treated as zero'
        rows.append(dict(source_name=words[0], model=model, terminals=dict(zip(terminals, words[1:1+len(terminals)])), queries=queries, mapping_status=status))
    assert len(rows) == 1036
    assert sum(r['source_name'].startswith('XM') for r in rows) == 336
    assert sum(r['source_name'].startswith('XQ') for r in rows) == 301
    assert sum(r['source_name'].startswith('XR') for r in rows) == 399
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    args = p.parse_args()
    base = HERE/'runs/bgr_one_draw_20260922_r1'
    qm = json.loads((base/'manifest.json').read_text())
    ref = base/'disabled'
    metadata = HERE/'runs/bgr586-terminal-metadata-20260922-a'
    mr, = json.loads((metadata/'summary.json').read_text())
    assert mr['status'].startswith('passed') and mr['full2842_before_after_original_exact'] and mr['original_dc_decoded_bytes_exact']
    source = (ref/'pex_nominal.spice').read_text()
    assert sha(ref/'pex_nominal.spice') == qm['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    rows = inventory(source)
    queries = sum([r['queries'] for r in rows], [])
    assert len(queries) == len(set(queries)) == 3885
    ports, = re.findall(r'^\.subckt g1_bgr (.+)$', source, re.M | re.I)
    ports = ports.split()
    external = dict(zip(ports, ['vdd', '0', 'r4', 'vref', 'iptat', 'pbias', 'pcasc', 'vbe', 'dvbe']))
    assert ports == ['vdd', 'vss', 'r4', 'vref', 'iptat', 'pbias', 'pcasc', 'vbe', 'dvbe']
    nodes = sorted(set(n for r in rows for n in r['terminals'].values()))
    # Ground is an exact fixture connection, not an independently solved vector.
    vectors = [('v(vdd)-v(vdd)' if external.get(n) == '0' else 'v('+external.get(n, 'xbgr.'+n)+')') for n in nodes]+['i(vdd)', 'i(vload)', 'i(vr4)', 'i(vsub)']
    original = (ref/'nominal.cir').read_text()
    assert original.count('\nop\n') == 1
    commands = 'echo RAW_CURRENT_LEDGER_BEGIN\n'+'\n'.join('print '+q for q in queries)+'\necho RAW_CURRENT_LEDGER_END\nwrdata op_nodes.dat '+' '.join(vectors)+'\n'
    deck = original.replace('\nop\n', '\nop\n'+commands)
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qm['runtime']['pdk_commit']
    assert args.image_id == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == qm['ngspice']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert qm['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    out = allocate_run(HERE.parent, args.run_id, relative_parent='qualification/runs')
    for name in ['pex_nominal.spice', '.spiceinit']:
        (out/name).write_bytes((ref/name).read_bytes())
    (out/'nominal.cir').write_text(deck)
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'declared_terminal_ledger_output.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), deck.splitlines(True), fromfile='qualifiedOriginal', tofile='rawCurrentOutputOnly')))
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), image_manifest=args.image_id, runtime=qm['runtime'], ngspice=qm['ngspice'], source_sha256=sha(out/'pex_nominal.spice'), deck_sha256=sha(out/'nominal.cir'),
                      reference_manifest_sha256=sha(base/'manifest.json'), metadata_summary_sha256=sha(metadata/'summary.json'), original_deck_sha256=sha(ref/'nominal.cir'), original_wave_sha256=sha(ref/'nominal.dat'), source_device_inventory=rows, node_order=nodes, exported_vectors=vectors,
                      scope='Nominal27C originalfirstOP, output-only1036device3885rawcurrent/modelpolarity fields and source-node voltages. No source/model changes. All2842/originalDCbytes exact required. Raw intrinsic/body fields are not automatically qualified external terminal currents; unavailable resistor substrate/end currents explicit.')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'nominal.cir'], stream, out/'run.json', 120, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    result = dict(status='failed', runtime=state, warnings=warning_inventory(log), scope=provenance['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0
        assert not re.search(r'^Error|no such vector|no such parameter|analysis aborted|Timestep too small', log, re.M)
        section, = re.findall(r'^RAW_CURRENT_LEDGER_BEGIN\n(.*?)^RAW_CURRENT_LEDGER_END$', log, re.M | re.S)
        values = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', section, re.M)
        assert [k for k, v in values] == queries and all(np.isfinite(float(v)) for k, v in values)
        remainder = log.replace(section, '')
        parameters = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', remainder, re.M)
        oldparams = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', (ref/'run.log').read_text(), re.M)
        assert parameters == oldparams and [k for k, v in parameters] == qm['parameters']*2
        assert parameters[:2842] == parameters[2842:]
        result['original_dc_bytes_exact'] = (out/'nominal.dat').read_bytes() == (ref/'nominal.dat').read_bytes()
        assert result['original_dc_bytes_exact']
        data = np.loadtxt(str(out/'op_nodes.dat'), skiprows=1, ndmin=2)
        assert data.shape == (1, len(vectors)+1) and np.isfinite(data).all()
        result.update(status='passed raw ledger and exact output-only parity; external mappings separately unqualified', raw_fields=values,
                      full2842_before_after_original_exact=True, op_node_and_supply_values=dict(zip(vectors, data[0, 1:].tolist())),
                      source_devices=1036, raw_fields_count=len(values), parameter_before=parameters[:2842], parameter_after=parameters[2842:])
    except (AssertionError, ValueError, OSError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['warnings', 'raw_fields', 'parameter_before', 'parameter_after', 'op_node_and_supply_values']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
