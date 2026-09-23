#!/usr/bin/env python3
"""Bind current logical IO instances to round-trip ODB masters and pinned hierarchy."""
import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import re
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--roundtrip', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    pnl = Path('designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top.pnl.v')
    pdk = Path('/foss/pdks/ihp-sg13g2')
    cdl = pdk / 'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
    gds = pdk / 'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    assert (pdk / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert sha(cdl) == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
    defs = {}
    for m in re.finditer(r'^\.SUBCKT\s+(\S+)([^\n]*)\n(.*?)^\.ENDS[^\n]*', cdl.read_text(), re.M | re.S | re.I):
        defs[m[1]] = dict(ports=m[2].split(), body=m[3], sha256=hashlib.sha256(m[0].encode()).hexdigest())
    graph = {name: [] for name in defs}
    for name, entry in defs.items():
        for line in entry['body'].splitlines():
            f = line.split()
            if f and f[0].upper().startswith('X') and f[-1] in defs:
                graph[name].append(dict(instance=f[0], master=f[-1], source=line))
    physical = {}
    for line in a.roundtrip.read_text().splitlines():
        f = line.split('\t')
        if f[0] == 'INST':
            assert f[1] not in physical
            physical[f[1]] = f[2]
    logical = {}
    for m in re.finditer(r'^\s*(\S+)\s+(\S+)\s*\(\.', pnl.read_text(), re.M):
        name = m[2].lstrip('\\')
        assert name not in logical
        logical[name] = m[1]
    assert len(physical) == 4904 and len(logical) == 4884
    assert all(physical.get(name) == master for name, master in logical.items())
    added = {name: master for name, master in physical.items() if name not in logical}
    assert len(added) == 20 and all(master.startswith('sg13g2_Filler') for master in added.values())
    ios = {name: master for name, master in physical.items() if master in defs}
    layout = pya.Layout()
    layout.read(str(gds))
    assert all(layout.cell(master) is not None for master in set(ios.values()))
    targets = ['sg13g2_io_inv_x1', 'sg13g2_LevelUpInv', 'sg13g2_Filler10000']
    paths = {}
    for target in targets:
        found = []
        for topname, master in ios.items():
            queue = deque([(master, [dict(instance=topname, master=master)])])
            while queue:
                cell, path = queue.popleft()
                if cell == target:
                    found.append(path)
                for edge in graph[cell]:
                    assert edge['master'] not in [r['master'] for r in path], 'Recursive library'
                    queue.append((edge['master'], path + [edge]))
        paths[target] = dict(reachable=bool(found), occurrence_count=len(found), paths=found)
    result = dict(status='passed source/native-master reachability audit only',
                  checks=dict(original_logical_instance_master_binding='passed', twenty_added_fillers='passed',
                              native_IO_master_presence='passed', internal_CDL_hierarchy='passed',
                              final_fullchip_CDL_LVS='not run', new_native_LVS='not run',
                              electrical_unit_correction='not run', stochastic_seed='not applicable'),
                  logical_instances=len(logical), physical_instances=len(physical),
                  io_instances=len(ios), io_master_counts=dict(Counter(ios.values())), added_fillers=added,
                  target_paths=paths, source_graph=graph,
                  inputs={'g1_chip_top.pnl.v': sha(pnl), 'fullchip-def-odb-r5-roundtrip.tsv': sha(a.roundtrip),
                          'sg13g2_io.cdl': sha(cdl), 'sg13g2_io.gds': sha(gds)},
                  worker_sha256=sha(Path(__file__)))
    a.output.mkdir(exist_ok=False)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('source_graph', 'target_paths')}, indent=2))
    print(json.dumps({k: {j: v[j] for j in ('reachable', 'occurrence_count')} for k, v in paths.items()}, indent=2))


if __name__ == '__main__':
    main()
