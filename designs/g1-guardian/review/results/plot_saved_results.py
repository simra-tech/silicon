#!/usr/bin/env python3
"""Plot saved G1 simulation evidence only; never invokes a circuit simulator.
From repository root: flow/run.sh python3 designs/g1-guardian/review/results/plot_saved_results.py
"""
from pathlib import Path
import csv, hashlib, json, re, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT/'designs/g1-guardian/review/results'
B = Path('designs/g1-guardian/blocks')
plt.rcParams.update({'font.size':12,'axes.titlesize':12,'axes.labelsize':12,'legend.fontsize':10,
                     'figure.titlesize':14,'axes.spines.top':False,'axes.spines.right':False,
                     'savefig.dpi':180,'font.family':'DejaVu Sans'})
C=['#24689c','#c46523','#287d57','#8b4c87']
manifest={'generation_command':'flow/run.sh python3 designs/g1-guardian/review/results/plot_saved_results.py',
          'python':sys.version.split()[0],'matplotlib':matplotlib.__version__,'numpy':np.__version__,
          'simulation_status':'No new simulations run. All plots derived from saved simulated data.',
          'pdk_commit':'84374023ee8b4b126bebbba67fcbada0a9c0ff0b','simulation_tool':'ngspice 46', 'figures':[]}
sources=[]
def read(p):
    p=str(p); sources.append(p); return (ROOT/p).read_text()
def dat(p):
    read(p); return np.loadtxt(ROOT/p,skiprows=1)
def rows(p):return list(csv.DictReader(read(p).splitlines()))
def export(name,fig,data,columns,notes):
    fig.tight_layout(rect=[0,.065,1,.94]);fig.text(.01,.015,'SIMULATED • saved evidence • '+notes,fontsize=8,color='#444444')
    fig.savefig(OUT/f'{name}.png');fig.savefig(OUT/f'{name}.svg',metadata={'Date':None});plt.close(fig)
    with (OUT/f'{name}.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(columns);w.writerows(data)
    used=sorted(set(sources)); sources.clear()
    manifest['figures'].append({'name':name,'data_columns':columns,'notes':notes,
      'sources':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in used]})
def grid(ax):ax.grid(alpha=.2)
def blocks(p):
    text=read(p)
    return [(m.group(1),m.group(2)) for m in re.finditer(r'^== ([^\n]+)\n(.*?)(?=^== |\Z)',text,re.M|re.S)]

# 1. Reference temperature sweep: three distinct existing netlists.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('BGR • reference and PTAT current versus temperature')
data=[]
variants=[('Schematic','sim/results/temp_hbt_typ_mos_tt_res_typ_3.3.dat'),
          ('Capacitance PEX','sim/postlayout/results/temp_hbt_typ_mos_tt_res_typ_3.3.dat'),
          ('PEX + estimated wire R','sim/postlayout/results/wire_hbt_typ_mos_tt_res_typ_temp_3.3.dat')]
for i,(label,path) in enumerate(variants):
    a=dat(B/'g1_bgr'/path)
    for ax,j,scale in [(axs[0],1,1),(axs[1],2,1e6)]:ax.plot(a[:,0],a[:,j]*scale,label=label,color=C[i]);grid(ax)
    data.extend((label,*r[:4]) for r in a)
for ax in axs:ax.axvspan(125,175,color='#f6dfb2',alpha=.6);ax.set_xlabel('Temperature (°C)');ax.legend(loc='best')
axs[0].set_ylabel('VREF (V)');axs[1].set_ylabel('IPTAT (µA)')
export('01_bgr_temperature',fig,data,['model','temperature_C','vref_V','iptat_A','total_current_A'],'Nominal process, 3.3 V; shaded region >125 °C is model extrapolation.')

