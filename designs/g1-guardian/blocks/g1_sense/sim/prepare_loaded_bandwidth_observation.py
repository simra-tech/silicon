#!/usr/bin/env python3
"""Prepare output-only observations of a completed loaded differential AC leaf.

No simulator launch, device edit, injected source or parameter choice. Runtime
qualification and exact baseline AC/OP/parameter parity remain required.
"""
import argparse
import json
from pathlib import Path
import re
from run_loaded_noise_audit import sha
from run_loaded_followthrough import get_reference

FIELDS = ['gm', 'gmb', 'gds', 'ids', 'vds', 'vgs', 'vsb', 'cgg', 'cgd', 'cgs']


def build(original, source, groups, old_output, output):
    devices = [q[:-3] for q in groups['NON_BGR']
               if q.startswith('@n.xs.xota.') and q.endswith('[w]')]
    assert len(devices) == len(set(devices)) == 19
    match = re.search(r'(?im)^\.subckt g1_ota_main_candidate (.+)$', source)
    assert match
    section = source[match.end():].split('.ends', 1)[0]
    ports = set(match.group(1).lower().split())
    nodes = set()
    for line in section.splitlines():
        parts = line.lower().split()
        if not parts or not parts[0].startswith('x'):
            continue
        if parts[0].startswith('xm'):
            nodes.update(parts[1:5])
        elif parts[0] == 'xrz':
            nodes.update(parts[1:4])
        elif parts[0] == 'xcc':
            nodes.update(parts[1:3])
        else:
            raise AssertionError('Unknown source primitive: '+line)
    internal = sorted(nodes - ports)
    assert set(internal) == {'vbp', 'vbnc', 'vbpc', 'tail', 'fn', 'fp',
                             'mir', 'out1', 'pc1', 'pc2', 'cz'}
    vectors = ['v(xs.xota.'+n+')' for n in internal]
    vectors += ['v(xs.vp)', 'v(xs.vn)', 'v(iptat)', 'v(isense)', 'v(vped)',
                'v(vref_buf)', 'v(vref)']
    queries = [device+'['+field+']' for device in devices for field in FIELDS]
    original_prefix, original_control = original.split('.control\n', 1)
    assert original_control.splitlines().count('op') == 1
    save = 'save '+' '.join(vectors)+'\n'
    observations = ('echo BANDWIDTH_DEVICE_OP_BEGIN\n'+
                    ''.join('print '+q+'\n' for q in queries)+
                    'echo BANDWIDTH_DEVICE_OP_END\n')
    marker = 'set numdgt=17\nset wr_singlescale\nset wr_vecnames\nac dec 100 1 1g\n'
    assert original_control.count(marker) == 1
    control = original_control.replace('\nop\n', '\n'+save+'op\n')
    control = control.replace(marker, observations+marker)
    columns = []
    extra = ''
    for index, vector in enumerate(vectors):
        for part in ['real', 'imag']:
            name = 'bw_%02d_%s' % (index, part)
            columns.append(name)
            extra += 'let '+name+'='+part+'('+vector+')\n'
    extra += 'wrdata '+str(old_output/'bandwidth_nodes.dat')+' '+' '.join(columns)+'\n'
    assert control.count('setplot op1\n') == 1
    control = control.replace('setplot op1\n', extra+'setplot op1\n')
    changed = original_prefix+'.control\n'+control
    # Remove exactly the output-only additions, then require byte-exact recovery.
    inverse = changed.replace('\n'+save+'op\n', '\nop\n')
    inverse = inverse.replace(observations, '').replace(extra, '')
    assert inverse == original
    changed = changed.replace(str(old_output), str(output))
    assert changed.replace(str(output), str(old_output)).replace(
        '\n'+save+'op\n', '\nop\n').replace(observations, '').replace(extra, '') == original
    assert changed.split('.control\n')[0] == original_prefix
    return changed, dict(devices=devices, fields=FIELDS, op_queries=queries,
                         vectors=vectors, columns=['frequency']+columns,
                         source_inverse_exact=True, precontrol_exact=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads((args.baseline/'summary.json').read_text())
    assert summary['status'] == 'passed source/OP/finite leaf'
    assert summary['kind'] == 'adverse' and summary['mode'] == 'differential'
    run, ref, preparation, expected, op = get_reference('adverse', summary['case'])
    assert summary['reference_summary_sha256'] == sha(ref/'summary.json')
    assert summary['full11512_and27_exact'] and summary['quiet_op_V'] == op
    contract = json.loads((args.baseline/'contract.json').read_text())
    assert sha(args.baseline/'probe.cir') == contract['deck_sha256']
    assert not args.output.exists()
    deck, inventory = build((args.baseline/'probe.cir').read_text(),
                            (ref/'sense.spice').read_text(), preparation['groups'],
                            args.baseline, args.output)
    inventory.update(status='prepared output-only observation; not run',
        case=summary['case'], reference_run=run,
        source_hashes=preparation['source_hashes'],
        baseline_sha256={name:sha(args.baseline/name) for name in
                         ['summary.json','contract.json','provenance.json','probe.cir','ac.dat','input_basis.dat']},
        runtime_contract='Exact expected_runtime_identity from qualified reference; unchanged cards/options',
        required_controls=['all11512+27 before/after exact', 'all9 original quietOP exact',
            'original901complex AC values bit-exact', 'differential input basis exact',
            'all190 model fields available/finite with exact names',
            'all18 native-source node spectra finite with exact headers/frequency grid',
            'log error gate independent of simulator exit', 'exact source inverse and hashes'],
        child_timeout_s=120,
        scope='Model small-signal observables, not physical terminal currents or junction reference-plane qualification. Signed cgg/cgd/cgs are model Jacobian fields, not assigned positive lumped capacitors. No compensation selection or adoption.')
    args.output.mkdir(parents=True)
    (args.output/'probe.cir').write_text(deck)
    (args.output/'contract.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (args.output/'preparer.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status=inventory['status'], devices=len(inventory['devices']),
                         model_queries=len(inventory['op_queries']),
                         native_nodes=len(inventory['vectors']))))


if __name__ == '__main__':
    main()
