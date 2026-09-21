#!/usr/bin/env python3
"""Prepare unique private analog cell names for Magic and check streamout geometry.

The source run and PDK remain untouched. Outputs must be in a new directory.
Use run_streamout_namespaced.sh for the complete replay and geometry check.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pya

SCRIPT_DIR = '/usr/local/lib/python3.12/dist-packages/librelane/scripts'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(left, right, top_name):
    a, b = pya.Layout(), pya.Layout()
    a.read(str(left)); b.read(str(right))
    if a.dbu != b.dbu: raise ValueError('Different database units')
    ca, cb = a.cell(top_name), b.cell(top_name)
    if ca is None or cb is None: raise ValueError('Required top cell missing')
    differences = []
    for layer, datatype in sorted({(i.layer, i.datatype) for ly in (a, b) for i in ly.layer_infos()}):
        ar = pya.Region(ca.begin_shapes_rec(a.layer(layer, datatype))).merged()
        br = pya.Region(cb.begin_shapes_rec(b.layer(layer, datatype))).merged()
        xor = ar ^ br
        if not xor.is_empty():
            differences.append({'layer': f'{layer}/{datatype}', 'polygons': xor.count(),
                                'area_um2': xor.area() * a.dbu ** 2})
    return differences


def prepare(run, out):
    if out.exists(): raise FileExistsError('Use a new output directory')
    out.mkdir(parents=True)
    config_path = run / '56-magic-streamout/config.json'
    env_path = run / '56-magic-streamout/_env.tcl'
    config = json.loads(config_path.read_text())
    files, mappings = [], []
    for top_name, spec in config['MACROS'].items():
        for source_name in spec['gds']:
            source = Path(source_name)
            # PDK standard cells remain shared exactly as in the original flow.
            if top_name == 'g1_digital':
                files.append(source)
                mappings.append({'top': top_name, 'source': source_name, 'sha256': sha(source),
                                 'action': 'unchanged standard-cell hierarchy'})
                continue
            ly = pya.Layout(); ly.read(str(source))
            top = ly.cell(top_name)
            if top is None: raise ValueError(f'No top cell {top_name}')
            renames = {}
            used = {top_name}
            for cell in list(ly.each_cell()):
                if cell.cell_index() == top.cell_index(): continue
                old = cell.name
                new = top_name + '__' + old
                if len(new) > 32:
                    new = top_name[:16] + '__' + hashlib.sha256(old.encode()).hexdigest()[:12]
                if new in used: raise ValueError('Unexpected name collision')
                used.add(new); renames[old] = new; cell.name = new
            dest = out / f'{top_name}.gds'
            if dest.exists(): raise FileExistsError('Multiple source files per macro unsupported')
            ly.write(str(dest))
            differences = compare(source, dest, top_name)
            if differences: raise ValueError(f'Geometry changed for {top_name}: {differences}')
            files.append(dest)
            mappings.append({'top': top_name, 'source': source_name, 'source_sha256': sha(source),
                             'output': dest.name, 'output_sha256': sha(dest), 'renames': renames,
                             'all_layer_polygon_identity': 'passed'})
    lines = [
        'source {' + str(env_path) + '}',
        'set ::env(SCRIPTS_DIR) {' + SCRIPT_DIR + '}',
        'set ::env(STEP_DIR) {' + str(out) + '}',
        'set ::env(SAVE_MAG_GDS) {' + str(out / 'g1_chip_top.magic.gds') + '}',
        'set ::env(SAVE_GDS) {' + str(out / 'g1_chip_top.gds') + '}',
        'set ::env(SAVE_MAG) {' + str(out / 'g1_chip_top.mag') + '}',
        'set ::env(MACRO_GDS_FILES) [list ' + ' '.join('{' + str(f) + '}' for f in files) + ']',
    ]
    (out / '_env.tcl').write_text('\n'.join(lines) + '\n')
    (out / 'namespace_manifest.json').write_text(json.dumps({
        'input_config_sha256': sha(config_path), 'input_env_sha256': sha(env_path),
        'script_sha256': sha(Path(__file__)), 'klayout_version': pya.__version__,
        'pdk_commit': Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),
        'macros': mappings, 'scope': 'Private analog subcell names only; no polygon modifications.',
        'texts': 'Retained through GDS read/write; polygon comparison does not independently compare text.',
    }, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--run', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('compare'); p.add_argument('--left', type=Path, required=True); p.add_argument('--right', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True); p.add_argument('--top', default='g1_chip_top')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.run.resolve(), args.out.resolve())
    else:
        if args.report.exists(): raise FileExistsError(args.report)
        diffs = compare(args.left, args.right, args.top)
        result = {'left': str(args.left), 'right': str(args.right), 'left_sha256': sha(args.left),
                  'right_sha256': sha(args.right), 'top': args.top, 'klayout_version': pya.__version__,
                  'status': 'failed' if diffs else 'passed', 'differences': diffs,
                  'comparison': 'Merged recursive polygons on every stored layer/datatype; no layer exclusions.',
                  'texts': 'not compared', 'other_checks': 'DRC/LVS/PEX/antenna not run by this helper'}
        args.report.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        if diffs: raise SystemExit(1)


if __name__ == '__main__': main()
