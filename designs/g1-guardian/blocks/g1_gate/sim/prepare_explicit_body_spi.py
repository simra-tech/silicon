#!/usr/bin/env python3
"""Source-only explicit-body electrical derivative of the pinned IO SPICE view.

This is not a CDL A/P-to-resistance conversion or a physical tap qualification.
All original SPICE primitive parameters, including supplied tap R, are held.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
PARSER = ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/explicit_vss_interface/prepare_r5.py'
SPI_SHA = '1d53ab7df431b717ef5aff43e1117c0224681d5cc84886da37a319280ee958d6'
CDL_SHA = '18b6ec3f70bdc74ab2acc98c97b8bcad7185a8d6de26288b6f66af0e159cd0fc'
BODY = 'G1_EXPLICIT_SUBSTRATE_VSS'
PREFIX = 'G1_VSS_DERIVATIVE__'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_parser():
    spec = importlib.util.spec_from_file_location('source_bound_cdl_parser', PARSER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse


def key(instance, include_parameters=False):
    fields = [instance['model'].upper(), tuple(n.upper() for n in instance['nodes'])]
    if include_parameters:
        fields.append(tuple(instance['params']))
    return tuple(fields)


def flattened(cells, root):
    rows = {}
    def walk(name, binding, path, stack):
        assert name not in stack
        def net(value):
            value = value.upper()
            return binding.get(value, '0' if value == '0' else path+'/'+value)
        for inst in cells[name]['instances']:
            nodes = [net(n) for n in inst['nodes']]
            model = inst['model'].upper()
            ipath = path+'/'+inst['name'].upper()
            if model in cells:
                pins = cells[model]['pins']
                assert len(pins) == len(nodes)
                walk(model, dict(zip((p.upper() for p in pins), nodes)), ipath, stack+[name])
            else:
                assert ipath not in rows
                rows[ipath] = dict(model=model, nodes=nodes, params=inst['params'])
    walk(root, {p.upper():p.upper() for p in cells[root]['pins']}, 'ROOT', [])
    return rows


def prepare(raw, cdl_raw, cdl_summary):
    assert sha(raw) == SPI_SHA and sha(cdl_raw) == CDL_SHA
    parse = load_parser()
    lines, cells = parse(raw)
    _, cdl = parse(cdl_raw)
    affected = set(cdl_summary['affected_cells'])-{'PLACED_CORE_NOT_CONNECTED_FULLCHIP'}
    assert len(affected) == 30 and cdl_summary['explicit_sha256'] == CDL_SHA
    assert not re.search(rb'^\s*\.?global\b', raw, re.I|re.M)
    assert BODY.encode() not in raw and PREFIX.encode() not in raw
    blocks, changes, crossview = [], [], []
    for name in sorted(affected):
        cell = cells[name]
        reference = cdl[name]
        assert cell['pins'] == reference['pins']
        # Compare complete local model/ordered-terminal multisets, not line order
        # or prefix spelling. This records the explicit IOVdd tap-name swap.
        assert Counter(key(i) for i in cell['instances']) == Counter(key(i) for i in reference['instances']), name
        remaining = list(reference['instances'])
        for inst in cell['instances']:
            candidates = [i for i in remaining if key(i) == key(inst)]
            assert candidates
            paired = sorted(candidates, key=lambda i:i['name'].upper())[0]
            remaining.remove(paired)
            crossview.append(dict(cell=name, spice_instance=inst['name'], cdl_instance=paired['name'],
                model=inst['model'], ordered_terminals=inst['nodes'],
                spice_parameters=inst['params'], cdl_parameters=paired['params'],
                parameter_equivalence='not inferred; original electrical SPICE parameters are authoritative for this diagnostic'))
        assert not remaining
        replacements = {}
        header = list(cell['header']['tokens'])
        header[1] = PREFIX+header[1]
        replacements[cell['header']['indices'][0]] = (' '.join(header+[BODY])+'\n', cell['header']['indices'])
        for inst in cell['instances']:
            old = inst['record']['tokens']; new = list(old)
            for j in range(1, inst['model_index']):
                if new[j].upper() == 'SUB!': new[j] = BODY
            if inst['model'].upper() in affected:
                mi = inst['model_index']
                new.insert(mi, BODY)
                new[mi+1] = PREFIX+inst['model']
            if new != old:
                idx = inst['record']['indices']
                replacements[idx[0]] = (' '.join(new)+'\n', idx)
                changes.append(dict(cell=name, instance=inst['name'], before=old, after=new))
        first = cell['header']['indices'][0]; last = cell['end']['indices'][-1]
        skip = {i for _, indices in replacements.values() for i in indices[1:]}
        block = ''.join(replacements[i][0] if i in replacements else lines[i]
                        for i in range(first, last+1) if i not in skip)
        block = re.sub(r'(?im)^(\.ends\s+)'+re.escape(cell['name'])+r'(?=\s|$)',
                       r'\1'+PREFIX+cell['name'], block)
        blocks.append(block)
    suffix = ('\n* Design-local explicit substrate interface; original electrical values held.\n'+''.join(blocks)).encode()
    candidate = raw+suffix
    assert candidate[:-len(suffix)] == raw
    _, newcells = parse(candidate)
    before_after = []
    for name in sorted(affected):
        original = flattened(cells, name)
        derived = flattened(newcells, PREFIX+name)
        expected = {path:dict(row, nodes=[BODY if n.endswith('/SUB!') else n for n in row['nodes']])
                    for path, row in original.items()}
        assert expected == derived
        clone = newcells[PREFIX+name]
        cdlclone = cdl[PREFIX+name]
        assert clone['pins'] == cdlclone['pins']
        assert Counter(key(i) for i in clone['instances']) == Counter(key(i) for i in cdlclone['instances'])
        taps = {p:r for p,r in derived.items() if r['model'] in ('PTAP1','NTAP1')}
        for path, row in taps.items():
            assert row['params'] == original[path]['params']
            supplied = [p for p in row['params'] if p.upper().startswith('R=')]
            assert len(supplied) == 1 and float(supplied[0].split('=')[1].rstrip('munp')) > 0
        changed = [(p,j) for p,r in expected.items() for j,n in enumerate(r['nodes']) if n==BODY]
        assert changed
        p,j = changed[0]
        wrong = {p:dict(r,nodes=list(r['nodes'])) for p,r in derived.items()}
        wrong[p]['nodes'][j] = 'IOVSS'
        omitted = dict(derived); omitted.pop(p)
        missing_terminal = {p:dict(r,nodes=list(r['nodes'])) for p,r in derived.items()}
        missing_terminal[p]['nodes'].pop(j)
        tied = {p:dict(r,nodes=['VSS' if n=='IOVSS' else n for n in r['nodes']]) for p,r in derived.items()}
        has_iovss = any('IOVSS' in r['nodes'] for r in expected.values())
        before_after.append(dict(cell=name, flat_primitives=len(original), taps=len(taps),
            changed_body_terminals=len(changed), exact_expected_flat_graph_and_parameters=True,
            wrong_bulk_rejected=wrong!=expected, omitted_device_rejected=omitted!=expected,
            missing_bulk_terminal_rejected=missing_terminal!=expected,
            VSS_IOVSS_short_rejected=(tied!=expected) if has_iovss else 'not applicable: no IOVSS port in cell'))
        assert before_after[-1]['wrong_bulk_rejected'] and before_after[-1]['omitted_device_rejected']
        assert before_after[-1]['missing_bulk_terminal_rejected']
        assert not has_iovss or before_after[-1]['VSS_IOVSS_short_rejected']
    return candidate, dict(status='passed source-only explicit-body electrical derivative controls; simulation not run',
        spi_sha256=sha(raw), cdl_r5_sha256=sha(cdl_raw), candidate_sha256=sha(candidate),
        parser_sha256=sha(PARSER.read_bytes()), affected_cells=sorted(affected),
        exact_original_library_prefix=True, exact_inverse_by_suffix_removal=True,
        original_parameter_and_tap_R_preservation=True, reversible_record_edits=changes,
        complete_local_crossview_mapping=crossview, flattened_controls=before_after,
        physical_tap_AP_R_applicability='unresolved; no A/P-to-R conversion or extraction fit',
        electrical_power_ESD_qualification='not run', canonical_source='unchanged')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spice',type=Path,required=True)
    parser.add_argument('--cdl',type=Path,required=True)
    parser.add_argument('--cdl-summary',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    try:
        candidate, report = prepare(args.spice.read_bytes(),args.cdl.read_bytes(),
                                    json.loads(args.cdl_summary.read_text()))
        (args.output/'explicit_body.spi').write_bytes(candidate)
    except (AssertionError,KeyError,ValueError) as exc:
        report = dict(status='failed source preparation', error=repr(exc))
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in
        ('reversible_record_edits','complete_local_crossview_mapping','flattened_controls')},indent=2))
    raise SystemExit(0 if report['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
