"""One fixed hard-regenerative NMOS pair area4 hypothesis; original clock held."""
import argparse
import difflib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
import numpy as np
from prepare_joint586_c45rz62_anchors import ROOT, SIM, CAP, CANDIDATE_SHA, candidate_source
from run_joint586_c45rz62_anchors import sha, runtime_gate, open_wave, archive_new_wave, run_bounded, analyze_wave, compare
from run_joint586_c45rz62_knownfailures import input_observation
from run_joint586_transients import phase_parameters
from run_bgr_substitution_draw_audit import read_group
from c45rz62_native_scale import scale_interval
from result_directory import allocate_run

PARENT='joint586-fast-nodeset-calibration-s78101-20260923-a'
PREFIX='joint586-regenpair4-c45rz62-20260923-a'


def trip_transform(text):
    call='XCH icmp vth_hard cmp_clk_n cmp_hard cmp_hard_n vdd vss g1_cmp'
    assert text.count(call+'\n')==1 and 'g1_cmp_regenpair4' not in text
    block,=re.findall(r'(?m)^\.subckt g1_cmp inp inn clk q qb vdd vss\n.*?^\.ends\n',text,re.S)
    clone=block.replace('g1_cmp inp','g1_cmp_regenpair4 inp')
    for name,nodes in [('XM3','xn yn xp'),('XM4','yn xn xq')]:
        old=name+' '+nodes+' vss sg13_lv_nmos w=3u l=0.13u ng=1 m=1 mm_ok=1'
        new=old.replace('w=3u l=0.13u','w=6u l=0.26u')
        assert clone.count(old+'\n')==1;clone=clone.replace(old,new)
    result=text.replace(call,call+'_regenpair4')+'\n'+clone
    assert result[:-len('\n'+clone)].replace(call+'_regenpair4',call)==text
    assert 'XCLKI cmp_clk cmp_clk_n vdd vss g1_inv\n' in result
    return result


def deck_transform(text,leaf,run):
    pairs=[('qualification/'+PARENT+'/sense.spice','qualification/'+run+'/sense.spice'),
           ('qualification/'+PARENT+'/trip.spice','qualification/'+run+'/trip.spice'),
           ('qualification/'+PARENT+'/'+leaf+'/phase0.dat','qualification/'+run+'/phase0.dat')]
    original=text
    assert text.count('tran 0.2n 1.02u 0 0.2n\n')==1 and 'setseed 78101\n' in text and '.options klu' not in text.lower()
    for old,new in pairs:assert text.count(old)==1;text=text.replace(old,new)
    inverse=text
    for old,new in reversed(pairs):inverse=inverse.replace(new,old)
    assert inverse==original
    return text


def rounding_relation(old,new,kind,nominal):
    """Outward binary64 and printed-decimal enclosures, not analog tolerances."""
    down=lambda x:float(np.nextafter(float(x),-np.inf))
    up=lambda x:float(np.nextafter(float(x),np.inf))
    def hull(values):return [down(min(values)),up(max(values))]
    def exported(value):
        a=Decimal(value);half=Decimal(10)**a.as_tuple().exponent/2
        return hull([float(a-half),float(a+half)])
    a=exported(old);b=exported(new)
    # Invert rounded agauss nominal+deviation, preserve the same random draw.
    if kind in ['w','l']:
        deviation=hull([down(a[0])-nominal,up(a[1])-nominal])
        predicted=hull([2*nominal+x for x in deviation])
    else:
        center=1. if kind=='factuo' else 0.
        deviation=hull([down(a[0])-center,up(a[1])-center])
        # Width2 and length2 keep m,ng and random-call order: drawn area4, sigma1/2.
        scaled=hull([x/2 for x in deviation])
        predicted=hull([center+x for x in scaled])
    assert max(predicted[0],b[0])<=min(predicted[1],b[1]),(kind,old,new,predicted,b)
    return dict(old=old,new=new,predicted_binary64_interval=predicted,observed_binary64_interval=b)


def parameter_gate(before,after,old,legacy,oldlegacy):
    assert len(before)==len(after)==len(old)==11512 and before==after
    assert [r[0] for r in before]==[r[0] for r in old] and len({r[0] for r in before})==11512
    changed={CAP}
    laws={CAP:scale_interval(dict(old)[CAP],dict(before)[CAP],'45')}
    assert laws[CAP]['status']=='passed'
    for instance in ['xm3','xm4']:
        prefix='@n.xt.xch.%s.nsg13_lv_nmos'%instance
        for kind in ['w','l','delvto','factuo']:
            key=prefix+'['+kind+']';changed.add(key)
            nominal=3e-6 if kind=='w' else .13e-6
            laws[key]=rounding_relation(dict(old)[key],dict(before)[key],kind,nominal)
    assert len(changed)==9
    assert [r for r in before if r[0] not in changed]==[r for r in old if r[0] not in changed]
    assert legacy==oldlegacy and len(legacy)==27
    return dict(parameters_before=before,parameters_after=after,legacy27=legacy),laws


