"""Source-only original-method references for four known electrical counterexamples."""
import difflib
import json
from pathlib import Path
from prepare_joint586_c45rz62_anchors import ROOT,SIM,CANDIDATE_SHA,candidate_source,CAP
from prepare_joint586_tmax_probe import OLD,sha
from wave_archive import open_wave

CASES=[(73023,'joint586-calibration-s73023-20260922-a','p26',125,.0245,False),
       (73073,'joint586-calibration-s73073-20260922-a','p26',125,.0245,False),
       (78101,'joint586-fast-nodeset-calibration-s78101-20260923-a','p57',-40,.0255,True),
       (78101,'joint586-fast-nodeset-calibration-s78101-20260923-a','p59',125,.0255,True)]


def transform(original,parent,leaf,destination,seed):
    source='.include qualification/'+parent+'/sense.spice';newsource='.include qualification/'+destination+'/sense.spice'
    oldoutput='qualification/'+parent+'/'+leaf+'/phase0.dat';newoutput='qualification/'+destination+'/phase0.dat'
    assert original.count(OLD)==1 and original.count('setseed %d\n'%seed)==1 and '.options klu' not in original.lower()
    assert original.count(source)==original.count(oldoutput)==1
    result=original.replace(source,newsource).replace(oldoutput,newoutput)
    assert result.replace(newsource,source).replace(newoutput,oldoutput)==original
    return result


def main():
    output=SIM/'qualification/joint586-c45rz62-knownfailures-prepared-20260923-a';assert not output.exists();output.mkdir()
    source=SIM/'qualification/joint586-c45rz62-s73001-p00-original-step-20260923-a/sense.spice';assert sha(source)==CANDIDATE_SHA
    records=[]
    for seed,parentname,leafname,temp,shunt,expected in CASES:
        parent=SIM/'qualification'/parentname;leaf=parent/leafname;summary=json.loads((leaf/'summary.json').read_text())
        assert summary['status']=='passed' and summary['watchdog_status']=='completed' and summary['returncode']==0 and not summary['errors']
        assert summary['kind']=='residual' and summary['temperature_C']==temp and summary['shunt_V']==shunt
        assert summary['decisions']['hard'] is not expected
        parameters=summary['parameter_audit'];assert parameters['parameters_before']==parameters['parameters_after'] and len(parameters['parameters_before'])==11512
        assert candidate_source((parent/'sense.spice').read_text())==source.read_text()
        run='joint586-c45rz62-knownfailure-s%d-%s-20260923-a'%(seed,leafname);old=(leaf/'probe.cir').read_text();new=transform(old,parentname,leafname,run,seed)
        assert [l for l in new.splitlines() if l.lower().startswith('.nodeset')]==[l for l in old.splitlines() if l.lower().startswith('.nodeset')]
        with open_wave(leaf/'phase0.dat','rt') as f:header=f.readline().split()
        (output/(run+'.cir')).write_text(new)
        (output/(run+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original failed electrical condition',tofile='candidate source path/output only')))
        bindings=[leaf/n for n in ['probe.cir','summary.json','run.json','run.log','phase0.dat.gz','phase0.dat.archive.json']]+[parent/n for n in ['provenance.json','sense.spice','trip.spice','bgr.spice','population_inventory.json']]
        records.append(dict(seed=seed,run_id=run,original_run=parentname+'/'+leafname,temperature_C=temp,shunt_V=shunt,codes=summary['codes'],condition=summary.get('condition'),
            original_decisions=summary['decisions'],unchanged_expected_hard=expected,watchdog_s=1200,original_tmax='0.2ns',solver='original SPARSE',
            original_nodesets=[l for l in old.splitlines() if l.lower().startswith('.nodeset')],wave_header=header,
            original_full11512=parameters['parameters_before'],original_legacy27=parameters['legacy27'],
            candidate_parameter_gate='Own BEFORE/AFTER all11512 exact; held11511+27 exact to original; only mainCMIM scale may change under pinned native69/45 law. Never guess the printed new scale.',
            changed_query=CAP,deck_sha256=sha(output/(run+'.cir')),bindings_sha256={str(f.relative_to(ROOT)):sha(f) for f in bindings}))
    result=dict(status='prepared references only; runner, independent audit, tests, ROOT source disposition and runtime lease not run',records=records,
        candidate_source_sha256=CANDIDATE_SHA,candidate_source_repository_path=str(source.relative_to(ROOT)),preparer_sha256=sha(Path(__file__)),
        scope='Four exact known failed residual conditions at original frozen codes/method. Candidate circuit behavior and original pass/fail predicates are reported separately. A replay is not new-source calibration or population qualification. No1ns or0.5ns candidate arms.',
        release_prerequisites=['Candidate native stock/source/port gates','Three original-step candidate anchors independently audited','Bounded source/runtime/full-vector harness review and explicit CPU lease'],
        no_stop_or_adoption=True)
    path=output/'contract.json';path.write_text(json.dumps(result,indent=2)+'\n');print(sha(path))


if __name__=='__main__':main()
