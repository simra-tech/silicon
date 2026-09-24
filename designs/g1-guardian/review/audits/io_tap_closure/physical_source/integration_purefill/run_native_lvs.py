#!/usr/bin/env python3
"""Single 600-second unchanged-stock pure-fill representation control."""
import hashlib
from pathlib import Path
import re
from bindings import GDS_RELATIVE,GDS_SHA,PROOF_SHA,CONTEXT_RELATIVE,CONTEXT_SHA,validate_inputs

validate_inputs();assert re.fullmatch('[0-9a-f]{64}',CONTEXT_SHA)
successor=Path(__file__).resolve()
base=successor.parent.parent/'integration_be54/run_native_lvs.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='b0f1f211c7c12717f64f08c20f1541d00d44a3806be9b6c5d499c71dbd7ab70c'
code=base.read_text()
edits=[
    ('wrapper=Path(__file__).resolve()','wrapper=SUCCESSOR_WRAPPER'),
    ('analog-pair-integration-20260923-r1/analog_pair_native.gds',GDS_RELATIVE),
    ('be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307',GDS_SHA),
    ('80575bbd6a51044a287bb091c6888a02acdb4fb096d95dc201278dcc7e74fab3',PROOF_SHA),
    ("assert pj['status'].startswith('passed') and pj['GDS_sha256']==sha(layout)",
     """assert pj['status'].startswith('passed') and pj['GDS_sha256']=='be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'
        assert cj['status']=='passed exact pure-fill hierarchy projection; native LVS not run'
        assert cj['all_fill_geometry_preserved'] and cj['all_other_cell_definitions_exact']
        assert cj['all_root_functional_geometry_text_properties_held'] and cj['inverse_saved_projection_all_definitions_exact']
        assert cj['source_bytes_exact'] and cj['inputs'][str(source)]==sha(source)
        assert cj['full_affected_layer_XOR'] and all(r['xor_dbu2']==0 for r in cj['full_affected_layer_XOR'])
        bindings_file=WRAPPER.with_name('bindings.py')
        expected[bindings_file]=sha(bindings_file)"""),
    ('analog-pair-context-20260923-r1/summary.json',CONTEXT_RELATIVE),
    ('0d1ab6ca320eea357b027c11219c7e98f50cb9f674d0d8cf21e150f2e0fccd44',CONTEXT_SHA),
    ('for old,new in rebindings:',
     "rebindings.extend([('watchdog_seconds=900','watchdog_seconds=600'), (\"a.output/'run.json',900\",\"a.output/'run.json',600\")])\nfor old,new in rebindings:")]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','SUCCESSOR_WRAPPER':successor})
