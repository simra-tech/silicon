#!/usr/bin/env python3
"""Use exact independently checked point boxes, not the empty deep text API."""
import hashlib
from pathlib import Path
import sys

here=Path(__file__).resolve().parent
sys.path.insert(0,str(here))
import box_text_regions
assert all(v in ('passed','rejected',8) for v in box_text_regions.controls().values())
previous=here/'derive_deep_taps_r3.py'
assert hashlib.sha256(previous.read_bytes()).hexdigest()=='20874516f2cc5d9f8dbc3e5f238bc363894c8b07d408820bb3a026aed38af00c'
text=previous.read_text();suffix="exec(compile(code,str(scope['original']),'exec'),globals())"
assert text.count(suffix)==1
namespace={'__file__':str(Path(__file__).resolve()),'__name__':'prepare_literal_label_control'}
exec(compile(text.replace(suffix,''),str(previous),'exec'),namespace)
code=namespace['code']
needle='        dss=pya.DeepShapeStore();dss.threads=1\n'
assert code.count(needle)==1
code=code.replace(needle,"        boxed_indices,flat_labels,label_records=box_text_regions.prepare(ly,top)\n"+needle)
old="""        labels={k:pya.Region(top.begin_shapes_rec(ly.layer(63,0)),dss,pattern,True,1)
            for k,pattern in [('ptap1','[sS][uU][bB]!'),('ntap1','[wW][eE][lL][lL]')]}"""
assert code.count(old)==1
code=code.replace(old,"""        labels={kind:pya.Region(top.begin_shapes_rec(index),dss) for kind,index in boxed_indices.items()}
        assert all((labels[k]^flat_labels[k]).is_empty() for k in labels)
        result['literal_label_records']=label_records
        result['literal_label_controls']=box_text_regions.controls()
        result['flat_API_vs_deep_boxes']='passed exact XOR before any raw-mask derivation'""")
needle="    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())"
assert code.count(needle)==1
code=code.replace(needle,"    inputs[str(here/'box_text_regions.py')]=sha(here/'box_text_regions.py')\n"+needle)
exec(compile(code,str(namespace['scope']['original']),'exec'),globals())
