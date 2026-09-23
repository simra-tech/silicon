#!/usr/bin/env python3
"""Validation-only four-output adapter; actual original return deck is untouched."""
import argparse
import json
from pathlib import Path
import run_joint586_fast_nodeset_rescue as base
from run_nominal_clock_probe import validate_saved_nodes as original_validator


def validate_each_phase(deck,trip):
    lines=deck.splitlines(True)
    outputs=[i for i,line in enumerate(lines) if line.startswith('wrdata ')]
    assert len(outputs)==4,'This adapter is only for original four-phase return'
    for selected in outputs:
        view=''.join(line if i not in outputs or i==selected else '* validation-only other phase output\n'
            for i,line in enumerate(lines))
        original_validator(view,trip)
    return dict(status='passed all4 source hierarchy/output phases; original simulation deck unchanged')


if __name__=='__main__':
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--contract-sha256',required=True);p.add_argument('--kind',required=True);p.add_argument('--label',required=True)
    a,_=p.parse_known_args();assert a.kind=='own' and a.label=='return'
    assert base.sha(a.contract)==a.contract_sha256
    packet=json.loads(a.contract.read_text());case,=[c for c in packet['cases'] if c['kind']==a.kind and c['label']==a.label]
    assert case['validation_adapter_sha256']==base.sha(Path(__file__))
    assert all(base.sha(base.ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    out=base.SIM/'qualification'/case['run']
    assert not (out/'run.log').exists() and not (out/'validation_adapter.py').exists()
    (out/'validation_adapter.py').write_text(Path(__file__).read_text())
    base.validate_saved_nodes=validate_each_phase
    base.main()
