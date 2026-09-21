#!/usr/bin/env python3
"""Plot retained modeled results, preserving failed samples and distinct mappings."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
rows=[r for r in csv.DictReader((HERE/'mc100_samples.csv').open()) if r['calibration_status']!='not run']
candidate={int(r['seed']):r for r in csv.DictReader((HERE/'curvature_candidate100_samples.csv').open())}
fig,axes=plt.subplots(1,2,figsize=(11,4.1),layout='constrained')
for suffix,color,label in [('cold','#176b87','−40 °C'),('hot','#aa3b24','125 °C')]:
 values=[float(r[f'{suffix}_residual_C']) for r in rows]
 axes[0].scatter([int(r['seed']) for r in rows],values,s=13,color=color,label=label)
 axes[1].scatter(values,[float(candidate[int(r['seed'])][f'candidate_{suffix}_residual_C']) for r in rows],s=15,color=color,label=label)
for ax in axes:
 ax.axhline(2,color='#555',linestyle='--',linewidth=.8);ax.axhline(-2,color='#555',linestyle='--',linewidth=.8);ax.grid(alpha=.18)
axes[0].axvline(51020.5,color='#777',linewidth=.7)
axes[0].set(xlabel='Physical-sample seed (divider: legacy / native runtime)',ylabel='Linear calibrated residual (°C)',title=f'Simulated joint C-PEX, {len(rows)} completed samples')
axes[0].ticklabel_format(useOffset=False,style='plain',axis='x');axes[0].tick_params(axis='x',rotation=25);axes[0].legend(loc='upper right')
axes[1].axvline(2,color='#555',linestyle='--',linewidth=.8);axes[1].axvline(-2,color='#555',linestyle='--',linewidth=.8)
axes[1].set(xlabel='Original linear residual (°C)',ylabel='Frozen nominal-curve residual (°C)',title='Unadopted correction; no fit to MC outcomes');axes[1].legend()
fig.savefig(HERE/'mc100_residuals.svg');fig.savefig(HERE/'mc100_residuals.png',dpi=160);plt.close(fig)
points=list(csv.DictReader((HERE/'mc20_intermediate_points.csv').open()))
fig,ax=plt.subplots(figsize=(7.5,4.4),layout='constrained')
for seed in sorted({int(r['seed']) for r in points}):
 p=sorted([r for r in points if int(r['seed'])==seed and r['linear_status']!='not run'],key=lambda r:float(r['temperature_C']))
 ax.plot([float(r['temperature_C']) for r in p],[float(r['linear_residual_C']) for r in p],'.-',color='#176b87',alpha=.35,linewidth=.8)
ax.axhline(2,color='#aa3b24',linestyle='--');ax.axhline(-2,color='#aa3b24',linestyle='--');ax.grid(alpha=.18)
ax.set(xlabel='Temperature (°C)',ylabel='Linear calibrated residual (°C)',title='20 fixed physical samples: four independent intermediate points')
fig.savefig(HERE/'mc20_intermediate_residuals.svg');plt.close(fig)
