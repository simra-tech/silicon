"""Current hard/R100 source; pending geometry hashes deliberately fail closed."""
import hashlib
import json
import os
from pathlib import Path
import re

QUALIFIED_PROJECTION='analog-pair-purefill-flat-20260923-r3/analysis.json'
QUALIFIED_PROJECTION_SHA='4bb4ce88aa3413dd311e0f33ddba6d6802975d8cd2744b2325a8f7f59e277626'
CONTROL='cached-fill-controls-20260923-r2/summary.json'
CONTROL_SHA='0fe02fbd5eb8c499ec493a5c7e099b207c0db05b0457d2df17f523049236e7e7'
GDS_RELATIVE='current-purefill-flat-20260923-r1/pure_fill_flattened.gds'
GDS_SHA='6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51'
PROOF_SHA='7131ac72e1c06e473e3da26ef3edf08c75d8c512eae1edb40b53008392cf0e2f'
CONTEXT_RELATIVE='current-purefill-context-20260923-r1/summary.json'
CONTEXT_SHA='1ceb352364c3c8176376b1b2ee66bc01647556a5167f7dff512c6c790c9c1c21'
ORIGINAL_GDS='trip-regenpair4-native-20260923-r1/candidate.gds'
ORIGINAL_SHA='1c9533180ec3d45265f3617298310a31aa01bb515fee6178a939ee6364502f22'
SOURCE_SHA='94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def bound(relative,digest):
    assert re.fullmatch('[0-9a-f]{64}',digest),relative
    p=Path(os.environ['G1_RESULTS_ROOT'])/relative;assert sha(p)==digest
    return p


def qualification():
    p=bound(QUALIFIED_PROJECTION,QUALIFIED_PROJECTION_SHA);j=json.loads(p.read_text())
    c=bound(CONTROL,CONTROL_SHA);cj=json.loads(c.read_text())
    assert j['status']=='passed exact pure-fill hierarchy projection; native LVS not run'
    assert cj['status'].startswith('passed detached/batched equivalence')
    assert cj['saved_input_baseline'] and cj['new_fill_shape_type_preserved']
    assert cj['all_native_geometry_text_properties_exact'] and cj['missing_shape_negative'] and cj['duplicate_native_instance_negative']
    assert j['all_fill_geometry_preserved'] and j['inverse_saved_projection_all_definitions_exact']
    assert all(r['xor_dbu2']==0 for r in j['full_affected_layer_XOR'])
    return p,j,c


def validate_inputs():
    qualification();gds=bound(GDS_RELATIVE,GDS_SHA);proof=bound(str(Path(GDS_RELATIVE).parent/'analysis.json'),PROOF_SHA)
    j=json.loads(proof.read_text());bulk=Path(os.environ['G1_RESULTS_ROOT'])
    assert j['status']=='passed exact pure-fill hierarchy projection; native LVS not run' and j['GDS_sha256']==GDS_SHA
    for k in ('all_other_cell_definitions_exact','all_root_functional_geometry_text_properties_held',
              'all_fill_geometry_preserved','inverse_saved_projection_all_definitions_exact','source_bytes_exact'):
        assert j[k] is True
    assert j['inputs'][str(bulk/ORIGINAL_GDS)]==ORIGINAL_SHA
    assert j['inputs'][str(bulk/'trip-hard-full-reference-20260923-r1/physical_taps_reader.cdl')]==SOURCE_SHA
    assert j['full_affected_layer_XOR'] and all(r['xor_dbu2']==0 for r in j['full_affected_layer_XOR'])
    assert all(sha(Path(p))==h for p,h in j['inputs'].items())
    return j