# 2. Startup: actual adaptive-step sampled waveform, not an interpolated synthetic response.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('BGR • startup with a 1 ms supply ramp')
data=[]
for i,(label,base) in enumerate([('Schematic','sim/results'),('Capacitance PEX','sim/postlayout/results')]):
    a=dat(B/'g1_bgr'/base/'startup_hbt_typ_mos_tt_res_typ_T27_3.0.dat')
    axs[0].plot(a[:,0]*1e3,a[:,1],label=label,color=C[i]);axs[1].plot(a[:,0]*1e3,a[:,1],label=label,color=C[i])
    data.extend((label,*r) for r in a)
axs[0].plot(a[:,0]*1e3,a[:,4],color='#777777',ls=':',label='Supply ramp');axs[0].set_xlim(0,3)
axs[1].set_xlim(.45,.65);axs[1].set_ylim(.75,1.06);axs[1].axhline(.93,ls=':',color='#777777',label='0.93 V threshold')
for ax in axs:ax.set_xlabel('Time (ms)');ax.set_ylabel('Voltage (V)');grid(ax);ax.legend()
export('02_bgr_startup',fig,data,['model','time_s','vref_V','iptat_A','pbias_V','vdd_V'],'27 °C, 0 → 3.0 V in 1 ms; right panel shows actual startup detail.')

# 3. T2F frequency and independently recalibrated residual, use only observed points.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('T2F revision 2 • frequency and two-point calibration')
data=[]
for i,(label,base) in enumerate([('Schematic','sim/results'),('Capacitance PEX','sim/postlayout/results')]):
    rr=rows(B/'g1_t2f'/base/'ftemp_summary.csv')
    a=sorted((float(r['deck'].split('_T')[1]),float(r['freq'])) for r in rr if r['deck'].startswith('ftemp_ptat_') and r['freq'])
    ts=np.array([t for t,f in a]);fs=np.array([f for t,f in a]);by=dict(a)
    slope=(by[100]-by[25])/75;err=(fs-by[25])/slope+25-ts
    axs[0].plot(ts,fs/1e6,'o-',label=label,color=C[i]);axs[1].plot(ts,err,'o-',label=label,color=C[i])
    data.extend((label,t,f,e,slope) for t,f,e in zip(ts,fs,err))
for ax in axs:ax.axvspan(125,175,color='#f6dfb2',alpha=.6);ax.set_xlabel('Temperature (°C)');grid(ax);ax.legend()
axs[0].set_ylabel('PTAT output frequency (MHz)');axs[1].set_ylabel('Temperature residual (°C)');axs[1].axhline(0,color='#777777',ls=':')
export('03_t2f_calibration',fig,data,['model','temperature_C','frequency_Hz','calibrated_error_C','fit_slope_Hz_per_C'],'25/100 °C fit per model; >125 °C extrapolated. Cold schematic runs aborted after measurements.')

# 4. OSC trim, same nominal supply and temperature, no interpolation claims between codes.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('OSC • trim range before and after capacitance extraction')
data=[]
for ax,model,p in [(axs[0],'Schematic',B/'g1_osc/sim/results_osc.txt'),(axs[1],'Capacitance PEX',B/'g1_osc/sim/postlayout/results_postlayout.txt')]:
    curves={}
    for tag,body in blocks(p):
        m=re.search(r'mos_(tt|ss|ff)_res_\w+_cap_\w+_1.2V_27C_code(\d+)$',tag)
        f=re.search(r'OSC f_MHz=\s*([\d.eE+-]+)',body)
        if m and f:curves.setdefault(m[1],{})[int(m[2])]=float(f[1])
    for i,corner in enumerate(['tt','ss','ff']):
        a=sorted(curves[corner].items());ax.plot(*zip(*a),'o-',label=corner.upper(),color=C[i]);data.extend((model,corner,k,f) for k,f in a)
    ax.axhline(10,color='#777777',ls=':',label='10 MHz target');ax.set_title(model);ax.set_xlabel('Trim code');ax.set_ylabel('Frequency (MHz)');ax.set_xticks([0,4,8,12,15]);grid(ax);ax.legend()
export('04_osc_trim',fig,data,['model','MOS_corner','trim_code','frequency_MHz'],'1.2 V / 27 °C; plotted markers are saved measurements; lines are visual guides only.')

