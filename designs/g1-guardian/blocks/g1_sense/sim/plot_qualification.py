#!/usr/bin/env python3
"""Render the completed modeled SENSE distribution; no unrun samples inferred."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);a=p.parse_args()
r=json.loads(a.analysis.read_text());d=r['sample_results']
x=[s['uncalibrated_input_error_V']*1e3 for s in d];y=[s['worst_frozen_continuous_correction_residual_V']*1e3 for s in d]
fig,ax=plt.subplots(1,3,figsize=(13.8,4.4),layout='constrained')
fig.suptitle(f'SENSE revision B: modeled mismatch screening, n={len(d)}',fontsize=15,weight='bold')
ax[0].hist(x,bins=14,color='#2d6d99',edgecolor='white');ax[0].set(xlabel='Uncalibrated input error at calibration point (mV)',ylabel='Samples',title='Room-temperature calibration error')
ax[1].hist(y,bins=14,color='#b84747',edgecolor='white');ax[1].axvline(.5,color='black',linestyle='--',label='0.5 mV limit');ax[1].set(xlabel='Worst absolute frozen-correction residual (mV)',ylabel='Samples',title=f"Residual failures: {r['offset_target_failures']}/{len(d)}");ax[1].legend(frameon=False)
ax[2].scatter(x,y,c=['#b84747' if v>=.5 else '#2d6d99' for v in y],s=23,alpha=.85);ax[2].axhline(.5,color='black',linestyle='--');ax[2].set(xlabel='Uncalibrated input error (mV)',ylabel='Worst residual (mV)',title='Error versus frozen-calibration residual')
for a0 in ax:a0.grid(axis='y',alpha=.18);a0.set_axisbelow(True)
fig.supxlabel('Simulated schematic only; ideal VREF/PTAT; ideal continuous correction at 25 °C and 25 mV shunt.\nResidual tested at −40/25/125 °C, SENSE_N −0.1/0/+0.3 V, shunt 0/25/50 mV. No joint-chain yield claim.',fontsize=9)
for suffix in ['png','svg']:fig.savefig(a.analysis.parent/f'distribution.{suffix}',dpi=160)
(a.analysis.parent/'plot_provenance.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,'input':str(a.analysis),'completed_samples':len(d),'command':'python3 plot_qualification.py '+str(a.analysis)},indent=2)+'\n')
