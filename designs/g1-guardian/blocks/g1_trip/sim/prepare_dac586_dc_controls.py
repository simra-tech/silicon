#!/usr/bin/env python3
"""Prepare deterministic behavioral-bit/DC-continuation method controls only."""
import difflib
import json
from pathlib import Path
import re
from prepare_dac586_static_controls import ROOT,SIM,CASES,sha
from result_directory import allocate_run

BITS=[prefix+str(bit) for prefix in ['s','h'] for bit in range(8)]
ADDED=['v('+node+')' for node in BITS]+['v(code)','i(vcode)']


def map_bits(original,soft,hard):
    replacements=[]
    for prefix,code in [('s',soft),('h',hard)]:
        for bit in range(8):
            pattern=r'^V'+prefix+str(bit)+r' '+prefix+str(bit)+r' 0 dc (\S+)$'
            match=re.search(pattern,original,re.M);assert match and float(match.group(1))==1.2*((code>>bit)&1)
            old=match.group(0)
            new='B%s%d %s%d 0 V=1.2*(floor((v(code)+%d+0.1)/%d)-2*floor((v(code)+%d+0.1)/%d))'%(prefix,bit,prefix,bit,code,2**bit,code,2**(bit+1))
            replacements.append((old,new))
    mapped=original
    for old,new in replacements:mapped=mapped.replace(old+'\n',new+'\n')
    mapped=mapped.replace('\n.control\n','\nVcode code 0 dc 0\n.control\n')
    inverse=mapped.replace('\nVcode code 0 dc 0\n.control\n','\n.control\n')
    for old,new in replacements:inverse=inverse.replace(new+'\n',old+'\n')
    assert inverse==original and len(replacements)==16
    return mapped


def transform(original,old_id,new_id,soft,hard,groups,dc=False):
    mapped=map_bits(original,soft,hard)
    saves=[line for line in mapped.splitlines() if line.startswith('.save ')]
    assert len(saves)==1;mapped=mapped.replace(saves[0]+'\n',saves[0]+' '+' '.join(ADDED)+'\n')
    output_lines=re.findall(r'^wrdata .+\n',mapped,re.M)
    assert output_lines
    for line in output_lines:mapped=mapped.replace(line,line.rstrip()+' '+' '.join(ADDED)+'\n')
    if dc:
        assert soft==hard==127 and len(output_lines)==1
        end='echo POPULATION_OP_END\nquit 0\n.endc\n.end\n';assert mapped.endswith(end)
        output,=re.findall(r'^wrdata .+\n',mapped,re.M)
        extra='echo DAC_DC_BEGIN\ndc Vcode 0 1 1\n'+output.replace('/op0.dat ','/forward.dat ')
        extra+='dc Vcode 1 0 -1\n'+output.replace('/op0.dat ','/reverse.dat ')
        for tag,keys in groups.items():
            extra+='echo DC_'+tag+'_AFTER_BEGIN\n'+''.join('print '+key+'\n' for key in keys)+'echo DC_'+tag+'_AFTER_END\n'
        extra+='echo DAC_DC_END\n';mapped=mapped[:-len(end)]+extra+end
    return mapped.replace(old_id,new_id)


