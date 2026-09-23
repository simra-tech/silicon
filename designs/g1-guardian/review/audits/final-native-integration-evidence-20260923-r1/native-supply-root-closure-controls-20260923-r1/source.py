#!/usr/bin/env python3
"""Synthetic integration controls; no silicon, stock-rule, or EM qualification."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import pya
from place_closed_analog import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    names = ['valid_join', 'seeded_join', 'seeded_unmapped_island', 'wrong_net_metal',
             'captured_native_cut', 'uncontained_cut', 'stale_hash',
             'assigned_island', 'seeded_assigned_island']
    results = []
    for name in names:
        folder = a.output/name; folder.mkdir()
        ly = pya.Layout(); ly.dbu = .001
        top = ly.create_cell('SYNTHETIC_NOT_A_CIRCUIT'); child = ly.create_cell('EMPTY_SOURCE_INSTANCE')
        for i in range(4904):
            top.insert(pya.CellInstArray(child.cell_index(), pya.Trans(i, 0)))
        probes = {}
        for n, y in [('VDD', 0), ('VSS', 10000), ('VDDA', 20000), ('IOVDD', 30000), ('IOVSS', 40000)]:
            top.shapes(ly.layer(30, 0)).insert(pya.Box(0, y, 1000, y+1000))
            probes[n] = {'root': dict(layer=30, xy=[500, y+500])}
        top.shapes(ly.layer(30, 0)).insert(pya.Box(6000, 0, 7000, 1000))
        probes['VDD']['target'] = dict(layer=30, xy=[6500, 500])
        if name == 'captured_native_cut':
            # Initially disconnected M2 belongs to VSS via the upper crossing.
            top.shapes(ly.layer(10, 0)).insert(pya.Box(400, 400, 3600, 10600))
            top.shapes(ly.layer(29, 0)).insert(pya.Box(450, 10450, 550, 10550))
            top.shapes(ly.layer(29, 0)).insert(pya.Box(3450, 450, 3550, 550))
        source = folder/'source.gds'; ly.write(str(source))
        meta = folder/'metadata.json'
        meta.write_text(json.dumps(dict(status='passed synthetic fixture only', GDS_sha256=sha(source),
                                        native_instances_retained=4904, decap_pin_pairs_held=9324))+'\n')
        evidence = folder/'evidence.json'
        evidence.write_text(json.dumps(dict(status='passed synthetic fixture only'))+'\n')
        ol = pya.Layout(); ol.dbu = .001; ot = ol.create_cell('SYNTHETIC_OVERLAY')
        ot.shapes(ol.layer(30, 0)).insert(pya.Box(500, 300, 6500, 700))
        if name == 'wrong_net_metal':
            ot.shapes(ol.layer(30, 0)).insert(pya.Box(400, 400, 600, 10600))
        if name == 'uncontained_cut':
            ot.shapes(ol.layer(19, 0)).insert(pya.Box(2000, 2000, 2190, 2190))
        if name in ('seeded_unmapped_island', 'assigned_island', 'seeded_assigned_island'):
            ot.shapes(ol.layer(30, 0)).insert(pya.Box(2000, 2000, 3000, 3000))
        overlay = folder/'overlay.gds'; ol.write(str(overlay))
        def bound(path): return dict(path=str(path), sha256=sha(path))
        em = bound(evidence); em['assertions'] = [dict(keys=['status'], equals='passed synthetic fixture only')]
        contract = dict(schema='native-supply-integration-v1', parent=bound(source),
                        parent_metadata=bound(meta), native_probes=probes,
                        overlays=[dict(name='synthetic', gds=bound(overlay), evidence=[em], single_net='VDD')])
        if name == 'stale_hash':
            contract['overlays'][0]['gds']['sha256'] = '0'*64
        if name.startswith('seeded_'):
            del contract['overlays'][0]['single_net']
            contract['overlays'][0]['seeds'] = {'VDD': [dict(layer=30, xy=[1000, 500])]}
            if name == 'seeded_assigned_island':
                contract['overlays'][0]['seeds']['VDD'].append(dict(layer=30, xy=[2500, 2500]))
        cp = folder/'contract.json'; cp.write_text(json.dumps(contract, indent=2)+'\n')
        with (folder/'run.log').open('w') as log:
            completed = subprocess.run([sys.executable, str(Path(__file__).with_name('merge_native_supply_manifest.py')),
                                        '--contract', str(cp), '--output', str(folder/'result')],
                                       stdout=log, stderr=subprocess.STDOUT, timeout=60)
        expected = name in ('valid_join', 'seeded_join')
        assert (completed.returncode == 0) == expected, (name, completed.returncode)
        result_file = folder/'result/analysis.json'
        if expected:
            result = json.loads(result_file.read_text())
            assert result['status'] == 'passed manifest-bound native supply integration'
            assert result['after']['VDD']['root'] == result['after']['VDD']['target']
        if name in ('wrong_net_metal', 'captured_native_cut'):
            contact = json.loads((folder/'result/contact_gate.json').read_text())
            assert contact['status'] == 'failed' and contact['errors']
            if name == 'captured_native_cut':
                assert any(r['reason'] == 'new metal touches old cut' for r in contact['errors'])
        results.append(dict(name=name, returncode=completed.returncode, expected_acceptance=expected,
                            status='passed control', log_sha256=sha(folder/'run.log')))
    out = dict(status='passed nine synthetic integration controls', checks=results,
               script_sha256=sha(Path(__file__)),
               integration_script_sha256=sha(Path(__file__).with_name('merge_native_supply_manifest.py')),
               not_run=['native circuit integration'],
               not_applicable=['stock DRC on deliberately non-DRC synthetic geometry',
                               'synthetic placeholder metadata as real decap qualification'])
    (a.output/'analysis.json').write_text(json.dumps(out, indent=2)+'\n'); print(json.dumps(out, indent=2))


if __name__ == '__main__': main()
