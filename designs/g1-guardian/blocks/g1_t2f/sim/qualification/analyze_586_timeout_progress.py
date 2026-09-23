#!/usr/bin/env python3
"""Read-only last60s host telemetry, distinct from accepted waveform evidence."""
import argparse,json,os
from pathlib import Path
from run_586_calibration_sample import HERE,sha


def assess(rows, hz):
    valid=[r for r in rows if r.get('last_reported_sim_time_s') is not None]
    assert len(valid)>1
    final=valid[-1];window=[r for r in valid if r['wall_s']>=final['wall_s']-60]
    assert len(window)>1
    first=window[0];span=final['wall_s']-first['wall_s'];assert span>0
    advance=final['last_reported_sim_time_s']-first['last_reported_sim_time_s']
    assert advance>=0
    unchanged_start=window[0];longest=0
    for a,b in zip(window,window[1:]):
        if b['last_reported_sim_time_s']!=a['last_reported_sim_time_s']:
            unchanged_start=b
        longest=max(longest,b['wall_s']-unchanged_start['wall_s'])
    cpu=[r for r in window if 'cpu_ticks' in r]
    result=dict(window_wall_s=[first['wall_s'],final['wall_s']],window_observed_span_s=span,
                reported_sim_time_s=[first['last_reported_sim_time_s'],final['last_reported_sim_time_s']],
                last60_window_advance_s=advance,simulated_seconds_per_wall_second=advance/span,
                longest_unchanged_reported_time_interval_s=longest,
                classification='advancing in final telemetry window' if advance>0 else 'no reported advance in final telemetry window',
                observed_rows=len(window),clock_ticks_per_second=hz,process_cpu_status='not run; no paired CPU telemetry')
    if len(cpu)>1:
        a,b=cpu[0],cpu[-1];ticks=[sum(map(int,r['cpu_ticks'])) for r in [a,b]]
        seconds=(ticks[1]-ticks[0])/hz;wall=b['wall_s']-a['wall_s']
        assert seconds>=0 and wall>0
        result.update(process_cpu_status='recorded process user+system ticks',process_cpu_window_wall_s=[a['wall_s'],b['wall_s']],
                      process_cpu_elapsed_s=seconds,process_cpu_to_wall_ratio=seconds/wall)
    if advance>0:
        result['linear_remaining_wall_s_at_observed_slope']=max(0,32e-6-final['last_reported_sim_time_s'])/(advance/span)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--leaf',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert Path(a.run_id).name==a.run_id and not a.output.exists()
    leaf=HERE/'runs'/a.run_id/('p%02d'%a.leaf);row,=json.loads((leaf/'summary.json').read_text())
    assert row['status']=='failed' and row['runtime']['status']=='timeout' and row['runtime']['timeout_s']==600
    rows=[json.loads(line) for line in (leaf/'run.progress.jsonl').read_text().splitlines()]
    result=dict(status='completed read-only timeout telemetry assessment; original failure retained',run=a.run_id,leaf=leaf.name,
                runtime=row['runtime'],last60s=assess(rows,os.sysconf('SC_CLK_TCK')),
                receipts_sha256={n:sha(leaf/n) for n in ['summary.json','run.json','run.progress.jsonl','run.log','probe.cir']},
                analyzer_sha256=sha(Path(__file__)),
                scope='Host-reported latest time is not an exported accepted waveform or proof of solver root cause. CPU ratio describes recorded process scheduling, not exclusive host capacity. Linear completion forecast assumes unchanged observed slope and is not a watchdog recommendation, recovery authorization, endpoint completion or accuracy result.')
    with a.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result['last60s'],indent=2))


if __name__=='__main__':main()
