"""Read-only saved-grid localization, not a waveform-bound waiver."""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_joint586_tmax_matrix import SIM,sha
from wave_archive import open_wave,wave_sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    out=SIM/'qualification'/a.run_id;prep=json.loads((out/'preparation.json').read_text());old=SIM/'qualification'/prep['original_run']
    arrays=[];headers=[]
    for run in [old,out]:
        with open_wave(run/'phase0.dat','rt') as stream:headers.append(stream.readline().split());arrays.append(np.loadtxt(stream))
    assert headers[0]==headers[1];header=headers[0];i=header.index('v(cmp_soft)');original,candidate=arrays
    grid=np.union1d(original[:,0],candidate[:,0]);oval=np.interp(grid,original[:,0],original[:,i]);nval=np.interp(grid,candidate[:,0],candidate[:,i]);error=oval-nval;k=int(np.argmax(abs(error)));when=float(grid[k])
    rows=[]
    for label,data in zip(['original','candidate'],arrays):
        j=int(np.searchsorted(data[:,0],when));lo=max(0,j-1);hi=min(len(data)-1,j)
        rows.append(dict(label=label,exact_saved_sample_at_worst=bool(np.any(data[:,0]==when)),bracket_s=[float(data[lo,0]),float(data[hi,0])],
            bracket_width_s=float(data[hi,0]-data[lo,0]),bracket_cmp_soft_V=[float(data[lo,i]),float(data[hi,i])],
            neighborhood_columns=['time','v(cmp_soft)','v(clk)'],neighborhood=data[max(0,j-3):j+4][:,[0,i,header.index('v(clk)')]].tolist()))
    summary=json.loads((out/'summary.json').read_text());events={key:value for key,value in summary['comparisons']['threshold_events'].items() if key.startswith('v(cmp_soft)')}
    clock=summary['wave_analysis']['actual_clock_rising_crossings_s']['soft'];closest=min(clock,key=lambda t:abs(when-t))
    result=dict(status='completed saved-data localization; original screen failure retained',run_id=a.run_id,original_run=prep['original_run'],node='v(cmp_soft)',
        worst_time_s=when,original_interpolated_V=float(oval[k]),candidate_interpolated_V=float(nval[k]),absolute_difference_V=float(abs(error[k])),
        nearest_actual_soft_clock_rising_s=closest,delay_after_nearest_clock_s=when-closest,discrete_observations=rows,output_events=events,
        decoded_wave_sha256={label:wave_sha(run/'phase0.dat') for label,run in [('original',old),('candidate',out)]},
        preparation_sha256=sha(out/'preparation.json'),summary_sha256=sha(out/'summary.json'),analyzer_sha256=sha(Path(__file__)),
        scope='Accepted saved points and linear interpolation only. Actual discrete brackets/neighborhoods exposed; no internal rejected-step or causal solver inference. First-clock location is descriptive, not an exemption from the50mV wholewave bound. No simulation, tolerance or decision-rule change.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(sha(a.output))

if __name__=='__main__':main()
