#!/usr/bin/env python3
"""Exact original proof with detached fill records and native update batching."""
import hashlib
from pathlib import Path
from cached_fill import relocate

HERE=Path(__file__).resolve().parent
base=HERE.parent/'integration_be54/flatten_pure_fill.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='8bf3d06ee1fa94d8dd63e4fc200ba90fdc5864c529b5c7ac2ec1227e59b9980b'
code=base.read_text()
start=code.index('    added=Counter();saved_instances=[];expanded=Counter();expectedchildren=rootchildren.copy()')
end=code.index('    assert shapes(ly,top)==rootshapes+added',start)
code=code[:start]+'''    def progress(**kw):result.update(kw);save()
    added,saved_instances,expanded,expectedchildren=CACHED_MOVE(ly,top,names,progress)
'''+code[end:]
for old,new in [
    ("expected[Path(__file__)]=sha(Path(__file__))", "expected[SELF_PATH]=sha(SELF_PATH);expected[CACHED_PATH]=sha(CACHED_PATH);expected[BASE_PATH]=sha(BASE_PATH)"),
    ("(a.output/'source.py').write_bytes(Path(__file__).read_bytes())", "(a.output/'source.py').write_bytes(SELF_PATH.read_bytes())\n    (a.output/'effective_source.py').write_text(EFFECTIVE_CODE)"),
    ("before={c.name:signature(ly,c) for c in ly.each_cell()};rootshapes=shapes(ly,top);rootchildren=children(top)",
     "result.update(phase='loaded original');save()\n    before={c.name:signature(ly,c) for c in ly.each_cell()};rootshapes=shapes(ly,top);rootchildren=children(top)\n    result.update(phase='original signatures complete');save()")]:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__',
    'SELF_PATH':Path(__file__).resolve(),'CACHED_PATH':HERE/'cached_fill.py','BASE_PATH':base,
    'CACHED_MOVE':relocate,'EFFECTIVE_CODE':code})
