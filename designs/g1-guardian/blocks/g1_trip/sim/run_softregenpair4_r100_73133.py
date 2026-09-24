"""Bounded same-seed candidate room binary calibration, then three heldout replays."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
from run_regenpair4_diagnostic import ROOT,SIM,PARENT,sha,trip_transform,parameter_gate,read_group,phase_parameters,runtime_gate,run_bounded,open_wave,archive_new_wave,analyze_wave,candidate_source
from run_regenpair4_r100_roomcal import serialized_replay as replay, sense_r100 as candidate_source
from result_directory import allocate_run

PARENT='joint586-calibration-s73133-20260922-a'
from soft_regenpair4 import trip_transform,parameter_gate
NAME='joint586-softregenpair4-r100-roomcal-s73133-20260923-a'


def make_deck(original,leaf,codes,rail):
    assert len(codes)==2 and all(type(c) is int and 0<=c<=255 for c in codes)
    assert original.count('setseed 73133\n')==1 and original.count('tran 0.2n 1.02u 0 0.2n\n')==1
    assert '.options klu' not in original.lower() and re.fullmatch(r'(?:c\d{2}|heldout-p27)',leaf)
    out=original.replace('qualification/'+PARENT+'/','qualification/'+NAME+'/')
    out,n=re.subn(r'(?m)^wrdata qualification/'+re.escape(NAME)+r'/p\d+/phase0.dat ',
                  'wrdata qualification/'+NAME+'/'+leaf+'/phase0.dat ',out);assert n==1
    def strip_bits(text):return re.sub(r'(?m)^(V[sh][0-7] [sh][0-7] 0 dc) .+$',r'\1 @BIT@',text)
    before=out
    for channel,code in zip(['s','h'],codes):
        for bit in range(8):
            out,n=re.subn(r'(?m)^V%s%d %s%d 0 dc .+$'%(channel,bit,channel,bit),
                'V%s%d %s%d 0 dc %s'%(channel,bit,channel,bit,format(rail,'.17g') if code&(1<<bit) else '0'),out)
            assert n==1
    assert strip_bits(before)==strip_bits(out)
    assert [x for x in before.splitlines() if x.startswith('.nodeset')]==[x for x in out.splitlines() if x.startswith('.nodeset')]
    return out


def wave_gate(blob,ref):
    header=blob.splitlines()[0].decode().split()
    assert header==ref['wave_header']
    data=np.array([list(map(float,l.split())) for l in blob.splitlines()[1:] if l.strip()])
    assert data.ndim==2 and data.shape[1]==len(header) and np.isfinite(data).all()
    assert np.all(np.diff(data[:,0])>0) and abs(data[-1,0]-1.02e-6)<1e-18
    return data


def prepare():
    parent=SIM/'qualification'/PARENT
    old=SIM/'qualification/joint586-regenpair4-r100-roomcal-s78101-20260923-a/contract.json'
    assert sha(old)=='7e88006e3b0c81414314949c743824f6e719a1f6b3f4cd1088a6bf12458f080f'
    packet=json.loads(old.read_text())
    assert all(sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    out=allocate_run(SIM,NAME)
    for name in ['bgr.spice','population_inventory.json']:(out/name).write_bytes((parent/name).read_bytes())
    (out/'sense.spice').write_text(candidate_source((parent/'sense.spice').read_text()))
    (out/'trip.spice').write_text(trip_transform((parent/'trip.spice').read_text()))
    refs={}
    bindings=dict(packet['bindings_sha256'])
    for leaf in ['p00','p27']:
        original=parent/leaf;row=json.loads((original/'summary.json').read_text())
        assert row['status']=='passed' and row['returncode']==0
        deck=(original/'probe.cir').read_text()
        assert '.param VDDA=3.3 VDD=1.2 VREF=1.04\n' in deck
        assert row['parameter_audit']['parameters_before']==row['parameter_audit']['parameters_after']
        with open_wave(original/'phase0.dat','rt') as stream:header=stream.readline().split()
        assert len(header)==18
        refs[leaf]=dict(wave_header=header,original_deck=deck,original_parameters=row['parameter_audit']['parameters_before'],
            legacy27=row['parameter_audit']['legacy27'],condition=['typical',row['temperature_C'],3.3,1.2,0.],
            shunt_V=row['shunt_V'],temperature_C=row['temperature_C'])
        for n in ['probe.cir','summary.json','run.json','run.log']:bindings[str((original/n).relative_to(ROOT))]=sha(original/n)
    assert refs['p00']['temperature_C']==25 and refs['p00']['shunt_V']==.025
    assert refs['p27']['temperature_C']==125 and refs['p27']['shunt_V']==.0255
    for n in ['sense.spice','trip.spice','bgr.spice','provenance.json','summary.json']:bindings[str((parent/n).relative_to(ROOT))]=sha(parent/n)
    for f in [Path(__file__).resolve(),SIM/'test_softregenpair4_r100_73133.py',SIM/'soft_regenpair4.py',SIM/'test_soft_regenpair4.py',old]:bindings[str(f.relative_to(ROOT))]=sha(f)
    packet.update(run_id=NAME,seed=73133,refs=refs,bindings_sha256=bindings,heldout_leaves=['p27'],
        parameter_scope='11495 unchanged;17 declared C45/hard+soft XM3/4 W/L/delvto/factuo native area laws. Input XM1/2 unchanged. No native-layout qualification/adoption.',
        source_hashes={n:sha(out/n) for n in ['sense.spice','trip.spice','bgr.spice']},inventory_sha256=sha(out/'population_inventory.json'),
        expected_runtime_identity=json.loads((parent/'provenance.json').read_text())['runtime_identity'],
        scope='One same73133 combined R100/hardarea4 plus soft regenerative XM3/4-only area4 own original ten-probe room calibration then original hot p27 with own codes. Original18 vectors/11512+27/.2ns/SPARSE/1200s. No old-code or population transfer. Original soft-positive failure retained.')
    with (out/'contract.json').open('x') as f:json.dump(packet,f,indent=2)
    print(str((out/'contract.json').relative_to(ROOT)),sha(out/'contract.json'))


def check_packet(path,digest):
    f=ROOT/path;assert sha(f)==digest;packet=json.loads(f.read_text());out=SIM/'qualification'/packet['run_id']
    assert packet['run_id']==NAME and packet['seed']==73133 and packet['watchdog_s']==1200
    assert all(sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in packet['source_hashes'].items())
    assert sha(out/'population_inventory.json')==packet['inventory_sha256']
    parent=SIM/'qualification'/PARENT
    assert (out/'trip.spice').read_text()==trip_transform((parent/'trip.spice').read_text())
    assert (out/'sense.spice').read_text()==candidate_source((parent/'sense.spice').read_text())
    assert (out/'bgr.spice').read_bytes()==(parent/'bgr.spice').read_bytes()
    return packet,out


def runtime(packet,image):
    pd=Path('/foss/pdks/ihp-sg13g2')
    r=dict(image_id_observed_by_host=image,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert r==packet['expected_runtime_identity'];return r


def inspect(leaf,packet,original,codes):
    ref=packet['refs'][original];rail=ref['condition'][3]
    assert (leaf/'probe.cir').read_text()==make_deck(ref['original_deck'],leaf.name,codes,rail)
    state=json.loads((leaf/'run.json').read_text());log=(leaf/'run.log').read_text();runtime_gate(state,log)
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S);g=packet['groups']
    before=read_group(section,'NON_BGR_BEFORE',g['NON_BGR'])+read_group(section,'BGR_BEFORE',g['BGR'])
    parsed=phase_parameters(section,g,before)
    params,laws=parameter_gate(before,parsed['parameters_after'],ref['original_parameters'],parsed['legacy27'],ref['legacy27'])
    with open_wave(leaf/'phase0.dat','rb') as f:blob=f.read()
    data=wave_gate(blob,ref)
    expected=18
    assert data.shape[1]==expected
    if expected==19:
        assert max(abs((data[:,17]+data[:,18])/2-ref['condition'][4]))<1e-12
        assert max(abs(data[:,17]-data[:,18]-ref['shunt_V']))<1e-12
    analysis=analyze_wave(data[:,:13].tolist(),packet['sampling']);assert analysis['sampling_status']=='passed'
    decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()}
    assert all(type(v) is bool for v in decisions.values())
    return dict(status='passed',run=NAME+'/'+leaf.name,codes=codes,decisions=decisions,parameter_audit=params,native_laws=laws,wave_analysis=analysis,
        wall_s=state['wall_s'],original_condition=original,decoded_wave_sha256=__import__('hashlib').sha256(blob).hexdigest(),wave_rows=len(data),deck_sha256=sha(leaf/'probe.cir'))


def probe(packet,out,original,leafname,codes,vector):
    leaf=out/leafname;leaf.mkdir();ref=packet['refs'][original]
    (leaf/'probe.cir').write_text(make_deck(ref['original_deck'],leafname,codes,ref['condition'][3]))
    with (leaf/'run.log').open('x') as stream:run_bounded(['ngspice','-b',str((leaf/'probe.cir').relative_to(SIM))],stream,leaf/'run.json',1200,cwd=SIM,interval_s=1)
    result=dict(status='failed',run=NAME+'/'+leafname,codes=codes,decisions={})
    try:
        result.update(inspect(leaf,packet,original,codes))
        if vector is not None:assert result['parameter_audit']['parameters_before']==vector
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result.update(status='failed',analysis_error=repr(error))
    (leaf/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if (leaf/'phase0.dat').exists():archive_new_wave(leaf/'phase0.dat')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','calibrate','heldout','audit-calibration','audit-heldout']);p.add_argument('--packet');p.add_argument('--packet-sha256');p.add_argument('--image-id');p.add_argument('--condition',choices=['p27']);a=p.parse_args()
    if a.mode=='prepare':prepare();return
    packet,out=check_packet(a.packet,a.packet_sha256);observed=runtime(packet,a.image_id)
    if a.mode=='calibrate':
        assert not (out/'calibration_state.json').exists()
        (out/'provenance.json').write_text(json.dumps(dict(packet_sha256=a.packet_sha256,runtime_identity=observed,runner_sha256=sha(Path(__file__)),arguments=sys.argv[1:]),indent=2)+'\n')
        records=[];vector=None
        for index in range(10):
            codes=[0,0] if index==0 else [255,255] if index==1 else replay(records).get('next_required_codes')
            if codes is None:break
            check_packet(a.packet,a.packet_sha256)
            row=probe(packet,out,'p00','c%02d'%index,codes,vector);records.append(row)
            if row['status']=='passed' and vector is None:vector=row['parameter_audit']['parameters_before']
            (out/'calibration_state.json').write_text(json.dumps(dict(status='running bounded binary diagnostic',records=records),indent=2)+'\n')
            if row['status']!='passed':break
        tree=replay(records);result=dict(status='passed' if tree['bracket_status']=='passed selected probes' else 'failed',tree=tree,parameters=vector,records=records,packet_sha256=a.packet_sha256)
        with (out/'calibration_complete.json').open('x') as stream:json.dump(result,stream,indent=2)
        raise SystemExit(0 if result['status']=='passed' else 1)
    complete=json.loads((out/'calibration_complete.json').read_text());assert complete['status']=='passed' and complete['packet_sha256']==a.packet_sha256
    if a.mode=='audit-calibration':
        records=[]
        for row in complete['records']:
            leaf=SIM/'qualification'/row['run'];r=inspect(leaf,packet,'p00',row['codes'])
            assert r==row==json.loads((leaf/'summary.json').read_text()) and r['parameter_audit']['parameters_before']==complete['parameters'];records.append(r)
        assert replay(records)==complete['tree']
        with (out/'calibration_audit.json').open('x') as stream:json.dump(dict(status='passed',calibration_sha256=sha(out/'calibration_complete.json'),packet_sha256=a.packet_sha256,leaf_count=len(records),codes=complete['tree']['fixed_residual_codes']),stream,indent=2)
        return
    calaudit=json.loads((out/'calibration_audit.json').read_text());assert calaudit['status']=='passed' and calaudit['calibration_sha256']==sha(out/'calibration_complete.json')
    codes=[complete['tree']['fixed_residual_codes'][k] for k in ['soft','hard']]
    if a.mode=='heldout':
        assert a.condition in packet['heldout_leaves']
        row=probe(packet,out,a.condition,'heldout-'+a.condition,codes,complete['parameters'])
        print(row['status'],row.get('decisions'));raise SystemExit(0 if row['status']=='passed' else 1)
    rows=[]
    for condition in packet['heldout_leaves']:
        leaf=out/('heldout-'+condition);r=inspect(leaf,packet,condition,codes)
        assert r==json.loads((leaf/'summary.json').read_text()) and r['parameter_audit']['parameters_before']==complete['parameters']
        rows.append(dict(condition=condition,original_residual_criteria_status='passed' if all(v is True for v in r['decisions'].values()) else 'failed',result=r))
    with (out/'heldout_audit.json').open('x') as stream:json.dump(dict(status='completed bounded diagnostic only',calibration_audit_sha256=sha(out/'calibration_audit.json'),records=rows),stream,indent=2)


if __name__=='__main__':main()



