"""Prepare exact matched typical-room/slow-cold/fast-hot residual pairs."""
import difflib
import json
from pathlib import Path
from prepare_joint586_tmax_probe import SIM,ROOT,OLD,NEW,sha
from result_directory import allocate_run

PARENTS=[('typical',73001,'joint586-calibration-s73001-20260922-a',['p22','p23']),
         ('slow',77101,'joint586-slow-calibration-s77101-20260923-a',['p52','p53']),
         ('fast',78101,'joint586-fast-nodeset-calibration-s78101-20260923-a',['p54','p55'])]


def matched_transform(original,original_run,new_run,seed):
    old_output='qualification/'+original_run+'/phase0.dat';new_output='qualification/'+new_run+'/phase0.dat'
    assert original.count(OLD)==original.count(old_output)==1
    assert original.count('setseed %d\n'%seed)==1 and '.options klu' not in original.lower()
    result=original.replace(OLD,NEW).replace(old_output,new_output)
    assert result.replace(NEW,OLD).replace(new_output,old_output)==original
    return result


def declared_pair(entries,seed):
    assert len(entries)==2
    temperature={73001:25,77101:-40,78101:125}[seed]
    condition={77101:'cold_legacy',78101:'hot_legacy'}.get(seed)
    for entry,shunt in zip(entries,[.0245,.0255]):
        assert entry['kind']=='residual' and entry['temperature_C']==temperature and entry['shunt_V']==shunt
        if seed!=73001:assert entry['condition']==[condition,temperature,3.3,1.2,None]
    assert entries[0]['codes']==entries[1]['codes']
    # Decisions/status are deliberately not selection predicates.


def prepare():
    pilot=SIM/'qualification/joint586-s73001p00-tmax1ns-20260923-a/preparation.json'
    pilotprep=json.loads(pilot.read_text());controls=[]
    global_bindings={str(pilot.relative_to(ROOT)):sha(pilot)}
    for corner,seed,parent_name,leaf_names in PARENTS:
        parent=SIM/'qualification'/parent_name;provenance=json.loads((parent/'provenance.json').read_text())
        entries=[json.loads((parent/leaf/'summary.json').read_text()) for leaf in leaf_names];declared_pair(entries,seed)
        for leaf,entry in zip(leaf_names,entries):
            original=parent/leaf;original_run=parent_name+'/'+leaf;old=(original/'probe.cir').read_text()
            assert entry['status']=='passed' and entry['watchdog_status']=='completed' and entry['returncode']==0 and not entry['errors']
            parameters=entry['parameter_audit'];assert parameters['parameters_before']==parameters['parameters_after'] and len(parameters['parameters_before'])==11512
            nodesets=[line for line in old.splitlines() if line.lower().startswith('.nodeset')]
            assert bool(nodesets)==(corner=='fast')
            run='joint586-tmax-matrix-s%d-%s-20260923-a'%(seed,leaf);out=allocate_run(SIM,run)
            deck=matched_transform(old,original_run,run,seed);(out/'probe.cir').write_text(deck)
            (out/'declared_tmax_difference.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),deck.splitlines(True),fromfile='original '+original_run,tofile='TMAX1ns-only')))
            for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:(out/name).write_bytes((parent/name).read_bytes())
            files=[original/n for n in ['probe.cir','run.json','run.log','summary.json','phase0.dat.gz','phase0.dat.archive.json']]
            files += [parent/n for n in ['provenance.json','sense.spice','trip.spice','bgr.spice','population_inventory.json']]
            files += [SIM/n for n in ['prepare_joint586_tmax_matrix.py','run_joint586_tmax_matrix.py','test_joint586_tmax_matrix.py',
                'prepare_joint586_tmax_probe.py','run_joint586_tmax_probe.py','compare_joint586_tmax_probe.py','run_joint586_transients.py',
                'run_nominal_clock_probe.py','run_bgr_substitution_draw_audit.py','analyze_bgr_substitution_outcomes.py','wave_archive.py','result_directory.py','.spiceinit']]
            prep=dict(run_id=run,original_run=original_run,seed=seed,corner=corner,kind=entry['kind'],codes=entry['codes'],shunt_V=entry['shunt_V'],
                deck_sha256=sha(out/'probe.cir'),original_deck_sha256=sha(original/'probe.cir'),source_hashes=provenance['source_hashes'],
                inventory_sha256=provenance['inventory_sha256'],groups=pilotprep['groups'],expected_runtime_identity=provenance['runtime_identity'],
                expected_parameters=parameters['parameters_before'],expected_legacy27=parameters['legacy27'],prospective_sampling=pilotprep['prospective_sampling'],
                bounds=pilotprep['bounds'],watchdog_s=1200,original_nodeset_lines=nodesets,
                temperature_C=entry['temperature_C'],original_condition=entry.get('condition'),
                scope='Matched original typical-room/slow-cold/fast-hot residual24.5/25.5mV pairs (±0.5mV), not±0.1mV. Fast preserves its original fixed nodeset; no cross-method equivalence implied. Original source and all sampling/criteria retained; no new-SENSE or population adoption.',
                live_bindings_sha256={str(f.relative_to(ROOT)):sha(f) for f in files})
            (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
            controls.append(dict(run_id=run,seed=seed,corner=corner,original_run=original_run,shunt_V=entry['shunt_V'],
                preparation_sha256=sha(out/'preparation.json'),watchdog_s=1200))
    packet=dict(status='prepared only; exact residual-scope ROOT review required',controls=controls,bindings_sha256=global_bindings,
        selection='Fixed declared residual lower/upper pair: typical73001 room25C, slow77101 cold−40C, fast78101 hot125C, nominalrails3.3/1.2 and legacySHN0. Chosen from kind/temperature/condition/shunt/codes definitions, never favorable observed decisions. ±0.1mV remains unqualified.',
        bounds=pilotprep['bounds'],scope='Six matched diagnostics only. Preserve exact waveform/grid failure separately from unchanged prospective engineering screen. No verified universal error bound or method/population adoption.',
        expected_bulk_GiB=.30)
    path=SIM/'qualification/joint586-tmax-matrix-20260923-a.json';assert not path.exists();path.write_text(json.dumps(packet,indent=2)+'\n');print(sha(path))


if __name__=='__main__':prepare()
