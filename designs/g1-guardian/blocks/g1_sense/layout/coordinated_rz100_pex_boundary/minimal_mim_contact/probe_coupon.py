#!/usr/bin/env python3
"""Run pinned native 7x7 CMIM-only R/RC probes without technology edits."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

import klayout.db as kdb
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coupon', type=Path, required=True)
    parser.add_argument('--mode', choices=['R', 'RC'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {1} and not args.output.exists()
    assert kdb.__version__ == '0.30.9'
    assert importlib.metadata.version('klayout-pex') == '0.3.12'
    assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    manifest = json.loads((args.coupon / 'manifest.json').read_text())
    assert manifest['status'] == 'passed native coupon geometry preparation'
    assert manifest['native_MIM_area_um2'] == 49
    gds = args.coupon / 'sense_mim_method_control.gds'
    cdl = args.coupon / 'sense_mim_method_control.cdl'
    assert sha(gds) == manifest['GDS_sha256'] == '546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20'
    assert sha(cdl) == manifest['CDL_sha256'] == 'bcc32a78962430e46e7269518c645681c3233e24337e87142e714c7fe85aa974'
    parsed = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D',
        '--mode', args.mode, '--blackbox', 'false', '--cache-lvs', 'false',
        '--gds', str(gds), '--cell', 'sense_mim_method_control',
        '--schematic', str(cdl), '--out_dir', str(args.output / 'engine')],
        Env.from_os_environ())
    KpexCLI.validate_args(parsed)
    techpath = Path(parsed.tech_pbjson_path)
    assert sha(techpath) == '6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92'
    # KpexCLI.validate_args may create its output directory.
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', mode=args.mode, GDS_sha256=sha(gds),
                  CDL_sha256=sha(cdl), technology_sha256=sha(techpath),
                  source_changes='none', model_deck_changes='none',
                  full_macro_PEX='not qualified')
    def save():
        (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    save()
    try:
        cli = KpexCLI()
        tech = TechInfo.from_json(str(techpath), dielectric_filter=parsed.dielectric_filter)
        db = cli.create_lvsdb(parsed)
        context = KLayoutExtractionContext.prepare_extraction(db, 'sense_mim_method_control', tech, False)
        result['unknown_layers'] = [q.lvs_layer_name for q in context.unnamed_layers]
        save()
        extraction = cli.run_kpex_2_5d_engine(parsed, context, tech,
            str(args.output / 'native_report.rdb.gz'), None, None)
        summary = extraction.summarize()
        result.update(status='completed raw coupon extraction',
                      capacitor_count=len(summary.capacitances),
                      resistor_count=len(summary.resistances))
    except Exception as exc:
        result.update(status='failed raw coupon extraction', error=repr(exc))
    finally:
        result['inputs_unchanged'] = (sha(gds) == manifest['GDS_sha256'] and
                                      sha(cdl) == manifest['CDL_sha256'] and
                                      sha(techpath) == result['technology_sha256'])
        save()
    print(json.dumps({k: result.get(k) for k in ['status', 'error', 'unknown_layers',
                                               'capacitor_count', 'resistor_count']}))
    raise SystemExit(1 if result['status'].startswith('failed') else 0)


if __name__ == '__main__':
    main()
