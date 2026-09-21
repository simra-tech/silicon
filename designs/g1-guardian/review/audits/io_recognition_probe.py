#!/usr/bin/env python3
"""Diagnostic-only PolyRes annotation on a scratch copy of a stock analog IO cell."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import pya

ROOT = Path(__file__).resolve().parents[4]
PDK = Path('/foss/pdks/ihp-sg13g2')
LVS = PDK / 'libs.tech/klayout/tech/lvs'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.work.exists() or args.report.exists(): raise FileExistsError('Use new directories')
    args.work.mkdir(parents=True); args.report.mkdir(parents=True)
    work, report = args.work.resolve(), args.report.resolve()
    source = PDK / 'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    cdl = PDK / 'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
    ly = pya.Layout(); ly.read(str(source))
    cell = ly.cell('sg13g2_SecondaryProtection')
    def reg(layer, datatype=0):
        return pya.Region(cell.begin_shapes_rec(ly.layer(layer, datatype))).merged()
    summary = {}
    for name, layer in [('PolyRes',128),('GatPoly',5),('SalBlock',28),('EXTBlock',111)]:
        r = reg(layer)
        summary[name] = {'polygons': r.count(), 'area_um2': r.area() * ly.dbu ** 2,
                         'polygon_bboxes_um': [str(p.bbox().to_dtype(ly.dbu)) for p in r.each()]}
    assert reg(128).is_empty()
    marker = pya.DBox(0.94, 1.37, 1.94, 3.37).to_itype(ly.dbu)
    # Coordinates taken from the source unsilicided poly body, not a resized resistor.
    body = reg(5) & reg(28)
    assert (pya.Region(marker) - body).is_empty(), 'Proposed marker extends outside existing body'
    cell.shapes(ly.layer(128,0)).insert(marker)
    annotated = work / 'sg13g2_io_annotation_only.gds'
    ly.write(str(annotated))
    # Verify that no other polygon layer changed anywhere in the analog-pad hierarchy.
    original = pya.Layout(); original.read(str(source))
    fresh = pya.Layout(); fresh.read(str(annotated))
    changed = []
    for layer, dtype in sorted({(i.layer,i.datatype) for l in (original,fresh) for i in l.layer_infos()}):
        a = pya.Region(original.cell('sg13g2_IOPadAnalog').begin_shapes_rec(original.layer(layer,dtype))).merged()
        b = pya.Region(fresh.cell('sg13g2_IOPadAnalog').begin_shapes_rec(fresh.layer(layer,dtype))).merged()
        xor = a ^ b
        if not xor.is_empty(): changed.append({'layer': f'{layer}/{dtype}', 'area_um2': xor.area()*ly.dbu**2})
    assert [x['layer'] for x in changed] == ['128/0'], changed
    cmd = ['python3', str(LVS/'run_lvs.py'), '--layout', str(annotated), '--netlist', str(cdl),
           '--topcell', 'sg13g2_IOPadAnalog', '--run_mode', 'deep', '--run_dir', str(report),
           '--top_lvl_pins', '--spice_comments']
    start = time.monotonic()
    with (report/'console.log').open('w') as log:
        run = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    text = (report/'console.log').read_text()
    status = 'passed' if 'Comparison mode: PASS (netlists match).' in text else 'failed'
    result = {'scope': 'NON-PRODUCTION DIAGNOSTIC ONLY; stock PDK and delivered GDS untouched.',
              'command': 'flow/run.sh python3 designs/g1-guardian/review/audits/io_recognition_probe.py --work '+str(args.work)+' --report '+str(args.report),
              'pdk_commit': (PDK/'COMMIT').read_text().strip(), 'klayout_version': pya.__version__,
              'input_gds_sha256': sha(source), 'input_cdl_sha256': sha(cdl),
              'annotated_gds_sha256': sha(annotated), 'script_sha256': sha(Path(__file__)),
              'deck_hashes': {str(p.relative_to(PDK)):sha(p) for p in [LVS/'sg13g2.lvs', LVS/'run_lvs.py', LVS/'rule_decks/res_derivations.lvs']},
              'stock_secondary_protection': summary, 'added_marker_cell_bbox_um': [0.94,1.37,1.94,3.37],
              'changed_layers': changed, 'solver_exit_code': run.returncode, 'lvs_status': status,
              'wall_seconds': time.monotonic()-start,
              'annotation_layer_reference': 'https://ihp-open-pdk-docs.readthedocs.io/en/latest/layout_rules/02_layer_table.html',
              'layer_interpretation': 'Documentation describes 128/0 as marking net resistors. Only this recognition layer changes; physical mask-processing acceptance is not established.',
              'not_run': ['Production IO repair', 'DRC of diagnostic variant', 'Full assembled IO-inclusive LVS', 'Physical/foundry acceptance']}
    (report/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'lvs_status':status,'solver_exit_code':run.returncode,'changed_layers':changed},indent=2))


if __name__ == '__main__': main()
