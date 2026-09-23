#!/usr/bin/env python3
"""Independent saved-graph accounting and literal source-chain witness."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def witness(source, native):
    return (source['terminals']['WELL']['degree'] == 1
            and source['terminals']['WELL']['physical_external'] is None
            and len(native) > 0
            and all(q['terminals']['WELL']['physical_external'] == 'VSS' for q in native))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('observation', 'source', 'scope-control', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    assert sha(a.source) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    j = json.loads(a.observation.read_text())
    assert j['status'] == 'passed exact non-equivalence witness; source/native topology FAILED'
    assert all(j['checks'].values()) and sha(a.source) in j['inputs'].values()
    scope = json.loads(a.scope_control.read_text())
    assert scope['source_sha256'] == sha(a.source)
    assert [(q['case'], q['substrate_net_count']) for q in scope['exact_reader_controls']] == [('absent',2),('explicit',1),('wrong_name',2)]
    raw = a.source.read_text()
    declarations = [(i+1, line) for i,line in enumerate(raw.splitlines())
                    if re.match(r'^\s*\*?\s*\.global\b', line, re.I)]
    assert not declarations
    lines = [
        'Xpad02_vss VDD VSS IOVDD IOVSS / sg13g2_IOPadVss',
        '.SUBCKT sg13g2_IOPadVss vdd vss iovdd iovss',
        'XI2 vss iovdd iovss / sg13g2_DCPDiode',
        '.SUBCKT sg13g2_DCPDiode anode cathode guard',
        'XR0 guard sub! ptap1 A=33.524p P=23.16u']
    chain = []
    for line in lines:
        hits = [i+1 for i,text in enumerate(raw.splitlines()) if text == line]
        assert hits
        chain.append(dict(text=line, source_line_numbers=hits))
    source_witness = j['shortest_witness']
    assert source_witness['name'] == 'PAD02_VSS.I2._G1_TAP_SYNTAX_XR0'
    native = j['views']['native']['tap_records']
    assert witness(source_witness, native)
    changed = copy.deepcopy(source_witness)
    changed['terminals']['WELL']['physical_external'] = 'VSS'
    changed_native = copy.deepcopy(native)
    changed_native[0]['terminals']['WELL']['physical_external'] = None
    controls = dict(positive=witness(source_witness, native),
                    source_WELL_external_rejected=not witness(changed,native),
                    native_nonexternal_WELL_rejected=not witness(source_witness,changed_native),
                    empty_native_inventory_rejected=not witness(source_witness,[]))
    assert all(controls.values())
    totals = {}
    for side,v in j['views'].items():
        counters = Counter((q['model'].lower(),q['terminal'].lower())
                           for rows in v['tap_well_partitions'].values() for q in rows)
        totals[side] = dict(well_partitions=v['well_partition_count'],
                           tap_records=len(v['tap_records']),
                           external_WELL_terminals=v['external_tap_well_count'],
                           TIE_equals_WELL=v['tie_well_same_net_count'],
                           degree_one_WELL=sum(t['terminals']['WELL']['degree']==1 for t in v['tap_records']),
                           TIE_external_ports=dict(Counter(t['terminals']['TIE']['physical_external'] for t in v['tap_records'])),
                           all_terminal_incidence_count=sum(counters.values()),
                           terminal_incidence=[dict(model=k[0],terminal=k[1],count=n) for k,n in sorted(counters.items())])
    result = dict(status='passed exact partition accounting and minimal witness controls; equivalence FAILED',
                  inputs={str(q):sha(q) for q in (a.source,a.observation,a.scope_control,Path(__file__))},
                  counts=totals, source_chain=chain, shortest_witness=source_witness,
                  predicate_controls=controls, explicit_CDL_or_SPICE_global_declarations=declarations,
                  pinned_reader_global_controls=scope['exact_reader_controls'],
                  interpretation='243 source body nodes are not equivalent to the one native external VSS body component. A/P does not affect this witness. This does not attribute every failed comparer pair to that cause.',
                  remedy_authority='not established: explicit source intent for substrate partition and VSS relationship is required before changing node binding',
                  not_run=['global substrate source correction','tap A/P correction','new geometry or extraction','electrical/ESD qualification'])
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(totals,indent=2))


if __name__ == '__main__':
    main()
