#!/usr/bin/env python3
"""Native merged-neighborhood control for repeated M5 GDS-pair lookup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import klayout.db as kdb
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.tech_info import TechInfo
from export_cc_api import sha


class Visitor(kdb.PolygonNeighborhoodVisitor):
    def __init__(self):
        super().__init__()
        self.rows = []

    def neighbors(self, layout, cell, polygon, neighborhood):
        row = [polygon.to_s(), polygon.property('net'),
               sorted((int(index), sorted((p.to_s(), p.property('net')) for p in polygons))
                      for index, polygons in neighborhood.items())]
        self.rows.append(json.dumps(row, sort_keys=True))


def observed(inside, secondary):
    visitor = Visitor()
    node = kdb.CompoundRegionOperationNode.new_polygon_neighborhood(
        [kdb.CompoundRegionOperationNode.new_secondary(secondary)], visitor)
    inside.complex_op(node)
    return sorted(visitor.rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert sha(args.database) == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    args.output.mkdir(exist_ok=False)
    receipt = dict(status='running', database_sha256=sha(args.database), script_sha256=sha(Path(__file__)),
                   extraction='not run: native geometry neighborhood only', electrical='not run')
    try:
        a = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                               '--lvsdb', str(args.database), '--cell', 'g1_bgr',
                               '--out_dir', str(args.output / 'api')], Env.from_os_environ())
        KpexCLI.validate_args(a)
        cli = KpexCLI()
        tech = TechInfo.from_json(a.tech_pbjson_path, dielectric_filter=a.dielectric_filter)
        db = cli.create_lvsdb(a)
        context = KLayoutExtractionContext.prepare_extraction(db, a.effective_cell_name, tech, False)
        assert tech.gds_pair('metal5_n_cap') == tech.gds_pair('metal5_cap') == (67, 0)
        native = context.shapes_of_layer((67, 0))
        once = kdb.Region()
        once.enable_properties()
        once += native
        twice = kdb.Region()
        twice.enable_properties()
        twice += native
        twice += native
        m4 = context.shapes_of_layer((50, 0))
        checks = []
        for name, left, right in [('M5_inside_M4_secondary', observed(once, m4), observed(twice, m4)),
                                 ('M4_inside_M5_secondary', observed(m4, once), observed(m4, twice)),
                                 ('M5_self_neighborhood', observed(once, once), observed(twice, twice))]:
            checks.append(dict(name=name, original_rows=len(left), duplicate_rows=len(right),
                               original_sha256=hashlib.sha256('\n'.join(left).encode()).hexdigest(),
                               duplicate_sha256=hashlib.sha256('\n'.join(right).encode()).hexdigest(),
                               status='passed' if left == right else 'failed'))
        receipt.update(checks=checks, once_raw_count=once.count(), twice_raw_count=twice.count(),
                       once_merged_semantics=once.merged_semantics, twice_merged_semantics=twice.merged_semantics,
                       canonical_pair_name=tech.canonical_layer_name_by_gds_pair[(67, 0)],
                       status='passed tested native polygon neighborhoods' if all(c['status'] == 'passed' for c in checks) else 'failed native polygon neighborhood parity',
                       full_numerical_alias_equivalence='not run; this is a geometry control, not a full numerical rerun')
    except Exception as error:
        receipt.update(status='failed audit', error=repr(error))
        raise
    finally:
        (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
        (args.output / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
