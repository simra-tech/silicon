#!/usr/bin/env python3
"""Report exact saved-record differences in the failed synthetic control."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('control_cached_fill.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='7dbf3c4751548340b58fc9fd236b955ba7d2d9fdc64fc83b95726e9a3e0f2dce'
code=base.read_text()
needle='    assert shapes(saved,st)==rs+added and children(st)==expected'
assert code.count(needle)==1
code=code.replace(needle,'''    actual=shapes(saved,st);wanted=rs+added
    old=pya.Layout();old.read(str(original));ot=old.cell('TOP')
    result=dict(status='diagnostic record differences only; equivalence control not passed',
        missing_shapes=[dict(record=list(k),count=v) for k,v in (wanted-actual).items()],
        additional_shapes=[dict(record=list(k),count=v) for k,v in (actual-wanted).items()],
        missing_children=[dict(record=list(k),count=v) for k,v in (expected-children(st)).items()],
        additional_children=[dict(record=list(k),count=v) for k,v in (children(st)-expected).items()],
        original_roundtrip_missing_shapes=[dict(record=list(k),count=v) for k,v in (rs-shapes(old,ot)).items()],
        original_roundtrip_added_shapes=[dict(record=list(k),count=v) for k,v in (shapes(old,ot)-rs).items()],
        original_roundtrip_properties=dict(memory=props,saved=properties(ot)),
        candidate_properties=dict(memory=properties(top),saved=properties(st)),
        native_definition_inmemory=before['NATIVE_HELD'],native_definition_original_saved=signature(old,old.cell('NATIVE_HELD')),
        native_definition_candidate_saved=signature(saved,saved.cell('NATIVE_HELD')),
        original_sha256=sha(original),candidate_sha256=sha(candidate))
    (a.output/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\\n')
    print(json.dumps(result));return''')
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
