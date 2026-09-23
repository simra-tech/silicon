#!/usr/bin/env python3
"""Full native context control of the independently derived IO junctions."""
import hashlib
from pathlib import Path

previous=Path(__file__).resolve().with_name('derive_deep_junctions.py')
assert hashlib.sha256(previous.read_bytes()).hexdigest()=='49da5eda44514cc8820bd359a38997fdc7ff92519f0ad09bd684b2d71bf53adf'
text=previous.read_text()
suffix="exec(compile(code,str(state['namespace']['scope']['original']),'exec'),state)"
assert text.count(suffix)==1
scope={'__file__':str(Path(__file__).resolve()),'__name__':'prepare_full_context_control'}
exec(compile(text.replace(suffix,''),str(previous),'exec'),scope)
code=scope['code']
code=code.replace("bulk/'digital-reroute-streamout-20260923-r1/signal_routed_native.gds'",
                  "bulk/'gshared-fill-20260923-r4/route_fill_pruned.gds'")
code=code.replace('9a52cc71122df8fcc56bbd3ec3e0842958e1f7eec0f73c64ed21a8e2c7ea1805',
                  '4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2')
needle="    assert j['inputs'][str(current)]==sha(current)"
assert code.count(needle)==1
code=code.replace(needle,"""    baseline=bulk/'io-deep-junction-20260923-r1/summary.json'
    baseline_data=json.loads(baseline.read_text())
    assert baseline_data['status'].startswith('passed')""")
needle='            else:\n                inst.delete()'
assert code.count(needle)==1
code=code.replace(needle,'            # All other native instances deliberately retained.')
needle="        result['local_junction_interpretation']='diagnostic only; stock extraction and source occurrence ownership not run'"
assert code.count(needle)==1
code=code.replace(needle,needle+"""
        expected={r['cell']:r for r in baseline_data['local_junctions']}
        actual={r['cell']:r for r in result['local_junctions']}
        checks={name:actual.get(name)==row for name,row in expected.items()}
        result['full_context_IO_junction_parity']=checks
        result['baseline_raw_junction_sha256']=sha(baseline)
        result['all_native_instances_preserved']=True
        result['additional_nonIO_junction_cells']=sorted(set(actual)-set(expected))
        assert checks and all(checks.values()),checks
""")
code=code.replace("'not run; scoped140 IO instances plus all exact original top-level raw mask context'",
                  "'passed full native instance context; exact local IO junction parity'")
code=code.replace('passed scoped140-IO raw hierarchical Boolean derivation; source ownership pending',
                  'passed full native context and scoped IO junction exact parity')
scope['state']['__name__']='__main__'
exec(compile(code,str(scope['state']['namespace']['scope']['original']),'exec'),scope['state'])
