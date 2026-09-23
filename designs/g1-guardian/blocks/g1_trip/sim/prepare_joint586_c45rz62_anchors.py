"""Prepare only candidate-source and same-candidate TMAX calibration-anchor pairs."""
import argparse
import difflib
import json
from pathlib import Path
from prepare_joint586_tmax_probe import ROOT,SIM,OLD,NEW,sha
from result_directory import allocate_run

CANDIDATE_SHA='b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97'
PARENT=SIM/'qualification/joint586-calibration-s73001-20260922-a'
CAP='@c.xs.xota.xcc.c1[scale]'
LEAVES=['p00','p08','p09']


def candidate_source(original):
    old='XCC cz out cap_cmim w=69u l=23u m=1 mm_ok=1';new=old.replace('w=69u','w=45u')
    assert original.count(old)==1 and new not in original
    changed=original.replace(old,new);prefix,main=changed.split('.subckt g1_ota_main_candidate ',1)
    rz='XRZ out1 cz vss rppd w=1u l=6.2u m=1 b=0 mm_ok=1';replacement=rz.replace('l=6.2u','l=62u')
    assert main.count(rz)==1 and replacement not in main
    result=prefix+'.subckt g1_ota_main_candidate '+main.replace(rz,replacement)
    restored=result.replace(new,old);p,m=restored.split('.subckt g1_ota_main_candidate ',1)
    assert p+'.subckt g1_ota_main_candidate '+m.replace(replacement,rz)==original
    return result


def deck_transform(original,parent_name,leaf,new_run,tmax):
    assert tmax in ['0.2n','1n'] and original.count(OLD)==1 and original.count('setseed 73001\n')==1
    source='.include qualification/'+parent_name+'/sense.spice';candidate='.include qualification/'+new_run+'/sense.spice'
    output='qualification/'+parent_name+'/'+leaf+'/phase0.dat';destination='qualification/'+new_run+'/phase0.dat'
    assert original.count(source)==original.count(output)==1
    result=original.replace(source,candidate).replace(output,destination)
    if tmax=='1n':result=result.replace(OLD,NEW)
    restored=result.replace(candidate,source).replace(destination,output)
    if tmax=='1n':restored=restored.replace(NEW,OLD)
    assert restored==original
    return result