# 5. SENSE dynamics directly from saved measured-value comparison table.
p=B/'g1_sense/sim/postlayout/results/compare.md';table=[]
for l in read(p).splitlines():
    if l.startswith('| mos_'):table.append([s.strip() for s in l.strip('|').split('|')])
selected=['mos_tt_res_typ_3.3V_-40C_cm0','mos_tt_res_typ_3.3V_27C_cm0','mos_tt_res_typ_3.3V_175C_cm0','mos_ff_res_bcs_3.3V_27C_cm0','mos_ss_res_wcs_3.3V_175C_cm0']
labels=['TT\n−40 °C','TT\n27 °C','TT\n175 °C*','FF/BCS\n27 °C','SS/WCS\n175 °C*']
fig,axs=plt.subplots(1,2,figsize=(10,4.8));fig.suptitle('SENSE • small-signal bandwidth and step overshoot')
data=[]
for ax,q,title,unit in [(axs[0],'-3 dB bandwidth [MHz]','Bandwidth','MHz'),(axs[1],'step overshoot [mV]','Overshoot','mV')]:
    for j,(model,col) in enumerate([('Schematic',2),('Capacitance PEX',3)]):
        vals=[float(next(r[col] for r in table if r[0]==tag and r[1]==q)) for tag in selected]
        ax.bar(np.arange(5)+(j-.5)*.34,vals,width=.34,label=model,color=C[j]);data.extend((tag,q,model,val) for tag,val in zip(selected,vals))
    ax.set_xticks(np.arange(5),labels);ax.set_title(title);ax.set_ylabel(unit);ax.set_ylim(0,ax.get_ylim()[1]*1.25);ax.legend();grid(ax)
export('05_sense_dynamics',fig,data,['run','quantity','model','value'],'3.3 V, common-mode 0 V. *175 °C is extrapolated. Bars are summary measurements, not waveforms.')

# 6. TRIP delay: commanded overdrive versus effective sampled overdrive are distinct columns.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('TRIP • comparator delay versus commanded overdrive')
data=[]
for tag,body in blocks(B/'g1_trip/sim/postlayout/results_postlayout.txt'):
    if '_cmp_delay_' not in tag:continue
    ax=axs[0] if 'mos_tt_' in tag else axs[1];model='Schematic' if tag.startswith('sch_') else 'Capacitance PEX'
    a=[]
    for m in re.finditer(r'DELAY od=\s*([\d.eE+-]+).*?od_eff_mV=\s*([\d.eE+-]+).*?td_ns=\s*([\d.eE+-]+)',body):
        od,eff,td=map(float,m.groups());a.append((od*1000,td));data.append((tag,model,od*1000,eff,td))
    a.sort();ax.semilogx(*zip(*a),'o-',label=model,color=C[model!='Schematic'])
for ax,title in zip(axs,['TT / 1.2 V / 27 °C','SS / 1.08 V / −40 °C']):
    ax.set_title(title);ax.set_xlabel('Commanded overdrive (mV)');ax.set_ylabel('Comparator delay (ns)');ax.set_xticks([1,5,50],['1','5','50']);grid(ax);ax.legend()
export('06_trip_delay',fig,data,['run','model','commanded_overdrive_mV','effective_overdrive_mV','delay_ns'],'5 MHz strobe, DAC code 128. Effective overdrive differs because of kickback; see CSV.')

# 7. GATE matched completed cases with full pad model. No-pad fallbacks intentionally excluded.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('GATE • fast-path delay with the IO pad and gate load')
data=[]
for j,(model,p) in enumerate([('Schematic',B/'g1_gate/sim/results_gate.txt'),('Capacitance PEX',B/'g1_gate/sim/postlayout/results_postlayout.txt')]):
    br=blocks(p)
    for ti,temp in enumerate([-40,27]):
        tag,body=next((tag,body) for tag,body in br if tag.endswith(f'mos_tt_3.3V_1.2V_{temp}C'))
        m=re.search(r'FASTPATH ns: hard_cmp->gate_core=\s*([\d.eE+-]+).*?->GATE 10%=\s*([\d.eE+-]+)',body)
        assert m,(tag,'missing measurement');core,pad=map(float,m.groups());data.append((model,temp,core,pad))
        for ax,val in zip(axs,[core,pad]):ax.bar(ti+(j-.5)*.34,val,.34,label=model if ti==0 else None,color=C[j])
