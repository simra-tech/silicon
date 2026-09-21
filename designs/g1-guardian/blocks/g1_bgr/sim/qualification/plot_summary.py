#!/usr/bin/env python3
"""Plot the retained 100-sample modeled ensemble (not silicon yield)."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
rows=list(csv.DictReader((ROOT/'summary.csv').open()))
mc=[r for r in rows if r['campaign']=='mc']
fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
axes[0].hist([float(r['vref25']) for r in mc],bins=16,color='#176b87',edgecolor='white')
axes[0].set(xlabel='VREF at 25 °C (V)',ylabel='Samples',title='Simulated PEX mismatch, 100 samples')
axes[1].hist([float(r['tc_ppm_C']) for r in mc],bins=16,color='#176b87',edgecolor='white')
axes[1].axvline(50,color='#b3261e',label='50 ppm/°C limit')
axes[1].set(xlabel='Box TC, −40 to 125 °C (ppm/°C)',ylabel='Samples',title='54 / 100 exceed the TC requirement');axes[1].legend()
fig.savefig(ROOT/'mc_distributions.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4.4),layout='constrained')
for run in ['bgr_mc20_20260921_01','bgr_mc100_20260921_01']:
 for case in json.loads((ROOT/'runs'/run/'manifest.json').read_text())['cases']:
  d=[[float(x) for x in row.split()] for row in (ROOT/'runs'/run/(case['name']+'.dat')).read_text().splitlines()[1:]]
  ax.plot([r[0] for r in d],[r[1] for r in d],color='#176b87',alpha=.22,linewidth=.7)
ax.set(xlabel='Temperature (°C)',ylabel='VREF (V)',title='Simulated BGR C-PEX: fixed mismatch sample over temperature')
ax.grid(alpha=.2);fig.savefig(ROOT/'mc_temperature_curves.svg')
