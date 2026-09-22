#!/usr/bin/env python3
"""Read-only geometry domain comparison; no alternate capacitance extraction."""
import argparse
import json
import os
from pathlib import Path
import klayout.db as kdb
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from export_cc_api import plain, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert sha(args.database) == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    args.output.mkdir(exist_ok=False)
    a = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                           '--lvsdb', str(args.database), '--cell', 'g1_bgr',
                           '--out_dir', str(args.output / 'api')], Env.from_os_environ())
    KpexCLI.validate_args(a)
    cli = KpexCLI()
    tech = TechInfo.from_json(a.tech_pbjson_path, dielectric_filter=a.dielectric_filter)
    db = cli.create_lvsdb(a)
    regions = {}
    for flag in (False, True):
        context = KLayoutExtractionContext.prepare_extraction(db, a.effective_cell_name, tech, flag)
        regions[flag] = {layer.lvs_layer_name: plain(layer.region)
                         for layers in context.extracted_layers.values() for layer in layers.source_layers}
    rows = []
    for name in sorted(set(regions[False]) | set(regions[True])):
        white = regions[False].get(name, kdb.Region())
        black = regions[True].get(name, kdb.Region())
        rows.append(dict(name=name, whitebox_um2=white.area() * 1e-6, blackbox_um2=black.area() * 1e-6,
                         removed_um2=plain(white - black).area() * 1e-6,
                         added_um2=plain(black - white).area() * 1e-6))
    model = Path('/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/resistors_mod.lib')
    report = dict(status='passed read-only domain comparison; combined model coverage not qualified',
                  inputs={str(p): sha(p) for p in (args.database, Path(__file__), model)}, layers=rows,
                  installed_resistor_model_observation='rppd/rhigh include intrinsic area/perimeter capacitance with postsim=0 default; no model/parameter change is authorized or performed.',
                  source_combination='whitebox CC plus unchanged intrinsic models requires domain reconciliation; no numerical capacitance subtraction performed',
                  blackbox_alternative_CC='not run', electrical='not run', adoption='not run')
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
