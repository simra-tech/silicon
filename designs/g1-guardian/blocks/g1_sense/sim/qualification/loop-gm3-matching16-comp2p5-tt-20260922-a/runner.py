#!/usr/bin/env python3
"""Conditional main-feedback two-injection diagnostic with unchanged DC connectivity.
Tian et al. (2001), equations21–30: https://kenkundert.com/docs/cd2001-01.pdf
Other OTA/pedestal/reference loops stay closed; this is not global stability proof.
"""
import argparse,cmath,hashlib,json,math,os,re,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_wave(path):
    rows=[list(map(float,line.split())) for line in path.read_text().splitlines()[1:] if line.strip()]
    assert rows and all(len(r)==5 and all(map(math.isfinite,r)) for r in rows)
    return rows

def return_ratio(voltage,current):
    assert len(voltage)==len(current)
    points=[];previous_phase=None
    for v,i in zip(voltage,current):
        assert v[0]==i[0]
        A=complex(*i[1:3]);B=complex(*v[1:3]);C=complex(*i[3:5]);D=complex(*v[3:5])
        delta=A*D-B*C;T=(2*delta-A+D)/(1+A-D-2*delta)
        phase=math.degrees(cmath.phase(T))
        if previous_phase is not None:
            while phase-previous_phase>180:phase-=360
            while phase-previous_phase< -180:phase+=360
        previous_phase=phase
        points.append({'frequency_Hz':v[0],'T_real':T.real,'T_imag':T.imag,'magnitude':abs(T),'phase_unwrapped_deg':phase,'return_difference_magnitude':abs(1+T)})
    crossings=[]
    for a,b in zip(points,points[1:]):
        if a['magnitude']>=1>b['magnitude']:
            fraction=-math.log(a['magnitude'])/(math.log(b['magnitude'])-math.log(a['magnitude']))
            phase=a['phase_unwrapped_deg']+fraction*(b['phase_unwrapped_deg']-a['phase_unwrapped_deg'])
            crossings.append({'frequency_Hz':math.exp(math.log(a['frequency_Hz'])+fraction*math.log(b['frequency_Hz']/a['frequency_Hz'])),'conditional_phase_margin_deg':180+phase})
    return points,crossings

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True)
    p.add_argument('--source-run',help='Preserved SENSE candidate run containing sense_substrate_tied.spice; otherwise canonical baseline')
    p.add_argument('--mos',choices=['tt','ss','ff'],default='tt');p.add_argument('--res',choices=['typ','bcs','wcs'],default='typ')
    p.add_argument('--vdda',type=float,default=3.3);p.add_argument('--temperature',type=float,default=27)
    p.add_argument('--common-mode',type=float,default=0);p.add_argument('--shunt',type=float,default=.025)
    a=p.parse_args();out=SIM/'qualification'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    (out/'runner.py').write_text(Path(__file__).read_text())
    source=SIM/'qualification'/a.source_run/'sense_substrate_tied.spice' if a.source_run else SIM/'netlist/g1_sense.spice'
    text=source.read_text().replace(' sub! ',' vss ');(out/'baseline.spice').write_text(text)
    changed,n=re.subn(r'^(XOTA vp )vn( iptat .+)$',r'\1main_loop_e\2',text,flags=re.M);assert n==1
    changed=changed.replace('.ends','Vmain_probe main_loop_e vn dc 0 ac {pv}\nImain_probe vss main_loop_e dc 0 ac {pi}\n.ends',1)
    (out/'probe.spice').write_text(changed)
    base=(SIM/'tb_sense.cir').read_text().split('.control')[0]
    for key,value in {'VDDA':a.vdda,'VCM':a.common_mode-a.shunt/2,'MOS':'mos_'+a.mos,'RES':'res_'+a.res,'CAP':'cap_typ','TEMP':a.temperature}.items():base=base.replace('@@'+key+'@@',str(value))
    base=base.replace('Vsh shp cm dc 0 ac 1',f'Vsh shp cm dc {a.shunt} ac 0')
    base+='.option reltol=1e-5 vntol=1e-7 abstol=1e-14\n'
    meta={'arguments':sys.argv[1:],'git_head':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [source,SIM/'tb_sense.cir',Path(__file__)]},'derived_source_hashes':{name:sha(out/name) for name in ['baseline.spice','probe.spice']},'model_hashes':{str(p.relative_to(PDK)):sha(p) for p in (PDK/'libs.tech/ngspice/models').rglob('*') if p.is_file()},'method':'Tian2001eqs21–30; Vprobe=e-f, current0→e, if=-i(Vprobe); implementation adapted from repository BGR validated analytic two-injection anchor','method_source':'https://kenkundert.com/docs/cd2001-01.pdf','method_reference_artifact':'designs/g1-guardian/blocks/g1_bgr/sim/qualification/runs/bgr_stability_anchor_20260921_01','scope':'Conditional main OTA external resistor-feedback loop, pedestal/reference and all internal loops closed. Ideal VREF/PTAT, real conditioner50k/50k/hold cap and300fF output load, no actualBGR/pads/PEX. No proof cut breaks every return path; no global stability acceptance.','cases':[]}
    (out/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    ops={};data={};summary={'status':'not run to completion','cases':[]}
    for name,pv,pi in [('baseline',0,0),('voltage',1,0),('current',0,1)]:
        if (out/'PAUSE_REQUESTED').exists():summary['pause_before']=name;break
        src=out/('baseline.spice' if name=='baseline' else 'probe.spice')
        deck=base.replace('.include netlist/g1_sense.spice','.include '+str(src.relative_to(SIM)))+f'.param pv={pv} pi={pi}\n.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\necho OP_BEGIN\nprint v(isense) v(vped) v(vref_buf) v(xdut.vp) v(xdut.vn) i(vdd)\necho OP_END\n'
        if name!='baseline':deck+='ac dec 100 1 1g\nlet ifout=-i(v.xdut.vmain_probe)\nlet ve=v(xdut.main_loop_e)\nwrdata '+str((out/(name+'.dat')).relative_to(SIM))+' real(ifout) imag(ifout) real(ve) imag(ve)\n'
        deck+='echo QUALIFICATION_END\nquit 0\n.endc\n.end\n';dp=out/(name+'.cir');dp.write_text(deck)
        with (out/(name+'.log')).open('x') as log:state=run_bounded(['ngspice','-b',str(dp.relative_to(SIM))],log,out/(name+'.json'),120,cwd=SIM,env=dict(os.environ,OMP_NUM_THREADS='1'),metadata={'deck_sha256':sha(dp)},interval_s=.2)
        log=(out/(name+'.log')).read_text();err=[line for line in log.splitlines() if re.search(r'(?i)(^Error|timestep too small|doAnalyses:)',line)]
        match=re.search(r'OP_BEGIN\n(.*?)OP_END',log,re.S)
        row={'name':name,'watchdog_status':state['status'],'wall_s':state['wall_s'],'returncode':state['returncode'],'status':'failed','errors':err}
        if match:
            parsed=dict(re.findall(r'^([^=]+?)\s*=\s*([-+0-9.eE]+)\s*$',match[1],re.M))
            names=['v(isense)','v(vped)','v(vref_buf)','v(xdut.vp)','v(xdut.vn)','i(vdd)']
            values=[float(parsed[k]) for k in names if k in parsed]
            if len(values)==6 and all(map(math.isfinite,values)):ops[name]=values;row['operating_point']=values
        if state['status'] in ['timeout','interrupted']:row['status']='not run to completion'
        elif state['returncode']==0 and not err and name in ops and 'QUALIFICATION_END' in log:
            row['status']='passed'
            if name!='baseline':
                try:
                    wave=parse_wave(out/(name+'.dat'));assert wave[-1][0]>=.999e9;data[name]=wave
                except (OSError,ValueError,AssertionError):row['status']='failed'
        summary['cases'].append(row);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        if row['status']!='passed':break
    if len(data)==2 and len(ops)==3:
        differences={name:[abs(x-y) for x,y in zip(ops[name],ops['baseline'])] for name in ['voltage','current']}
        op_ok=all(max(values[:5])<=1e-6 and values[5]<=1e-9 for values in differences.values())
        points,crossings=return_ratio(data['voltage'],data['current'])
        (out/'return_ratio.json').write_text(json.dumps(points,indent=2)+'\n')
        summary.update(status='passed' if op_ok else 'failed DC-equivalence',DC_probe_equivalence_status='passed' if op_ok else 'failed',operating_point_absolute_differences=differences,unity_downcrossings=crossings,minimum_return_difference_magnitude=min(x['return_difference_magnitude'] for x in points),conditional_60deg_screen='passed' if op_ok and crossings and all(x['conditional_phase_margin_deg']>=60 for x in crossings) else 'failed',global_stability_status='not run')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
