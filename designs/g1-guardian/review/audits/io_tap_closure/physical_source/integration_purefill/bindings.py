"""Prospective pure-fill control bindings; unqualified placeholders fail closed."""
import hashlib
import json
import os
from pathlib import Path
import re

GDS_RELATIVE='analog-pair-purefill-flat-20260923-r2/pure_fill_flattened.gds'
GDS_SHA='NOT_PREPARED'
PROOF_SHA='NOT_PREPARED'
CONTEXT_RELATIVE='analog-pair-purefill-context-20260923-r1/summary.json'
CONTEXT_SHA='NOT_PREPARED'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def validate_inputs():
    assert re.fullmatch('[0-9a-f]{64}',GDS_SHA) and re.fullmatch('[0-9a-f]{64}',PROOF_SHA)
    bulk=Path(os.environ['G1_RESULTS_ROOT']);gds=bulk/GDS_RELATIVE;proof=gds.parent/'analysis.json'
    assert sha(gds)==GDS_SHA and sha(proof)==PROOF_SHA
    j=json.loads(proof.read_text())
    assert j['status']=='passed exact pure-fill hierarchy projection; native LVS not run'
    assert j['GDS_sha256']==GDS_SHA
    for key in ('all_other_cell_definitions_exact','all_root_functional_geometry_text_properties_held',
                'all_fill_geometry_preserved','inverse_saved_projection_all_definitions_exact','source_bytes_exact'):
        assert j[key] is True,key
    assert j['instance_arrays']>0 and j['added_shape_count']>0 and j['expanded_occurrences']
    assert j['full_affected_layer_XOR'] and all(r['xor_dbu2']==0 for r in j['full_affected_layer_XOR'])
    assert j['inputs'][str(bulk/'analog-pair-overlay-flat-20260923-r1/overlay_flattened.gds')]=='dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333'
    assert j['inputs'][str(bulk/'analog-pair-reference-20260923-r1/physical_taps_reader.cdl')]=='35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51'
    assert all(sha(Path(p))==h for p,h in j['inputs'].items())
    return j
