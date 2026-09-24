#!/usr/bin/env python3
"""One unchanged-stock current hard/R100 native LVS, 600-second engine bound."""
import hashlib
from pathlib import Path
import current_bindings as binding

binding.validate_inputs();binding.bound(binding.CONTEXT_RELATIVE,binding.CONTEXT_SHA)
WRAPPER=Path(__file__).resolve();base=WRAPPER.parent.parent/'run_native_lvs.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='6892817984fe3917b3882e33f8d11b81d2ad81b4f0c643968b1773a1fda7626a'
code=base.read_text()
edits=[
    ('gshared-fill-20260923-r4/route_fill_pruned.gds',binding.GDS_RELATIVE),
    ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2',binding.GDS_SHA),
    ('a3a0bccc4ba71f6b5821061839a5efce048046e54dff0feb09d2cc5d49c22107',binding.PROOF_SHA),
    ('io-physical-ap-source-20260923-r2/summary.json','trip-hard-full-reference-20260923-r1/summary.json'),
    ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4',binding.SOURCE_SHA),
    ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','be00e66f12309bb26f16165860271936ee3f8eb74bc84c3fa56e1ee3295ccd90'),
    ("assert pj['status'].startswith('passed') and pj['reader_sha256']==sha(source)\n        assert pj['source_sha256']==sha(source_original) and pj['reachable_taps']==386",
     """assert sha(preparation)=='0bcfd96f2a8a5e2de9fd337d96cab5c695284180c1be7901193e0534b134adf7'
        assert pj['status']=='passed exact hard-only current fullchip reference splice'
        assert pj['GDS_sha256']=='1c9533180ec3d45265f3617298310a31aa01bb515fee6178a939ee6364502f22'
        assert len(pj['arms'])==2
        for arm in pj['arms']:
            assert sha(preparation.parent/arm['file'])==arm['output_sha256']
            assert arm['reverse_bytes_exact'] and arm['standalone_wholeTRIP_body_exact']
            assert arm['all386taps_other_source_blocks_and_pins_exact'] and arm['shared_soft_source_held']
            assert arm['wrong_clone_negative_rejected'] and len(arm['flattened_differences'])==2
        context=BINDING.bound(BINDING.CONTEXT_RELATIVE,BINDING.CONTEXT_SHA)
        proof=json.loads(context.read_text())
        assert proof['status']=='passed full native context and scoped IO junction exact parity'
        assert proof['all_native_instances_preserved'] and all(proof['full_context_IO_junction_parity'].values())
        assert sha(layout) in proof['inputs'].values()
        expected[context]=sha(context);expected[WRAPPER]=sha(WRAPPER)
        expected[WRAPPER.with_name('current_bindings.py')]=sha(WRAPPER.with_name('current_bindings.py'))"""),
    ('watchdog_seconds=900','watchdog_seconds=600'),("a.output/'run.json',900","a.output/'run.json',600"),
    ("(a.output/'source.py').write_bytes(Path(__file__).read_bytes())", "(a.output/'source.py').write_text(EFFECTIVE_CODE)\n    (a.output/'binding_wrapper.py').write_bytes(WRAPPER.read_bytes())"),
    ('Current digital source; owner-authorized explicit VSS','Current hard-comparator/R100 SENSE source; exact pure-fill representation; owner-authorized explicit VSS')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','WRAPPER':WRAPPER,'BINDING':binding,'EFFECTIVE_CODE':code})
