"""Source-only eight-code throughput hypothesis; no scaling or simulator launch."""
import difflib
import json
import re
from pathlib import Path
from prepare_dac586_dc_controls import ROOT,SIM,transform,sha
from result_directory import allocate_run

RUN='dac586-lowcarry-controls-20260923-a'
REFERENCE=SIM/'qualification/dac586-static-controls-20260923-a-c0-room'


def chunk_deck(original,old_id,new_id,groups):
    # Existing qualified behavioral transform supplies the exact16-bit mapping.
    mapped=transform(original,old_id,new_id,0,0,groups,dc=False)
    end='echo POPULATION_OP_END\nquit 0\n.endc\n.end\n'
    assert mapped.endswith(end) and mapped.count(end)==1
    output,=re.findall(r'^wrdata .+\n',mapped,re.M)
    extra='echo DAC_LOWCARRY_BEGIN\ndc Vcode 0 7 1\n'+output.replace('/op0.dat ','/forward.dat ')
    extra+='dc Vcode 7 0 -1\n'+output.replace('/op0.dat ','/reverse.dat ')
    for tag,keys in groups.items():
        extra+='echo DC_'+tag+'_AFTER_BEGIN\n'+''.join('print '+key+'\n' for key in keys)+'echo DC_'+tag+'_AFTER_END\n'
    extra+='echo DAC_LOWCARRY_END\n'
    result=mapped[:-len(end)]+extra+end
    assert result.replace(extra,'')==mapped
    return result


def prepare():
    audit=SIM/'qualification/dac586-dc-method-audit-20260923-a.json'
    assert sha(audit)=='d518ce4faf592aa633989a8af76514abcf96f4d2dc365afbc50c9b8e40e70ed2'
    assert json.loads(audit.read_text())['status']=='passed conditional DC method controls'
    prep=json.loads((REFERENCE/'preparation.json').read_text());original=(REFERENCE/'dac_static.cir').read_text()
    assert sha(REFERENCE/'dac_static.cir')==prep['deck_sha256'] and prep['codes']==[0,0] and prep['temperatures_C']==[25]
    controls=[];bindings={str(audit.relative_to(ROOT)):sha(audit)}
    for label in ['room','room-repeat']:
        out=allocate_run(SIM,RUN+'-'+label)
        for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
            (out/name).write_bytes((REFERENCE/name).read_bytes())
        deck=chunk_deck(original,REFERENCE.name,out.name,prep['groups']);(out/'dac_lowcarry.cir').write_text(deck)
        difference=''.join(difflib.unified_diff(original.replace(REFERENCE.name,'@RUN@').splitlines(True),deck.replace(out.name,'@RUN@').splitlines(True),fromfile='qualified original code0 static',tofile='prospective eight-code DC'))
        (out/'declared_difference.diff').write_text(difference)
        new=dict(prep,run=out.name,label=label,deck_sha256=sha(out/'dac_lowcarry.cir'),watchdog_s=600,
            method='eight-code forward/reverse throughput probe',forward_codes=list(range(8)),reverse_codes=list(range(7,-1,-1)),
            scope='Source-only preparation. All analog sources/runtime/model/options/seed/reset unchanged. No all-code, population, dynamic, isolated-leakage or new-SENSE qualification.')
        (out/'preparation.json').write_text(json.dumps(new,indent=2)+'\n')
        controls.append(dict(label=label,run=out.name,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'dac_lowcarry.cir'),watchdog_s=600))
    for f in [Path(__file__).resolve(),SIM/'test_dac586_lowcarry_probe.py',SIM/'prepare_dac586_dc_controls.py',SIM/'prepare_dac586_static_controls.py',SIM/'result_directory.py']:
        bindings[str(f.relative_to(ROOT))]=sha(f)
    for name in ['preparation.json','dac_static.cir','run.json','run.log','summary.json','op0.dat']:
        f=REFERENCE/name;bindings[str(f.relative_to(ROOT))]=sha(f)
    packet=dict(status='prepared only; runner/auditor review and explicit CPU lease required',controls=controls,bindings_sha256=bindings,
        hypothesis='Determine whether contiguous low-bit transitions avoid the per-point dynamic-gmin fallback observed at127↔128. Two fresh identical chunks permit actual same-method repeat testing; no speedup assumed.',
        gates=['Full11512+27 exact original OP before/after and after each completed sweep pair; source/runtime and originalSPARSE unchanged.',
            'Named30 finite columns, exact16actual bit voltages for every integer0..7 in forward/reverse order; actualVcode exact.',
            'Original code0 static comparison reports strict equality separately from prospective100nV/1nA method screen; no originalstatic comparison exists for codes1..7.',
            'Same-method literal repeat requires exact full30-column OP and both completeDC tables; report forward/reverse differences separately.',
            'Preserve fatalzeroexit errors, timeout/partial output and all original exact failures. Completion is not DAC acceptance.',
            'Count dynamicgmin attempts separately for initial2OP/forward8/reverse8 and bracket elapsed sections from saved progress. No extrapolated all256 acceptance.'],
        bound=dict(children=2,seconds_each=600,serial_cpu_count=1,expected_bulk_GiB=.08),
        uncertainty='100nV/1nA remains a prospective consistency screen, not a proved uniform solver error; no unanchored DNL/monotonicity or guard claim.')
    path=SIM/'qualification'/(RUN+'.json');assert not path.exists();path.write_text(json.dumps(packet,indent=2)+'\n');print(sha(path))


if __name__=='__main__':prepare()
