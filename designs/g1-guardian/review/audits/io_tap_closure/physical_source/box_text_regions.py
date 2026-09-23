#!/usr/bin/env python3
"""Literal text-origin boxes with independent flat API and negative controls."""
import pya

PATTERNS={'ptap1':'[sS][uU][bB]!','ntap1':'[wW][eE][lL][lL]'}


def prepare(layout,top):
    indices={kind:layout.layer(401+i,0) for i,kind in enumerate(PATTERNS)}
    assert all(cell.shapes(index).is_empty() for cell in layout.each_cell() for index in indices.values())
    originals={kind:pya.Region(top.begin_shapes_rec(layout.layer(63,0)),pattern,True,1)
               for kind,pattern in PATTERNS.items()}
    records=[]
    for cell in layout.each_cell():
        for shape in cell.shapes(layout.layer(63,0)).each():
            if not shape.is_text():
                continue
            text=shape.text
            kind={'sub!':'ptap1','well':'ntap1'}.get(text.string.lower())
            if kind is None:
                continue
            cell.shapes(indices[kind]).insert(pya.Box(text.x-1,text.y-1,text.x+1,text.y+1))
            records.append(dict(cell=cell.name,text=text.string,point=[text.x,text.y],kind=kind))
    for kind,index in indices.items():
        assert (pya.Region(top.begin_shapes_rec(index))^originals[kind]).is_empty()
    return indices,originals,records


def controls():
    layout=pya.Layout();layout.dbu=.001;top=layout.create_cell('CONTROL');child=layout.create_cell('CHILD')
    layer=layout.layer(63,0)
    top.shapes(layer).insert(pya.Text('sub!',pya.Trans(100,100)))
    child.shapes(layer).insert(pya.Text('SUB!',pya.Trans(200,200)))
    child.shapes(layer).insert(pya.Text('SUBSTRATE',pya.Trans(400,400)))
    top.insert(pya.CellInstArray(child.cell_index(),pya.Trans(1000,1000)))
    indices,originals,records=prepare(layout,top)
    dss=pya.DeepShapeStore();dss.threads=1
    actual=pya.Region(top.begin_shapes_rec(indices['ptap1']),dss)
    assert actual.area()==originals['ptap1'].area()==8 and len(records)==2
    assert (actual^originals['ptap1']).is_empty()
    moved=originals['ptap1'].moved(1,0)
    missing=originals['ptap1']-pya.Region(pya.Box(99,99,101,101))
    wrong_name=originals['ptap1']+pya.Region(pya.Box(1399,1399,1401,1401))
    assert not (actual^moved).is_empty()
    assert not (actual^missing).is_empty()
    assert not (actual^wrong_name).is_empty()
    return dict(positive_hierarchical_XOR='passed',shifted_point='rejected',missing_label='rejected',
        wrong_name='rejected',expected_area_dbu2=8)
