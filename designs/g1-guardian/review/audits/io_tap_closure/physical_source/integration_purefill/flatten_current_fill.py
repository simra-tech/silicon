#!/usr/bin/env python3
"""Same qualified fill representation transform on current hard/R100 geometry."""
import hashlib
import json
from pathlib import Path
from cached_fill_r2 import relocate
import current_projection_bindings as binding

HERE=Path(__file__).resolve().parent
qualified,qj,control=binding.qualification()
base=HERE.parent/'integration_be54/flatten_pure_fill.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='8bf3d06ee1fa94d8dd63e4fc200ba90fdc5864c529b5c7ac2ec1227e59b9980b'
code=base.read_text();start=code.index('    added=Counter();saved_instances=[];expanded=Counter();expectedchildren=rootchildren.copy()')
end=code.index('    assert shapes(ly,top)==rootshapes+added',start)
code=code[:start]+'''    assert templates==QUALIFIED['templates'], 'current fill definitions differ from qualified zero-device witnesses'
    def progress(**kw):result.update(kw);save()
    added,saved_instances,expanded,expectedchildren=CACHED_MOVE(ly,top,names,progress)
'''+code[end:]
edits=[('analog-pair-overlay-flat-20260923-r1/overlay_flattened.gds',binding.ORIGINAL_GDS),
    ('dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333',binding.ORIGINAL_SHA),
    ('analog-pair-reference-20260923-r1/physical_taps_reader.cdl','trip-hard-full-reference-20260923-r1/physical_taps_reader.cdl'),
    ('35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51',binding.SOURCE_SHA),
    ('expected[Path(__file__)]=sha(Path(__file__))',
     "expected[SELF_PATH]=sha(SELF_PATH);expected[QUALIFIED_PATH]=sha(QUALIFIED_PATH);expected[CONTROL_PATH]=sha(CONTROL_PATH)\n    for dependency in DEPENDENCIES:expected[dependency]=sha(dependency)"),
    ("(a.output/'source.py').write_bytes(Path(__file__).read_bytes())",
     "(a.output/'source.py').write_bytes(SELF_PATH.read_bytes())\n    (a.output/'effective_source.py').write_text(EFFECTIVE_CODE)")]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','SELF_PATH':Path(__file__).resolve(),
    'QUALIFIED_PATH':qualified,'QUALIFIED':qj,'CONTROL_PATH':control,'CACHED_MOVE':relocate,'EFFECTIVE_CODE':code,
    'DEPENDENCIES':[base,HERE/'current_projection_bindings.py',HERE/'cached_fill.py',HERE/'cached_fill_r2.py']})
