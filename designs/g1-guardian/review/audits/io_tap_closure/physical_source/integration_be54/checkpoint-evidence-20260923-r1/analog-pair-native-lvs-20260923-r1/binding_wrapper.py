#!/usr/bin/env python3
"""Bound unchanged stock native LVS to the independently prepared analog-pair reference."""
import hashlib
from pathlib import Path

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'run_native_lvs.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='6892817984fe3917b3882e33f8d11b81d2ad81b4f0c643968b1773a1fda7626a'
code=base.read_text()
rebindings=[
 ('gshared-fill-20260923-r4/route_fill_pruned.gds','analog-pair-integration-20260923-r1/analog_pair_native.gds'),
 ('io-physical-ap-source-20260923-r2/summary.json','analog-pair-reference-20260923-r1/summary.json'),
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'),
 ('a3a0bccc4ba71f6b5821061839a5efce048046e54dff0feb09d2cc5d49c22107','80575bbd6a51044a287bb091c6888a02acdb4fb096d95dc201278dcc7e74fab3'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51'),
 ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','ac740690d87f2c1b27ecfa803aba8b11541da617e39e2e7f131aa90fa930fb2e'),
 ("        assert pj['status'].startswith('passed') and pj['reader_sha256']==sha(source)\n        assert pj['source_sha256']==sha(source_original) and pj['reachable_taps']==386", """        assert sha(preparation)=='0e6bb78e137b01c17d3b0ee4893d12aa1193342b3148be948ad22ed688ea2a1b'
        assert pj['status'].startswith('passed') and pj['GDS_sha256']==sha(layout)
        assert len(pj['arms'])==2
        for arm in pj['arms']:
            assert sha(preparation.parent/arm['file'])==arm['output_sha256']
            assert arm['all386tap_records_and_nodes_exact'] and arm['all_other_blocks_and_source_bytes_exact']
            assert arm['reverse_bytes_exact'] and arm['exact_standalone_SENSE_body_after_top_name_projection']
            assert len(arm['flattened_differences'])==2 and all(arm['negative_controls'].values())
            normalized=arm['new_region'].rstrip('\\n')
            assert normalized.replace('l=62u','l=61u')!=normalized
            assert normalized.replace('w=45u','w=44u')!=normalized
        context=bulk/'analog-pair-context-20260923-r1/summary.json'
        assert sha(context)=='0d1ab6ca320eea357b027c11219c7e98f50cb9f674d0d8cf21e150f2e0fccd44'
        proof=json.loads(context.read_text())
        assert proof['status']=='passed full native context and scoped IO junction exact parity'
        assert proof['all_native_instances_preserved'] and all(proof['full_context_IO_junction_parity'].values())
        assert sha(layout) in proof['inputs'].values()
        expected[context]=sha(context)
        expected[WRAPPER]=sha(WRAPPER)
"""),
 ("(a.output/'source.py').write_bytes(Path(__file__).read_bytes())", "(a.output/'source.py').write_text(EFFECTIVE_CODE)\n    (a.output/'binding_wrapper.py').write_bytes(WRAPPER.read_bytes())"),
 ('Current digital source; owner-authorized explicit VSS', 'Current digital and two-passive SENSE source; owner-authorized explicit VSS')]
for old,new in rebindings:
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','WRAPPER':wrapper,'EFFECTIVE_CODE':code})
