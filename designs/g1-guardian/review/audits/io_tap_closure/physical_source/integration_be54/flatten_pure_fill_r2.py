#!/usr/bin/env python3
"""Same exact fill projection, batched instance-list replacement with progress."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('flatten_pure_fill.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='8bf3d06ee1fa94d8dd63e4fc200ba90fdc5864c529b5c7ac2ec1227e59b9980b'
code=base.read_text()
edits=[
    ("before={c.name:signature(ly,c) for c in ly.each_cell()};rootshapes=shapes(ly,top);rootchildren=children(top)",
     "result.update(phase='loaded original');save()\n    before={c.name:signature(ly,c) for c in ly.each_cell()};rootshapes=shapes(ly,top);rootchildren=children(top)\n    result.update(phase='original signatures complete');save()"),
    ('added=Counter();saved_instances=[];expanded=Counter();expectedchildren=rootchildren.copy()',
     "result.update(phase='templates validated',selected_arrays=len(selected));save()\n    survivors=[(i.cell_inst.dup(),i.properties()) for i in top.each_inst() if i.cell.name not in names]\n    added=Counter();saved_instances=[];expanded=Counter();expectedchildren=rootchildren.copy()"),
    ('for inst in selected:', 'for ordinal,inst in enumerate(selected):'),
    ('        inst.delete()',
     "        if ordinal%10000==0:\n            result.update(phase='expanding fill records',completed_arrays=ordinal+1);save()\n    # Rebuild only the root instance container in one operation. Every survivor\n    # keeps its exact CellInstArray and property dictionary; the complete\n    # signatures and saved inverse below remain the acceptance gates.\n    top.clear_insts()\n    for array,props in survivors:\n        inserted=top.insert(array)\n        if props:inserted.set_properties(props)\n    result.update(phase='batched root instance replacement complete');save()")]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(Path(__file__).resolve()),'__name__':'__main__'})
