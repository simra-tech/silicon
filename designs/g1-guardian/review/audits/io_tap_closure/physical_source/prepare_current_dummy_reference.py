#!/usr/bin/env python3
"""Exactly three already-purged dummies, comparison-only source projection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parents[1]/'fullchip_reference_closure/physical_lvs/explicit_vss_interface'
sys.path.insert(0,str(PRIOR))
from prepare_r5 import parse,flattened,TOP
from prepare_dummy_reference import allowed


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--proof',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    proof=json.loads(a.proof.read_text())
    assert proof['status']=='passed independent three-dummy source/native-terminal proof'
    assert '4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2' in proof['inputs'].values()
    assert '796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf' in proof['inputs'].values()
    assert len(proof['source_occurrences'])==len(proof['physical_instances'])==3
    assert 'target_netlist.purge_devices' in proof['unconditional_purge_rule']
    bulk=Path(os.environ['G1_RESULTS_ROOT']);source=bulk/'io-physical-ap-source-20260923-r2/physical_taps_reader.cdl'
    raw=source.read_bytes();assert sha(source)=='d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4'
    lines,cells=parse(raw);before,_=flattened(cells)
    cell=cells['G1_VSS_DERIVATIVE__SG13G2_LEVELDOWN']
    inst,=[i for i in cell['instances'] if i['name'].upper()=='MP0']
    assert inst['model'].upper()=='SG13_HV_PMOS' and [n.upper() for n in inst['nodes']]==['VDD']*4
    assert inst['params']==['m=1','w=4.65u','l=450.00n','ng=1']
    index,=inst['record']['indices'];line=lines[index].encode();offset=sum(len(s.encode()) for s in lines[:index])
    projected=raw[:offset]+raw[offset+len(line):]
    assert projected[:offset]+line+projected[offset:]==raw
    _,cc=parse(projected);after,_=flattened(cc)
    removed={p:before[p] for p in set(before)-set(after)}
    assert allowed(removed) and all(after[p]==before[p] for p in after)
    assert cells[TOP]['pins']==cc[TOP]['pins'] and len(cc[TOP]['pins'])==22
    wrong={p:dict(r,nodes=list(r['nodes'])) for p,r in removed.items()};first=sorted(wrong)[0];wrong[first]['nodes'][3]='IOVDD'
    missing=dict(removed);missing.pop(first);extra=dict(removed);extra['UNAUTHORIZED']=removed[first]
    controls=dict(positive=allowed(removed),wrong_body_rejected=not allowed(wrong),missing_rejected=not allowed(missing),extra_rejected=not allowed(extra))
    assert all(controls.values())
    a.output.mkdir(parents=True);dest=a.output/'physical_AP_three_dummy_comparison_only.cdl';dest.write_bytes(projected)
    (a.output/'summary.json').write_text(json.dumps(dict(
        status='passed exact reversible current three-dummy projection; comparison not run',
        input_sha256=sha(source),output_sha256=sha(dest),native_proof_sha256=sha(a.proof),
        removed_record=line.decode(),offset=offset,removed=removed,controls=controls,
        all_other_source_records_terminals_parameters_held=True,reverse_bytes_exact=True,
        original_electrical_source_and_native_devices='all retained',
        rule_model_parameter_changes='not applicable',strict_comparison='not run'),indent=2)+'\n')


if __name__=='__main__':main()
