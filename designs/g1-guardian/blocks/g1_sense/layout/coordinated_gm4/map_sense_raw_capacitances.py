#!/usr/bin/env python3
"""Map raw incomplete CC data to all134source nets; never generate a circuit."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('recovery','coverage','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    recovery=json.loads((args.recovery/'summary.json').read_text())
    coverage=json.loads(args.coverage.read_text())
    assert recovery['status']=='passed full-precision raw data recovery; completeness not qualified'
    assert recovery['all_inputs_tools_cards_unchanged'] and recovery['capacitor_count']==958
    assert coverage['source_net_mapping_status']=='passed' and coverage['source_net_count']==134
    caps_path=args.recovery/'exact_capacitances.json'
    assert sha(caps_path)==recovery['exact_capacitances_sha256']
    mapping={row['extracted_nets'][0]:row['source_net'] for row in coverage['mapping']}
    assert len(mapping)==len(set(mapping.values()))==134 and set(mapping.values())==set(coverage['source_nets'])
    caps=json.loads(caps_path.read_text());raw_nodes={row[key] for row in caps for key in ('net1','net2')}
    assert raw_nodes-set(mapping)=={'VSUBS'}
    # VSUBS remains an explicitly identified extractor substrate conductor.
    # It is not silently bound to source vss or simulation ground.
    mapping['VSUBS']='EXTRACTOR_SUBSTRATE_UNBOUND'
    rows=[];matrix={}
    for index,row in enumerate(caps):
        assert float.fromhex(row['capacitance_fF_hex'])==row['capacitance_fF']
        value=row['capacitance_F'];a=mapping[row['net1']];b=mapping[row['net2']]
        assert math.isfinite(value) and value>=0 and a!=b
        rows.append(dict(index=index,raw_nets=[row['net1'],row['net2']],source_nodes=[a,b],
                         capacitance_F=value,capacitance_fF_hex=row['capacitance_fF_hex']))
        for x,y,sign in ((a,a,1),(b,b,1),(a,b,-1),(b,a,-1)):
            matrix[(x,y)]=matrix.get((x,y),0)+sign*value
    nodes=sorted(set(mapping[node] for node in raw_nodes))
    residual=max(abs(math.fsum(matrix.get((a,b),0) for b in nodes)) for a in nodes)
    assert math.isfinite(residual) and residual<=1e-25
    assert all(matrix.get((a,b),0)==matrix.get((b,a),0) for a in nodes for b in nodes)
    result=dict(status='passed134source-net attribution of INCOMPLETE raw CC data',
                recovery_summary_sha256=sha(args.recovery/'summary.json'),coverage_sha256=sha(args.coverage),
                raw_capacitances_sha256=sha(caps_path),script_sha256=sha(Path(__file__)),
                source_sha256=recovery['source_sha256'],source_net_count=134,raw_capacitor_count=len(rows),
                raw_conductor_count=len(raw_nodes),mapping=mapping,capacitors=rows,
                finite_symmetric_charge_matrix='passed',max_charge_row_residual_F=residual,
                substrate_binding='not run; extractor substrate remains explicitly unbound',
                completeness='failed blackbox MIM plate/tap-contact omissions; no completeness waiver',
                intrinsic_model_applicability='not qualified',electrical_netlist_generated=False,
                zero_parasitic_source_equivalence='not run',electrical_adoption='not run')
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('mapping','capacitors')},indent=2))


if __name__=='__main__':main()
