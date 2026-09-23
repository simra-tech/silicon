#!/usr/bin/env python3
"""Read-only source/port-bound top-label audit and pinned pin-creation controls."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import pya


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('candidate', 'observations', 'reference', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    source = a.candidate/'sealed_native.gds'
    metadata = a.candidate/'analysis.json'
    ports_path = a.observations/'external_bterms.json'
    paths = [source, metadata, ports_path, a.reference]
    hashes = {str(q): sha(q) for q in paths}
    meta = json.loads(metadata.read_text())
    ports = json.loads(ports_path.read_text())
    assert meta['status'].startswith('passed') and ports['status'].startswith('passed')
    assert meta['GDS_sha256'] == ports['GDS_sha256'] == sha(source)
    assert ports['logical_BTerms'] == 22 and ports['physical_ports'] == 24 and not ports['errors']
    topname = 'placed_core_NOT_CONNECTED_FULLCHIP'
    header, = re.findall(r'^\.SUBCKT '+topname+r' ([^\n]+)$', a.reference.read_text(), re.M)
    pins = header.split()
    assert len(pins) == len(set(pins)) == 22
    assert set(pins) == {row['pin'] for row in ports['ports']}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    ly = pya.Layout()
    ly.read(str(source))
    top = ly.cell(topname)
    assert top is not None and len(ly.top_cells()) == 1
    texts = []
    direct = []
    for layer in ly.layer_indices():
        info = ly.get_info(layer)
        for shape in top.shapes(layer).each():
            if shape.is_text():
                direct.append(dict(layer=[info.layer,info.datatype], text=shape.text.string,
                                   xy=[shape.text.trans.disp.x,shape.text.trans.disp.y]))
        it = top.begin_shapes_rec(layer)
        while not it.at_end():
            shape = it.shape()
            if shape.is_text():
                value = shape.text
                pt = it.trans()*pya.Point(value.trans.disp.x,value.trans.disp.y)
                texts.append(dict(layer=[info.layer,info.datatype], text=value.string,
                                  xy=[pt.x,pt.y], source_cell=it.cell().name))
            it.next()
    annotations = []
    for name in pins:
        matching = [row for row in ports['ports'] if row['pin'] == name]
        assert all(row['status'] == 'passed' and len(row['actual_components']) == 1 for row in matching)
        assert len({tuple(row['actual_components'][0]) for row in matching}) == 1
        port = matching[0]
        layer = port['layer']
        x1,y1,x2,y2 = port['bbox_dbu']
        at_port = [r for r in texts if r['layer'] == [layer,25]
                   and x1 <= r['xy'][0] <= x2 and y1 <= r['xy'][1] <= y2]
        annotations.append(dict(pin=name, layer=[layer,25], proposed_xy=[(x1+x2)//2,(y1+y2)//2],
            source_bound_port=port, present_texts=at_port,
            exact_expected_label_present=any(r['text'] == name for r in at_port)))
    # Test the actual API, not an assumption that existing .SUBCKT pins or
    # arbitrary internal labels receive the same make_top_level_pins treatment.
    controls = []
    for name, header in [('explicit','A B'),('unlabelled','')]:
        path = a.output/(name+'.cir')
        path.write_text('* Pin-creation API control, not a circuit qualification\n.SUBCKT T '+header+'\nR1 A INTERNAL 1\nR2 INTERNAL B 1\n.ENDS T\n')
        netlist = pya.Netlist()
        netlist.read(str(path), pya.NetlistSpiceReader())
        circuit = netlist.circuit_by_name('T')
        before = [pin.name() for pin in circuit.each_pin()]
        netlist.make_top_level_pins()
        after = [pin.name() for pin in circuit.each_pin()]
        controls.append(dict(case=name, before=before, after=after,
                             nets=[net.name for net in circuit.each_net()], input_sha256=sha(path)))
    lvs = pdk/'libs.tech/klayout/tech/lvs'
    rules = {name: sha(lvs/name) for name in ['sg13g2.lvs','rule_decks/layers_definitions.lvs','rule_decks/general_connections.lvs']}
    assert hashes == {str(q): sha(q) for q in paths}
    result = dict(status='passed read-only annotation and API observations', input_hashes=hashes,
        script_sha256=sha(Path(__file__)), KLayout=pya.__version__, stock_rule_hashes=rules,
        topcell=topname, direct_top_texts=direct, recursive_text_count=len(texts),
        label_layers=dict(collections.Counter(str(r['layer']) for r in texts)),
        source_pins=pins, missing_expected_port_labels=[r['pin'] for r in annotations if not r['exact_expected_label_present']],
        proposed_annotations=annotations, api_controls=controls,
        api_documentation=pya.Netlist.make_top_level_pins.__doc__,
        not_run=['annotation mutation','new extraction','strict LVS acceptance'],
        not_applicable=['label-based virtual physical joining'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('proposed_annotations','input_hashes')},indent=2))


if __name__ == '__main__':
    main()
