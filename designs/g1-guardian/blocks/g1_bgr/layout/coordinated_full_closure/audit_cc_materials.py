#!/usr/bin/env python3
"""Read-only distinction between drawn material, typed contacts and CC inputs."""
import argparse
import json
import os
from pathlib import Path

import klayout.db as kdb
from google.protobuf.json_format import MessageToDict
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from export_cc_api import plain, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    digest = sha(args.database)
    assert digest == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    args.output.mkdir(exist_ok=False)
    cli_args = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                                  '--lvsdb', str(args.database), '--cell', 'g1_bgr',
                                  '--out_dir', str(args.output / 'api')], Env.from_os_environ())
    KpexCLI.validate_args(cli_args)
    cli = KpexCLI()
    tech = TechInfo.from_json(cli_args.tech_pbjson_path, dielectric_filter=cli_args.dielectric_filter)
    db = cli.create_lvsdb(cli_args)
    raw = {db.layer_name(i): plain(db.layer_by_index(i)) for i in db.layer_indexes()}
    context = KLayoutExtractionContext.prepare_extraction(db, cli_args.effective_cell_name, tech, False)
    regions = {layer.lvs_layer_name: plain(layer.region)
               for layers in context.extracted_layers.values() for layer in layers.source_layers}
    typed = kdb.Region()
    for name in ('cont_poly_con', 'cont_nsd_con', 'cont_psd_con'):
        typed += regions.get(name, kdb.Region())
    contact = raw['cont_drw']
    missing = plain(contact - typed)
    taps = plain(raw.get('ntap', kdb.Region()) + raw.get('ptap', kdb.Region()))
    area = lambda r: plain(r).area() * context.dbu**2
    metals = []
    for layer in tech.process_metal_layers:
        pair = tech.gds_pair(layer.name)
        region = context.shapes_of_layer(pair) if pair else None
        metals.append(dict(name=layer.name, gds_pair=list(pair) if pair else None,
                           area_um2=area(region) if region is not None else 0,
                           technology=MessageToDict(layer)))
    report = dict(status='passed read-only inventory; completeness not qualified', database_sha256=digest,
                  script_sha256=sha(Path(__file__)), technology_sha256=sha(Path(cli_args.tech_pbjson_path)),
                  blackbox=False, raw_layers={name: area(r) for name, r in raw.items()},
                  contact=dict(raw_um2=area(contact), typed_um2=area(typed), missing_um2=area(missing),
                               missing_in_taps_um2=area(missing & taps), missing_outside_taps_um2=area(missing - taps)),
                  CC_process_metal_inputs=metals, process_stack=MessageToDict(tech.tech.process_stack),
                  extraction='not run: read-only inventory', model_coverage='not qualified',
                  electrical='not run', VSUBS='unbound; no internal HBT substrate/thermal equivalence asserted')
    assert sha(args.database) == digest
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('raw_layers', 'process_stack', 'CC_process_metal_inputs')}, indent=2))


if __name__ == '__main__':
    main()
