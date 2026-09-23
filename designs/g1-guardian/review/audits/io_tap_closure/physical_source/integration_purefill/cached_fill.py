"""Detached fill records and bounded native layout-update transaction."""
from collections import Counter


def prop(obj):return repr(sorted(obj.properties().items(),key=lambda pair:repr(pair[0])))


def relocate(layout,top,names,progress=lambda **kwargs:None):
    templates={};selected=[];survivors=[];expectedchildren=Counter()
    # Nothing is modified until every child, array and shape has been detached.
    for inst in top.each_inst():
        name=inst.cell.name;array=inst.cell_inst.dup();props=inst.properties()
        key=(name,str(inst.cplx_trans),str(inst.a),str(inst.b),inst.na,inst.nb,prop(inst))
        if name not in names:
            survivors.append((array,props));expectedchildren[key]+=1;continue
        assert not props
        if name not in templates:
            child=inst.cell;assert not child.properties() and not list(child.each_inst())
            template=[]
            for li in layout.layer_indexes():
                info=layout.get_info(li);pair=(info.layer,info.datatype)
                for s in child.shapes(li).each():
                    assert not s.properties() and (s.is_box() or s.is_polygon())
                    assert pair[1]==22 and pair[0] in (1,5,8,10,30,50,67,126,134)
                    template.append((li,pair,s.box.dup() if s.is_box() else s.polygon.dup()))
            assert template;templates[name]=template
        selected.append((name,array))
    assert selected and set(templates)==set(names)
    target={li:top.shapes(li) for t in templates.values() for li,_,_ in t}
    added=Counter();expanded=Counter()
    progress(phase='all fill templates and arrays detached',selected_arrays=len(selected))
    layout.update();layout.start_changes()
    try:
        for ordinal,(name,array) in enumerate(selected):
            for trans in array.each_cplx_trans():
                assert trans.mag==1 and trans.angle in (0,90,180,270)
                expanded[name]+=1
                for li,pair,obj in templates[name]:
                    shape=target[li].insert(obj.transformed(trans))
                    added[(pair[0],pair[1],shape.to_s(),prop(shape))]+=1
            if ordinal%10000==0:progress(phase='cached transaction expansion',completed_arrays=ordinal+1)
        top.clear_insts()
        for array,props in survivors:
            inst=top.insert(array)
            if props:inst.set_properties(props)
    finally:
        layout.end_changes()
    progress(phase='cached transaction ended',completed_arrays=len(selected))
    return added,selected,expanded,expectedchildren