for ax,title in zip(axs,['To gate_core','To GATE falling below 10%']):
    ax.set_title(title);ax.set_xticks([0,1],['−40 °C','27 °C']);ax.set_ylabel('Delay (ns)');ax.legend();grid(ax)
export('07_gate_delay',fig,data,['model','temperature_C','hard_cmp_to_core_ns','hard_cmp_to_GATE_10percent_ns'],'TT, 3.3 V IO / 1.2 V core. Complete matched cases only; failed extreme pad cases omitted, not passed.')

# 8. DOSE leakage table: first (default HV/LV) section only, valid-temperature points.
txt=read(B/'g1_dose/sim/results_variants.md').split('## g1_dose_pair_nw:')[0]
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('DOSE default HV/LV pair • pre-irradiation leakage baseline')
data=[]
for i,corner in enumerate(['mos_tt','mos_ss','mos_ff']):
    a=[]
    for l in txt.splitlines():
        if l.startswith('| '+corner+' |'):
            r=[s.strip() for s in l.strip('|').split('|')]
            if 'extrapolated' in r[1]:continue
            t,hv,lv,ratio=map(float,r[1:5]);a.append((t,hv,lv,ratio));data.append((corner,t,hv,lv,ratio))
    a=np.array(sorted(a));axs[0].semilogy(a[:,0],a[:,1],'^--',label=corner[4:].upper()+' HV',color=C[i]);axs[0].semilogy(a[:,0],a[:,2],'o-',label=corner[4:].upper()+' LV',color=C[i]);axs[1].semilogy(a[:,0],a[:,3],'o-',label=corner[4:].upper(),color=C[i])
for ax in axs:ax.set_xlabel('Temperature (°C)');grid(ax);ax.legend(ncol=2 if ax==axs[0] else 1)
axs[0].set_ylabel('Drain current (A)');axs[1].set_ylabel('LV/HV current ratio')
export('08_dose_leakage',fig,data,['MOS_corner','temperature_C','HV_current_A','LV_current_A','LV_over_HV_ratio'],'VGS=0, VDS=0.1 V. No radiation or pad-leakage model; these are device-only simulated currents.')

# 9. DUT actual Gummel sweeps at characterized temperatures, retain full data in CSV.
fig,axs=plt.subplots(1,2,figsize=(10,4.5));fig.suptitle('DUT • Gummel curves and current gain of one npn13G2')
data=[]
for i,temp in enumerate([-40,27,85,125]):
    code='m40' if temp==-40 else f'p{temp}'
    a=dat(B/f'g1_dut/sim/decks/hbt_typ_T{code}C_gummel.dat')
    axs[0].semilogy(a[:,0],a[:,1],color=C[i],label=f'{temp} °C collector');axs[0].semilogy(a[:,0],a[:,2],color=C[i],ls='--')
    axs[1].semilogx(a[:,1],a[:,3],color=C[i],label=f'{temp} °C');data.extend((temp,*r) for r in a)
axs[0].set_xlim(.4,.95);axs[0].set_ylim(1e-14,1e-2);axs[0].set_xlabel('Base-emitter voltage (V)');axs[0].set_ylabel('Current (A)');axs[0].legend()
axs[1].set_xlim(1e-9,1e-3);axs[1].set_xlabel('Collector current (A)');axs[1].set_ylabel('Current gain β');axs[1].legend()
for ax in axs:grid(ax)
export('09_dut_gummel',fig,data,['temperature_C','VBE_V','collector_current_A','base_current_A','beta'],'Typical HBT, Nx=1, VCB=0. Solid = IC; dashed = IB (left). Plotting recorded data, not new runs.')

(OUT/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Wrote {len(manifest["figures"])} figures, PNG + SVG + CSV, with source hashes.')
