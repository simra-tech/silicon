#!/usr/bin/env python3
"""Isolated r7 derivative: retain source and ports, clear the R90 TM2 ring band."""
import json
import sys
from pathlib import Path
from build_native_prototypes import sha

HERE = Path(__file__).resolve().parent
BASE_SHA = '95c631cf43f464572410e3eaace36907935a8b61dad4863b45091da986a9f74d'


def main():
    original = HERE / 'build_power_revision.py'
    assert sha(original) == BASE_SHA
    text = original.read_text()
    changes = [
        ("wire(134,[(3,172),(383,172),(383,218)],2.,'vdd')",
         "wire(134,[(40,172),(383,172),(383,218)],2.,'vdd')"),
        ("('vdd',(20.,54.,180.,200.,220.),145.)",
         "('vdd',(40.,54.,180.,200.,220.),145.)"),
        ("""                for layer in(49,66):array(layer,x,y,4,3,net)
                upper_pod(x,y,net)
                if net=='vdd':wire(134,[(x,y),(3.+dx,y),(3.+dx,172.)],2.,net)
                else:wire(126,[(x,y),(14.+dx,y),(14.+dx,178.)],2.,net)""",
         """                array(49,x,y,4,3,net)
                escape=40. if net=='vdd' and dx==0. else x
                if escape!=x:
                    bridge=region_box(x-1,y-1,escape+1,y+1)
                    assert (bridge.sized(239)&foreign[net][50]).is_empty(), 'M4 bridge foreign-net clearance'
                    wire(50,[(x,y),(escape,y)],2.,net)
                array(66,escape,y,4,3,net)
                upper_pod(escape,y,net)
                if net=='vdd':
                    stem=40. if dx==0. else 3.+dx
                    wire(134,[(escape,y),(stem,y),(stem,172.)],2.,net)
                else:wire(126,[(x,y),(14.+dx,y),(14.+dx,178.)],2.,net)"""),
        ("gds=a.output/'g1_sense_physical.gds';ly.write(str(gds))",
         """gds=a.output/'g1_sense_physical.gds';ly.write(str(gds))
        saved=pya.Layout();saved.read(str(gds));saved_cell=saved.cell('g1_sense_physical')
        tm2=snapshot(saved_cell,134);tv2=snapshot(saved_cell,133)
        assert not tm2.is_empty() and tm2.bbox().left>=36160
        assert not tv2.is_empty() and tv2.bbox().left>=36160
        result['ring_keepout']=dict(status='passed',required_min_local_x_um=36.16,
            actual_TM2_min_local_x_um=tm2.bbox().left*.001,
            actual_TopVia2_min_local_x_um=tv2.bbox().left*.001,
            R90_translation_um=[1031,331],global_TM2_min_y_um=331+tm2.bbox().left*.001,
            nearest_ring_top_y_um=362.16,spacing_um=331+tm2.bbox().left*.001-362.16,
            scope='All saved TM2 and TopVia2 geometry; parent full-core check remains separate')"""),
    ]
    for old, new in changes:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    output = Path(sys.argv[sys.argv.index('--output') + 1])
    prep = output.with_name(output.name + '-preparation')
    assert not prep.exists()
    prep.mkdir(parents=True)
    (prep / 'derived_builder.py').write_text(text)
    (prep / 'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (prep / 'bindings.json').write_text(json.dumps(dict(
        original_builder_sha256=BASE_SHA, derived_builder_sha256=sha(prep / 'derived_builder.py'),
        adapter_sha256=sha(Path(__file__)), exact_patch_count=len(changes),
        immutable_r6_GDS_sha256='5d640799cb0a4257d34e82a1018237a6bfa0d595bc0d6520522d40125322c170',
        source_ports='unchanged nine r6 ports', full_core_check='not run'), indent=2) + '\n')
    namespace = {'__file__': str(original), '__name__': 'ring_power_derivative'}
    exec(compile(text, str(prep / 'derived_builder.py'), 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
