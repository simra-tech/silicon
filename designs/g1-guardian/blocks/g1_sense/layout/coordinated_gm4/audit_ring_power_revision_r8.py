#!/usr/bin/env python3
"""r8 saved delta: 5 um ring rule and explicit changed MIM outer context."""
import sys
from pathlib import Path
from build_native_prototypes import sha

HERE=Path(__file__).resolve().parent


def main():
    original=HERE/'audit_ring_power_revision.py'
    assert sha(original)=='76d2a4f6f75ba7278cde1185e37f3b7e0e3eee5412c62c450859dee88aa1f71c'
    text=original.read_text()
    old="""        window = pya.Region(plate.bbox().enlarged(5000))
        for layer in (36,67,126,129):
            delta = (snapshot(cell,layer)^snapshot(prior,layer)) & window
            contexts.append(dict(plate_bbox=str(plate.bbox()),layer=layer,XOR_um2=delta.area()*1e-6))
            assert delta.is_empty(), contexts[-1]"""
    new="""        for margin in (1500,5000):
            window = pya.Region(plate.bbox().enlarged(margin))
            for layer in (36,67,126,129):
                delta = (snapshot(cell,layer)^snapshot(prior,layer)) & window
                contexts.append(dict(plate_bbox=str(plate.bbox()),layer=layer,margin_um=margin*.001,XOR_um2=delta.area()*1e-6))
                if margin==1500:assert delta.is_empty(), contexts[-1]"""
    changes=[(old,new),
        ('5d640799cb0a4257d34e82a1018237a6bfa0d595bc0d6520522d40125322c170','9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02'),
        ('tm2.bbox().left >= 33160 and tv2.bbox().left >= 33160','tm2.bbox().left >= 36160 and tv2.bbox().left >= 36160'),
        ('MIM_5um_context_XOR=contexts','MIM_context_XOR=contexts'),
    ]
    for old,new in changes:
        assert text.count(old)==1,old
        text=text.replace(old,new)
    output=Path(sys.argv[sys.argv.index('--output')+1])
    prep=output.with_name(output.stem+'-preparation')
    assert not prep.exists()
    prep.mkdir(parents=True)
    (prep/'derived_audit.py').write_text(text)
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    namespace={'__file__':str(original),'__name__':'ring_r8_saved_audit'}
    exec(compile(text,str(prep/'derived_audit.py'),'exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    main()
