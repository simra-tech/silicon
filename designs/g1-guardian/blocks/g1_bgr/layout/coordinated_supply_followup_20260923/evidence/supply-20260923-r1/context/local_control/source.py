#!/usr/bin/env python3
"""Saved local hierarchy versus exact-flat source-probe identity control."""
import argparse
import json
import os
from pathlib import Path
import time
import pya
from check_full_context_flat import graph,flatten_conductors,PAIRS,sha,dump

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT']);path=bulk/'bgr-supply-candidate-20260923-r1/bank.gds'
    routes=bulk/'bgr-assembly-20260922-r5/routing.json'
    assert sha(path)=='e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
    ly=pya.Layout();ly.read(str(path));top=ly.top_cell();hg,hs=graph(ly,top)
    flat,ft,counts=flatten_conductors(ly,top);fg,fs=graph(flat,ft)
    result={}
    for name,ng,ns in [('hierarchical',hg,hs),('exact_flat',fg,fs)]:
        groups={};witness=[]
        for row in json.loads(routes.read_text())['source_probes']:
            pair=(PAIRS[row['layer']][0],0);n=ng.probe_net(ns[pair],pya.Point(*row['point']));assert n
            key=(n.circuit().name,n.cluster_id)
            groups.setdefault(row['net'],set()).add(key)
            if len(groups[row['net']])>1:witness.append(dict(source_probe=row,returned_circuit=key[0],cluster=key[1]))
        result[name]=dict(source_nets=len(groups),one_identity_per_net=all(len(v)==1 for v in groups.values()),
                          distinct_identities=len(set().union(*groups.values())),
                          identities={k:sorted(v) for k,v in groups.items()},counterexamples=witness[:20])
    assert result['exact_flat']['source_nets']==result['exact_flat']['distinct_identities']==55 and result['exact_flat']['one_identity_per_net']
    raw_ids={cluster for values in result['hierarchical']['identities'].values() for circuit,cluster in values}
    result['hierarchical']['distinct_raw_cluster_ids']=len(raw_ids)
    result['hierarchical']['raw_cluster_id_scope_collision_reproduced']=len(raw_ids)<55
    assert result['hierarchical']['one_identity_per_net'] and result['hierarchical']['distinct_identities']==55
    assert len(raw_ids)<55
    result['original_criterion_failure']='Cluster IDs are circuit-local; raw integers alone are not global net identities.'
    result.update(status='passed reproduction and exact-flat recovery control',GDS_sha256=sha(path),source_probes_sha256=sha(routes),
                  exact_flat_XOR=True,geometry_change='not run',wall_s=time.monotonic()-start)
    dump(a.output/'analysis.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
