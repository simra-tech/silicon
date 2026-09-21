#!/usr/bin/env python3
"""Gate/pad + vendor-FET characterization; assumed board loads, not board qualification."""
import argparse,datetime,hashlib,json,math,os,re,subprocess,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded,atomic_json
MODEL_SHA='c5572438f1a79c8e9f48cfcf5a8d152daafdad8e8ec26ac30f807f0211edf2df'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--model',required=True,type=Path);ap.add_argument('--image-id',required=True);ap.add_argument('--bus',type=float,default=5);ap.add_argument('--current',type=float,default=1);ap.add_argument('--inductance',type=float,default=1e-7);ap.add_argument('--trip-us',type=float,default=2);ap.add_argument('--stop-us',type=float,default=30);ap.add_argument('--timeout',type=float,default=300)
 ap.add_argument('--corner',choices=['tt','ss','ff'],default='tt');ap.add_argument('--temp',type=float,default=27)
 ap.add_argument('--vdd',type=float,default=1.2);ap.add_argument('--vdda',type=float,default=3.3);ap.add_argument('--gate-r',type=float,default=10)
 ap.add_argument('--power-sequence',choices=['none','core_first','io_first','io_off_first','core_off_first'],default='none',help='EN-low real-FET rail sequence instead of trip fixture')
 ap.add_argument('--method',choices=['trap','gear'],default='gear');ap.add_argument('--accuracy',choices=['baseline','tight'],default='baseline')
 ap.add_argument('--maxord',type=int,choices=[1,2],default=2,help='integration order cap; order1 is a damping diagnostic requiring separate convergence qualification')
 ap.add_argument('--pad',choices=['out','buffered_analog'],default='out',help='unadopted IO-powered buffer + protected analogpad candidate')
 ap.add_argument('--maxstep-ps',type=float,default=1000)
 ap.add_argument('--set-node',choices=['n_34','n_35']);ap.add_argument('--set-charge-fc',type=float,default=-1000);ap.add_argument('--set-us',type=float,default=8)
 a=ap.parse_args()
 if sha(a.model)!=MODEL_SHA:ap.error('vendor model SHA mismatch')
 if not 0<a.bus<=12 or not 0<a.current<=4 or not 0<a.inductance<=1e-4:ap.error('outside declared characterization range')
 if not 2<=a.trip_us<a.stop_us or a.stop_us>300:ap.error('invalid timing')
 if not 1.08<=a.vdd<=1.32 or not 3.0<=a.vdda<=3.6 or not -40<=a.temp<=125 or not 0<a.gate_r<=100:ap.error('outside supported driver screening range')
 if a.power_sequence!='none' and a.stop_us<16:ap.error('power sequence requires at least16us')
 if a.set_node and (a.power_sequence!='none' or not a.trip_us+1<a.set_us<a.stop_us-1):ap.error('SET requires settled tripped state before injection')
 if not 1<=a.maxstep_ps<=1000:ap.error('maxstep must be1..1000ps')
 trip=a.trip_us*1e-6;stop=a.stop_us*1e-6
 out=HERE/'campaigns'/('fet_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
 init=(HERE/'.spiceinit').read_text();(out/'.spiceinit').write_text(init)
 net=HERE/'postlayout/g1_gate_pex.spice';text=(HERE/'tb_gate.cir').read_text().split('.control')[0]
 for x,y in {'@@VDDA@@':str(a.vdda),'@@VDD@@':str(a.vdd),'@@MOS@@':'mos_'+a.corner,'@@TEMP@@':str(a.temp)}.items():text=text.replace(x,y)
 text=text.replace('.include netlist/g1_gate.spice','.include '+str(net))
 candidate=None
 if a.pad=='buffered_analog':
  candidate=out/'candidate_source.spice';candidate.write_bytes((HERE/'candidates/io_buffer/driver.spice').read_bytes())
  text=text.replace('XPG gate gate_core vdd 0 vdda 0 sg13g2_IOPadOut30mA',f'.include {candidate}\nXreceiver gate_core padres pad_a 0 g1_io_buffer_candidate\nXPG gate padres pad_d 0 pad_a 0 sg13g2_IOPadAnalog')
 text=text.replace('method=gear','method='+a.method)
 text=text.replace('itl4=100',f'itl4=100 maxord={a.maxord}')
 if a.accuracy=='tight':text=text.replace('reltol=0.005','reltol=1e-5').replace('abstol=1e-9','abstol=1e-14').replace('vntol=1e-5','vntol=1e-7').replace('chgtol=1e-13','chgtol=1e-14')
 text=re.sub(r'^Ven .*$', f'Ven en_core 0 pwl(0 0 0.2u 0 0.202u {a.vdd} {a.stop_us:g}u {a.vdd})',text,flags=re.M)
 text=re.sub(r'^Vtrip .*$', f'Vtrip trip_d 0 pwl(0 0 {a.trip_us:g}u 0 {a.trip_us+.002:g}u {a.vdd} {a.stop_us:g}u {a.vdd})',text,flags=re.M)
 for name in ['Vclr','Vhard','Vfast']:text=re.sub(r'^'+name+r' (\S+) 0 .*$',name+r' \1 0 0',text,flags=re.M)
 text=text.replace('Cgate gfet 0 5n',f'''* Vendor model unchanged; D/G/S pin order. Board loads are engineering assumptions.
* Compatibility wrapper supplies the vendor's four unchanged constants because
* legacy PSpice .PARAM name value declarations are not resolved by this parser.
.param ptrc1=3.25e-3 ptrc2=9.0e-6 pwidth=1.3392864 perim=2.7
.incpslt {a.model.resolve()}
Vbus bus 0 {a.bus:g}
Rload bus load {a.bus/a.current:g}
Lload load drain {a.inductance:g}
Vfet drain dfet 0
XFET dfet gfet source CSD16340Q3
Rshunt source kelvin 25m
Rreturn kelvin 0 10m
* Assumed flyback clamp across the R-L load, not a selected board diode.
Dfly drain bus fixture_clamp
.model fixture_clamp D(is=1n n=1 rs=0.05 tt=10n cjo=50p bv=60)
Rpulldown gfet source 10k
Vig gate gate_rg 0''').replace('Rg gate gfet 10',f'Rg gate_rg gfet {a.gate_r}')
 if a.power_sequence!='none':
  from run_power_campaign import SEQUENCES
  pa,pd=SEQUENCES[a.power_sequence]
  pa=pa.replace('3.3',str(a.vdda));pd=pd.replace('1.2',str(a.vdd))
  text=re.sub(r'^Vdda .*$',f'Vdda vdda_s 0 pwl({pa})',text,flags=re.M)
  text=re.sub(r'^Vdd .*$',f'Vdd vdd_s 0 pwl({pd})',text,flags=re.M)
  text=re.sub(r'^Ven .*$','Ven en_core 0 0',text,flags=re.M)
  text=re.sub(r'^Vtrip .*$','Vtrip trip_d 0 0',text,flags=re.M)
 if a.set_node:
  current=a.set_charge_fc*1e-6;t=a.set_us
  text+=f'\n* Electrical SET fixture, no LET mapping. Digital trip remains asserted.\nIinj 0 xg.{a.set_node} pwl(0 0 {t}u 0 {t+.00001}u {current} {t+.001}u {current} {t+.00101}u 0)\n'
 # Separate supply-current probes while retaining the original shared upstream
 # rails/decoupling. This does not model the assembled separate IO/core mesh.
 text=text.replace('tripped vdd vdda 0 g1_gate','tripped core_d core_a 0 g1_gate')
 text=text.replace('vdd 0 vdda 0 sg13g2_IOPadOut','pad_d 0 pad_a 0 sg13g2_IOPadOut')
 text+='\nVcorea vdda core_a 0\nVcored vdd core_d 0\nVpada vdda pad_a 0\nVpadd vdd pad_d 0\n'
 wave=out/'wave.tsv';text+=f'''\n.control
set num_threads=1
set numdgt=15
set wr_singlescale
set wr_vecnames
tran 1n {a.stop_us:g}u 0 {a.maxstep_ps:g}p
wrdata {wave} v(gate) v(gfet,source) i(vfet) i(Lload) v(dfet,source) i(vig) v(fault_n) v(tripped)
wrdata {out/'power_wave.tsv'} v(vdd_s) v(vdda_s) v(vdd) v(vdda) i(vdd) i(vdda)
wrdata {out/'split_power_wave.tsv'} v(vdd) v(vdda) i(vcored) i(vcorea) i(vpadd) i(vpada)
echo FET_END
quit 0
.endc
.end
'''
 if a.set_node:text=text.replace('echo FET_END',f'wrdata {out/"set_wave.tsv"} v(gate_core) v(xg.n_34) v(xg.n_35) v(trip_d)\necho FET_END')
 if candidate:text=text.replace('echo FET_END',f'wrdata {out/"candidate_wave.tsv"} v(gate_core) v(xreceiver.sense) v(padres) v(gate)\necho FET_END')
 deck=out/'fixture.cir';deck.write_text(text)
 md=dict(options={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},fixture='CSD16340Q3 vendor transient model; assumed R-L load and flyback diode; direct core EN; detailed30mA output pad; block C-PEX; no self-heating',vendor_url='https://www.ti.com/lit/zip/sllm127b',vendor_model_sha256=sha(a.model),source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),net,HERE/'tb_gate.cir',HERE/'.spiceinit']},deck_sha256=sha(deck),runtime_init_sha256=sha(out/'.spiceinit'),ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),pdk_commit=Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip())
 pdk=Path('/foss/pdks/ihp-sg13g2')
 md['model_hashes']={str(p.relative_to(pdk)):sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').rglob('*')) if p.is_file()}
 md['io_sha256']=sha(pdk/'libs.ref/sg13g2_io/spice/sg13g2_io.spi')
 if candidate:md['candidate_sha256']=sha(candidate)
 if a.power_sequence!='none':md['source_hashes'][str((HERE/'run_power_campaign.py').relative_to(ROOT))]=sha(HERE/'run_power_campaign.py')
 with (out/'run.log').open('x') as log:r=run_bounded(['ngspice','-b',str(deck)],log,out/'run.json',a.timeout,cwd=out,metadata=md,interval_s=2)
 r['electrical_acceptance']='not run'
 try:
  log=(out/'run.log').read_text()
  if r['status']!='completed' or re.search(r'Timestep too small|simulation aborted|doAnalyses:|^Error:',log,re.M|re.I):raise ValueError('solver incomplete/error')
  lines=wave.read_text().splitlines();r['columns']=lines[0].split();rows=[list(map(float,x.split())) for x in lines[1:] if x.strip()]
  if len(rows)<2 or any(len(row)!=9 or not all(map(math.isfinite,row)) for row in rows) or abs(rows[-1][0]-stop)>1e-12:raise ValueError('incomplete/nonfinite vectors')
  before=[row for row in rows if trip-.2e-6<=row[0]<trip];after=[row for row in rows if row[0]>=trip];current=sum(row[4] for row in before)/len(before)
  def delay(col,limit):
   for i,row in enumerate(after):
    if abs(row[col])<limit and all(abs(x[col])<limit for x in after[i:]):return row[0]-trip
   return None
  def integral(col,start,end,other=None):
   rr=[row for row in rows if start<=row[0]<=end]
   return sum((b[0]-aa[0])*(aa[col]*(aa[other] if other else 1)+b[col]*(b[other] if other else 1))/2 for aa,b in zip(rr,rr[1:]))
  metrics=dict(armed_load_A=current,gate_low_delay_s=delay(1,1),vgs_low_delay_s=delay(2,1),fet_current_1pct_delay_s=delay(3,abs(current)*.01),load_current_1pct_delay_s=delay(4,abs(current)*.01),peak_vds_V=max(row[5] for row in rows),turnoff_energy_J=integral(3,trip,stop,5),driver_charge_on_including_pulldown_C=integral(6,.2e-6,trip),driver_charge_off_including_pulldown_C=integral(6,trip,stop),fet_gate_charge_on_C=integral(6,.2e-6,trip)-integral(2,.2e-6,trip)/1e4,fet_gate_charge_off_C=integral(6,trip,stop)-integral(2,trip,stop)/1e4,gate_end_V=rows[-1][1],load_end_A=rows[-1][4])
  r['metrics']=metrics;r['electrical_acceptance']='passed' if (metrics['gate_low_delay_s'] is not None and metrics['gate_low_delay_s']<10e-6 and .9*a.current<current<1.1*a.current and rows[-1][7]<.33 and rows[-1][8]>1) else 'failed'
  if a.power_sequence!='none':
   metrics=dict(gate_max_EN_low_V=max(row[1] for row in rows),vgs_max_EN_low_V=max(row[2] for row in rows),load_peak_EN_low_A=max(abs(row[4]) for row in rows),gate_end_V=rows[-1][1],load_end_A=rows[-1][4]);r['metrics']=metrics
   r['electrical_acceptance']='passed' if metrics['gate_max_EN_low_V']<1 and metrics['vgs_max_EN_low_V']<1 and metrics['load_peak_EN_low_A']<a.current*.01 else 'failed'
  if a.set_node:
   pre_set=[row for row in rows if (a.set_us-.2)*1e-6<=row[0]<a.set_us*1e-6]
   post_set=[row for row in rows if row[0]>=a.set_us*1e-6]
   metrics.update(set_precondition_tripped=all(row[1]<1 and row[8]>1 for row in pre_set) and bool(pre_set),set_gate_max_V=max(row[1] for row in post_set),set_vgs_max_V=max(row[2] for row in post_set),set_load_peak_A=max(abs(row[4]) for row in post_set),set_charge_C=a.set_charge_fc*1e-15)
   set_rows=[list(map(float,line.split())) for line in (out/'set_wave.tsv').read_text().splitlines()[1:] if line.strip()]
   if not set_rows or abs(set_rows[-1][0]-stop)>1e-12 or any(not all(map(math.isfinite,row)) for row in set_rows):raise ValueError('SET observation waveform missing/incomplete')
   metrics.update(set_core_gate_peak_V=max(row[1] for row in set_rows if row[0]>=a.set_us*1e-6),set_node_min_V=min(min(row[2:4]) for row in set_rows),set_node_max_V=max(max(row[2:4]) for row in set_rows))
   r['set_safety_screen']='passed' if metrics['set_precondition_tripped'] and metrics['set_gate_max_V']<1 and metrics['set_vgs_max_V']<1 and metrics['set_load_peak_A']<.01*a.current else 'failed'
  r['limitation']='Gate<10us and selected latch/end-state only; load decay reported separately; no final-board/thermal/SOA qualification'
  if a.power_sequence!='none':r['limitation']='EN-low selected rail sequence only; gate/VGS<1V and modeled load current<1% nominal; no full board/PVT safety qualification'
 except (ValueError,OSError,IndexError,ZeroDivisionError) as e:r['acceptance_error']=str(e)
 atomic_json(out/'run.json',r);print(out.relative_to(ROOT));print(json.dumps({k:r.get(k) for k in ['status','wall_s','electrical_acceptance','acceptance_error','metrics']},indent=2))
 if r['electrical_acceptance']!='passed' or r.get('set_safety_screen')=='failed':raise SystemExit(1)
if __name__=='__main__':main()
