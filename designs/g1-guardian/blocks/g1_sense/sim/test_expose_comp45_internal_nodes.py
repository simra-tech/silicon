#!/usr/bin/env python3
"""Topology rejection controls for private instrumentation, no simulation."""
import argparse,copy
from pathlib import Path
from expose_comp45_internal_nodes import expose,parse,flatten

def tests(raw):
    text,report=expose(raw);expected=flatten(parse(raw.decode()))
    aliases={v:k for k,v in report['node_mapping'].items() if v!=k}
    assert flatten(parse(text),aliases)==expected
    bads=[]
    wrong=copy.deepcopy(parse(text));wrong['g1_ota_main_candidate']['devices'][0]['nodes'][3]='vdd';bads.append(wrong)
    wrong=copy.deepcopy(parse(text));wrong['g1_ota_main_candidate']['devices'][-1]['params'][0]='w=46u';bads.append(wrong)
    wrong=copy.deepcopy(parse(text));wrong['g1_sense']['devices'][-3]['nodes'][-1]='__pex_xbuf_vbpc';bads.append(wrong)
    wrong=copy.deepcopy(parse(text));wrong['g1_ota_main_candidate']['devices'].pop();bads.append(wrong)
    for wrong in bads:
        try:assert flatten(wrong,aliases)==expected
        except AssertionError:continue
        raise AssertionError('non-equivalent private view accepted')
    return dict(positive_topology=True,wrong_body_rejected=True,changed_model_parameter_rejected=True,
                cross_instance_private_short_rejected=True,missing_primitive_rejected=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    print(tests(a.source.read_bytes()))
