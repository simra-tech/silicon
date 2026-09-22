#!/usr/bin/env python3
"""Read-only native/contact conductor proof for the nine dummy B probes."""
import hashlib
import json
from pathlib import Path
import pya

ROOT=Path(__file__).resolve().parents[6]
path=ROOT/'build/scratch/bgr-hbt-contact-prototypes-20260922-r1/bgr_hbt_proto_00.gds'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='4948bc29ccb28e2275ea2255fdf23f49f6e3e87bb4560fc5119f6ac64e071308'
ly=pya.Layout();ly.read(str(path));top=ly.top_cell();inst=list(top.each_inst())
assert len(inst)==1 and ly.dbu==.001
native=pya.Region(inst[0].cell.begin_shapes_rec(ly.layer(8,0)));native.flatten()
native_base=pya.Region(pya.Box(-975,-1260,975,-1020))
assert (native_base-native).is_empty()
local=pya.Point(0,-1140)
assert any(p.inside(local) for p in native_base.each())
placed_native=native.transformed(inst[0].trans)
contact=pya.Region(top.begin_shapes_rec(ly.layer(8,0)));contact.flatten()
new=inst[0].trans*local
old=pya.Point(10600,8500)
assert any(p.inside(new) for p in placed_native.each())
assert any(p.inside(new) for p in contact.each())
assert not any(p.inside(old) for p in contact.each())
print(json.dumps(dict(status='passed read-only native dummy-base seed proof',
    original_dummy_GDS_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    native_base_M1_bbox_dbu=[-975,-1260,975,-1020],new_local_seed_dbu=[0,-1140],
    new_contact_seed_dbu=[new.x,new.y],new_seed_inside_native_base_and_contact=True,
    old_contact_seed_dbu=[10600,8500],old_seed_in_contact=False,
    geometry_mutated=False,stock_LVS='not rerun; original dummy stock control retained')))
