#!/usr/bin/env python3
"""Plot retained selected HBT pulse traces and summarize on/off comparisons."""
import argparse,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);(a.output/'runner.py').write_text(Path(__file__).read_text());d=json.loads((a.run/'manifest.json').read_text());assert len(d['cases'])==4 and all(x['status']=='passed' for x in d['cases']);fig,axes=plt.subplots(3,1,figsize=(9,7),sharex=True,layout='constrained');pairs=[]
for on in [c for c in d['cases'] if c['selft']==1]:
 off=next(c for c in d['cases'] if c['corner']==on['corner'] and c['ambient_C']==on['ambient_C'] and c['selft']==0);pairs.append({'corner':on['corner'],'ambient_C':on['ambient_C'],'thermal_rise_high_K':on['high_plateau_rise_K'],'thermal_10to90_s':on['thermal_10to90_s'],'high_IC_on_A':on['IC_high_A'],'high_IC_off_A':off['IC_high_A'],'high_IC_on_over_off':on['IC_high_A']/off['IC_high_A'],'return_to_initial_thermal_error_K':on['final_rise_K']-on['initial_rise_K'],'max_junction_C':on['maximum_junction_C']});rows=[list(map(float,l.split())) for l in (a.run/on['name']/'wave.tsv').read_text().splitlines()[1:]];s=rows[::10];label=f"{on['corner']}, {on['ambient_C']}°C";t=[r[0]*1e9 for r in s];axes[1].plot(t,[r[6]*1e6 for r in s],label=label);axes[2].plot(t,[r[8] for r in s],label=label)
 if on['corner']=='typ':axes[0].plot(t,[r[1] for r in s],color='black')
axes[0].set_ylabel('Base source (V)');axes[1].set_ylabel('Collector current (µA)');axes[2].set_ylabel('Model temperature rise (K)');axes[2].set_xlabel('Time (ns)');axes[1].legend();axes[2].legend();axes[0].set_title('HBT with actual pads and estimated routes; device-local thermal model')
for ax in axes:ax.grid(alpha=.2);ax.set_xlim(50,500)
fig.savefig(a.output/'thermal_pulse.svg');fig.savefig(a.output/'thermal_pulse.png',dpi=150);plt.close(fig);summary={'source_manifest_sha256':hashlib.sha256((a.run/'manifest.json').read_bytes()).hexdigest(),'paired_conditions':pairs,'scope':'0.65V-biased pulse response. Starts beyond low-voltage antenna-diode transition; no startup-from0 qualification. Rise time includes10nsinputedge and electrical/thermalfeedback, not an isolatedRthCth time constant.','physical_thermal_accuracy':'not run'};(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
