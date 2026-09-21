#!/usr/bin/env python3
"""Passive supply-impedance sensitivity; all L/C and load steps are assumptions."""
import argparse,csv,hashlib,itertools,json,math,shutil
from pathlib import Path
import numpy as np
import scipy
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),a.output/'runner.py')
def simulate(res,ind,cap,rise,refine=1):
    amp=1e-3;start=10e-9;hold=100e-9;fall=start+rise+hold;end=200e-9
    dt=min(rise/200,math.sqrt(ind*cap)/80 if ind and cap else rise/200,res*cap/80 if cap else rise/200)/refine
    t=np.linspace(0,end,math.ceil(end/dt)+1);u=amp*(np.clip((t-start)/rise,0,1)-np.clip((t-fall)/rise,0,1))
    if not cap:
        di=amp/rise*(((t>=start)&(t<start+rise)).astype(float)-((t>=fall)&(t<fall+rise)).astype(float))
        v=res*u+ind*di;peak=res*amp+ind*amp/rise;trough=-ind*amp/rise;poles=[]
    else:
        sys=signal.TransferFunction([ind,res] if ind else [res],[ind*cap,res*cap,1] if ind else [res*cap,1])
        _,v,_=signal.lsim(sys,U=u,T=t);peak=float(max(v));trough=float(min(v));poles=[{'real':float(z.real),'imag':float(z.imag)} for z in sys.poles]
        assert all(z['real']<0 for z in poles)
    plateau=float(np.interp(start+rise+90e-9,t,v));err=abs(plateau-res*amp)/(res*amp)
    assert err<1e-3,(res,ind,cap,rise,err)
    return {'R_ohm':res,'L_H_assumed':ind,'C_F_assumed':cap,'rise_s_assumed':rise,'load_step_A':amp,'hold_s':hold,'peak_drop_V':peak,'peak_rise_V':-trough,'plateau_drop_V':plateau,'plateau_relative_error':err,'sample_step_s':float(t[1]-t[0]),'samples':len(t),'poles':poles},t,u,v
rows=[];traces={};worst=None
for res,ind,cap,rise in itertools.product([20.,40.,80.],[0.,1e-9,5e-9,10e-9],[0.,10e-12,100e-12],[1e-9,10e-9]):
    row,t,u,v=simulate(res,ind,cap,rise);rows.append(row)
    if ind and cap and (worst is None or row['peak_drop_V']>worst['peak_drop_V']):worst=row
    if ind==5e-9 and cap==10e-12 and rise==1e-9:traces[res]=(t,u,v)
refined,_,_,_=simulate(worst['R_ohm'],worst['L_H_assumed'],worst['C_F_assumed'],worst['rise_s_assumed'],2)
convergence=abs(refined['peak_drop_V']-worst['peak_drop_V'])/refined['peak_drop_V'];assert convergence<5e-4
# Independent first-order RC step expression validates transfer-function sign/units.
t=np.linspace(0,100e-9,10001);_,calc,_=signal.lsim(signal.TransferFunction([40.],[40.*100e-12,1]),U=np.full(len(t),1e-3),T=t)
expected=.04*(1-np.exp(-t/(40*100e-12)));rc_error=float(max(abs(calc-expected)));assert rc_error<1e-10
summary={'scope':'Calculated passive lumped RLC sensitivity. No PDK transient, extracted L/C, measured waveform, package qualification or functional acceptance. R20/40/80ohm bracket modeled access scales; L,C,current amplitudes/edges are declared assumptions.','equation':'Z(s)=(R+sL)/(1+sRC+s^2LC); droop=Z*load_current. C is effective local rail-to-return capacitance.','versions':{'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'validation':{'all_DC_plateau_checks':'passed','first_order_RC_closed_form':'passed','RC_max_absolute_error_V':rc_error,'worst_RLC_peak_refinement_relative_error':convergence,'worst_RLC_case':worst},'step_scaling':[{'step_A':amp,'worst_drop_V':max(r['peak_drop_V'] for r in rows)*amp/1e-3,'best_drop_V':min(r['peak_drop_V'] for r in rows)*amp/1e-3} for amp in [.5e-3,1e-3,5e-3]],'whole_chip_IR_and_function':'not run'}
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
grid=np.linspace(0,150e-9,1501)
with (a.output/'representative_traces.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['time_ns','load_mA','drop_R20_mV','drop_R40_mV','drop_R80_mV']);values={r:np.interp(grid,t,v) for r,(t,u,v) in traces.items()};load=np.interp(grid,traces[20.][0],traces[20.][1])
    writer.writerows(zip(grid*1e9,load*1e3,values[20.]*1e3,values[40.]*1e3,values[80.]*1e3))
fig,axes=plt.subplots(2,1,figsize=(8,5),sharex=True,gridspec_kw={'height_ratios':[1,3]},layout='constrained');axes[0].plot(grid*1e9,load*1e3,color='black');axes[0].set_ylabel('Load step (mA)')
for r in [20.,40.,80.]:axes[1].plot(grid*1e9,values[r]*1e3,label=f'{r:g} ohm')
axes[1].set_ylabel('Incremental droop (mV)');axes[1].set_xlabel('Time (ns)');axes[1].legend();axes[0].set_title('Assumed L=5 nH, C=10 pF, 1 ns edges — analytical sensitivity')
for ax in axes:ax.grid(alpha=.25)
fig.savefig(a.output/'sensitivity.svg');fig.savefig(a.output/'sensitivity.png',dpi=160);plt.close(fig)
print(json.dumps({'case_count':len(rows),'validation':summary['validation'],'step_scaling':summary['step_scaling']},indent=2))
