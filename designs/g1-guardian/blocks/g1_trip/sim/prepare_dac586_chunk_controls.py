#!/usr/bin/env python3
"""Prepare two same-instance127→128→127 DC warm-start controls; never run."""
import argparse
import difflib
import json
import re
from pathlib import Path
from prepare_dac586_static_controls import SIM, ROOT, sha
from result_directory import allocate_run


def alter_code(code):
    assert type(code) is int and 0 <= code <= 255
    return ''.join('alter V%s%d dc=%s\n' % (prefix, bit, '1.2' if (code >> bit)&1 else '0')
                   for prefix in ['s','h'] for bit in range(8))


def transform(original, old_id, new_id, groups):
    end='echo POPULATION_OP_END\nquit 0\n.endc\n.end\n'
    assert original.endswith(end)
    assert original.count('\nsetseed ') == original.count('\nreset\n') == 1
    output,=re.findall(r'^wrdata .+\n',original,re.M)
    assert '/op0.dat ' in output
    extra='echo DAC_CHUNK_WARM_BEGIN\n'+alter_code(128)+'op\n'
    extra+=output.replace('/op0.dat ','/code128.dat ')
    extra+=alter_code(127)+'op\n'+output.replace('/op0.dat ','/return127.dat ')
    for tag,queries in groups.items():
        extra+='echo CHUNK_'+tag+'_AFTER_BEGIN\n'+''.join('print '+q+'\n' for q in queries)+'echo CHUNK_'+tag+'_AFTER_END\n'
    extra+='echo DAC_CHUNK_WARM_END\n'
    result=original[:-len(end)]+extra+end
    assert result.replace(extra,'') == original
    assert result.count('\nop\n') == 4
    assert not re.search(r'^(altermod|tran|dc|ac|noise|reset)\b',extra,re.M)
    return result.replace(old_id,new_id)


def prepare(prefix):
    rows=[]
    for label in ['room','hot']:
        ref=SIM/'qualification'/('dac586-static-controls-20260923-a-c127-'+label)
        prep=json.loads((ref/'preparation.json').read_text())
        original=(ref/'dac_static.cir').read_text()
        assert sha(ref/'dac_static.cir') == prep['deck_sha256'] and prep['codes']==[127,127]
        out=allocate_run(SIM,prefix+'-'+label)
        for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
            (out/name).write_bytes((ref/name).read_bytes())
        deck=transform(original,ref.name,out.name,prep['groups'])
        (out/'dac_chunk.cir').write_text(deck)
        (out/'declared_difference.diff').write_text(''.join(difflib.unified_diff(
            original.replace(ref.name,'@RUN@').splitlines(True),deck.replace(out.name,'@RUN@').splitlines(True),
            fromfile='qualifiedStatic127',tofile='sameInstance127_128_127')))
        result=dict(status='prepared only; no simulation or method qualification',run=out.name,
            initial_reference=ref.name,anchor128_reference='dac586-static-controls-20260923-a-c128-'+label,
            source_hashes=prep['source_hashes'],inventory_sha256=prep['inventory_sha256'],
            deck_sha256=sha(out/'dac_chunk.cir'),groups=prep['groups'],expected_full_parameters=prep['expected_full_parameters'],
            expected_runtime_identity=prep['expected_runtime_identity'],temperatures_C=prep['temperatures_C'],seed=73001,
            initial_output='op0.dat',changed_output='code128.dat',returned_output='return127.dat',
            control_schedule='OriginaltwoOP/fullBEFORE+AFTER at127; alter16voltage-sourceDCvalues→128/oneOP; restore127/oneOP; full11512+27 CHUNK_AFTER',
            source_transform='No circuit/source/card/options change beyond output directory; only appended controlcommands. No reset/reseed/IC/UIC/nodeset/solverchange.',
            required_gates=['All static11controls independently qualify before dependent chunk launch',
                'Exact same11512 and27 before/after/CHUNK_AFTER, source/runtime, finite correctlynamed12column OP rows and no fatalerrors',
                'Initial and returned127 all12 numeric+decodedtokenbytes exactly qualifiedstatic127;128 exactly qualifiedstatic128',
                'False exactcomparisons retained as FAILED; no tolerance substitute or allcode acceptance inferred'],
            prospective_watchdog_s=600,prospective_home_GiB=.04,
            scope='Conditional DC continuation/warm-start only; actualruntime/costpercode NOTRUN. No dynamic majorcarry, leakage isolation, temperature-return or all256claim.',
            planning='Measure cold initialization vs subsequentOP time from actualrunprogress before any largerchunk,20or100. No naiveper-codeprocess ensemble.',
            bindings_sha256={str(path.relative_to(ROOT)):sha(path) for path in
                [ref/'preparation.json',ref/'dac_static.cir',Path(__file__).resolve(),SIM/'prepare_dac586_static_controls.py']})
        (out/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
        rows.append(dict(run=out.name,preparation_sha256=sha(out/'preparation.json')))
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prefix',required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.prefix),indent=2))
