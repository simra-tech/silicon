#!/usr/bin/env python3
"""Prepare the exact three-record projection, then unchanged strict diagnostic."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    here=Path(__file__).resolve().parent
    projector=here/'prepare_current_dummy_reference.py'
    base=here/'run_saved_comparison.py'
    proof=Path(os.environ['G1_RESULTS_ROOT'])/'io-current-dummy-proof-20260923-r1/summary.json'
    a.output.mkdir(parents=True)
    projection=a.output/'projection'
    spec=importlib.util.spec_from_file_location('current_exact_projection',projector)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sys.argv=[str(projector),'--proof',str(proof),'--output',str(projection)]
    module.main()
    prepared=json.loads((projection/'summary.json').read_text())
    assert prepared['status'].startswith('passed exact reversible') and all(prepared['controls'].values())
    selected=projection/'physical_AP_three_dummy_comparison_only.cdl'
    assert hashlib.sha256(selected.read_bytes()).hexdigest()==prepared['output_sha256']
    old=base.read_text();code=old
    edits=[("source=bulk/'io-physical-ap-source-20260923-r2/physical_taps_reader.cdl'","source=PROJECTED_SOURCE"),
        ("sourcehash='d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4'","sourcehash=PROJECTED_SHA"),
        ('all three all-VDD source dummies retained','exact three independently proved all-VDD dummies projected out for comparison only; original source/native held'),
        ('report[:extraction_reference_excludes_exact_three_dummies] = false','report[:extraction_reference_excludes_exact_three_dummies] = true')]
    for before,after in edits:
        assert code.count(before)==1,(before,code.count(before));code=code.replace(before,after)
    manifest=dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
        projector_sha256=hashlib.sha256(projector.read_bytes()).hexdigest(),
        proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),edits=edits,
        projection=prepared,model_rules='unchanged',original_strict_failure='preserved')
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    sys.argv=[str(base),'--output',str(a.output/'comparison')]
    scope=dict(__file__=str(base),__name__='__main__',PROJECTED_SOURCE=selected,PROJECTED_SHA=prepared['output_sha256'])
    exec(compile(code,str(base),'exec'),scope)
    assert hashlib.sha256(base.read_bytes()).hexdigest()==manifest['base_sha256']
    assert hashlib.sha256(projector.read_bytes()).hexdigest()==manifest['projector_sha256']


if __name__=='__main__':main()
