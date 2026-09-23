#!/usr/bin/env python3
"""Unchanged stock LVS of the exact isolated overlay representation control."""
import hashlib
from pathlib import Path

successor=Path(__file__).resolve()
base=successor.with_name('run_native_lvs.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='b0f1f211c7c12717f64f08c20f1541d00d44a3806be9b6c5d499c71dbd7ab70c'
code=base.read_text()
edits=[
 ('wrapper=Path(__file__).resolve()','wrapper=SUCCESSOR_WRAPPER'),
 ('analog-pair-integration-20260923-r1/analog_pair_native.gds','analog-pair-overlay-flat-20260923-r1/overlay_flattened.gds'),
 ('be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307','dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333'),
 ('80575bbd6a51044a287bb091c6888a02acdb4fb096d95dc201278dcc7e74fab3','1ee297f84ea49fa24960205f23be75a893fcdb2843778c21756237af57c11bda'),
 ("assert pj['status'].startswith('passed') and pj['GDS_sha256']==sha(layout)","""assert pj['status'].startswith('passed') and pj['GDS_sha256']=='be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'
        assert cj['original_GDS_sha256']=='9f7bb2edd378cb008f2431887fbd982e1e0342ddb7bf51b841dd76bd24cfce4a'
        assert cj['object_count']==33 and cj['via_cut_count']==26 and cj['metal_landing_count']==7
        assert cj['all_other_cell_definitions_exact'] and cj['all_root_text_and_nonoverlay_objects_exact']
        assert cj['inverse_saved_projection_all_definitions_exact'] and cj['source_bytes_exact']
        assert cj['inputs'][str(source)]==sha(source)
        assert len(cj['full_affected_layer_XOR'])==7 and all(r['xor_dbu2']==0 for r in cj['full_affected_layer_XOR'])"""),
 ('analog-pair-context-20260923-r1/summary.json','analog-pair-flat-context-20260923-r1/summary.json'),
 ('0d1ab6ca320eea357b027c11219c7e98f50cb9f674d0d8cf21e150f2e0fccd44','88e134ab3f6c43fecf1be4144f6449113bb9c432574d8f108466ebd3ea57a6b8')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','SUCCESSOR_WRAPPER':successor})
