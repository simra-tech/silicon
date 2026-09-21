#!/usr/bin/env python3
"""Diagnose/reproduce Magic PCell-name collisions without changing delivered GDS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import pya

ROOT = Path(__file__).resolve().parents[4]
BLOCK = ROOT / 'designs/g1-guardian/blocks/g1_padring'
RUN = BLOCK / 'flow/runs/assembly-1350'
ORIGINAL = RUN / '56-magic-streamout/g1_chip_top.magic.gds'
REFERENCE = RUN / '57-klayout-streamout/g1_chip_top.klayout.gds'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def open_layout(path):
    ly = pya.Layout(); ly.read(str(path)); return ly


def geometry(ly, cell, info):
    return pya.Region(cell.begin_shapes_rec(ly.layer(info))).merged()


def compare_cells(a, ca, b, cb):
    assert a.dbu == b.dbu
    differences = []
    infos = sorted({(i.layer, i.datatype) for ly in (a, b) for i in ly.layer_infos()})
    for layer, datatype in infos:
        info = pya.LayerInfo(layer, datatype)
        xor = geometry(a, ca, info) ^ geometry(b, cb, info)
        if not xor.is_empty():
            differences.append({'layer': f'{layer}/{datatype}', 'merged_xor_polygons': xor.count(),
                                'xor_area_um2': xor.area() * a.dbu ** 2})
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.work.exists() or args.report.exists():
        raise FileExistsError('Preserve old evidence: both directories must be new')
    args.work.mkdir(parents=True); args.report.mkdir(parents=True)
    work, report = args.work.resolve(), args.report.resolve()
    rel = lambda p: str(p.relative_to(ROOT))
    a, b = open_layout(ORIGINAL), open_layout(REFERENCE)
    macros = sorted({i.cell.name for i in b.cell('g1_chip_top').each_inst() if i.cell.name.startswith('g1_')})
    before = []
    for name in macros:
        ca, cb = a.cell(name), b.cell(name)
        bad_instances = []
        if ca is not None and cb is not None:
            bi = {}
            for i in cb.each_inst(): bi.setdefault(str(i.dcplx_trans), []).append(i)
            for i in ca.each_inst():
                matches = bi.get(str(i.dcplx_trans), [])
                if len(matches) == 1 and i.cell.dbbox() != matches[0].cell.dbbox():
                    j = matches[0]
                    bad_instances.append({'transform': str(i.dcplx_trans),
                                          'magic_cell': i.cell.name, 'magic_bbox_um': str(i.cell.dbbox()),
                                          'klayout_cell': j.cell.name, 'klayout_bbox_um': str(j.cell.dbbox())})
        before.append({'macro': name, 'magic_bbox_um': str(ca.dbbox()), 'klayout_bbox_um': str(cb.dbbox()),
                       'different_child_bboxes': bad_instances,
                       'geometry_differences': compare_cells(a, ca, b, cb)})
    (report / 'original_macro_differences.json').write_text(json.dumps(before, indent=2) + '\n')

    config = json.loads((RUN / '56-magic-streamout/config.json').read_text())
    files, prepared = [], []
    # Retain standard-cell source policy; namespace only private analog hierarchies.
    for name, cfg in config['MACROS'].items():
        for original_name in cfg['gds']:
            original = Path(original_name)
            if name == 'g1_digital':
                files.append(original); continue
            ly = open_layout(original)
            top = ly.cell(name)
            assert top is not None, name
            renames = {}
            for cell in list(ly.each_cell()):
                if cell.cell_index() == top.cell_index(): continue
                old = cell.name
                new = name + '__' + old
                if len(new) > 32:
                    new = name[:16] + '__' + hashlib.sha256(old.encode()).hexdigest()[:12]
                renames[old] = new
                cell.name = new
            destination = work / (name + '.gds')
            ly.write(str(destination))
            # Reload and compare every layer against the original, not only bbox.
            source = open_layout(original); rewritten = open_layout(destination)
            diff = compare_cells(source, source.cell(name), rewritten, rewritten.cell(name))
            assert not diff, (name, diff)
            prepared.append({'macro': name, 'source': rel(original), 'source_sha256': sha(original),
                             'renamed': rel(destination), 'renamed_sha256': sha(destination),
                             'renames': renames, 'per_layer_geometry_identity': 'passed'})
            files.append(destination)
    scripts = '/usr/local/lib/python3.12/dist-packages/librelane/scripts'
    env_file = work / 'audit_env.tcl'
    output = work / 'g1_chip_top.magic.gds'
    lines = [
        'source {' + str(RUN / '56-magic-streamout/_env.tcl') + '}',
        'set ::env(SCRIPTS_DIR) {' + scripts + '}',
        'set ::env(STEP_DIR) {' + str(work) + '}',
        'set ::env(SAVE_MAG_GDS) {' + str(output) + '}',
        'set ::env(SAVE_MAG) {' + str(work / 'g1_chip_top.mag') + '}',
        'set ::env(SAVE_GDS) {' + str(work / 'unused.gds') + '}',
        'set ::env(MACRO_GDS_FILES) [list ' + ' '.join('{' + str(p) + '}' for p in files) + ']',
    ]
    env_file.write_text('\n'.join(lines) + '\n')
    env = dict(os.environ, _TCL_ENV_IN=str(env_file),
               _MAGIC_SCRIPT=scripts + '/magic/def/mag_gds.tcl')
    command = ['magic', '-dnull', '-noconsole', '-rcfile',
               '/foss/pdks/ihp-sg13g2/libs.tech/magic/ihp-sg13g2.magicrc',
               scripts + '/magic/wrapper.tcl']
    start = time.monotonic()
    with (report / 'magic.log').open('w') as log:
        proc = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    result = {'command': 'flow/run.sh python3 designs/g1-guardian/review/audits/audit_streamout.py --work ' + str(args.work) + ' --report ' + str(args.report),
              'klayout_version': pya.__version__, 'macro_inputs': prepared,
              'reference_sha256': sha(REFERENCE), 'original_magic_sha256': sha(ORIGINAL),
              'script_sha256': sha(Path(__file__)), 'magic_exit_code': proc.returncode,
              'magic_wall_seconds': time.monotonic() - start,
              'pdk_commit': Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),
              'changes': 'Cell names in isolated intermediate analog GDS only. No geometry, source macro, deck or delivered GDS changes.',
              'limitations': ['Geometry XOR is merged polygon comparison on all stored layers; texts are not compared.',
                              'Reference is preserved pre-fill KLayout streamout, not final filled delivered GDS.',
                              'No full-flow implementation adopted; namespace experiment is isolated.',
                              'DRC/LVS/PEX/antenna are not run on the alternate output.']}
    if proc.returncode == 0 and output.exists():
        fixed = open_layout(output)
        result['experimental_magic_sha256'] = sha(output)
        result['experimental_output'] = rel(output)
        result['full_chip_geometry_differences'] = compare_cells(fixed, fixed.cell('g1_chip_top'), b, b.cell('g1_chip_top'))
        result['macro_geometry_differences'] = {
            name: compare_cells(fixed, fixed.cell(name), b, b.cell(name)) for name in macros}
        result['xor_status'] = 'passed' if not result['full_chip_geometry_differences'] else 'failed'
    else:
        result['xor_status'] = 'not run'
    (report / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('magic_exit_code', 'magic_wall_seconds', 'xor_status')}, indent=2))
    if 'full_chip_geometry_differences' in result:
        print(json.dumps(result['full_chip_geometry_differences'], indent=2))


if __name__ == '__main__': main()
