#!/usr/bin/env python3
"""Add explanatory macro boundaries to a GDS-derived view, without modifying GDS.
Run via flow/run.sh python3 designs/g1-guardian/review/layouts/annotate_layouts.py
"""
import pathlib,json
import pya
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Patch
out=pathlib.Path('/work/designs/g1-guardian/review/layouts')
m=json.loads((out/'layout_manifest.json').read_text())
lay=pya.Layout();lay.read('/work/'+m['layouts'][0]['source'])
placements=[]
for inst in lay.top_cell().each_inst():
 if not inst.cell.name.startswith('g1_'):continue
 b=inst.dbbox();placements.append({'cell':inst.cell.name,'bbox_um':[b.left,b.bottom,b.right,b.top],'transform':str(inst.dcplx_trans)})
(out/'assembly_placements.json').write_text(json.dumps(placements,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(9,9),dpi=250)
fig.patch.set_facecolor('#101820');ax.set_facecolor('#101820')
ax.imshow(plt.imread(out/'chip_core.png'),extent=(342.2,1007.8,342.2,1007.8))
labels={'g1_digital':'CTRL + SEU','g1_bgr':'BGR','g1_t2f':'T2F','g1_osc':'OSC','g1_trip':'TRIP','g1_sense':'SENSE','g1_gate':'GATE','g1_dose_macro':'DOSE','g1_dut_macro':'DUT'}
for p in placements:
 x0,y0,x1,y1=p['bbox_um'];name=p['cell']
 ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='white',lw=1.1,linestyle='--',alpha=.85))
 if name=='g1_ls_up':continue
 cx,cy=(x0+x1)/2,(y0+y1)/2
 if name in ['g1_dose_macro','g1_dut_macro']:
  tx=432;ty=cy
  ax.annotate(labels[name],(cx,cy),xytext=(tx,ty),color='white',ha='center',va='center',fontsize=10,weight='bold',bbox=dict(facecolor='#101820',edgecolor='white',pad=3),arrowprops=dict(arrowstyle='-',color='white',lw=1.2))
 else:
  ax.text(cx,cy,labels[name],color='white',ha='center',va='center',fontsize=11,weight='bold',bbox=dict(facecolor='#101820',edgecolor='white',pad=4))
ax.annotate('LS ×3',(570,866),xytext=(594,821),color='white',ha='center',va='center',fontsize=10,weight='bold',bbox=dict(facecolor='#101820',edgecolor='white',pad=3),arrowprops=dict(arrowstyle='-',color='white',lw=1.2))
ax.set_xlim(342.2,1007.8);ax.set_ylim(342.2,1007.8)
ax.set_xlabel('x (µm from die origin)',color='white');ax.set_ylabel('y (µm from die origin)',color='white');ax.tick_params(colors='white',labelsize=8)
for s in ax.spines.values():s.set_color('white')
fig.tight_layout();fig.savefig(out/'chip_core_annotated.png',facecolor=fig.get_facecolor());plt.close(fig)
selected=[('Activ.drawing','Active'),('GatPoly.drawing','Gate/poly resistor'),('Cont.drawing','Contact'),('Metal1.drawing','Metal1'),('Metal2.drawing','Metal2'),('Metal3.drawing','Metal3'),('Metal4.drawing','Metal4'),('Metal5.drawing','Metal5'),('TopMetal1.drawing','TopMetal1'),('TopMetal2.drawing','TopMetal2'),('MIM.drawing','MIM'),('Via1.drawing','Via1')]
colors={x['name']:x['color'] for x in m['legend']}
fig,ax=plt.subplots(figsize=(10,1.3),dpi=220);fig.patch.set_facecolor('#101820');ax.set_facecolor('#101820');ax.axis('off')
handles=[Patch(facecolor=colors[n],edgecolor='none',label=t) for n,t in selected]
leg=ax.legend(handles=handles,ncol=6,loc='center',frameon=False,fontsize=10,labelcolor='white',handlelength=1.3,columnspacing=1.3)
fig.tight_layout(pad=.4);fig.savefig(out/'layer_legend.png',facecolor=fig.get_facecolor());plt.close(fig)
