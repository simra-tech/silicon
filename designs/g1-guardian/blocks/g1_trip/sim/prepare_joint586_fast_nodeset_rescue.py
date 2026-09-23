#!/usr/bin/env python3
"""Freeze original fast own6, SHN pair and six fixtures with fixed nodeset."""
import difflib
import json
from pathlib import Path
import re
from prepare_joint586_fastcold_nodeset import SIM, ROOT, ORIGINAL, NODES, guesses, sha
from result_directory import allocate_run

PACKET=SIM/'qualification/joint586-fast-nodeset-rescue-contract-20260923-a.json'
LABELS=['enabled','repeat','changed','disabled','disabledchanged','return','cm0_old18','cm0_shn19']
FIXTURES=['low_cold_cm0','low_hot_cm0','high_cold_cm0','high_hot_cm0','room_cm_low','room_cm_high']
REUSE='joint586-fastcold-nodeset-transient-sparse-20260923-b'


def transform(original, old_run, new_run, values):
    assert list(values)==NODES and '.nodeset' not in original and '.options klu' not in original
    assert original.count('\n.control\n')==1
    lines=original.splitlines(True)
    outputs=[]
    for i,line in enumerate(lines):
        if line.startswith('wrdata '):
            old='qualification/'+old_run+'/'
            assert line.count(old)==1
            new=line.replace(old,'qualification/'+new_run+'/')
            outputs.append((i,line,new));lines[i]=new
    assert len(outputs) in [1,4]
    # Includes deliberately remain the exact archived source paths. Both the
    # archived and local identical source copies are mandatory live bindings.
    added='.nodeset '+' '.join('v('+n+')='+values[n] for n in NODES)+'\n'
    deck=''.join(lines).replace('\n.control\n','\n'+added+'.control\n')
    inverse=deck.replace('\n'+added+'.control\n','\n.control\n').splitlines(True)
    for i,old,new in outputs:
        assert inverse[i]==new;inverse[i]=old
    assert ''.join(inverse)==original
    return deck,dict(exact_inverse=True,fixed_nodeset=added,output_paths=[dict(line=i+1,old=o,new=n) for i,o,n in outputs],
        archived_source_includes_unchanged=True)


