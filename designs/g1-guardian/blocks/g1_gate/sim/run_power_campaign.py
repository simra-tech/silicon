#!/usr/bin/env python3
"""Detailed IO-pad power-order screening, with bounded solver and saved vectors.

Uses the existing 5 nF/10 ohm external gate stand-in, not a real FET.
Safety criterion for EN-low intervals: both gate and gfet stay below 1 V.
"""
import argparse
import datetime
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded, atomic_json
PDK=Path(os.environ.get('PDK_ROOT','/foss/pdks'))/'ihp-sg13g2'
SEQUENCES={
    'io_first': ('0 0 1u 0 3u 3.3 16u 3.3','0 0 5u 0 7u 1.2 16u 1.2'),
    'core_first': ('0 0 5u 0 7u 3.3 16u 3.3','0 0 1u 0 3u 1.2 16u 1.2'),
    'simultaneous': ('0 0 1u 0 3u 3.3 16u 3.3','0 0 1u 0 3u 1.2 16u 1.2'),
    'missing_core': ('0 0 1u 0 3u 3.3 16u 3.3','0 0 16u 0'),
    'missing_io': ('0 0 16u 0','0 0 1u 0 3u 1.2 16u 1.2'),
    'core_brownout': ('0 3.3 16u 3.3','0 1.2 5u 1.2 7u 0.2 9u 0.2 11u 1.2 16u 1.2'),
    'io_brownout': ('0 3.3 5u 3.3 7u 0.5 9u 0.5 11u 3.3 16u 3.3','0 1.2 16u 1.2'),
    'core_off_first': ('0 3.3 10u 3.3 12u 0 16u 0','0 1.2 5u 1.2 7u 0 16u 0'),
    'io_off_first': ('0 3.3 5u 3.3 7u 0 16u 0','0 1.2 10u 1.2 12u 0 16u 0'),
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cases',nargs='*',default=['io_first','core_first'])
    ap.add_argument('--netlist',choices=['sch','pex'],default='pex')
    ap.add_argument('--image-id',required=True)
    ap.add_argument('--timeout',type=float,default=300)
    ap.add_argument('--en',choices=['low','late'],default='low')
    ap.add_argument('--full',action='store_true',help='four temperatures and three correlated contract rail pairs')
    ap.add_argument('--corner',choices=['tt','ss','ff'],default='tt')
    ap.add_argument('--ramp-scales',type=float,nargs='+',default=[1.0])
    ap.add_argument('--accuracy',choices=['baseline','tight'],default='baseline')
    ap.add_argument('--pad',choices=['out','tristate','buffered_analog'],default='out',help='isolated unadopted pad/driver candidates; delivered design remains out')
    a=ap.parse_args()
    if a.timeout<=0 or any(c not in SEQUENCES for c in a.cases) or any(not 0.1<=s<=10 for s in a.ramp_scales): ap.error('invalid timeout, sequence or ramp scale')
    tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=HERE/'campaigns'/tag;out.mkdir(parents=True,exist_ok=False)
    net=HERE/('netlist/g1_gate.spice' if a.netlist=='sch' else 'postlayout/g1_gate_pex.spice')
    ios=PDK/'libs.ref/sg13g2_io/spice/sg13g2_io.spi'
    md=dict(options=vars(a),fixture='5nF + 10ohm + 10kohm pulldown; real FET not run',
        image_id=a.image_id,pdk_commit=(PDK/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),net,HERE/'tb_gate_pwr.cir',HERE/'.spiceinit']},
        io_sha256=sha(ios),
        model_sha256={str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').rglob('*')) if p.is_file()},
        git_revision=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    atomic_json(out/'campaign.json',dict(md,status='running',cases=[]))
    results=[]
    if a.pad=='buffered_analog':
        candidate=HERE/'candidates/io_buffer/driver.spice'
        md['source_sha256'][str(candidate.relative_to(ROOT))]=sha(candidate)
        snapshot=out/'candidate_source.spice';snapshot.write_bytes(candidate.read_bytes());candidate=snapshot
    points=itertools.product(a.cases,[-40,27,85,125] if a.full else [27],[(1.08,3.0),(1.2,3.3),(1.32,3.6)] if a.full else [(1.2,3.3)],a.ramp_scales)
    for sequence,temp,(vdd,vdda),scale in points:
        case=f'{sequence}_{a.corner}_{temp}_{vdd}_{vdda}_ramp{scale:g}'
        def scaled(pwl,rail,nominal):
            tokens=pwl.split()
            return ' '.join(f'{float(t.rstrip("u"))*scale:g}u' if i%2==0 else f'{float(t)*rail/nominal:g}' for i,t in enumerate(tokens))
        pa,pd=SEQUENCES[sequence]
        pa=scaled(pa,vdda,3.3);pd=scaled(pd,vdd,1.2)
        en=scaled('0 0 16u 0' if a.en=='low' else '0 0 9u 0 9.1u 3.3 16u 3.3',vdda,3.3)
        stop=16e-6*scale
        deck=(HERE/'tb_gate_pwr.cir').read_text().split('.control')[0]
        for key,value in {'@@ORDER@@':case,'@@PWLA@@':pa,'@@PWLD@@':pd,'@@ENPWL@@':en,'@@RPD@@':'10k'}.items(): deck=deck.replace(key,value)
        deck=deck.replace('.include netlist/g1_gate.spice','.include '+str(net))
        if a.pad=='tristate':deck=deck.replace('XPG gate gate_core vdd 0 vdda 0 sg13g2_IOPadOut30mA','XPG gate gate_core vdd vdd 0 vdda 0 sg13g2_IOPadTriOut30mA')
        if a.pad=='buffered_analog':
            deck=deck.replace('XPG gate gate_core vdd 0 vdda 0 sg13g2_IOPadOut30mA',f'.include {candidate}\nXreceiver gate_core padres vdda 0 g1_io_buffer_candidate\nXPG gate padres vdd 0 vdda 0 sg13g2_IOPadAnalog')
        deck=deck.replace('mos_tt','mos_'+a.corner).replace('dio_tt','dio_'+a.corner).replace('.temp 27',f'.temp {temp}')
        if a.accuracy=='tight':deck=deck.replace('reltol=0.005','reltol=1e-5').replace('abstol=1e-9','abstol=1e-14').replace('vntol=1e-5','vntol=1e-7').replace('chgtol=1e-13','chgtol=1e-14')
        waves=out/(case+'.tsv')
        deck+=f'\n.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\ntran {5*scale:g}n {16*scale:g}u\n'
        deck+='wrdata '+str(waves)+' v(gate) v(gfet) v(gate_core) v(en_core) v(vdd) v(vdda) i(vdda) i(vdd)\n'
        if a.pad=='buffered_analog':deck+=f'wrdata {out/(case+"_candidate.tsv")} v(xreceiver.sense) v(padres) v(gate_core) v(vdda) v(vdd) i(vdda) i(vdd)\n'
        deck+='let endpoint=time[length(time)-1]\necho ENDPOINT $&endpoint\nrusage all\n.endc\n.end\n'
        dp=out/(case+'.cir');dp.write_text(deck)
        with (out/(case+'.log')).open('x') as log:
            result=run_bounded(['ngspice','-b',str(dp)],log,out/(case+'.json'),a.timeout,cwd=HERE,metadata=dict(md,case=case,deck_sha256=sha(dp)),interval_s=2)
        result['electrical_acceptance']='not run'
        text=(out/(case+'.log')).read_text()
        bad=re.search(r'Timestep too small|simulation aborted|doAnalyses:|^Error:',text,re.M|re.I)
        try:
            with waves.open() as f:
                header=f.readline().split()
                if header!=['time','v(gate)','v(gfet)','v(gate_core)','v(en_core)','v(vdd)','v(vdda)','i(vdda)','i(vdd)']: raise ValueError('unexpected vectors')
                data=[list(map(float,line.split())) for line in f if line.strip()]
            if len(data)<2 or any(len(r)!=9 or not all(map(math.isfinite,r)) for r in data): raise ValueError('invalid rows')
            if data[0][0]!=0 or abs(data[-1][0]-stop)>1e-12 or any(y[0]<x[0] for x,y in zip(data,data[1:])):raise ValueError('incomplete endpoint/time')
            if bad or result['status']!='completed':raise ValueError('solver incomplete/error')
            end=stop if a.en=='low' else 8.9e-6*scale
            safe=[r for r in data if r[0]<=end]
            result['metrics']={'gate_max_EN_low_V':max(r[1] for r in safe),'gfet_max_EN_low_V':max(r[2] for r in safe),'gate_end_V':data[-1][1],'end_s':data[-1][0]}
            result['electrical_acceptance']='passed' if max(result['metrics']['gate_max_EN_low_V'],result['metrics']['gfet_max_EN_low_V'])<1 else 'failed'
            if a.en=='late' and sequence in ['core_first','io_first','simultaneous']:
                result['metrics']['late_enable_high_pass']=data[-1][1]>2.5 and data[-1][2]>2.5
                if not result['metrics']['late_enable_high_pass']:result['electrical_acceptance']='failed'
            result['completion']='passed'
        except (OSError,ValueError) as exc:
            result['completion']='not run to completion' if result['status'] in ['timeout','interrupted'] else 'failed'
            result['acceptance_error']=str(exc)
        atomic_json(out/(case+'.json'),result)
        results.append({k:result.get(k) for k in ['case','status','returncode','wall_s','completion','electrical_acceptance','metrics','acceptance_error']})
        atomic_json(out/'campaign.json',dict(md,status='running',cases=results))
        print(case,json.dumps(results[-1]),flush=True)
    atomic_json(out/'campaign.json',dict(md,status='completed',cases=results))
    print('Evidence',out.relative_to(ROOT),flush=True)
    if any(r['completion']!='passed' or r['electrical_acceptance']!='passed' for r in results):raise SystemExit(1)

if __name__=='__main__':main()
