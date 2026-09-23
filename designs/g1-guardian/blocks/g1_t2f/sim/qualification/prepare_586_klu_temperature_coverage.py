#!/usr/bin/env python3
"""Prepare required paired temperatures and same-instance return coverage; no launch."""
import difflib,json
from pathlib import Path
from prepare_586_klu_controls import HERE,ROOT,REFERENCES,sha
from run_bgr_substitution_draw_audit import read_group
from result_directory import allocate_run


def transform(original):
    assert original.count('\n.control\n')==1 and '.options klu' not in original
    assert original.count('setseed ')==1 and original.count('\nreset\n')==1
    assert original.count('tran 5n 32u\n') in [1,4]
    trial=original.replace('\n.control\n','\n.options klu\n.control\n')
    assert trial.replace('.options klu\n','')==original
    return trial


def main():
    packet=HERE/'t2f586-klu-temperature-coverage-20260923-a.json';assert not packet.exists()
    rows=[]
    typical=HERE/'runs'/REFERENCES['typical'];baseprep=json.loads((typical/'preparation.json').read_text())
    cases=[dict(label=label,corner='typical',original='t2f586-calibration-s74101-20260922-a/p%02d'%index,temps=[temp],watchdog=600)
        for label,index,temp in [('typical-t100',1,100),('typical-tcold',2,-40),('typical-thot',3,125)]]
    cases += [dict(label=corner+'-return',corner=corner,original=name.replace('-enabled','-return'),temps=[25,125,-40,25],watchdog=2400) for corner,name in REFERENCES.items()]
    for case in cases:
        old=HERE/'runs'/case['original'];original=(old/'probe.cir').read_text()
        oldrow,=json.loads((old/'summary.json').read_text())
        prep=json.loads((old/'preparation.json').read_text()) if (old/'preparation.json').exists() else dict(baseprep)
        enabled=HERE/'runs'/REFERENCES[case['corner']];enabledrow,=json.loads((enabled/'summary.json').read_text())
        if len(case['temps'])==1:
            assert oldrow['status']=='passed' and oldrow['full3180_status']=='passed'
            expected=oldrow['parameters_before'];assert expected==oldrow['parameters_after']
        else:
            expected=enabledrow['phases'][0]['parameters_before']
            actual={tag:read_group((old/'run.log').read_text(),'P0_'+tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()}
            assert actual==expected
        assert sum(map(len,expected.values()))==3180
        run_id='t2f586-klu-'+case['label']+'-20260923-a';out=allocate_run(HERE.parent,run_id,relative_parent='qualification/runs')
        for name in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json']:
            source=old/name if (old/name).exists() else old.parent/name
            (out/name).write_bytes(source.read_bytes())
        trial=transform(original);(out/'probe.cir').write_text(trial)
        (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),trial.splitlines(True),fromfile='originalSparse'+case['label'],tofile='prospectiveKlu'+case['label'])))
        recipe=dict(status='prepared only; runner and launch not qualified',run_id=run_id,label=case['label'],corner=case['corner'],
            original_run=case['original'],original_outcome=oldrow.get('control_status',oldrow.get('status')),
            original_deck_sha256=sha(old/'probe.cir'),deck_sha256=sha(out/'probe.cir'),watchdog_s=case['watchdog'],temperatures_C=case['temps'],
            source_hashes={n:sha(out/n) for n in ['bgr.spice','t2f.spice','.spiceinit']},groups=prep['groups'],expected_parameters=expected,
            inventory_sha256=sha(out/'population_inventory.json'),expected_runtime_identity=prep['runtime'],
            source_revision='final586 mismatch source; copied original exact model-level source, not physical source adoption',
            prospective_contract=['Sole.optionsklu change; original one seed/reset and all original measurement commands retained',
                'All3180 before/after EVERY phase exactoriginalsame-draw; full13finitevectors/32us/VCE<=1.6/positive finiteoriginalscalars',
                'SameKLU25C return exactdecodedbytes/numericrows/grid; report failures distinctly without tolerance substitution',
                'Completed originalSPARSE phases: compare exactwave/grid separately, fullwave uniongrid errors, frequencies, eventcounts/times, HBTterminal maxima',
                'Originalfastreturn2400failure retained; no missing originalphase wave inferred; no repeatedwatchdogextension',
                'No solveradoption, populationreplacement, refit or changedlinear2C criteria'],
            bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in [old/'probe.cir',old/'summary.json',old/'run.log',enabled/'summary.json',Path(__file__).resolve()]})
        (out/'preparation.json').write_text(json.dumps(recipe,indent=2)+'\n')
        rows.append(dict(case,run_id=run_id,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir')))
    packet.write_text(json.dumps(dict(status='prepared only; six additional required temperature contracts not run',cases=rows,
        nominal25C_controls_do_not_cover_temperature=True,maximum_total_cpu_s=sum(r['watchdog'] for r in cases),expected_external_growth_GiB=.45,
        implementation_status='runner and independent fullphase audit not yet qualified; no launch'),indent=2)+'\n')
    print(packet.relative_to(ROOT),sha(packet))


if __name__=='__main__':main()
