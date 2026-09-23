#!/usr/bin/env python3
"""Independently bind the 24 physical openings and 22 nets to the RZ GDS."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import pya
import current_rz_bindings as binding

TOP='placed_core_NOT_CONNECTED_FULLCHIP'
OLD_MAP_SHA='73ed1fc85aaea04b4c975d799dc5843c28f2762c2d33a54c5df0d771bacf3521'
OLD_PROOF_SHA='c7f94e715c0f089adc0e51a3777736ee96f06bb6bf0c9a441866500d5c2398de'
PAD='retained_fullchip_bondpad_70x70_tm1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def records(p):
    with Path(p).open(newline='') as stream:return list(csv.DictReader(stream))
def region(cell,layer):
    it=cell.begin_shapes_rec(layer)
    it.shape_flags=pya.Shapes.SBoxes|pya.Shapes.SPolygons|pya.Shapes.SPaths
    return pya.Region(it).merged()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--old-map',type=Path,required=True)
    ap.add_argument('--new-map',type=Path,required=True)
    ap.add_argument('--old-proof',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert sha(a.old_map)==OLD_MAP_SHA and sha(a.old_proof)==OLD_PROOF_SHA
    old_proof=json.loads(a.old_proof.read_text())
    assert old_proof['status'].startswith('passed all24 public physical opening centres')
    assert old_proof['map_sha256']==OLD_MAP_SHA and old_proof['GDS_sha256']=='ab02b653c6b0e29e7693bed55e097081e6e41f67e24c59102494e6fbc1724541'
    old=records(a.old_map);new=records(a.new_map);assert len(old)==len(new)==24
    candidate=binding.bound(binding.CANDIDATE)
    for i,(before,after) in enumerate(zip(old,new),1):
        assert int(after['pad_number'])==i and before.keys()==after.keys()
        assert all(before[k]==after[k] for k in before if k!='candidate_gds_sha256'),i
        assert after['candidate_gds_sha256']==binding.CANDIDATE[1]
    assert len({r['logical_pin'] for r in new})==22
    ly=pya.Layout();ly.read(str(candidate));assert ly.dbu==.001
    top=ly.cell(TOP);assert top and [c.name for c in ly.top_cells()]==[TOP]
    pads=[i for i in top.each_inst() if i.cell.name==PAD]
    assert len(pads)==24 and all(i.na<=1 and i.nb<=1 for i in pads)
    opening_layer=ly.layer(pya.LayerInfo(9,0));openings={}
    for inst in pads:
        opening=region(inst.cell,opening_layer).transformed(inst.cplx_trans)
        assert opening.count()==1 and opening.area()==opening.bbox().area()
        box=opening.bbox();assert box.width()==box.height()==65800
        centre=box.center();key=(centre.x,centre.y)
        assert key not in openings;openings[key]=(inst,box)
    db_path=binding.bound(binding.STRICT_DB)
    db=pya.LayoutVsSchematic();db.read(str(db_path))
    circuit=db.netlist().circuit_by_name(TOP);assert circuit
    pin_clusters={p.name():circuit.net_for_pin(p.id()).cluster_id for p in circuit.each_pin()}
    strict=json.loads(binding.bound(binding.STRICT_ANALYSIS).read_text())
    assert strict['status']=='passed strict saved comparison' and all(strict['checks'].values())
    assert sorted(pin_clusters)==sorted(strict['database']['layout'][TOP]['pins'])
    assert set(pin_clusters)=={r['logical_pin'] for r in new}
    text_layer=next((db.layer_by_index(i) for i in db.layer_indexes()
                    if str(db.layer_info(i))=='134/25'),None)
    assert text_layer is not None
    details=[]
    for row in new:
        xy=(round(float(row['opening_center_x_um'])*1000),round(float(row['opening_center_y_um'])*1000))
        inst,box=openings[xy]
        assert box.width()/1000==float(row['opening_width_um'])==65.8
        assert box.height()/1000==float(row['opening_height_um'])==65.8
        assert str(row['die_width_um'])==str(row['die_height_um'])=='1414'
        net=db.probe_net(text_layer,pya.Point(*xy))
        assert net is not None and net.circuit().name==TOP,(row['pad_number'],'no top net')
        assert net.cluster_id==pin_clusters[row['logical_pin']],(row['pad_number'],row['logical_pin'],net.cluster_id,pin_clusters[row['logical_pin']])
        details.append(dict(pad=int(row['pad_number']),logical_pin=row['logical_pin'],
                            opening_bbox_dbu=[box.left,box.bottom,box.right,box.top],
                            extracted_net_cluster_id=net.cluster_id,physical_cell=inst.cell.name))
    assert len(details)==24 and len({r['pad'] for r in details})==24
    physical={}
    for name,spec in binding.PHYSICAL.items():
        summary=json.loads(binding.bound(spec).read_text())
        assert summary['status'].startswith('passed') and summary['GDS_sha256']==binding.CANDIDATE[1]
        assert summary['inputs_rules_unchanged']
        if 'decks' in summary:
            assert len(summary['decks'])==1 and summary['decks'][0]['status']=='passed'
            assert len(summary['decks'][0]['reports'])==1 and summary['decks'][0]['reports'][0]['markers']==0
        else:assert summary['markers']==0
        physical[name]=spec[1]
    proof=json.loads(binding.bound(binding.IDENTITY_PROOF).read_text())
    assert proof['status'].startswith('passed serialized exact all-layer nontext identity')
    assert proof['candidate_GDS_sha256']==binding.CANDIDATE[1]
    result=dict(status='passed exact 24 physical openings and 22 extracted pad-net identities on strict-LVS GDS',
                candidate_gds_sha256=binding.CANDIDATE[1],new_map_sha256=sha(a.new_map),
                prior_map_sha256=OLD_MAP_SHA,prior_map_proof_sha256=OLD_PROOF_SHA,
                strict_lvs_analysis_sha256=binding.STRICT_ANALYSIS[1],strict_lvs_database_sha256=binding.STRICT_DB[1],
                physical_summary_sha256=physical,pads=details,unique_logical_pins=22,
                all_other_map_fields_exact=True,all_pad_openings_exact=True,all_pad_nets_exact=True,
                not_run=['bonding/package measurements','PEX/currentIR/EM','post-integration electrical adoption'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],physical_pads=len(details),unique_logical_pins=22)))
if __name__=='__main__':main()
