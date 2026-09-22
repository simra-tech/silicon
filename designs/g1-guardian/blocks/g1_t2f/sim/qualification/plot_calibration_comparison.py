#!/usr/bin/env python3
"""Plot retained independent endpoint errors; do not refit any calibration."""
import argparse, csv, hashlib, json, platform
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-prefix',default='calibration_comparison_final300_20260922')
    args=parser.parse_args()
    if Path(args.output_prefix).name!=args.output_prefix:
        parser.error('--output-prefix must be a filename stem')
    destinations=[HERE/f'{args.output_prefix}.{suffix}' for suffix in ['png','svg','json']]
    if any(p.exists() for p in destinations):
        parser.error('output exists; select a fresh prefix to preserve prior evidence')
    sources=['mc300_samples.csv','curvature_candidate300_samples.csv',
             'reciprocal_candidate300_points.csv','adverse_pilot_summary_20260922.json']
    linear={int(r['seed']):r for r in csv.DictReader((HERE/sources[0]).open()) if r['calibration_status']!='not run'}
    lut={int(r['seed']):r for r in csv.DictReader((HERE/sources[1]).open())}
    reciprocal={}
    for r in csv.DictReader((HERE/sources[2]).open()):
        seed=int(r['seed']);temp=float(r['temperature_C'])
        if seed in linear and temp in [-40,125]:reciprocal.setdefault(seed,{})[temp]=float(r['residual_C'])
    seeds=sorted(set(linear)&set(lut)&set(reciprocal))
    assert len(seeds)==len(linear)
    methods=[('Original linear','#9f303b'),('Frozen nominal LUT*','#247da5'),('Reciprocal candidate*','#277654')]
    arrays=[[(float(linear[s]['cold_residual_C']),float(linear[s]['hot_residual_C'])) for s in seeds],
            [(float(lut[s]['candidate_cold_residual_C']),float(lut[s]['candidate_hot_residual_C'])) for s in seeds],
            [(reciprocal[s][-40],reciprocal[s][125]) for s in seeds]]
    fig,axes=plt.subplots(1,3,figsize=(15.5,5.3))
    for (label,color),pairs in zip(methods,arrays):
        xx=sorted(max(map(abs,p)) for p in pairs)
        axes[0].step(xx,[(i+1)/len(xx) for i in range(len(xx))],where='post',label=label,color=color,lw=2)
        axes[1].scatter([p[0] for p in pairs],[p[1] for p in pairs],s=10,alpha=.5,color=color,label=label)
    axes[0].axvline(2,color='black',ls='--',lw=1)
    axes[0].set(xlabel='Maximum absolute endpoint error (°C)',ylabel='Fraction of completed samples',title=f'{len(seeds)}/300 samples completed',ylim=(0,1.02))
    axes[0].legend(loc='lower right',fontsize=8)
    for value in [-2,2]:
        axes[1].axvline(value,color='black',ls='--',lw=.8)
        axes[1].axhline(value,color='black',ls='--',lw=.8)
    axes[1].set(xlabel='Error at −40°C (°C)',ylabel='Error at 125°C (°C)',title='Same per-sample 25/100°C calibration')
    pilots=json.loads((HERE/sources[3]).read_text())['groups']
    for i,(label,color) in enumerate(methods):
        method=['linear','nominal_lut','reciprocal'][i]
        axes[2].bar([j+(i-1)*.23 for j in range(3)],
                    [pilots[c]['calibration_methods'][method]['maximum_abs_error_C'] for c in ['slow','nominal','fast']],
                    width=.23,label=label,color=color)
    axes[2].axhline(2,color='black',ls='--',lw=1)
    axes[2].set(xticks=[0,1,2],xticklabels=['Slow','Nominal','Fast'],ylabel='Maximum absolute error (°C)',title='One sample per process: rail pilots')
    for ax in axes:
        ax.grid(alpha=.18);ax.set_axisbelow(True)
    fig.suptitle('Simulated joint BGR/T2F calibration comparison',fontsize=15,y=.98)
    fig.text(.5,.025,'* Unadopted candidates. Left/center: nominal rails and two independent endpoints per sample. Right: four rail/temperature points per process sample.\nModel-local mismatch, C-PEX and ideal IPTAT/output fixtures; no packaged-silicon yield claim. Original linear failures retained.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.13,1,.94))
    for suffix in ['png','svg']:fig.savefig(HERE/f'{args.output_prefix}.{suffix}',dpi=170)
    result={'completed_samples':len(seeds),'expected_samples':300,'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources},
            'endpoint_failure_counts':{label:sum(max(map(abs,p))>2 for p in pairs) for (label,_),pairs in zip(methods,arrays)},
            'analysis_runtime':{'python':platform.python_version(),'matplotlib':matplotlib.__version__},
            'scope':'Plot only; no calibration refitting or altered acceptance. Completion count applies to nominal endpoint samples; rail pilots are separate.'}
    (HERE/f'{args.output_prefix}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