def prepare(candidate_dir):
    assert sha(candidate_dir/'candidate.spice')==CANDIDATE_SHA
    physical=json.loads((candidate_dir/'summary.json').read_text());pg=physical['parameter_gate']
    assert pg['unchanged11511_exact'] and pg['candidate11512_before_after_exact'] and pg['legacy27_exact']
    assert pg['changed_cap_scale']['status']=='passed' and pg['changed_cap_scale']['area_ratio']=='69/45'
    original=(PARENT/'sense.spice').read_text();source=candidate_source(original)
    assert source==(candidate_dir/'candidate.spice').read_text()
    provenance=json.loads((PARENT/'provenance.json').read_text());parent_result,=json.loads((PARENT/'summary.json').read_text())
    calibration=[r for r in parent_result['probes'] if r['kind']=='calibration']
    assert [r['run'].split('/')[-1] for r in [calibration[0],calibration[-2],calibration[-1]]]==LEAVES
    expected=parent_result['parameters_before_first_probe'];candidate_parameters=pg['parameters']
    assert len(expected)==len(candidate_parameters)==11512
    assert [r for r in expected if r[0]!=CAP]==[r for r in candidate_parameters if r[0]!=CAP]
    pilot=SIM/'qualification/joint586-s73001p00-tmax1ns-20260923-a/preparation.json';oldprep=json.loads(pilot.read_text())
    target_inventory=json.loads((PARENT/'population_inventory.json').read_text());assert target_inventory['full_parameter_count']==11512
    source_hashes=dict(provenance['source_hashes'],**{'sense.spice':CANDIDATE_SHA});controls=[]
    for leaf_name in LEAVES:
        leaf=PARENT/leaf_name;summary=json.loads((leaf/'summary.json').read_text());deck=(leaf/'probe.cir').read_text()
        assert summary['status']=='passed' and summary['kind']=='calibration' and summary['shunt_V']==.025 and summary['temperature_C']==25
        for tmax,label in [('0.2n','original-step'),('1n','tmax1ns')]:
            run='joint586-c45rz62-s73001-'+leaf_name+'-'+label+'-20260923-a';out=allocate_run(SIM,run)
            changed=deck_transform(deck,PARENT.name,leaf_name,run,tmax);(out/'probe.cir').write_text(changed);(out/'sense.spice').write_text(source)
            for name in ['trip.spice','bgr.spice','population_inventory.json']:(out/name).write_bytes((PARENT/name).read_bytes())
            (out/'declared_deck_difference.diff').write_text(''.join(difflib.unified_diff(deck.splitlines(True),changed.splitlines(True),fromfile='original '+leaf_name,tofile='candidate '+label)))
            (out/'declared_source_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),source.splitlines(True),fromfile='original baab',tofile='candidate C45 RZ62')))
            files=[leaf/n for n in ['probe.cir','summary.json','run.json','run.log','phase0.dat.gz','phase0.dat.archive.json']]+[PARENT/n for n in ['sense.spice','trip.spice','bgr.spice','population_inventory.json','provenance.json','summary.json']]
            files += [Path(__file__).resolve(),SIM/'test_joint586_c45rz62_anchors.py',SIM/'result_directory.py',pilot]
            prep=dict(status='prepared only; no source adoption or execution authority',run_id=run,original_leaf=leaf_name,tmax=tmax,seed=73001,codes=summary['codes'],
                deck_sha256=sha(out/'probe.cir'),source_hashes=source_hashes,inventory_sha256=sha(out/'population_inventory.json'),
                expected_runtime_identity=provenance['runtime_identity'],groups=oldprep['groups'],expected_old_parameters=expected,
                expected_candidate_parameters=candidate_parameters,expected_legacy27=oldprep['expected_legacy27'],changed_query=CAP,
                native_scale_law=pg['changed_cap_scale'],physical_candidate_summary_sha256=sha(candidate_dir/'summary.json'),physical_candidate_contract_sha256=sha(candidate_dir/'contract.json'),
                prospective_sampling=oldprep['prospective_sampling'],method_comparison_bounds=oldprep['bounds'],watchdog_s=1200,
                live_bindings_sha256={str(f.relative_to(ROOT)):sha(f) for f in files},
                scope='Only two declared main source geometry changes, candidate include path/output destination and optional TMAX. Identical primitive/query inventory does not mean unchanged circuit. No calibration rerun, population or physical/new-SENSE adoption.')
            (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n');controls.append(dict(run_id=run,leaf=leaf_name,tmax=tmax,codes=summary['codes'],preparation_sha256=sha(out/'preparation.json'),watchdog_s=1200))
    packet=dict(status='source-only prepared; runner/auditor, physical-source gates and ROOT review still required',candidate_source_sha256=CANDIDATE_SHA,controls=controls,
        selection='73001 first calibration endpoint p00 plus final two selected binary nodes p08/p09, independent of favorable new outcomes. Frozen old codes reused as diagnostic stimuli, not adopted new-source calibration.',
        independent_comparisons=['Candidate original0.2ns versus originalsource0.2ns: intentional circuit change, exact failures/decision shifts reported, no old criterion waiver.',
            'Candidate1ns versus candidate0.2ns: full11512 exact to own-source evidence and unchanged prospective engineering screen; no universal error bound.',
            'All11511 other fingerprints and27anchors exact to original, oneCMIM scale follows pinned native area law. XRZ geometry/resistance/parasitics intentionally differ despite unchanged random fingerprints.'],
        broad_qualification='not run; no300/30 source transfer or source adoption',expected_bulk_GiB=.30,
        original_inventory_scope='Unchanged target paths/models/queries only; source geometry changes separately explicit.')
    path=SIM/'qualification/joint586-c45rz62-calibration-anchors-20260923-a.json';assert not path.exists();path.write_text(json.dumps(packet,indent=2)+'\n');print(sha(path))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate-dir',type=Path,required=True);a=p.parse_args();prepare(a.candidate_dir)
