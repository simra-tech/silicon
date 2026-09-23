#!/usr/bin/env python3
"""Enable documented deep text conversion and retain the disabled control."""
import hashlib
from pathlib import Path

original=Path(__file__).resolve().with_name('probe_text_regions.py')
assert hashlib.sha256(original.read_bytes()).hexdigest()=='0b85cd72e5d17eeaf17108b6f1262d7737a5f1beb1be9a267837695fb5635a65'
code=original.read_text()
needle='    dss=pya.DeepShapeStore();dss.threads=1\n'
assert code.count(needle)==1
code=code.replace(needle,needle+"    dss.text_enlargement=1;dss.text_property_name='G1_RAW_TEXT'\n")
line="    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())\n"
assert code.count(line)==1
code=code.replace(line,'')
needle="    assert controls[0]['flat_area']==controls[1]['flat_area']==4\n"
assert code.count(needle)==1
code=code.replace(needle,line+"""    disabled=pya.DeepShapeStore();disabled.threads=1
    disabled_area=pya.Region(t.begin_shapes_rec(layer),disabled,'sub!',False,1).area()
    (a.output/'raw_control.json').write_text(json.dumps(dict(synthetic=controls,masters=rows,
        disabled_default_text_enlargement=disabled.text_enlargement,disabled_area=disabled_area),indent=2)+'\\n')
    assert disabled_area==0
"""+needle)
exec(compile(code,str(original),'exec'),globals())
