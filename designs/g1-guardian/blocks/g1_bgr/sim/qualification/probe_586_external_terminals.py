#!/usr/bin/env python3
"""Copied-source22port probe control; preserve original model cards and failed comparisons."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from run_586_pvt import sha
from observe_586_current_ledger import inventory
from audit_586_raw_terminal_mapping import candidate_mos

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory

SELECTED = ['XM34', 'XM35', 'XM38', 'XR1', 'XR16', 'XQ56']


def json_orientation(value):
    return None if value is None else bool(value)


def instrument(source):
    selected = [r for name in SELECTED for r in inventory(source) if r['source_name'] == name]
    assert len(selected) == 6
    records = []
    changed = source
    for row in selected:
        line, = re.findall(r'^'+re.escape(row['source_name'])+r' .+$', changed, re.M)
        fields = line.split()
        branches = []
        for i, (terminal, node) in enumerate(row['terminals'].items()):
            monitor = 'obs_'+row['source_name'].lower()+'_'+terminal.lower()
            meter = 'V'+monitor
            fields[i+1] = monitor
            branches.append(dict(terminal=terminal, source_node=node, monitor_node=monitor, meter=meter,
                                 line=meter+' '+node+' '+monitor+' 0'))
        replacement = ' '.join(fields)+'\n'+'\n'.join(b['line'] for b in branches)
        changed = changed.replace(line+'\n', replacement+'\n')
        records.append(dict(row, original_line=line, replacement=replacement, branches=branches))
    restored = changed
    for row in records:
        restored = restored.replace(row['replacement']+'\n', row['original_line']+'\n')
    assert restored == source and sum(len(r['branches']) for r in records) == 22
    return changed, records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    args = p.parse_args()
    base = HERE/'runs/bgr_one_draw_20260922_r1'
    qm = json.loads((base/'manifest.json').read_text())
    ref = base/'disabled'
    rawref = HERE/'runs/bgr586-raw-current-ledger-20260922-a'
    rr, = json.loads((rawref/'summary.json').read_text())
    assert rr['status'].startswith('passed raw ledger') and rr['original_dc_bytes_exact']
    source = (ref/'pex_nominal.spice').read_text()
    assert sha(ref/'pex_nominal.spice') == qm['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    instrumented, records = instrument(source)
    queries = sum([r['queries'] for r in records], [])
    branches = sum([r['branches'] for r in records], [])
    vectors = ['i(v.xbgr.'+b['meter'].lower()+')' for b in branches]+['v(xbgr.'+b['monitor_node']+')' for b in branches]
    original = (ref/'nominal.cir').read_text()
    assert original.count('\nop\n') == 1
    additions = 'echo EXTERNAL_PORT_QUERY_BEGIN\n'+'\n'.join('print '+q for q in queries)+'\necho EXTERNAL_PORT_QUERY_END\nwrdata external_ports.dat '+' '.join(vectors)+'\n'
    deck = original.replace('\nop\n', '\nop\n'+additions)
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qm['runtime']['pdk_commit']
    assert args.image_id == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == qm['ngspice']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert qm['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    spinit = Path('/foss/tools/ngspice/share/ngspice/scripts/spinit')
    # This standalone fixture differs from joint SENSE: no 1Tohm global rshunt.
    for text in [deck, instrumented, (ref/'.spiceinit').read_text(), spinit.read_text()]+[f.read_text(errors='replace') for f in (pd/'libs.tech/ngspice/models').glob('*.lib')]:
        assert not re.search(r'(?im)^[^*\n]*\brshunt\b', text)
    out = allocate_run(HERE.parent, args.run_id, relative_parent='qualification/runs')
    (out/'pex_nominal.spice').write_text(instrumented)
    (out/'.spiceinit').write_bytes((ref/'.spiceinit').read_bytes())
    (out/'nominal.cir').write_text(deck)
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'declared_external_port_source.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True), instrumented.splitlines(True), fromfile='canonical586', tofile='copied22PortProbes')))
    (out/'declared_external_port_deck.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), deck.splitlines(True), fromfile='originalNominal', tofile='sameSettingsCurrentOutputs')))
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), image_manifest=args.image_id, runtime=qm['runtime'], ngspice=qm['ngspice'], canonical_source_sha256=sha(ref/'pex_nominal.spice'), source_sha256=sha(out/'pex_nominal.spice'), deck_sha256=sha(out/'nominal.cir'),
                      reference_manifest_sha256=sha(base/'manifest.json'), raw_ledger_summary_sha256=sha(rawref/'summary.json'), source_restoration_exact=True, source_changes=records,
                      original_spiceinit_sha256=sha(ref/'.spiceinit'), system_spinit_sha256=sha(spinit),
                      effective_settings_basis='Exact inherited standalone deck/.spiceinit/systemspinit and all pinned model libraries checked: no rshunt setting. No shunt added. Original seed44001/gmin1e-15/abstol1e-14/reltol1e-5/vntol1e-7 preserved. Measured port-vs-field branch law independently checked.',
                      prospective_mapping_maximum_abs_delta_A=1e-12,
                      scope='One nominal27C22port copied-source zeroVprobe control: forwardNMOSXM34/reverseNMOSXM35/PMOSXM38, rhighXR1/rppdXR16,HBTXQ56. No modelcard edits. Exact canonical source restoration/full2842; originalDCwave exactcomparison remains independent. Perportmapping1pA prospective bound; not all-temperature/transient external-port qualification.')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'nominal.cir'], stream, out/'run.json', 120, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    result = dict(status='failed', runtime=state, warnings=warning_inventory(log), scope=provenance['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0
        assert not re.search(r'^Error|no such vector|no such parameter|analysis aborted|Timestep too small', log, re.M)
        section, = re.findall(r'^EXTERNAL_PORT_QUERY_BEGIN\n(.*?)^EXTERNAL_PORT_QUERY_END$', log, re.M | re.S)
        values = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', section, re.M)
        assert [k for k, v in values] == queries and all(np.isfinite(float(v)) for k, v in values)
        params = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log.replace(section, ''), re.M)
        oldparams = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', (ref/'run.log').read_text(), re.M)
        assert params == oldparams and [k for k, v in params] == qm['parameters']*2 and params[:2842] == params[2842:]
        result['full2842_original_before_after_exact'] = True
        result['original_dc_bytes_exact'] = (out/'nominal.dat').read_bytes() == (ref/'nominal.dat').read_bytes()
        oldwave = np.loadtxt(str(ref/'nominal.dat'), skiprows=1)
        newwave = np.loadtxt(str(out/'nominal.dat'), skiprows=1)
        assert newwave.shape == oldwave.shape == (34, 12) and np.isfinite(newwave).all()
        result['original_dc_numeric_rows_exact'] = bool(np.array_equal(oldwave, newwave))
        result['original_dc_maximum_abs_column_deltas'] = np.abs(newwave-oldwave).max(axis=0).tolist()
        data = np.loadtxt(str(out/'external_ports.dat'), skiprows=1, ndmin=2)
        assert data.shape == (1, 45) and np.isfinite(data).all()
        measured, voltages = data[0, 1:23], data[0, 23:]
        rawvalues = {k: float(v) for k, v in values}
        mapped, offset = [], 0
        for row in records:
            n = len(row['branches'])
            observed = measured[offset:offset+n]
            nodev = voltages[offset:offset+n]
            q = [rawvalues[k] for k in row['queries']]
            if row['source_name'].startswith('XM'):
                predicted, swap = candidate_mos(q, nodev[0], nodev[2])
            elif row['source_name'].startswith('XQ'):
                predicted, swap = q[:3]+[-q[4]-q[5]], None
            else:
                predicted, swap = [-q[0], q[0], 0.0], None
            delta = observed-np.array(predicted)
            mapped.append(dict(source_name=row['source_name'], terminals=list(row['terminals']), measured_external_currents_A=observed.tolist(), monitor_voltages_V=nodev.tolist(),
                               model_field_predicted_A=predicted, delta_A=delta.tolist(), maximum_abs_delta_A=float(np.abs(delta).max()),
                               signed_port_current_sum_A=float(observed.sum()), internal_drain_source_swapped=json_orientation(swap),
                               resistor_substrate_scope='Measured explicitly; zero prediction is tested at this one OP only, not assumed at other states.' if row['source_name'].startswith('XR') else 'not applicable'))
            offset += n
        result['representative_external_mapping'] = mapped
        result['raw_model_fields'] = values
        result['all22_mapping_within_1pA'] = all(r['maximum_abs_delta_A'] <= 1e-12 for r in mapped)
        assert result['all22_mapping_within_1pA']
        result['status'] = 'passed nominal representative22port mapping; originalDCexact status separate'
    except (AssertionError, ValueError, OSError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['warnings', 'raw_model_fields']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
