#!/usr/bin/env python3
"""Read-only native analog identity and existing BGR-overlay preflight."""
import argparse
import json
import os
from pathlib import Path
import klayout.db as k
from replace_analog_pair_candidate import sha, structural_digest, effective_bgr
from replace_digital_macro_candidate import equal_macro


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['parent', 'sense', 'bgr', 'effective-bgr', 'output']:
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert k.__version__ == '0.30.9'
    expected = [(a.parent, '4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2'),
                (a.sense, '8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'),
                (a.bgr, '6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'),
                (a.effective_bgr, 'e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb')]
    assert all(sha(path) == digest for path, digest in expected)
    result = dict(status='running', inputs={str(path): digest for path,digest in expected}, roles=[])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        layout = k.Layout(); layout.read(str(a.parent)); top = layout.top_cell()
        result['top_cell'] = top.name
        for role, path, local, target in [('BGR', a.bgr, 'g1_bgr', 'g1_bgr_candidate'),
                                          ('SENSE', a.sense, 'g1_sense_physical', 'g1_sense_candidate')]:
            source = k.Layout(); source.read(str(path)); cell = source.cell(local)
            native = layout.cell(target); assert native is not None
            instance, = [i for i in top.each_inst() if i.cell_index == native.cell_index()]
            equal_macro(source, cell, layout, native)
            record = dict(role=role, cell=target, transform=str(instance.cplx_trans),
                          physical_geometry_and_texts='passed',
                          original_hierarchy_digest=structural_digest(cell),
                          embedded_hierarchy_digest=structural_digest(native),
                          parent_cells=native.parent_cells())
            result['roles'].append(record)
            assert record['original_hierarchy_digest'] == record['embedded_hierarchy_digest']
        result['effective_bgr'] = effective_bgr(layout, top, dict(path=str(a.effective_bgr), cell='g1_bgr'))
        assert all(sha(path) == digest for path,digest in expected)
        result.update(status='passed exact original analog hierarchy and effective BGR union',
                      not_run=['New analog-pair integration', 'Affected stock checks and electrical qualification'])
    except Exception as exc:
        result.update(status='failed original analog identity preflight', error=repr(exc))
        raise
    finally:
        a.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
