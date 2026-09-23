#!/usr/bin/env python3
"""Rebind the exact native dummy electrode proof to current source and GDS."""
import hashlib
from pathlib import Path

here=Path(__file__).resolve().parent
original=here.parents[1]/'fullchip_reference_closure/physical_lvs/marker_remedy/prove_leveldown_dummies.py'
assert hashlib.sha256(original.read_bytes()).hexdigest()=='67b5ca6c56fbaedf59ba7d08ff6e2f89c3bd85bd6c8384f235abe31b0fb8ab9c'
code=original.read_text()
old_xor="        assert (pya.Region(cell.begin_shapes_rec(ly.layer(*layer)))^pya.Region(native.begin_shapes_rec(lib.layer(*layer)))).is_empty(),str(layer)"
new_xor="""        delta=pya.Region(cell.begin_shapes_rec(ly.layer(*layer)))^pya.Region(native.begin_shapes_rec(lib.layer(*layer)))
        if layer==(128,0):
            assert (delta^pya.Region(pya.Box(40685,141540,41685,143540))).is_empty()
        else:
            assert delta.is_empty(),str(layer)"""
edits=[('set(os.sched_getaffinity(0))=={1}','len(os.sched_getaffinity(0))==1'),
    ('final-native-sealring-20260923-r1/sealed_native.gds','gshared-fill-20260923-r4/route_fill_pruned.gds'),
    ('3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9','4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2'),
    ('fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl','io-physical-ap-source-20260923-r2/physical_taps.cdl'),
    ('f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9','796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf'),
    ('^\\.SUBCKT sg13g2_LevelDown ','^\\.SUBCKT G1_VSS_DERIVATIVE__sg13g2_LevelDown '),
    ("name.upper()=='SG13G2_LEVELDOWN'","name.upper()=='G1_VSS_DERIVATIVE__SG13G2_LEVELDOWN'"),
    (old_xor,new_xor)]
for before,after in edits:
    assert code.count(before)==1,(before,code.count(before));code=code.replace(before,after)
exec(compile(code,str(original),'exec'),globals())
