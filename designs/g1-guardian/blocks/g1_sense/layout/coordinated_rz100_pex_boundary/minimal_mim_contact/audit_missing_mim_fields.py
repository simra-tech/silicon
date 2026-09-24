#!/usr/bin/env python3
"""Inventory pinned native CMIM fields required by KPEX/2.5D without filling them."""
import argparse
import hashlib
import json
from pathlib import Path

TECH_SHA = '6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92'
MODEL_SHA = '94b569e695fd8a223a5a49a5b5a6b0d8a62408820bf0c2ed9dbcb0a8ab7d957e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(tech):
    computed = {r['layer_info']['name']: r for r in tech['lvs_computed_layers']}
    stack = {r['name']: r for r in tech['process_stack']['layers']}
    para = tech['process_parasitics']
    resist = {r['layer_name']: r for r in para['resistance']['layers']}
    caps = para['capacitance']
    required = ['metal5_cap', 'cmim_top']
    assert all(name in computed and name in stack for name in required)
    assert 'mim_via' in computed
    assert all(computed[name]['layer_info']['purpose'] == 'PURPOSE_MIM_CAP'
               for name in required)
    assert stack['metal5_cap']['metal_layer']['z'] == 4.96
    assert stack['cmim_top']['metal_layer']['z'] == 5.49
    assert 'Metal5' in resist and resist['Metal5']['resistance'] == 88
    missing = {}
    for name in required:
        missing[name] = dict(sheet_resistance=name not in resist,
            substrate_capacitance=not any(r['layer_name'] == name for r in caps['substrates']),
            overlap_top=not any(r['top_layer_name'] == name for r in caps['overlaps']),
            overlap_bottom=not any(r['bottom_layer_name'] == name for r in caps['overlaps']),
            sidewall=not any(r['layer_name'] == name for r in caps['sidewalls']),
            sideoverlap=not any(name in (r['in_layer_name'], r['out_layer_name'])
                                for r in caps['sideoverlaps']))
    assert all(all(fields.values()) for fields in missing.values())
    return dict(status='pinned fields absent; no local numerical adapter justified',
                computed_CMIM_layers=required, stack_geometry_present=True,
                canonical_Metal5_sheet_resistance_milliohm_per_square=88,
                missing_direct_parameters=missing,
                model_plane='intrinsic cap_cmim and extrinsic plate ownership not resolved',
                project_local_adapter='not made', numerical_R_RC='not run')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--technology', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    assert sha(a.technology) == TECH_SHA and sha(a.model) == MODEL_SHA
    model = a.model.read_text()
    assert 'top/bottom plate parasitic capacitance is included by parasiticC extraction' in model
    result = audit(json.loads(a.technology.read_text()))
    result.update(technology_sha256=TECH_SHA, model_sha256=MODEL_SHA)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
