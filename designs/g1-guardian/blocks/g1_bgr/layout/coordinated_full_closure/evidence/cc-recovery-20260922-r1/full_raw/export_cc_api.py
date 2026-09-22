#!/usr/bin/env python3
"""Exact native CC API, with optional output-only marker suppression.

The adapter changes only four report callbacks. Numerical result accumulation,
geometry, technology, rule decks and extraction algorithms remain installed code.
Raw VSUBS is intentionally not renamed. Material completeness is a separate gate.
"""
import argparse
import collections
import faulthandler
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
import klayout_pex.rcx25.extractor as engine


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def plain(region):
    output = kdb.Region()
    for polygon in region.each():
        output.insert(kdb.Polygon(polygon))
    return output.merged()


class CountOnlyReporter(engine.ExtractionReporter):
    """Keep the normal valid RDB container/save; omit diagnostic marker shapes."""
    counts = collections.Counter()

    def output_overlap(self, *args, **kwargs):
        self.counts['overlap'] += 1

    def output_sidewall(self, *args, **kwargs):
        self.counts['sidewall'] += 1

    def output_sideoverlap(self, *args, **kwargs):
        self.counts['sideoverlap'] += 1

    def output_edge_neighborhood(self, *args, **kwargs):
        self.counts['edge_neighborhood'] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--database-sha256', required=True)
    ap.add_argument('--cell', required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--reporter', choices=('original', 'count-only'), required=True)
    ap.add_argument('--audit-only', action='store_true')
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert kdb.__version__ == '0.30.9' and importlib.metadata.version('klayout-pex') == '0.3.12'
    assert sha(args.database) == args.database_sha256
    args.output.mkdir(parents=True, exist_ok=False)
    package = Path(klayout_pex.__file__).parent
    tool_files = {str(p.relative_to(package)): sha(p) for p in package.rglob('*')
                  if p.is_file() and p.suffix not in ('.pyc', '.pyo')}
    own_hash = sha(Path(__file__))
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    receipt = dict(status='running', database_sha256=args.database_sha256,
                   script_sha256=own_hash, tool_files=tool_files, reporter=args.reporter,
                   numerical_engine='unchanged installed native CC', geometry='unchanged LVSDB',
                   material_completeness='not qualified', electrical='not run', resistance='not applicable: CC only',
                   adoption='not run', seed='not applicable', VSUBS='unbound raw extracted node')
    save = lambda: dump(args.output / 'summary.json', receipt)
    save()
    start = time.monotonic()
    original = engine.ExtractionReporter
    faulthandler.enable()
    faulthandler.dump_traceback_later(60, repeat=True)
    try:
        cli_args = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                                      '--lvsdb', str(args.database), '--cell', args.cell,
                                      '--out_dir', str(args.output / 'engine')], Env.from_os_environ())
        KpexCLI.validate_args(cli_args)
        cli = KpexCLI()
        tech = TechInfo.from_json(cli_args.tech_pbjson_path, dielectric_filter=cli_args.dielectric_filter)
        db = cli.create_lvsdb(cli_args)
        context = KLayoutExtractionContext.prepare_extraction(db, cli_args.effective_cell_name, tech, cli_args.blackbox_devices)
        regions = {}
        inventory = []
        for pair, layers in context.extracted_layers.items():
            for layer in layers.source_layers:
                region = plain(layer.region)
                regions[layer.lvs_layer_name] = region
                inventory.append(dict(name=layer.lvs_layer_name, pair=list(pair),
                                      area_um2=region.area() * context.dbu**2, polygons=region.count()))
        unknown = []
        for layer in context.unnamed_layers:
            region = plain(layer.region)
            row = dict(name=layer.lvs_layer_name, area_um2=region.area() * context.dbu**2)
            if layer.lvs_layer_name == 'cont_drw':
                covered = kdb.Region()
                for name in ('cont_poly_con', 'cont_nsd_con', 'cont_psd_con'):
                    covered += regions.get(name, kdb.Region())
                missing = plain(region - covered)
                row.update(uncovered_um2=missing.area() * context.dbu**2,
                           typed_union_XOR_um2=plain(region ^ covered).area() * context.dbu**2)
            unknown.append(row)
        circuit = db.netlist().circuit_by_name(cli_args.effective_cell_name)
        receipt.update(blackbox=cli_args.blackbox_devices, technology_sha256=sha(Path(cli_args.tech_pbjson_path)),
                       extracted_layers=inventory, unknown_layers=unknown,
                       source_net_names=sorted(n.expanded_name() for n in circuit.each_net()),
                       native_capacitors=sum(isinstance(d.device_class(), kdb.DeviceClassCapacitor) for d in circuit.each_device()))
        save()
        if args.audit_only:
            receipt['status'] = 'passed read-only inventory; extraction not run'
        else:
            if args.reporter == 'count-only':
                engine.ExtractionReporter = CountOnlyReporter
            result = cli.run_kpex_2_5d_engine(cli_args, context, tech, str(args.output / 'report.rdb.gz'), None, None)
            summary = result.summarize()
            rows = []
            for key, value in sorted(summary.capacitances.items()):
                value = float(value)
                assert math.isfinite(value) and value >= 0 and key.net1 != key.net2
                rows.append(dict(net1=key.net1, net2=key.net2, capacitance_fF=value, capacitance_fF_hex=value.hex()))
            assert rows and not summary.resistances
            dump(args.output / 'exact_capacitances.json', rows)
            assert all(float.fromhex(r['capacitance_fF_hex']) == r['capacitance_fF'] for r in rows)
            receipt.update(status='passed raw CC generation; completeness not qualified', capacitor_count=len(rows),
                           capacitance_sha256=sha(args.output / 'exact_capacitances.json'),
                           report_callback_counts=dict(CountOnlyReporter.counts), binary64_roundtrip='passed')
    except Exception as error:
        receipt.update(status='failed native API', error=repr(error))
        raise
    finally:
        engine.ExtractionReporter = original
        faulthandler.cancel_dump_traceback_later()
        unchanged = sha(args.database) == args.database_sha256 and sha(Path(__file__)) == own_hash
        unchanged &= all(sha(package / p) == h for p, h in tool_files.items())
        receipt.update(all_inputs_tools_unchanged=unchanged, wall_s=time.monotonic() - start)
        if not unchanged:
            receipt['status'] = 'failed changed input'
        save()
    print(json.dumps({k: v for k, v in receipt.items() if k != 'tool_files'}, indent=2))


if __name__ == '__main__':
    main()
