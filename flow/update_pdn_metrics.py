#!/usr/bin/env python3
"""Record post-strap abstract-view connectivity without implicit exceptions."""
import json,re,sys
from pathlib import Path


def update_metrics(state,log):
    nets=sorted(set(re.findall(r'check_power_grid -net (\w+)',log)))
    if not nets:raise ValueError('No post-strapping supply checks found; refusing success metrics')
    passed=set(re.findall(r'All shapes on net (\w+) are connected',log))
    failed=set(re.findall(r'Check connectivity failed on (\w+)',log))
    failed.update(re.findall(r'Unconnected shape on net (\w+)',log))
    metrics=state['metrics']
    for net in nets:
        metrics['design__power_grid_violation__count__net:'+net]=0 if net in passed and net not in failed else 1
    metrics['design__power_grid_violation__count']=sum(metrics['design__power_grid_violation__count__net:'+net] for net in nets)
    metrics['design__power_grid_violation__count__source']='flow/analog_straps.tcl explicit post-strapping check results; count of failed/incomplete checked nets; no geometric exceptions'
    return state


def main():
    step=Path(sys.argv[1]);path=step/'state_out.json'
    result=update_metrics(json.loads(path.read_text()),(step/'analog_straps.log').read_text())
    path.write_text(json.dumps(result,indent=2)+'\n')
    print('[run_dryrun] Failed/incomplete post-strap supply nets:',result['metrics']['design__power_grid_violation__count'])


if __name__=='__main__':main()