def prepare():
    parent=SIM/'qualification'/PARENT
    template=SIM/'qualification/joint586-c45rz62-knownfailure-s78101-p57-20260923-a/preparation.json'
    base=json.loads(template.read_text());provenance=json.loads((parent/'provenance.json').read_text())
    helper_names=['run_regenpair4_diagnostic.py','test_regenpair4_diagnostic.py','run_joint586_c45rz62_knownfailures.py','run_joint586_c45rz62_anchors.py',
        'prepare_joint586_c45rz62_anchors.py','run_joint586_transients.py','run_bgr_substitution_draw_audit.py','run_nominal_clock_probe.py',
        'compare_joint586_tmax_probe.py','c45rz62_native_scale.py','result_directory.py','wave_archive.py','.spiceinit']
    bindings={str((SIM/n).relative_to(ROOT)):sha(SIM/n) for n in helper_names}
    bindings[str(template.relative_to(ROOT))]=sha(template)
    controls=[]
    for index in [57,61]:
        leafname='p%d'%index;old=parent/leafname;summary=json.loads((old/'summary.json').read_text())
        assert summary['status']=='passed' and summary['returncode']==0 and summary['shunt_V']==.0255
        run=PREFIX+'-'+leafname;out=allocate_run(SIM,run)
        for name in ['bgr.spice','population_inventory.json']:(out/name).write_bytes((parent/name).read_bytes())
        (out/'sense.spice').write_text(candidate_source((parent/'sense.spice').read_text()))
        (out/'trip.spice').write_text(trip_transform((parent/'trip.spice').read_text()))
        deck=deck_transform((old/'probe.cir').read_text(),leafname,run);(out/'probe.cir').write_text(deck)
        for name in ['trip.spice','probe.cir']:
            prior=(parent/name if name=='trip.spice' else old/name).read_text()
            (out/(name+'.diff')).write_text(''.join(difflib.unified_diff(prior.splitlines(True),(out/name).read_text().splitlines(True),fromfile='original',tofile='isolated hard regenpair4 candidate')))
        with open_wave(old/'phase0.dat','rt') as stream:header=stream.readline().split()
        assert len(header)==19
        prep=dict(base,run_id=run,original_run=PARENT+'/'+leafname,codes=summary['codes'],condition=summary['condition'],
            shunt_V=summary['shunt_V'],temperature_C=summary['temperature_C'],wave_header=header,
            original_full11512=summary['parameter_audit']['parameters_before'],original_legacy27=summary['parameter_audit']['legacy27'],
            source_hashes={n:sha(out/n) for n in ['sense.spice','trip.spice','bgr.spice']},deck_sha256=sha(out/'probe.cir'),
            inventory_sha256=sha(out/'population_inventory.json'),bindings_sha256=dict(bindings),expected_runtime_identity=provenance['runtime_identity'],
            original_decisions=summary['decisions'],unchanged_expected_hard=True,
            inventory_scope='Same3500primitive identities/11512queries. Query inventory is not geometry. Hard XCH XM3/XM4 only: w3→6um and l0.13→0.26um, m1/ng1 held, drawn W/L held; all other TRIP geometry and original clock driver held. C45/R62 separately bound. Geometry changes may change short-channel behavior and capacitance, not noise-only isolation.')
        for n in ['probe.cir','summary.json','run.json','run.log']:
            prep['bindings_sha256'][str((old/n).relative_to(ROOT))]=sha(old/n)
        for n in ['sense.spice','trip.spice','bgr.spice','provenance.json']:
            prep['bindings_sha256'][str((parent/n).relative_to(ROOT))]=sha(parent/n)
        assert sha(out/'sense.spice')==CANDIDATE_SHA
        (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
        controls.append(dict(run_id=run,preparation_sha256=sha(out/'preparation.json'),watchdog_s=1200,original_expected=True,original_decision=summary['decisions']))
    packet=SIM/'qualification'/(PREFIX+'-execution.json');assert not packet.exists()
    packet.write_text(json.dumps(dict(controls=controls,bindings_sha256=bindings,scope='Two fixed failedlowrail/passedhighrail cold conditions; isolated hard XM3/4 area4+C45/R62. No canonical edits, no population/solver adoption. Original1200s/0.2ns/SPARSE/seed/rails/clocks/codes/criteria. Width/mismatch law and all11512 held except declared9 fields. No adaptive sizing variants.'),indent=2)+'\n')
    print(packet.name,sha(packet))


def source_gate(out,prep):
    original=SIM/'qualification'/prep['original_run'];parent=original.parent
    assert all(sha(ROOT/p)==v for p,v in prep['bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert (out/'trip.spice').read_text()==trip_transform((parent/'trip.spice').read_text())
    assert (out/'sense.spice').read_text()==candidate_source((parent/'sense.spice').read_text())
    assert (out/'probe.cir').read_text()==deck_transform((original/'probe.cir').read_text(),original.name,prep['run_id'])
    assert sha(out/'probe.cir')==prep['deck_sha256'] and sha(out/'population_inventory.json')==prep['inventory_sha256']
    return original


def inspect(out,prep,state,log):
    runtime_gate(state,log)
    original=source_gate(out,prep)
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S);g=prep['groups']
    before=read_group(section,'NON_BGR_BEFORE',g['NON_BGR'])+read_group(section,'BGR_BEFORE',g['BGR'])
    parsed=phase_parameters(section,g,before)
    params,laws=parameter_gate(before,parsed['parameters_after'],prep['original_full11512'],parsed['legacy27'],prep['original_legacy27'])
    with open_wave(out/'phase0.dat','rb') as f:blob=f.read()
    with open_wave(original/'phase0.dat','rb') as f:oldblob=f.read()
    names=blob.splitlines()[0].decode().split();assert names==prep['wave_header']==oldblob.splitlines()[0].decode().split()
    values=lambda b:np.array([list(map(float,line.split())) for line in b.splitlines()[1:] if line.strip()])
    data,old=values(blob),values(oldblob);observation=input_observation(data,prep)
    assert np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
    analysis=analyze_wave(data[:,:13].tolist(),prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
    prior=json.loads((original/'summary.json').read_text())
    decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()}
    return dict(numerical_status='passed',parameter_audit=params,mismatch_geometry_laws=laws,actual_input_observation=observation,
        wave_analysis=analysis,observed_decisions=decisions,original_frozen_code_residual_status='passed' if all(v is True for v in decisions.values()) else 'failed',
        intentional_cross_source_comparison=compare(old[:,:18],data[:,:18],names[:18],prior['wave_analysis'],analysis,prep['comparison_bounds']),
        exact_old_wave_bytes=blob==oldblob,exact_old_numeric=np.array_equal(old,data),exact_old_grid=np.array_equal(old[:,0],data[:,0]),wall_s=state['wall_s'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run','audit']);p.add_argument('--packet');p.add_argument('--packet-sha256');p.add_argument('--run-id');p.add_argument('--image-id');p.add_argument('--output');a=p.parse_args()
    if a.mode=='prepare':prepare();return
    packet=ROOT/a.packet;assert sha(packet)==a.packet_sha256;d=json.loads(packet.read_text())
    assert all(sha(ROOT/n)==v for n,v in d['bindings_sha256'].items())
    rows=[]
    for case in d['controls']:
        if a.mode=='run' and case['run_id']!=a.run_id:continue
        out=SIM/'qualification'/case['run_id'];assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text())
        if a.mode=='run':
            assert not (out/'run.json').exists()
            source_gate(out,prep)
            pd=Path('/foss/pdks/ihp-sg13g2')
            runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
            assert runtime==prep['expected_runtime_identity']
            assert all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items())
            (out/'runner.py').write_bytes(Path(__file__).read_bytes())
            (out/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,packet_sha256=a.packet_sha256,runner_sha256=sha(Path(__file__)),arguments=sys.argv[1:]),indent=2)+'\n')
            with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b',str((out/'probe.cir').relative_to(SIM))],stream,out/'run.json',1200,cwd=SIM,interval_s=1)
            result=dict(numerical_status='failed',original_frozen_code_residual_status='not run')
            try:result.update(inspect(out,prep,state,(out/'run.log').read_text()))
            except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result['analysis_error']=repr(error)
            (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
            if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
            print(result['numerical_status'],result['original_frozen_code_residual_status']);raise SystemExit(0 if result['numerical_status']=='passed' else 1)
        else:
            result=inspect(out,prep,json.loads((out/'run.json').read_text()),(out/'run.log').read_text())
            assert result==json.loads((out/'summary.json').read_text())
            rows.append(dict(run_id=case['run_id'],independent_reconstruction='passed',result=result))
    output=ROOT/a.output;assert not output.exists()
    output.write_text(json.dumps(dict(status='completed bounded hypothesis audit; no adoption',packet_sha256=sha(packet),records=rows),indent=2)+'\n')


if __name__=='__main__':main()
