#!/usr/bin/env python3
"""Recover full-precision native CC results from the existing, frozen LVSDB.

Uses supported installed APIs without changing any tool, deck, card or geometry.
The result is raw diagnostic data, not a completeness/electrical qualification.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

import klayout.db as kdb
import klayout_pex
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(region):
    copy = kdb.Region()
    for polygon in region.each():
        copy.insert(kdb.Polygon(polygon))
    return copy.merged()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {6}
    assert kdb.__version__ == '0.30.9'
    assert importlib.metadata.version('klayout-pex') == '0.3.12'
    prior = json.loads((args.pilot / 'summary.json').read_text())
    assert prior['status'] == 'failed bounded CC diagnostic' and prior['returncode'] == 1
    assert prior['termination_reason'] is None
    assert all(prior[key] for key in ('inputs_unchanged', 'tool_files_unchanged', 'model_cards_unchanged'))
    package = Path(klayout_pex.__file__).parent
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert all(sha(package / name) == value for name, value in prior['tool_hashes'].items())
    assert all(sha(pdk / name) == value for name, value in prior['card_hashes'].items())
    source = Path(__file__).resolve().parents[2] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source) == prior['source_sha256']
    dbs = list(args.pilot.rglob('*.lvsdb.gz'))
    assert len(dbs) == 1
    database = dbs[0]
    database_hash = sha(database)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', source_sha256=sha(source), saved_LVSDB_sha256=database_hash,
                  pilot_summary_sha256=sha(args.pilot / 'summary.json'), script_sha256=sha(Path(__file__)),
                  prior_stock_writer='failed; preserved', repeated_LVS=False, engine='unchanged native 2.5D CC',
                  completeness='not qualified', MIM_extrinsic_coverage='not qualified',
                  source_mapping='not qualified', electrical_equivalence='not run', adoption='not run')
    def save():
        (args.output / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    save()
    start = time.monotonic()
    try:
        cli_args = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                                       '--blackbox', 'true', '--cache-lvs', 'false', '--lvsdb', str(database),
                                       '--out_dir', str(args.output / 'engine')], Env.from_os_environ())
        KpexCLI.validate_args(cli_args)
        cli = KpexCLI()
        tech = TechInfo.from_json(cli_args.tech_pbjson_path, dielectric_filter=cli_args.dielectric_filter)
        db = cli.create_lvsdb(cli_args)
        context = KLayoutExtractionContext.prepare_extraction(db, cli_args.effective_cell_name, tech, True)
        inventory = []
        regions = {}
        for pair, layers in context.extracted_layers.items():
            for layer in layers.source_layers:
                regions[layer.lvs_layer_name] = materialize(layer.region)
                inventory.append(dict(name=layer.lvs_layer_name, gds_pair=list(pair),
                                      area_um2=regions[layer.lvs_layer_name].area() * context.dbu**2,
                                      polygons=regions[layer.lvs_layer_name].count()))
        unknown = []
        for layer in context.unnamed_layers:
            region = materialize(layer.region)
            record = dict(name=layer.lvs_layer_name, area_um2=region.area() * context.dbu**2)
            if layer.lvs_layer_name == 'cont_drw':
                covered = kdb.Region()
                for name in ('cont_poly_con', 'cont_nsd_con', 'cont_psd_con'):
                    covered += regions.get(name, kdb.Region())
                record.update(typed_union_XOR_um2=materialize(region ^ covered).area() * context.dbu**2,
                              uncovered_um2=materialize(region - covered).area() * context.dbu**2)
            unknown.append(record)
        native_caps = []
        circuit = db.netlist().circuit_by_name(cli_args.effective_cell_name)
        for device in circuit.each_device():
            if isinstance(device.device_class(), kdb.DeviceClassCapacitor):
                native_caps.append(dict(id=device.id(), name=device.name, model=device.device_class().name,
                                        parameters={p.name: device.parameter(p.name) for p in device.device_class().parameter_definitions()},
                                        terminals={t.name: device.net_for_terminal(t.name).expanded_name() for t in device.device_class().terminal_definitions()}))
        result.update(layer_inventory=inventory, unknown_layer_inventory=unknown, native_capacitors=native_caps,
                      technology_sha256=sha(Path(cli_args.tech_pbjson_path)))
        save()
        if not args.audit_only:
            extraction = cli.run_kpex_2_5d_engine(cli_args, context, tech,
                                                 str(args.output / 'exact_engine_report.rdb.gz'), None, None)
            summary = extraction.summarize()
            rows = []
            for key, value in sorted(summary.capacitances.items()):
                value = float(value)
                assert math.isfinite(value) and value >= 0 and key.net1 != key.net2
                rows.append(dict(net1=key.net1, net2=key.net2, capacitance_fF=value,
                                 capacitance_fF_hex=value.hex(), capacitance_F=value * 1e-15))
            assert rows and not summary.resistances
            exact = args.output / 'exact_capacitances.json'
            exact.write_text(json.dumps(rows, indent=2, allow_nan=False) + '\n')
            loaded = json.loads(exact.read_text())
            assert all(float.fromhex(row['capacitance_fF_hex']) == row['capacitance_fF'] for row in loaded)
            prior_csvs = list(args.pilot.rglob('*_k25d_pex_netlist.csv'))
            assert len(prior_csvs) == 1
            with prior_csvs[0].open() as handle:
                previous = {(row['Net1'], row['Net2']): float(row['Capacitance [fF]']) for row in csv.DictReader(handle, delimiter=';') if row['Device'].startswith('C')}
            current = {(row['net1'], row['net2']): row['capacitance_fF'] for row in rows}
            assert current.keys() == previous.keys()
            assert all(round(value, 3) == previous[key] for key, value in current.items())
            result.update(capacitor_count=len(rows), exact_capacitances_sha256=sha(exact),
                          binary64_roundtrip='passed all values', original_rounded_CSV_parity='passed all entries',
                          status='passed full-precision raw data recovery; completeness not qualified')
        else:
            result['status'] = 'passed read-only API inventory; extraction not run'
    except Exception as error:
        result.update(status='failed API diagnostic', exception=repr(error))
        raise
    finally:
        unchanged = sha(database) == database_hash and sha(source) == prior['source_sha256']
        unchanged &= all(sha(package / name) == value for name, value in prior['tool_hashes'].items())
        unchanged &= all(sha(pdk / name) == value for name, value in prior['card_hashes'].items())
        result.update(all_inputs_tools_cards_unchanged=unchanged, wall_s=time.monotonic() - start)
        if not unchanged:
            result['status'] = 'failed changed inputs'
        save()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
