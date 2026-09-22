#!/usr/bin/env python3
"""Read-only native R request/domain preparation; no numerical R extraction."""
import argparse
import collections
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
from google.protobuf.json_format import MessageToDict
import klayout.db as kdb
import klayout_pex
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from klayout_pex.rcx25.r.r_extractor import RExtractor
from klayout_pex_protobuf.kpex.klayout.r_extractor_tech_pb2 import RExtractorTech

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from export_cc_api import sha, dump


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    import datetime
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert kdb.__version__ == '0.30.9' and importlib.metadata.version('klayout-pex') == '0.3.12'
    assert sha(args.database) == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    package = Path(klayout_pex.__file__).parent
    files = {str(p.relative_to(package)): sha(p) for p in package.rglob('*')
             if p.is_file() and p.suffix not in ('.pyc', '.pyo')}
    receipt = dict(status='running', script_sha256=sha(Path(__file__)), database_sha256=sha(args.database),
        package_files=files, resource_gate_sha256=sha(args.resource_gate), numerical_R='not run',
        source_coverage='1027 extracted active devices plus nine independently verified geometric grounded dummies',
        canonical_electrical_source='1036 devices unchanged', geometry='original r5 exact-union extraction view, not new four-cut geometry',
        cards_decks='unchanged', adoption='not run', seed='not applicable')
    start = time.monotonic()
    dump(args.output / 'summary.json', receipt)
    try:
        cli_args = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'R',
            '--lvsdb', str(args.database), '--cell', 'g1_bgr', '--out_dir', str(args.output / 'engine')], Env.from_os_environ())
        KpexCLI.validate_args(cli_args)
        cli = KpexCLI()
        tech = TechInfo.from_json(cli_args.tech_pbjson_path, dielectric_filter=cli_args.dielectric_filter)
        db = cli.create_lvsdb(cli_args)
        context = KLayoutExtractionContext.prepare_extraction(db, cli_args.effective_cell_name, tech, cli_args.blackbox_devices)
        rex = RExtractor(context, substrate_algorithm=RExtractorTech.ALGORITHM_SQUARE_COUNTING,
            wire_algorithm=RExtractorTech.ALGORITHM_SQUARE_COUNTING, delaunay_b=cli_args.delaunay_b,
            delaunay_amax=cli_args.delaunay_amax, via_merge_distance=0, skip_simplify=True)
        request = rex.prepare_request()
        (args.output / 'request.pb').write_bytes(request.SerializeToString(deterministic=True))
        data = MessageToDict(request, preserving_proto_field_name=True)
        dump(args.output / 'request.json', data)
        conductors = {x.layer.id: x.layer.lvs_layer_name for x in request.tech.conductors}
        vias = {x.layer.id: x.layer.lvs_layer_name for x in request.tech.vias}
        regions = collections.Counter()
        terminal_layers = collections.Counter()
        unsupported_terminal_layers = collections.Counter()
        terminals_without_geometry = []
        for device in data.get('devices', []):
            for terminal in device.get('terminals', []):
                for layer in terminal.get('region_by_layer', []):
                    name = layer['layer'].get('lvs_layer_name', '')
                    terminal_layers[name] += 1
                    if int(layer['layer'].get('id', 0)) not in conductors:
                        unsupported_terminal_layers[name] += 1
                if not terminal.get('region_by_layer'):
                    terminals_without_geometry.append(terminal)
        for net in request.net_extraction_requests:
            for layer in net.region_by_layer:
                regions[layer.layer.lvs_layer_name] += len(layer.region.shapes)
        receipt.update(status='passed request preparation; completeness not qualified',
            technology_sha256=sha(Path(cli_args.tech_pbjson_path)), blackbox_devices=cli_args.blackbox_devices,
            conductors=conductors, vias=vias, request_devices=len(request.devices), pins=len(request.pins),
            networks=len(request.net_extraction_requests), region_shapes_by_layer=dict(regions),
            terminal_regions_by_layer=dict(terminal_layers), unsupported_terminal_layers=dict(unsupported_terminal_layers),
            terminals_without_geometry=terminals_without_geometry,
            request_pb_sha256=sha(args.output / 'request.pb'), request_json_sha256=sha(args.output / 'request.json'))
    except Exception as error:
        receipt.update(status='failed native request preparation', error=repr(error))
        raise
    finally:
        receipt.update(wall_s=time.monotonic() - start, database_unchanged=sha(args.database) == receipt['database_sha256'],
            package_unchanged=all(sha(package / p) == h for p, h in files.items()))
        dump(args.output / 'summary.json', receipt)
        print(json.dumps({k: v for k, v in receipt.items() if k != 'package_files'}, indent=2))


if __name__ == '__main__':
    main()
