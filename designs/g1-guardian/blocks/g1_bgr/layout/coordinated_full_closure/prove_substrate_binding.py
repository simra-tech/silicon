#!/usr/bin/env python3
"""Physical LVS substrate ownership, separate from synthetic CC-plane accuracy."""
import argparse
import collections
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
    ap.add_argument('--extraction', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    database = args.extraction / 'extraction.lvsdb'
    audit_path = args.extraction / 'source_device_audit.json'
    assert sha(database) == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    assert sha(audit_path) == 'b7e34e2f40436510355aaa50de4dd341f15ddab0d7774d499795c361bf0f5389'
    audit = json.loads(audit_path.read_text())
    assert audit['status'] == 'passed' and audit['instance_count'] == 1027
    args.output.mkdir(exist_ok=False)
    receipt = dict(status='running', inputs={str(p): sha(p) for p in (database, audit_path, Path(__file__))},
                   synthetic_VSUBS_plane_accuracy='not run', finite_substrate_resistance='not run',
                   internal_HBT_s1_t_equivalence='not applicable: no physical mapping asserted',
                   electrical='not run', adoption='not run')
    try:
        a = KpexCLI.parse_args(['--pdk', 'ihp-sg13g2', '--threads', '1', '--2.5D', '--mode', 'CC',
                               '--lvsdb', str(database), '--cell', 'g1_bgr',
                               '--out_dir', str(args.output / 'api')], Env.from_os_environ())
        KpexCLI.validate_args(a)
        cli = KpexCLI()
        tech = TechInfo.from_json(a.tech_pbjson_path, dielectric_filter=a.dielectric_filter)
        db = cli.create_lvsdb(a)
        context = KLayoutExtractionContext.prepare_extraction(db, a.effective_cell_name, tech, False)
        ownership = {}
        for layers in context.extracted_layers.values():
            for layer in layers.source_layers:
                if layer.lvs_layer_name not in ('pwell_sub', 'pwell', 'ptap', 'ntap', 'nwell_drw'):
                    continue
                grouped = collections.defaultdict(kdb.Region)
                for polygon in layer.region.each():
                    net = polygon.property('net')
                    assert net in audit['net_map'], (layer.lvs_layer_name, net)
                    grouped[audit['net_map'][net]].insert(kdb.Polygon(polygon))
                ownership[layer.lvs_layer_name] = {net: plain(region).area() * context.dbu**2
                                                  for net, region in sorted(grouped.items())}
        assert set(ownership) == {'pwell_sub', 'pwell', 'ptap', 'ntap', 'nwell_drw'}
        assert all(set(ownership[name]) == {'vss'} for name in ('pwell_sub', 'pwell', 'ptap'))
        assert set(ownership['nwell_drw']) == set(ownership['ntap']) == {'vdd', 'd1', 'd2', 'd3', 'd4', 'd5'}
        bodies = collections.defaultdict(collections.Counter)
        for row in audit['rows']:
            terminal = ('S' if row['model'] == 'npn13G2' else
                        row['model'] + '_sub' if row['model'] in ('rppd', 'rhigh') else 'B')
            assert terminal in row['terminals']
            bodies[row['model']][row['terminals'][terminal]] += 1
        assert bodies['npn13G2'] == {'vss': 292}
        assert bodies['sg13_hv_nmos'] == {'vss': 101}
        assert bodies['rppd'] == {'vss': 384} and bodies['rhigh'] == {'vss': 15}
        assert set(bodies['sg13_hv_pmos']) == {'vdd', 'd1', 'd2', 'd3', 'd4', 'd5'}
        rules = Path('/usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/ihp-sg13g2/libs.tech/kpex/rule_decks')
        semantics = {}
        for name in ('general_connections.lvs', 'general_derivations.lvs', 'bjt_connections.lvs', 'res_connections.lvs'):
            path = rules / name
            semantics[name] = dict(sha256=sha(path), relevant_lines=[dict(line=i, text=line)
                                  for i, line in enumerate(path.read_text().splitlines(), 1)
                                  if any(word in line for word in ('pwell', 'ptap', 'ntap', 'connect(cont_drw, metal1_con)'))])
        receipt.update(status='passed physical generalVSS substrate ownership; synthetic-plane accuracy not qualified',
                       region_net_area_um2=ownership, extracted_device_body_counts={k: dict(v) for k, v in bodies.items()},
                       nine_grounded_dummies='separate proof0d146e08 retained; not extracted here',
                       pinned_connectivity_semantics=semantics,
                       synthetic_substrate_name=tech.internal_substrate_layer_name,
                       conclusion='Physical pwell_sub/pwell/ptap are VSS; selecting generalVSS for the synthetic CC reference is node-consistent, not proof of ideal equipotential/field accuracy.',
                       PMOS_nwell_domains='six distinct domains preserved; not merged into physical VSS',
                       unchanged=all(sha(Path(p)) == h for p, h in receipt['inputs'].items()))
        assert receipt['unchanged']
    except Exception as error:
        receipt.update(status='failed proof', error=repr(error))
        raise
    finally:
        (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
        (args.output / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'pinned_connectivity_semantics'}, indent=2))


if __name__ == '__main__':
    main()
