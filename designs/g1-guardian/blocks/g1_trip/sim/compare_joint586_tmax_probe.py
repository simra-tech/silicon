"""Prospective saved-grid comparisons; interpolation is not a universal error bound."""
import numpy as np

ANALOG=[2,3,4,7,13,14,15,16,17]
EVENTS=[1,8,5,6]


def crossings(data,index,rising):
    rows=[]
    for a,b in zip(data[:-1],data[1:]):
        if (a[index]<.6<=b[index]) if rising else (a[index]>.6>=b[index]):
            rows.append(dict(time_s=float(a[0]+(.6-a[index])*(b[0]-a[0])/(b[index]-a[index])),bracket_s=[float(a[0]),float(b[0])]))
    return rows


def compare(old,new,names,old_analysis,new_analysis,bounds):
    assert old.shape[1]==new.shape[1]==len(names)==18
    assert np.isfinite(old).all() and np.isfinite(new).all()
    grid=np.unique(np.concatenate([old[:,0],new[:,0]]));whole={};events={};event_pass=True
    for i,name in enumerate(names[1:],1):
        difference=np.interp(grid,new[:,0],new[:,i])-np.interp(grid,old[:,0],old[:,i])
        whole[name]=dict(maximum_abs_V=float(np.max(np.abs(difference))),rms_V=float(np.sqrt(np.mean(difference*difference))))
    for i in EVENTS:
        for rising in [True,False]:
            a,b=crossings(old,i,rising),crossings(new,i,rising);same=len(a)==len(b)
            shifts=[y['time_s']-x['time_s'] for x,y in zip(a,b)]
            widths=[r['bracket_s'][1]-r['bracket_s'][0] for r in a+b]
            passed=same and max(map(abs,shifts),default=0)<=bounds['clock_output_event_shift_s'] and max(widths,default=0)<=bounds['event_bracket_width_s']*(1+1e-9)
            events[names[i]+(' rising' if rising else ' falling')]=dict(original=a,candidate=b,count_exact=same,paired_shift_s=shifts,passed=passed)
            event_pass=event_pass and passed
    phase=[];phase_max=0.;decisions_same=True
    for comparator in ['soft','hard']:
        a=old_analysis['comparators'][comparator];b=new_analysis['comparators'][comparator]
        decisions_same=decisions_same and all(a[key]==b[key] for key in ['measured_edge_decision','legacy_phase_decision']) and b['sampling_policies_agree']
        for original_edge,candidate_edge in zip(old_analysis['actual_clock_rising_crossings_s'][comparator][-3:],new_analysis['actual_clock_rising_crossings_s'][comparator][-3:]):
            for delay in [-10e-9,20e-9,50e-9]:
                differences={names[i]:float(np.interp(candidate_edge+delay,new[:,0],new[:,i])-np.interp(original_edge+delay,old[:,0],old[:,i])) for i in ANALOG}
                phase_max=max(phase_max,max(map(abs,differences.values())))
                phase.append(dict(comparator=comparator,delay_s=delay,original_time_s=original_edge+delay,candidate_time_s=candidate_edge+delay,analog_differences_V=differences))
    whole_pass=all(whole[names[i]]['maximum_abs_V']<=bounds['wholewave_analog_abs_V' if i in ANALOG else 'wholewave_other_abs_V'] for i in range(1,18))
    def stats(data,ceiling):
        steps=np.diff(data[:,0]);selected=np.abs(steps-ceiling)<1e-17
        return dict(rows=len(data),min_step_s=float(np.min(steps)),max_step_s=float(np.max(steps)),median_step_s=float(np.median(steps)),
            ceiling_count_fraction=float(np.mean(selected)),ceiling_time_fraction=float(np.sum(steps[selected])/(data[-1,0]-data[0,0])))
    return dict(wholewave_uniongrid_errors=whole,threshold_events=events,phase_aligned_samples=phase,
        phase_maximum_analog_abs_V=phase_max,original_grid=stats(old,.2e-9),candidate_grid=stats(new,1e-9),
        checks=dict(same_original_actual_and_legacy_decisions=bool(decisions_same),event_counts_times_resolution=bool(event_pass),
            quiet_decision_analog_consistency=bool(phase_max<=bounds['quiet_decision_analog_abs_V']),wholewave_consistency=bool(whole_pass)),
        scope='Linear interpolation of saved grids and observed crossing brackets only; no hidden/rejected solver-step inference, universal numerical bound or population adoption.')
