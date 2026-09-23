#!/usr/bin/env python3
"""Physical/source proof for three stock-purged all-VDD LevelDown dummies."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import pya

PDK=Path('/foss/pdks/ihp-sg13g2')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('gate','bulk','output'):ap.add_argument('--'+k,type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={1}
    gate=json.loads(a.gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and gate['project_cpu_budget']>=44 and 0<=age<1800
    assert pya.__version__=='0.30.9'
    a.output.mkdir(parents=True);(a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    gds=a.bulk/'full-io-marker-20260923-r2/io_marker_native.gds'
    stock=PDK/'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    source=a.bulk/'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    rule=PDK/'libs.tech/klayout/tech/lvs/rule_decks/rfmos_model_mapping.lvs'
    assert sha(gds)=='ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
    assert sha(stock)=='4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    assert sha(source)=='f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    text=source.read_text();body=re.search(r'(?m)^\.SUBCKT sg13g2_LevelDown .*?^\.ENDS',text,re.S).group(0)
    record='MP0 vdd vdd vdd vdd sg13_hv_pmos m=1 w=4.65u l=450.00n ng=1'
    assert body.splitlines().count(record)==1
    # Source-only top reachability: the three IO inputs instantiate LevelDown
    # exactly once each; this proof does not use comparer-selected identity.
    definitions={m.group(1).upper():(m.group(2).split(),m.group(3).splitlines()) for m in
                 re.finditer(r'(?im)^\.SUBCKT\s+(\S+)([^\n]*)\n(.*?)^\.ENDS[^\n]*',text,re.S)}
    occurrences=[]
    def walk(name,nodes,path):
        pins,lines=definitions[name.upper()]; assert len(pins)==len(nodes)
        mapping=dict(zip((p.upper() for p in pins),nodes))
        if name.upper()=='SG13G2_LEVELDOWN':
            occurrences.append(dict(path='.'.join(path+['MP0']),model='sg13_hv_pmos',
                source_record=record,terminal_nodes={k:mapping['VDD'] for k in ('D','G','S','B')}))
        for line in lines:
            tokens=line.split()
            if not tokens or not tokens[0].upper().startswith('X') or '/' not in tokens:continue
            pos=tokens.index('/');child=tokens[pos+1]
            assert child.upper() in definitions,child
            net=lambda n:mapping.get(n.upper(),'.'.join(path+[n.upper()]))
            walk(child,[net(n) for n in tokens[1:pos]],path+[tokens[0][1:].upper()])
    topname='PLACED_CORE_NOT_CONNECTED_FULLCHIP'
    walk(topname,[p.upper() for p in definitions[topname][0]],[])
    assert {r['path'] for r in occurrences}=={'PAD12_EN.I0.MP0','PAD14_SCLK.I0.MP0','PAD15_SDI.I0.MP0'}
    assert all(set(r['terminal_nodes'].values())=={'VDD'} for r in occurrences)
    ly,lib=pya.Layout(),pya.Layout();ly.read(str(gds));lib.read(str(stock))
    actual_names=sorted({i.cell.name for i in ly.top_cell().each_inst() if i.cell.name.endswith('sg13g2_IOPadIn')})
    assert len(actual_names)==1,actual_names
    cell=ly.cell(actual_names[0]);native=lib.cell('sg13g2_IOPadIn')
    assert cell and native
    for layer in {(i.layer,i.datatype) for l in (ly,lib) for i in l.layer_infos()}:
        delta = pya.Region(cell.begin_shapes_rec(ly.layer(*layer))) ^ pya.Region(native.begin_shapes_rec(lib.layer(*layer)))
        if layer == (128, 0):
            # Exact isolated Secondary body translated through its held
            # LevelDown and IOPadIn instances; no other marker is permitted.
            assert (delta ^ pya.Region(pya.Box(40685, 141540, 41685, 143540))).is_empty()
        else:
            assert delta.is_empty(), str(layer)
    reg=lambda layer:pya.Region(cell.begin_shapes_rec(ly.layer(layer,0))).merged()
    gatebox=pya.Box(41540,161620,41990,166270)
    gatepoly=(reg(1)&reg(5))&pya.Region(gatebox)
    assert (gatepoly^pya.Region(gatebox)).is_empty() and gatepoly.area()==2092500
    # Explicit physical domains: p-diffusion is NOT connected to nwell.
    # Only native ntap active connects nwell to the contact/metal graph.
    raw={'poly':reg(5),'pdiff':(reg(1)-reg(5))&reg(14)&reg(31),
         'ntap':(reg(1)-reg(5)-reg(14))&reg(31),'nwell':reg(31),'cont':reg(6)}
    sequence=[8,19,10,29,30,49,50,66,67,125,126,133,134]
    raw.update({str(i):reg(i) for i in sequence})
    flat=pya.Layout();flat.dbu=.001;tc=flat.create_cell('independent_device_terminal_graph')
    for i,(name,r) in enumerate(raw.items()):tc.shapes(flat.layer(i+1,0)).insert(r)
    graph=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,tc,[]))
    layers={name:graph.make_layer(flat.layer(i+1,0),name) for i,name in enumerate(raw)}
    for r in layers.values():graph.connect(r)
    for x,y in [('poly','cont'),('pdiff','cont'),('ntap','cont'),('ntap','nwell'),('cont','8')]:graph.connect(layers[x],layers[y])
    for x,y in zip(sequence,sequence[1:]):graph.connect(layers[str(x)],layers[str(y)])
    graph.extract_netlist()
    probes={}
    for name,layer,x,y in [('G','poly',41765,164000),('S','pdiff',41350,164000),
                          ('D','pdiff',42180,164000),('B','nwell',41765,164000),
                          ('VDD_native_pin','30',41120,171000)]:
        net=graph.probe_net(layers[layer],pya.Point(x,y));assert net is not None,(name,layer,x,y)
        probes[name]=dict(layer=layer,point_dbu=[x,y],cluster=net.cluster_id)
    assert len({p['cluster'] for p in probes.values()})==1
    transforms=[('PAD12_EN',pya.Trans(pya.Trans.R90,1273000,915000)),
                ('PAD14_SCLK',pya.Trans(pya.Trans.M0,467000,1273000)),
                ('PAD15_SDI',pya.Trans(pya.Trans.M0,579000,1273000))]
    instances=list(ly.top_cell().each_inst());physical=[]
    for name,tr in transforms:
        found=[i for i in instances if i.cell.name.endswith('sg13g2_IOPadIn') and i.trans==tr]
        assert len(found)==1,name
        physical.append(dict(source_instance=name,transform=str(tr),gate_box_dbu=str(tr*gatebox),
                             all_four_terminals_to_native_VDD='passed local physical graph with held exact instance transform'))
    ruletext=rule.read_text();assert 'target_netlist.purge_devices' in ruletext
    result=dict(status='passed independent three-dummy source/native-terminal proof',
                source_occurrences=occurrences,physical_instances=physical,native_gate_area_um2=2.0925,
                actual_native_source_alias=actual_names[0],
                sole_native_delta='One declared 128/0 Secondary body; all dummy electrode and conductor layers unchanged',
                local_terminal_probes=probes,unconditional_purge_rule=ruletext,
                inputs={str(p):sha(p) for p in (gds,stock,source,rule)},script_sha256=sha(Path(__file__)),
                not_run=['extraction-only source derivative','fullchip strict LVS with exclusion','electrical/ESD qualification'],
                original_fullchip_LVS='failed retained',source_or_geometry_changes='not applicable',
                scope='Three original all-VDD source dummies, not deletion from canonical design; body proved through actual nwell/ntap/contact/metal path.')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])


if __name__=='__main__':main()
