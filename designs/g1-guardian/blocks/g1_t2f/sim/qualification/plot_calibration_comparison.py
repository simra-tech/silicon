#!/usr/bin/env python3
"""All original and candidate endpoint results, without dropping failed samples."""
import argparse,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,choices=[100,300],default=100);a=ap.parse_args()
linear={int(r['seed']):r for r in csv.DictReader((HERE/f'mc{a.samples}_samples.csv').open()) if r['calibration_status']!='not run'}
lut={int(r['seed']):r for r in csv.DictReader((HERE/f'curvature_candidate{a.samples}_samples.csv').open())}
recipstem='reciprocal_candidate' if a.samples==100 else 'reciprocal_candidate300'
recip={(int(r['seed']),float(r['temperature_C'])):r for r in csv.DictReader((HERE/(recipstem+'_points.csv')).open()) if int(r['seed']) in linear and float(r['temperature_C']) in [-40,125]}
fig,axes=plt.subplots(1,3,figsize=(13,4.7),sharey=True,layout='constrained')
for ax,method,title in zip(axes,['linear','lut','reciprocal'],['Original linear calibration','Frozen nominal LUT — unadopted','Reciprocal model — unadopted']):
 for temp,suffix,color,label in [(-40,'cold','#176b87','−40 °C'),(125,'hot','#aa3b24','125 °C')]:
  seeds=sorted(linear);values=[float(linear[s][suffix+'_residual_C']) if method=='linear' else float(lut[s]['candidate_'+suffix+'_residual_C']) if method=='lut' else float(recip[(s,temp)]['residual_C']) for s in seeds]
  ax.scatter(seeds,values,s=11,color=color,label=label)
 ax.axhline(-2,color='#555',ls='--',lw=.8);ax.axhline(2,color='#555',ls='--',lw=.8);ax.axvline(51020.5,color='#888',lw=.6);ax.grid(alpha=.15);ax.set_title(title,fontsize=11);ax.set_xlabel('Physical sample seed');ax.ticklabel_format(style='plain',useOffset=False,axis='x');ax.tick_params(axis='x',rotation=30);ax.set_ylim(-3,2.5)
axes[0].set_ylabel('Independent endpoint residual (°C)');axes[0].legend(loc='upper right',fontsize=9)
fig.suptitle(f'Simulated joint BGR/T2F C-PEX: {len(linear)} completed physical samples\nEach sample calibrated only at25/100 °C; typical process,3.3/1.2 V',fontsize=12)
for extension in ['png','svg']:fig.savefig(HERE/f'mc{a.samples}_calibration_comparison.{extension}',dpi=180)
