#!/usr/bin/env python3
"""Source-only rejection tests; creates no circuit file and runs no analog."""
import argparse,copy,json
from pathlib import Path
from prepare_comp45_partial_c import prepare

def tests(raw,view,rows):
    text,report=prepare(raw,view,rows)
    from run_comp45_partial_c_ac import probe
    derived=probe(text)
    assert derived.count('Vmain_probe main_loop_e vn dc 0 ac {pv}')==1
    assert derived.count('Imain_probe vss main_loop_e dc 0 ac {pi}')==1
    assert report['added_count']==844 and report['excluded_count']==134 and report['exact_inverse']
    bads=[]
    changed=copy.deepcopy(rows);changed[0]['net1']='UNMAPPED_NET';bads.append(changed)
    changed=copy.deepcopy(rows);changed[0]['capacitance_fF']=-1.;changed[0]['capacitance_fF_hex']=float(-1).hex();bads.append(changed)
    changed=copy.deepcopy(rows);changed[0]['capacitance_fF_hex']=float(12345).hex();bads.append(changed)
    changed=copy.deepcopy(rows);changed.append(changed[0]);bads.append(changed)
    for bad in bads:
        try:prepare(raw,view,bad)
        except AssertionError:continue
        raise AssertionError('invalid annotation accepted')
    return dict(exact_full_pair_accounting=True,unmapped_node_rejected=True,negative_C_rejected=True,
                hexadecimal_mismatch_rejected=True,duplicate_pair_rejected=True,analog='not run')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['source','view','caps']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(tests(a.source.read_bytes(),json.loads(a.view.read_text()),json.loads(a.caps.read_text())))
