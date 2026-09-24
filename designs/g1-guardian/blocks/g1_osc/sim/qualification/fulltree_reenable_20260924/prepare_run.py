#!/usr/bin/env python3
"""Reproduce a saved re-enable deck using the existing exact load inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'fulltree_r095_load_20260924'
spec = importlib.util.spec_from_file_location('osc_loaded_fixture', BASE / 'prepare_run.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def prepare(case, destination):
    prior = {'nominal': 'nominal_code8', 'slowhot': 'slowhot_code0'}[case]
    manifest = json.loads((HERE / (case + '_manifest.json')).read_text())
    data = (HERE / (case + '.cir')).read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest['input_bindings']['receiver.cir']
    result = base.prepare(prior, destination)
    for name, digest in result['inputs_sha256'].items():
        assert digest == manifest['source_input_bindings'][name]
    (destination / 'receiver.cir').write_bytes(data)
    result['inputs_sha256']['receiver.cir'] = hashlib.sha256(data).hexdigest()
    result['case'] = case
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=['nominal', 'slowhot'])
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.case, args.destination), indent=2))
