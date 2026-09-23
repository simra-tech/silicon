"""Immutable generation bindings, separate from later output/context hashes."""
import hashlib
import json
import os
from pathlib import Path

ORIGINAL_GDS='trip-regenpair4-native-20260923-r1/candidate.gds'
ORIGINAL_SHA='1c9533180ec3d45265f3617298310a31aa01bb515fee6178a939ee6364502f22'
SOURCE_SHA='94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def qualification():
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    p=bulk/'analog-pair-purefill-flat-20260923-r3/analysis.json'
    c=bulk/'cached-fill-controls-20260923-r2/summary.json'
    assert sha(p)=='4bb4ce88aa3413dd311e0f33ddba6d6802975d8cd2744b2325a8f7f59e277626'
    assert sha(c)=='0fe02fbd5eb8c499ec493a5c7e099b207c0db05b0457d2df17f523049236e7e7'
    j=json.loads(p.read_text());cj=json.loads(c.read_text())
    assert j['status']=='passed exact pure-fill hierarchy projection; native LVS not run'
    assert cj['status'].startswith('passed detached/batched equivalence')
    assert cj['saved_input_baseline'] and cj['new_fill_shape_type_preserved']
    assert cj['all_native_geometry_text_properties_exact'] and cj['missing_shape_negative'] and cj['duplicate_native_instance_negative']
    assert j['all_fill_geometry_preserved'] and j['inverse_saved_projection_all_definitions_exact']
    assert j['all_other_cell_definitions_exact'] and j['all_root_functional_geometry_text_properties_held']
    assert j['full_affected_layer_XOR'] and all(r['xor_dbu2']==0 for r in j['full_affected_layer_XOR'])
    return p,j,c
