#!/usr/bin/env python3
"""Inventory pinned local Academy evidence; does not run candidate verification."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import pya

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'build/sources/IHP-AnalogAcademy'
PREFIXES = [
    'modules/module_1_bandgap_reference/part_1_OTA',
    'modules/module_1_bandgap_reference/part_3_layout/OTA_layout',
    'modules/module_3_8_bit_SAR_ADC/part_1_comparator',
    'modules/module_3_8_bit_SAR_ADC/part_5_analog_layout/comparator',
]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    git = lambda *a: subprocess.check_output(['git', '-C', str(SOURCE), *a], text=True).strip()
    rev = git('rev-parse', 'HEAD')
    records = []
    extensions = {'.sch', '.sym', '.spice', '.cir', '.cdl', '.ext', '.gds', '.lyrdb', '.csv', '.py', '.sh', '.md'}
    for prefix in PREFIXES:
        for file in sorted((SOURCE / prefix).rglob('*')):
            if not file.is_file() or file.suffix not in extensions: continue
            rel = str(file.relative_to(SOURCE))
            rec = {'path': rel, 'sha256': sha(file), 'bytes': file.stat().st_size,
                   'pinned_url': f'https://github.com/IHP-GmbH/IHP-AnalogAcademy/blob/{rev}/{rel}'}
            if file.suffix == '.gds':
                ly = pya.Layout(); ly.read(str(file))
                rec['top_cells'] = [{'name': c.name, 'bbox_um': [c.dbbox().left, c.dbbox().bottom,
                                     c.dbbox().right, c.dbbox().top]} for c in ly.top_cells()]
            if file.suffix == '.lyrdb':
                report = ET.parse(file)
                rec['stored_report_items'] = len(report.findall('.//items/item'))
                rec['status'] = 'stored report only; deck/input/run provenance not independently established'
            records.append(rec)
    result = {'repository': git('remote', 'get-url', 'origin'), 'revision': rev,
              'working_tree_status': git('status', '--short'),
              'pdk_commit_in_upstream_readme': 'eb1b540c58346cf6259285a38d09b2a04feb344a',
              'g1_pdk_commit': Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),
              'license': 'Apache-2.0', 'license_sha256': sha(SOURCE / 'LICENSE'),
              'upstream_readme_sha256': sha(SOURCE / 'README.md'), 'klayout_version': pya.__version__,
              'command': 'flow/run.sh python3 designs/g1-guardian/review/audits/audit_reuse.py --output ' + str(args.output),
              'files': records,
              'not_run': ['Candidate G1-PDK DRC/LVS/PEX', 'Candidate nominal/adverse G1 interface simulation',
                          'Candidate same-fixture mismatch/kickback A/B', 'Candidate silicon measurements'],
              'limitations': ['Repository images, saved results and extracted text are not independently reproduced checks.',
                              'OTA schematic and separate layout variant equivalence remains not run.',
                              'Comparator module-3 part-1 schematic and part-5 layout equivalence remains not run.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'revision': rev, 'files': len(records),
                      'reports': [(r['path'], r['stored_report_items']) for r in records if 'stored_report_items' in r]}, indent=2))


if __name__ == '__main__': main()
