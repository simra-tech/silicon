#!/usr/bin/env python3
"""Exact private-node projection for the R100 candidate, no added capacitors."""
import copy
from expose_comp45_internal_nodes import expose as parent_expose,parse,flatten,sha
from prepare_comp45_rz_remedy import change,OLD
SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
def expose(raw):
    assert sha(raw)==SOURCE
    original=raw.decode();new=OLD.replace('l=62u','l=100u');assert original.count(new)==1
    parent=original.replace(new,OLD);text,proof=parent_expose(parent.encode());text=change(text,100)
    aliases={v:k for k,v in proof['node_mapping'].items() if v!=k}
    expected=flatten(parse(original));actual=flatten(parse(text),aliases);assert expected==actual
    restored=text
    for edit in reversed(proof['edits']):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'])
    assert restored==original
    proof.update(original_sha256=SOURCE,diagnostic_sha256=sha(text.encode()),primitive_inventory=expected,projected_inventory=actual,
        zero_C_electrical='not run for this candidate',exact_inverse=True)
    return text,proof
def topology_tests(raw):
    text,proof=expose(raw);expected=flatten(parse(raw.decode()));aliases={v:k for k,v in proof['node_mapping'].items() if v!=k}
    mutants=[]
    wrong=copy.deepcopy(parse(text));wrong['g1_ota_main_candidate']['devices'][0]['nodes'][3]='vdd';mutants.append(wrong)
    wrong=copy.deepcopy(parse(text));wrong['g1_ota_main_candidate']['devices'][-1]['params'][0]='w=46u';mutants.append(wrong)
    wrong=copy.deepcopy(parse(text));wrong['g1_sense']['devices'][-3]['nodes'][-1]='__pex_xbuf_vbpc';mutants.append(wrong)
    wrong=copy.deepcopy(parse(text));wrong['g1_ota_main_candidate']['devices'].pop();mutants.append(wrong)
    for wrong in mutants:
        try:assert flatten(wrong,aliases)==expected
        except AssertionError:continue
        raise AssertionError('non-equivalent R100 private view accepted')
    return dict(positive_topology=True,wrong_body_rejected=True,changed_parameter_rejected=True,cross_instance_short_rejected=True,missing_primitive_rejected=True)
