#!/usr/bin/env python3
"""Independently review all routed-net reports; do not waive physical omissions."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from audit_routed_spef import parse


def wire_values(text):
    matches=re.findall(r'^ Wire capacitance: ([0-9.]+(?:-[0-9.]+)?)$',text,re.M)
    assert len(matches)==1
    values=[float(v)for v in matches[0].split('-')]
    assert all(math.isfinite(v) and v>0 for v in values)
    return values


def macro_totals(text):
    names={};totals={}
    for line in text.splitlines():
        m=re.fullmatch(r'\*(\d+) ([^ ]+)',line)
        if m:
            assert m[1] not in names
            names[m[1]]=m[2].replace('\\','')
        m=re.fullmatch(r'\*D_NET \*(\d+) ([0-9.eE+-]+)',line)
        if m:
            name=names[m[1]];assert name not in totals
            value=float(m[2]);assert math.isfinite(value) and value>=0
            totals[name]=value
    assert totals
    return totals


def review(run,nets,macro):
    summary=json.loads((run/'summary.json').read_text())
    assert summary['status'].startswith('passed ')
    assert summary['shared_parasitics'] and summary['keep_couplings']
    assert {k:int(v)for k,v in summary['counts'].items()}=={'SCLK':52,'osc_clk':1148}
    reports=summary['net_reports'];assert len(reports)==57 and set(reports.values())==set(nets)
    annotation=(run/'annotation.rpt').read_text()
    assert annotation.startswith('Found 101 unannotated drivers.\n')
    assert annotation.endswith('Found 0 partially unannotated drivers.\n')
    rows=[]
    for filename,name in sorted(reports.items()):
        text=(run/filename).read_text()
        assert text.splitlines()[0].replace('\\','')=='Net '+name
        values=wire_values(text)
        ports=[pin for inst,pin in nets[name]['connections'] if inst=='i_core.u_digital']
        assert len(ports)<=1
        expected=float(nets[name]['total'])+sum(macro[pin]for pin in ports)
        rows.append(dict(net=name,macro_ports=ports,source_printed_total_pF=expected,
                         reported_wire_pF=values,
                         difference_pF=[value-expected for value in values],
                         capacitance_accuracy_status='not run: descriptive comparison, no new tolerance'))
    slacks=summary['slacks_ns'];assert set(slacks)=={'hold','setup'}
    assert all(math.isfinite(v)for v in slacks.values())
    violators=(run/'violators.rpt').read_text()
    assert '(VIOLATED)' in violators
    return dict(corner=summary['corner'],rows=rows,slacks_ns=slacks,
                constrained_slack_status='passed' if min(slacks.values())>=0 else 'failed',
                existing_slew_fanout_status='failed',unannotated_drivers=101,
                partially_unannotated_drivers=0,
                maximum_absolute_capacitance_difference_pF=max(abs(d)for r in rows for d in r['difference_pF']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,action='append',required=True)
    p.add_argument('--top-spef',type=Path,required=True)
    p.add_argument('--macro-spef',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    nets,_=parse(a.top_spef.read_text());macro=macro_totals(a.macro_spef.read_text())
    rows=[review(run,nets,macro)for run in a.run]
    assert len(rows)==3 and {r['corner']for r in rows}=={'fast','typ','slow'}
    files=[a.top_spef,a.macro_spef,Path(__file__)]+[f for run in a.run for f in run.iterdir()if f.is_file()]
    result=dict(status='passed report/source coverage audit; integrated qualification remains incomplete',corners=rows,
                input_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in files},
                passed=['57 distinct positive wire-capacitance reports per corner','Original 1200 clocked-register coverage','Zero partial drivers'],
                failed=['Existing slew/fanout constraints','Complete physical annotation: 101 unannotated drivers retained'],
                not_run=['Analog timing and physical clock/load bounds','Final native/fill/power/moved-pad extraction','Full-chip timing sign-off','Capacitance numerical acceptance beyond descriptive source comparison'],
                not_applicable=['Stochastic seed'])
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('input_sha256','corners')},indent=2))


if __name__=='__main__':main()
