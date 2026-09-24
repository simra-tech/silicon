#!/usr/bin/env python3
"""Saved-input baseline and exact fill type preservation; old failures retained."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('control_cached_fill.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='7dbf3c4751548340b58fc9fd236b955ba7d2d9fdc64fc83b95726e9a3e0f2dce'
code=base.read_text()
edits=[
    ('from cached_fill import relocate','from cached_fill_r2 import relocate'),
    ("original=a.output/'original.gds';ly.write(str(original))", """original=a.output/'original.gds';ly.write(str(original))
    constructed_properties=properties(top)
    # The production operation starts from an existing GDS, not an unsaved
    # synthetic cell-property extension that the GDS writer cannot represent.
    ly=pya.Layout();ly.read(str(original));top=ly.cell('TOP')
    original_saved_properties=properties(top)
    assert constructed_properties==\"[(11, 'top-property')]\" and original_saved_properties=='[]'"""),
    ('fill.name',"'Met1_M_FILL_CELL'"),
    ('(shape.box if shape.is_box() else shape.polygon)',
     '(shape.box if shape.is_box() else (shape.simple_polygon if shape.is_simple_polygon() else shape.polygon))'),
    ("sources={p.name:sha(p) for p in (Path(__file__),HERE/'cached_fill.py')}",
     "sources={p.name:sha(p) for p in (SELF_PATH,HERE/'cached_fill.py',HERE/'cached_fill_r2.py',Path(__file__))}"),
    ("fullchip_prep='not run',native_LVS='not run',physical_change='not applicable')",
     "fullchip_prep='not run',native_LVS='not run',physical_change='not applicable',\n        saved_input_baseline=True,new_fill_shape_type_preserved=True,\n        synthetic_unsaved_cell_property_roundtrip='failed separately and preserved',\n        original_saved_properties=original_saved_properties,candidate_saved_properties=properties(saved.cell('TOP')))" )]
for old,new in edits:
    assert code.count(old)>0,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','SELF_PATH':Path(__file__).resolve()})
