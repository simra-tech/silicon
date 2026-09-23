#!/usr/bin/env python3
"""Prepare own six-control KLU gate per corner; reuse only exact existing inputs."""
import difflib
import json
from pathlib import Path
from prepare_586_klu_temperature_coverage import HERE,ROOT,REFERENCES,sha,transform
from run_bgr_substitution_draw_audit import read_group
from result_directory import allocate_run

LABELS=['enabled','repeat','changed','disabled','disabledchanged','return']
FILES=['bgr.spice','t2f.spice','.spiceinit','population_inventory.json']

def candidate(corner,label):
    if label in ['enabled','repeat']:
        return 't2f586-klu-'+corner+'-'+('replay' if label=='enabled' else 'repeat')+'-20260923-a'
    if label=='return':return 't2f586-klu-'+corner+'-return-20260923-a'
    if corner=='fast' and label=='changed':return 't2f586-fast76002-klu32us-20260923-a'
    return None

def exact_reuse(old,new):
    assert (new/'probe.cir').read_text()==transform((old/'probe.cir').read_text())
    assert all(sha(old/n)==sha(new/n) for n in FILES)
    return {n:sha(new/n) for n in ['probe.cir']+FILES}

def main():
    output=HERE/'t2f586-klu-own6-preparation-20260923-a.json';assert not output.exists()
    cases=[]
    for corner,enabled_name in REFERENCES.items():
        for label in LABELS:
            old=HERE/'runs'/enabled_name.replace('-enabled','-'+label)
            prep=json.loads((old/'preparation.json').read_text())
            log=(old/'run.log').read_text()
            expected={tag:read_group(log,'P0_'+tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()}
            assert sum(map(len,expected.values()))==3180
            original=(old/'probe.cir').read_text();new_name=candidate(corner,label)
            record=dict(corner=corner,label=label,seed=prep['seed'],mismatch_enabled=prep['mismatch_enabled'],
                original_run=old.name,temperatures_C=prep['temperatures_C'],watchdog_s=prep['watchdog_s'],
                expected_full3180=expected,original_deck_sha256=sha(old/'probe.cir'),
                source_hashes={n:sha(old/n) for n in FILES})
            if new_name:
                new=HERE/'runs'/new_name
                record.update(run_id=new_name,scheduling='reuse exact existing input; never rerun',input_binding=exact_reuse(old,new),
                    result_gate='Independent own6 audit must bind terminal receipt/runtime/log/full3180/waves; currently pending or completed, no pass assumed.')
            else:
                new_name='t2f586-klu-own6-'+corner+'-'+label+'-20260923-a'
                out=allocate_run(HERE.parent,new_name,relative_parent='qualification/runs')
                for n in FILES:(out/n).write_bytes((old/n).read_bytes())
                deck=transform(original);(out/'probe.cir').write_text(deck)
                (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),deck.splitlines(True),fromfile=corner+'-original-'+label,tofile=corner+'-klu-'+label)))
                recipe=dict(status='prepared only; no launch',run_id=new_name,label=corner+'-'+label,corner=corner,
                    original_run=old.name,original_outcome=json.loads((old/'summary.json').read_text())[0]['control_status'],
                    original_deck_sha256=sha(old/'probe.cir'),deck_sha256=sha(out/'probe.cir'),watchdog_s=prep['watchdog_s'],
                    temperatures_C=prep['temperatures_C'],source_hashes={n:sha(out/n) for n in FILES if n!='population_inventory.json'},
                    groups=prep['groups'],expected_parameters=expected,inventory_sha256=sha(out/'population_inventory.json'),
                    expected_runtime_identity=prep['runtime'],mismatch_enabled=prep['mismatch_enabled'],
                    prospective_contract=['Same original full32us/OP/reset/seed/13columns and600s; sole.optionsklu selector.',
                        'All3180 exact original and before/after; disablednominal and crossseed exactness independently audited.',
                        'Six-control crossrun wave/parameter equality and1129changedprimitives mandatory; originalSPARSEfailures retained.',
                        'No population/adoption/refit/replacement; no analog launch authorized by this preparation.'],
                    bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in [old/'probe.cir',old/'preparation.json',old/'run.log',old/'summary.json',old/'provenance.json',Path(__file__).resolve()]})
                (out/'preparation.json').write_text(json.dumps(recipe,indent=2)+'\n')
                record.update(run_id=new_name,scheduling='new control not run',preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir'))
            cases.append(record)
    new=[r for r in cases if r['scheduling']=='new control not run']
    assert len(cases)==18 and len(new)==8
    payload=dict(status='prepared only; independent own6 audit and implementation binding not yet qualified',cases=cases,
        new_controls=len(new),exact_existing_input_reuses=10,new_watchdog_CPU_s=sum(r['watchdog_s'] for r in new),
        expected_new_external_growth_GiB=.40,
        prospective_checks=['Per-corner enabled/repeat exact3180+decodedwave/numeric/grid',
            'Per-corner enabled730? No: original T2F seeds74001/75001/76001 and changed74002/75002/76002 retained exactly',
            'All1129randomizedprimitives change across enabled seeds, groupedBGR1036/T2F93',
            'Disabled/disabledchanged full3180 and fullwave exact; zero/one nominal mismatch fields checked explicitly',
            'SameKLU return everyphase full3180 plus initial/finalroom exact against enabled; no tolerance substitution',
            'Everyreceipt hashbound and everyexplicit numerical error fatal despiteexit0; source/runtime equality mandatory',
            'SPARSE-to-KLU exact failures retained separately; completed exact-input controls reused, never repeated',
            'No statistical solver switch or failedsample replacement from preparation or isolated controls'],
        preparer_sha256=sha(Path(__file__)))
    output.write_text(json.dumps(payload,indent=2)+'\n');print(output.relative_to(ROOT),sha(output),len(new))

if __name__=='__main__':main()