def main():
    assert not PACKET.exists()
    values=guesses((ORIGINAL/'run.log').read_text())
    cases=[];bindings={}
    originals=[('own',label,'joint586-fast-transqual-shn-20260923-b-'+label) for label in LABELS]
    originals += [('fixture',label,'joint586-fast-fixture-controls-20260923-b-'+label) for label in FIXTURES]
    for kind,label,old_run in originals:
        old=SIM/'qualification'/old_run;prep=json.loads((old/'preparation.json').read_text())
        assert prep['corner']=='fast' and prep['watchdog_s']==(4800 if label=='return' else 1200)
        reuse=kind=='fixture' and label=='low_cold_cm0'
        run=REUSE if reuse else 'joint586-fast-nodeset-rescue-'+kind+'-'+label.replace('_','-')+'-20260923-a'
        deck,audit=transform((old/'population_transient.cir').read_text(),old_run,run,values)
        if reuse:
            out=SIM/'qualification'/run
            assert (out/'population_transient.cir').read_text()==deck
            row,=json.loads((out/'summary.json').read_text())
            assert row['parameter_wave_status']==row['decision_sampling_status']=='passed'
            reuse_receipts={n:sha(out/n) for n in ['population_transient.cir','summary.json','run.json','run.log','provenance.json','runner.py','error_inventory_adapter.py']}
            for n in reuse_receipts:bindings[str((out/n).relative_to(ROOT))]=sha(out/n)
        else:
            out=allocate_run(SIM,run)
            for n in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
                (out/n).write_bytes((old/n).read_bytes())
            (out/'population_transient.cir').write_text(deck)
            (out/'transform_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
            (out/'declared_initialization_difference.diff').write_text(''.join(difflib.unified_diff(
                (old/'population_transient.cir').read_text().splitlines(True),deck.splitlines(True),fromfile=old_run,tofile=run)))
            reuse_receipts=None
        inputs=dict(run=run,kind=kind,label=label,original_run=old_run,seed=prep['seed'],
            temperatures_C=prep.get('temperatures_C',[prep.get('condition',[None,None])[1]]),
            expected_vectors=prep['expected_vectors'] if kind=='own' else [prep['expected_vector']],
            common_mode_V=prep.get('common_mode_V') if kind=='own' else prep['condition'][4],
            columns=prep['columns'],groups=prep['groups'],source_hashes=prep['source_hashes'],
            inventory_sha256=prep['inventory_sha256'],runtime_identity=prep['expected_runtime_identity'],
            prospective_sampling=prep['prospective_sampling'],watchdog_s=prep['watchdog_s'],physical_scope=prep['physical_scope'],
            scheduling='reuse exact completed independent SPARSE nodeset fixture' if reuse else 'new independent process',
            reuse_receipts_sha256=reuse_receipts,deck_sha256=sha(out/'population_transient.cir'),transform=audit)
        assert len(inputs['temperatures_C'])==len(inputs['expected_vectors']) and all(len(v)==11512 for v in inputs['expected_vectors'])
        if not reuse:
            (out/'preparation.json').write_text(json.dumps(inputs,indent=2)+'\n')
        cases.append(inputs)
        for n in ['population_transient.cir','preparation.json','summary.json','run.json','run.log','provenance.json',
                'sense.spice','trip.spice','bgr.spice','population_inventory.json']:
            bindings[str((old/n).relative_to(ROOT))]=sha(old/n)
        for n,v in prep['live_bindings_sha256'].items():
            assert sha(ROOT/n)==v;bindings[n]=v
    helpers=['prepare_joint586_fast_nodeset_rescue.py','run_joint586_fast_nodeset_rescue.py',
        'audit_joint586_fast_nodeset_rescue.py','test_joint586_fast_nodeset_rescue.py',
        'prepare_joint586_fastcold_nodeset.py','run_joint586_transients.py',
        'run_nominal_clock_probe.py','run_bgr_substitution_draw_audit.py',
        'audit_joint586_adverse_transients.py','audit_joint586_population_op.py',
        'run_joint586_adverse_transient.py','analyze_bgr_substitution_outcomes.py','wave_archive.py','.spiceinit']
    bindings.update({str((SIM/n).relative_to(ROOT)):sha(SIM/n) for n in helpers})
    packet=dict(status='prepared only; no rescue qualification or population release',cases=cases,
        fixed_guesses=values,fixed_guesses_source=str((ORIGINAL/'run.log').relative_to(ROOT)),
        bindings_sha256=bindings,planned_controls=14,new_processes=13,reused_completed_controls=1,
        scope='Original fast own6 plus SHN18/19 pair and six fixtures, source/cards/11512/27/seed/stimulus/clock/codes/options unchanged except ONE fixed eight-node SPARSE nodeset line. Guesses are canonical original78001 OP literals, never retuned per seed/condition. No IC/UIC/tolerance change. Preserve old waveform/decision comparisons separately; no numerical bound can promote failed exact comparisons. Original failures retained. No fast30 or calibration/physical adoption.',
        gates=['Full11512beforeafter plus27 exact to corresponding original owncorner draw in every phase.',
            'Exact new enabled repeat, changed3500primitive draws, disabledchanged, initial/returnedroom waves and fullvectors.',
            'New SHN18-to19 original18 projection exact; actual mean/differential checks.',
            'All six fixture numerical/parameter/sampling outcomes retained; matched originalfive fullwaves exact checks separate, failed original lowcold no originalfullwave claim.'],
        bounds=dict(single_phase_s=1200,same_instance_return_s=4800,maximum_new_CPU_s=12*1200+4800,
            expected_HOME_growth_GiB=.65),population_release='not run; separately reviewed disposition required')
    PACKET.write_text(json.dumps(packet,indent=2)+'\n');print(PACKET.relative_to(ROOT),sha(PACKET))


if __name__=='__main__':main()
