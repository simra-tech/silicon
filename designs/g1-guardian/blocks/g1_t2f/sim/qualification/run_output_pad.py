#!/usr/bin/env python3
"""Joint T2F/BGR C-PEX with stock TEMP_OUT pad and explicit external load."""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[3]
PDK=Path('/foss/pdks/ihp-sg13g2')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def edges(rows,col,level,rising=True):
    out=[]
    for a,b in zip(rows,rows[1:]):
        if (a[col]<level<=b[col]) if rising else (a[col]>level>=b[col]):
            out.append(a[0]+(level-a[col])*(b[0]-a[0])/(b[col]-a[col]))
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True)
    ap.add_argument('--tuple',choices=['nominal','slowcold','fasthot'],default='nominal')
    ap.add_argument('--external-load-pF',type=float,default=10)
    a=ap.parse_args();assert 0<=a.external_load_pF<=100
    h,m,r,c,v33,v12,temp={'nominal':('typ','tt','typ','typ',3.3,1.2,25),
                         'slowcold':('wcs','ss','wcs','wcs',3.0,1.08,-40),
                         'fasthot':('bcs','ff','bcs','bcs',3.6,1.32,125)}[a.tuple]
    out=HERE/'runs'/a.run_id;out.mkdir(exist_ok=False)
    shutil.copy(__file__,out/Path(__file__).name)
    sources={'bgr.spice':DESIGN/'blocks/g1_bgr/sim/postlayout/g1_bgr_pex.spice',
             't2f.spice':HERE.parent/'postlayout/g1_t2f_pex.spice',
             '.spiceinit':HERE.parent/'.spiceinit',
             'io.spi':PDK/'libs.ref/sg13g2_io/spice/sg13g2_io.spi',
             'route.json':DESIGN/'review/audits/temp-output-route-20260922-r2.json'}
    for name,path in sources.items():shutil.copy(path,out/name)
    io=(out/'io.spi').read_text()
    assert re.search(r'(?im)^\.subckt\s+sg13g2_IOPadOut16mA\s+pad\s+c2p\s+vdd\s+vss\s+iovdd\s+iovss\s*$',io)
    deck=(HERE.parent/'postlayout/decks/ftemp_ptat_T-40.cir').read_text().split('.control')[0]
    deck=deck.replace('.include ../../../../g1_bgr/xschem/g1_bgr.spice','.include bgr.spice')
    deck=deck.replace('.include ../g1_t2f_pex.spice','.include t2f.spice\n.include io.spi\n.lib '+str(PDK)+'/libs.tech/ngspice/models/cornerDIO.lib dio_tt')
    for kind,value in [('hbt',h),('mos',m),('res',r),('cap',c)]:
        default='tt' if kind=='mos' else 'typ';deck=deck.replace(' '+kind+'_'+default,' '+kind+'_'+value)
    deck=deck.replace('.temp -40',f'.temp {temp}').replace('Vdd vdd 0 dc 3.3',f'Vdd vdd 0 dc {v33}').replace('Vdd12 vdd12 0 dc 1.2',f'Vdd12 vdd12 0 dc {v12}').replace('1.01u 3.3',f'1.01u {v33}')
    assert 'Cout fout 0 50f' in deck
    network=f'''* Stock pad and estimated assembly pi RC replace50fF stand-in
Rroute fout pad_c2p 210.936
Croute_near fout 0 11.72035f
Croute_far pad_c2p 0 11.72035f
Vpad12 pad_vdd 0 {v12}
Vpad33 pad_iovdd 0 {v33}
Xpad temp_pad pad_c2p pad_vdd 0 pad_iovdd 0 sg13g2_IOPadOut16mA
'''
    if a.external_load_pF:network+=f'Cexternal temp_pad 0 {a.external_load_pF:g}p\n'
    deck=deck.replace('Cout fout 0 50f',network)
    deck+='''.control
set num_threads=1
set numdgt=15
set wr_singlescale
set wr_vecnames
save v(fout) v(pad_c2p) v(temp_pad) v(vref) i(vdd) i(vdd12) i(vpad33) i(vpad12)
tran 2n 32u
wrdata pad.dat v(fout) v(pad_c2p) v(temp_pad) v(vref) i(vdd) i(vdd12) i(vpad33) i(vpad12)
quit
.endc
.end
'''
    deck='* Joint BGR/T2F C-PEX with actual stock TEMP_OUT pad; explicit load sensitivity\n'+'\n'.join(deck.splitlines()[1:])+'\n'
    (out/'pad.cir').write_text(deck)
    result={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),
            'pdk_commit':(PDK/'COMMIT').read_text().strip(),'source_sha256':{name:sha(path) for name,path in sources.items()},
            'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
            'deck_sha256':sha(out/'pad.cir'),'tuple':a.tuple,'temperature_C':temp,'vdda_V':v33,'vdd_V':v12,
            'external_assumed_load_pF':a.external_load_pF,'route_estimated_R_ohm':210.936,'route_estimated_C_fF':23.4407,
            'limitations':'Actual stock output pad and joint BGR/T2F C-PEX; assembly route is geometry estimate. External capacitance is an explicit sensitivity assumption, not a declared instrument/board. Ideal separate pad/core supplies, ideal1V IPTAT termination. No package/bond inductance, mismatch, power-order, full terminal/reliability or pad DRC/LVS qualification.',
            'status':'not run'}
    save=lambda:(out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');save();start=time.monotonic()
    with (out/'pad.log').open('w') as log,(out/'pad.stderr').open('w') as err:
        try:rc=subprocess.run(['ngspice','-b','pad.cir'],cwd=out,stdout=log,stderr=err,timeout=300).returncode;timed=False
        except subprocess.TimeoutExpired:rc=None;timed=True
    result.update(solver_exit=rc,timed_out=timed,wall_seconds=time.monotonic()-start,status='not run' if timed else 'failed')
    try:
        with (out/'pad.dat').open() as f:next(f);rows=[list(map(float,line.split())) for line in f if line.strip()]
        log=(out/'pad.log').read_text()+'\n'+(out/'pad.stderr').read_text()
        result['saved_rows']=len(rows)
        result['last_saved_time_s']=rows[-1][0] if rows else None
        result['numerical_errors']=re.findall(r'(?im)^.*(?:Timestep too small|analysis aborted|simulation\(s\) aborted|^Error).*$' ,log)
        assert rc==0, 'solver exit is not zero'
        assert rows, 'no saved waveform rows'
        assert all(len(r)==9 and all(map(math.isfinite,r)) for r in rows), 'invalid/nonfinite saved waveform'
        assert not result['numerical_errors'], 'solver reported a numerical failure'
        assert abs(rows[-1][0]-32e-6)<1e-12, 'required32us endpoint not reached'
        result['status']='passed';clocks={}
        for name,col,rail in [('core',1,v12),('pad_input',2,v12),('pad_output',3,v33)]:
            ee=[t for t in edges(rows,col,rail/2) if 8e-6<=t<=31e-6]
            vv=[r[col] for r in rows if 8e-6<=r[0]<=31e-6]
            clocks[name]={'rising_edges':len(ee),'frequency_Hz':(len(ee)-1)/(ee[-1]-ee[0]) if len(ee)>1 else None,
                          'minimum_V':min(vv),'maximum_V':max(vv)}
        result['clock_windows']=clocks
        result['output_function_status']='passed' if all(c['rising_edges']>=10 for c in clocks.values()) and max(c['rising_edges'] for c in clocks.values())-min(c['rising_edges'] for c in clocks.values())<=1 else 'failed'
        powers={}
        for name,col,rail in [('core_vdda',5,v33),('core_vdd',6,v12),('pad_iovdd',7,v33),('pad_vdd',8,v12)]:
            rr=[r for r in rows if 8e-6<=r[0]<=31e-6]
            avg=-sum((b[0]-a[0])*(a[col]+b[col])/2 for a,b in zip(rr,rr[1:]))/(rr[-1][0]-rr[0][0])
            powers[name]={'mean_A':avg,'mean_power_W':avg*rail,'maximum_sampled_A':max(-r[col] for r in rr)}
        result['supply_windows']=powers
    except (OSError,ValueError,IndexError,StopIteration,AssertionError) as exc:result['analysis_error']=str(exc)
    save();print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','model_sha256','ngspice']},indent=2))


if __name__=='__main__':main()
