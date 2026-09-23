#!/usr/bin/env python3
"""Initialize extent before immutable deep-store import; reject empty results."""
import hashlib
from pathlib import Path

previous=Path(__file__).resolve().with_name('derive_deep_taps_r2.py')
assert hashlib.sha256(previous.read_bytes()).hexdigest()=='910b99e679bd58d821e47e9ea2bfdc48dc404b9ccda69a48ce0c085cec910ecb'
text=previous.read_text()
scope={'__file__':str(Path(__file__).resolve()),'__name__':'prepare_cache_order_control'}
suffix="exec(compile(code,str(original),'exec'),globals())"
assert text.count(suffix)==1
exec(compile(text.replace(suffix,''),str(previous),'exec'),scope)
code=scope['code']
line="        extent_layer=ly.layer(300,0);top.shapes(extent_layer).insert(top.bbox())\n"
assert code.count(line)==1
code=code.replace(line,'')
needle='        dss=pya.DeepShapeStore();dss.threads=1\n'
assert code.count(needle)==1
code=code.replace(needle,line+needle)
needle="        outputs={}\n"
assert code.count(needle)==1
code=code.replace(needle,"""        result['coverage']={'raw_active_area':active.area(),'extent_area':extent.area(),
            'pwell_area':pwell.area(),'ptap_label_area':labels['ptap1'].area(),
            'ptap_marker_area':markers['ptap1'].area(),'ptap_tie_area':derived['ptap1'].area()}
        assert all(v>0 for v in result['coverage'].values()),result['coverage']
        assert not all(v>0 for v in dict(result['coverage'],ptap_tie_area=0).values())
        result['empty_tap_negative_control']='passed rejection'
        result['preserved_r2_false_completion']='failed semantic coverage: zero area, not accepted'
"""+needle)
exec(compile(code,str(scope['original']),'exec'),globals())
