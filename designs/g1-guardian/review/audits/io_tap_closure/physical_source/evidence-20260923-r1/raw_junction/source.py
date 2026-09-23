#!/usr/bin/env python3
"""Diagnose local TIE/body junction ownership from pinned raw-mask semantics."""
import hashlib
from pathlib import Path

previous=Path(__file__).resolve().with_name('derive_deep_taps_r5.py')
assert hashlib.sha256(previous.read_bytes()).hexdigest()=='7fe970585b5a91bdcb890a385836ef19baf30685f78acd5eabae03a9329c33d4'
text=previous.read_text();suffix="exec(compile(code,str(namespace['scope']['original']),'exec'),globals())"
assert text.count(suffix)==1
state={'__file__':str(Path(__file__).resolve()),'__name__':'prepare_raw_junction_control'}
exec(compile(text.replace(suffix,''),str(previous),'exec'),state)
code=state['code']
needle='        out=pya.Layout();out.dbu=ly.dbu;ot=out.create_cell(top.name)'
assert code.count(needle)==1
code=code.replace(needle,"""        derived['ptap1_body']=regs['substrate_drw'] & markers['ptap1'].covering(derived['ptap1'])
        derived['ntap1_body']=nw & markers['ntap1'].covering(derived['ntap1'])
"""+needle)
code=code.replace('        outputs={}\n','        outputs={};material_indices={}\n')
needle='            layer=out.layer(301+n,0);reg.insert_into(out,ot.cell_index(),layer)'
assert code.count(needle)==1
code=code.replace(needle,needle+'\n            material_indices[kind]=layer')
code=code.replace('for p in pya.Region(c.shapes(layer)).each()', 'for p in pya.Region(c.shapes(layer)).merged().each()')
needle="        out.write(str(a.output/'derived_tap_masks.gds'))"
assert code.count(needle)==1
code=code.replace(needle,"""        result['local_junctions']=[]
        for cell in out.each_cell():
            tie=pya.Region(cell.shapes(material_indices['ptap1'])).merged()
            if tie.is_empty():continue
            body=pya.Region(cell.shapes(material_indices['ptap1_body'])).merged()
            junction=(tie&body).merged();outside=(tie-body).merged()
            result['local_junctions'].append(dict(cell=cell.name,tie_area_dbu2=tie.area(),
                local_body_area_dbu2=body.area(),junction_area_dbu2=junction.area(),
                tie_outside_local_body_area_dbu2=outside.area(),
                junction_polygons=[measure(p) for p in junction.each()],
                outside_polygons=[measure(p) for p in outside.each()]))
        result['local_junction_interpretation']='diagnostic only; stock extraction and source occurrence ownership not run'
"""+needle)
state['__name__']='__main__'
exec(compile(code,str(state['namespace']['scope']['original']),'exec'),state)
