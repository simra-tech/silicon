import os
SIM=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lst import *
import glob,os
def lg(p):
    m=sorted(os.path.basename(x) for x in glob.glob(L+'/'+p))
    assert len(m)==1,(p,m); return m[0]
sec=sys.argv[1]
if sec=='supply':
  it=[]
  for case in ('c_mid','q'):
    for cor,t,v,a in [('tt','27C','1p08','3p0'),('tt','27C','1p08','3p6'),('tt','27C','1p32','3p0'),('tt','27C','1p32','3p6'),('ss','125C','1p08','3p0'),('ff','-40C','1p32','3p6')]:
      it.append(('%s, %s %s, VDD %s V, VDDA=IOVDD %s V'%(case,cor,t.replace('-','−').replace('C',' °C'),v.replace('p','.'),a.replace('p','.')),case,lg('%s_pex_c1414_tl_%s_%s_vdd%s_vdda%s_*r3_c1414m.log'%(case,cor,t,v,a))))
  emit('Case, corner, supplies',it)
if sec=='k1':
  it=[]
  for case in ('c_mid','q','f_mid'):
    for cor in ('ss','ff'):
      for t in ('-40C','85C'):
        it.append(('%s, %s %s'%(case,cor,t.replace('-','−').replace('C',' °C')),case,lg('%s_pex_c1414_tl_%s_%s_ovr-bgrsch_clockfix_functional_c1414k1.log'%(case,cor,t))))
  emit('Case, corner, T',it)
if sec=='hot':
  it=[]
  for case in ('c','e20'):
    for t in ('27','85','125'):
      it.append(('%s, tt %s °C, default timeline'%(case,t),case,lg('%s_pex_c1414_tl_tt_%sC_ovr-bgrsch_nodcn_clockfix_functional_c1414hot_%s_tt_%s.log'%(case,t,case,t))))
      it.append(('%s, tt %s °C, compact'%(case,t),case,lg('%s_pex_c1414_tl_tt_%sC_ovr-bgrsch_nodcn_clockfix_compact_functional_c1414hot_%s_tt_%s_compact.log'%(case,t,case,t))))
  it.append(('c, ss 125 °C, default timeline','c',lg('c_pex_c1414_tl_ss_125C_ovr-bgrsch_nodcn_clockfix_functional_c1414hot_c_ss_125.log')))
  it.append(('c, ss 125 °C, compact','c',lg('c_pex_c1414_tl_ss_125C_ovr-bgrsch_nodcn_clockfix_compact_functional_c1414hot_c_ss_125_compact.log')))
  it.append(('c, ff −40 °C, default timeline','c',lg('c_pex_c1414_tl_ff_-40C_*c1414hot_c_ff_-40.log')))
  it.append(('c_mid, ff −40 °C, default timeline','c_mid',lg('c_mid_pex_c1414_tl_ff_-40C_*c1414hot_c_mid_ff_-40.log')))
  emit('Case, T, timeline',it)
if sec=='n2':
  it=[]
  for case in ('q','a_s','b_s','c','c_fast','c_mid','e20','f','f_mid','hard_pulse'):
    it.append((case,case if case!='f' else 'f_mid',lg('%s_pex_c1414_tl_tt_27C_ovr-bgrsch_clockfix_functional_c1414n2.log'%case)))
  emit('Case',it)
if sec=='full':
  emit('Case',[('q, default timeline (44 µs)','q',lg('q_pex_c1414_tl_tt_27C_clockfix_functional_c1414full.log')),('c_mid, default timeline (42 µs)','c_mid',lg('c_mid_pex_c1414_tl_tt_27C_clockfix_functional_c1414full.log')),('c_mid, compact (28 µs)','c_mid',lg('c_mid_pex_c1414_tl_tt_27C_clockfix_compact_functional_c1414fullc.log'))])
if sec=='thr':
  it=[]
  for m,tag in [('1p1','thr3'),('1p15','thr3'),('1p2','thr3'),('1p25','thr'),('1p4','thr'),('1p55','thr'),('1p7','thr')]:
    x=float(m.replace('p','.'))
    it.append(('%.2f× (%.2f mV, %.2f of code 200)'%(x,25*x,25*x/39.25),'fm' if x>=1.25 else 'fm_no',lg('c_mid_pex_c1414_tl_tt_27C_fm%s_ovr-bgrsch_nodcn_clockfix_functional_c1414%s.log'%(m,tag))))
  it.append(('1.80× (45.00 mV, 1.15 of code 200), night c_mid tt 27 °C','c_mid',lg('c_mid_*tt_27C_r2_r3_c1414m.log')))
  emit('Fault level (shunt)',it)