def prepare():
    static_path=SIM/'qualification/dac586-static-execution-20260923-a.json'
    static=json.loads(static_path.read_text());audit_path=SIM/'qualification/dac586-static-qualification-20260923-a.json'
    audit=json.loads(audit_path.read_text());assert audit['status']=='passed static anchor qualification'
    assert all(sha(ROOT/name)==value for name,value in static['source_sha256'].items())
    packet_rows=[];bindings=dict(static['source_sha256'])
    specs=[(label,soft,hard,False,label) for label,soft,hard,temps in CASES]
    specs += [('dc-room',127,127,True,'c127-room'),('dc-room-repeat',127,127,True,'c127-room'),('dc-hot',127,127,True,'c127-hot')]
    for label,soft,hard,dc,reference_label in specs:
        ref=SIM/'qualification'/('dac586-static-controls-20260923-a-'+reference_label)
        original=(ref/'dac_static.cir').read_text();oldprep=json.loads((ref/'preparation.json').read_text())
        assert sha(ref/'dac_static.cir')==oldprep['deck_sha256']
        out=allocate_run(SIM,'dac586-dc-controls-20260923-a-'+label)
        for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:(out/name).write_bytes((ref/name).read_bytes())
        deck=transform(original,ref.name,out.name,soft,hard,oldprep['groups'],dc);(out/'dac_dc.cir').write_text(deck)
        (out/'declared_difference.diff').write_text(''.join(difflib.unified_diff(original.replace(ref.name,'@RUN@').splitlines(True),
            deck.replace(out.name,'@RUN@').splitlines(True),fromfile='originalStatic',tofile='behavioralBits'+('DC' if dc else 'OP'))))
        prep=dict(oldprep,run=out.name,label=label,original_static_label=reference_label,reference_static=ref.name,
            method='dc-two-point-forward-reverse' if dc else 'behavioral-bit OP',deck_sha256=sha(out/'dac_dc.cir'),
            added_vectors=ADDED,prospective_bound_s=600 if dc else oldprep['prospective_bound_s'],
            changes='Only ideal bit-driver V→B with deterministic integer map, one independent ideal code source and18additional vectors; optional two-pointDC forward/reverse. No analogdevice/model/options/clock/seed/reset change.',
            output_equivalence=dict(voltage_abs_V=1e-7,current_abs_A=1e-9,
                scope='PROPOSED prospectively, needs review before execution. Original vntol1e-7 provides a numerical comparison scale, NOT a guaranteed global solver error bound. 1nA current screen reuses prior sourceheld OP-consistency scale, not a leakage allocation. Strict exact comparisons remain separate.'))
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
        packet_rows.append(dict(label=label,run=out.name,preparation_sha256=sha(out/'preparation.json'),watchdog_s=prep['prospective_bound_s']))
        for name in ['preparation.json','dac_static.cir','summary.json','run.json','run.log','provenance.json']+[p.name for p in ref.glob('op*.dat')]:
            bindings[str((ref/name).relative_to(ROOT))]=sha(ref/name)
    for path in [Path(__file__).resolve(),SIM/'test_dac586_dc_controls.py',static_path,audit_path]:bindings[str(path.relative_to(ROOT))]=sha(path)
    result=dict(status='prepared only; no simulation or method acceptance',controls=packet_rows,bindings_sha256=bindings,
        required_gates=['All16 actual bit voltages exactly intended integer0/1.2 in every OP/DC row; code range0..255; full11512+27 exact before/after across every phase.',
            'Source/model/runtime identity, named finite30columns, no fatalzeroexit errors, exact query order and endpoint coverage.',
            'All11 static reference comparisons report exact and separately proposed100nV/1nA bounds. B-method output repeat and temperature-return exact remain required.',
            'Three two-point DC controls only after static source-control gate; same-method literal repeat exact, forward/reverse/static differences separately retained.',
            'No all256/20/100 release without measured continuation cost and independent method audit.'],
        uncertainty='For accepted per-point voltage comparison epsilon=100nV: deltaV interval [deltaV-2epsilon,deltaV+2epsilon]; endpointLSB interval [(V255-V0-2epsilon)/255,(V255-V0+2epsilon)/255]. DNL bounds use interval division minus1; require entireinterval>−1 and positive deltaV for robust pass. Near-boundary/overlappingintervals require fresh original-static refinement, not favorable selection. No automatic global bound inferred from finite anchors.',
        guards='DC cannot establish clocked decision/guard/settling acceptance. Existing joint transient gates unchanged; no inferred input-referred bound without independently justified gain. INL reported only, no invented allocation.',
        auxiliary_node='New code source controls ideal B inputs and its own existing1Tohm shunt; explicitly observei(Vcode). This auxiliary current is not DAC/supply leakage. Analog model device count and random target inventory unchanged.',
        runtime_forecast='NOTRUN. Static11 historical587.571s observed; newB-node method may differ. Child caps4200s static+1800s DC, oneCPU/.4GiB output bound; no forecast from old sourceDC timeouts.',
        scope='Fresh final586/gm4 method; all previous old-sourceDC120s failures, oneOP/twoOP exact failures retained. No circuit/source adoption.')
    output=SIM/'qualification/dac586-dc-proposal-20260923-a.json';assert not output.exists()
    output.write_text(json.dumps(result,indent=2)+'\n');print(sha(output))


if __name__=='__main__':prepare()
