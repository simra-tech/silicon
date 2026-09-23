#!/usr/bin/env python3
"""Separate unprojected and exact-three-dummy strict saved-data comparison arms."""
import hashlib
import json
import os
from pathlib import Path
import sys

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'run_saved_comparison.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='d45923cc954c5b73e6cf3b6e4247c72f595613d861acf3c7898ff4a0980ee900'
index=sys.argv.index('--database-sha256');dbhash=sys.argv[index+1]
assert len(dbhash)==64 and all(c in '0123456789abcdef' for c in dbhash)
del sys.argv[index:index+2]
project='--project-three' in sys.argv
if project:sys.argv.remove('--project-three')
output=Path(sys.argv[sys.argv.index('--output')+1])
original_args=list(sys.argv)
assert not output.exists()
code=base.read_text()
edits=[
 ('io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb','analog-pair-native-lvs-20260923-r1/reports/analog_pair_native.lvsdb'),
 ('1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f',dbhash),
 ('io-current-diagnostics-20260923-r1','analog-pair-diagnostics-20260923-r1'),
 ('io-physical-ap-source-20260923-r2','analog-pair-reference-20260923-r1'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51'),
 ('Current digital + authorized explicit VSS','Current digital + two-passive SENSE + authorized explicit VSS')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
scope={'__file__':str(base),'__name__':'__main__'}
if project:
    output.mkdir(parents=True)
    projector=base.with_name('prepare_current_dummy_reference.py')
    assert hashlib.sha256(projector.read_bytes()).hexdigest()=='39b7d84bb57864ee96124b08e5e50ea890cd83cf4c90dade0be2748aaccaccd3'
    pcode=projector.read_text()
    for old,new in [
        ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'),
        ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','ac740690d87f2c1b27ecfa803aba8b11541da617e39e2e7f131aa90fa930fb2e'),
        ('io-physical-ap-source-20260923-r2','analog-pair-reference-20260923-r1'),
        ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51')]:
        assert pcode.count(old)==1;pcode=pcode.replace(old,new)
    proof=Path(os.environ['G1_RESULTS_ROOT'])/'analog-pair-dummy-proof-20260923-r1/summary.json'
    sys.argv=[str(projector),'--proof',str(proof),'--output',str(output/'projection')]
    exec(compile(pcode,str(projector),'exec'),{'__file__':str(projector),'__name__':'__main__'})
    projected=output/'projection/physical_AP_three_dummy_comparison_only.cdl'
    pj=json.loads((output/'projection/summary.json').read_text())
    assert pj['status'].startswith('passed') and all(pj['controls'].values()) and pj['reverse_bytes_exact']
    phash=hashlib.sha256(projected.read_bytes()).hexdigest();assert phash==pj['output_sha256']
    extra=[("source=bulk/'analog-pair-reference-20260923-r1/physical_taps_reader.cdl'",'source=PROJECTED_SOURCE'),
        ("sourcehash='35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51'",'sourcehash=PROJECTED_SHA'),
        ('all three all-VDD source dummies retained','exact three independently proved all-VDD dummies projected out for comparison only; original source/native held'),
        ('report[:extraction_reference_excludes_exact_three_dummies] = false','report[:extraction_reference_excludes_exact_three_dummies] = true')]
    for old,new in extra:
        assert code.count(old)==1;code=code.replace(old,new)
    edits+=extra
    scope.update(PROJECTED_SOURCE=projected,PROJECTED_SHA=phash)
    (output/'projector_source.py').write_text(pcode)
    sys.argv=[str(base),'--output',str(output/'comparison')]
else:
    sys.argv=original_args
exec(compile(code,str(base),'exec'),scope)
(output/'binding.json').write_text(json.dumps(dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
    wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),database_sha256=dbhash,
    edits=edits,three_dummy_projection=project),indent=2)+'\n')
(output/'effective_source.py').write_text(code)
