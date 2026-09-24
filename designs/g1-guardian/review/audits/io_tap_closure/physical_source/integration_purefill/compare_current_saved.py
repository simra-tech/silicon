#!/usr/bin/env python3
"""Current saved graph, exact physical pins, and proven comparison-only source."""
import hashlib
import json
import os
from pathlib import Path
import sys

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'run_saved_comparison.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='d45923cc954c5b73e6cf3b6e4247c72f595613d861acf3c7898ff4a0980ee900'
bulk=Path(os.environ['G1_RESULTS_ROOT'])
proof=bulk/'current-purefill-dummy-proof-20260923-r1/summary.json'
projection=bulk/'current-purefill-dummy-projection-20260923-r1/summary.json'
pj=json.loads(proof.read_text());sj=json.loads(projection.read_text())
assert pj['status']=='passed independent three-dummy source/native-terminal proof'
assert '6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51' in pj['inputs'].values()
assert 'be00e66f12309bb26f16165860271936ee3f8eb74bc84c3fa56e1ee3295ccd90' in pj['inputs'].values()
assert len(pj['source_occurrences'])==len(pj['physical_instances'])==3
assert sj['status']=='passed exact reversible current three-dummy projection; comparison not run'
assert sj['native_proof_sha256']==hashlib.sha256(proof.read_bytes()).hexdigest()
assert sj['input_sha256']=='94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b'
assert sj['reverse_bytes_exact'] and sj['all_other_source_records_terminals_parameters_held'] and all(sj['controls'].values())
source=projection.parent/'physical_AP_three_dummy_comparison_only.cdl'
sourcehash=hashlib.sha256(source.read_bytes()).hexdigest()
assert sourcehash==sj['output_sha256']=='9f38371f303672a7169733493c9d444cacbda2d5889e0f79659b5e1224490369'
output=Path(sys.argv[sys.argv.index('--output')+1])
code=base.read_text()
edits=[
 ('io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb','current-purefill-native-lvs-20260923-r1/reports/pure_fill_flattened.lvsdb'),
 ('1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f','7efa28056f533df4fec8b585654e5445e8d932d4a775747ee5813ae65660cf85'),
 ('io-current-diagnostics-20260923-r1','current-purefill-saved-diagnostics-20260923-r1'),
 ("source=bulk/'io-physical-ap-source-20260923-r2/physical_taps_reader.cdl'","source=PROJECTED_SOURCE"),
 ("sourcehash='d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4'","sourcehash=PROJECTED_SHA"),
 ('all three all-VDD source dummies retained','exact three independently proved all-VDD source dummies projected for comparison only; canonical source/native retained'),
 ('report[:extraction_reference_excludes_exact_three_dummies] = false','report[:extraction_reference_excludes_exact_three_dummies] = true')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__',
                                    'PROJECTED_SOURCE':source,'PROJECTED_SHA':sourcehash})
(output/'current_binding.json').write_text(json.dumps(dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
    wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),
    effective_source_sha256=hashlib.sha256(code.encode()).hexdigest(),
    native_proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
    projection_sha256=hashlib.sha256(projection.read_bytes()).hexdigest(),edits=edits),indent=2)+'\n')
