#!/usr/bin/env python3
"""Audit replacement timing reports without treating missing top RC as covered."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).parent/'final_route_context'))
from audit_digital_routed_sta import annotation_control
from fullchip_reference_closure.audit_reference import parse_verilog
from final_route_context.audit_expanded_sta import macro_totals,wire_values
from final_route_context.audit_routed_spef import parse


def drivers(text):
    match=re.fullmatch(r'Found (\d+) unannotated drivers\.\n(.*?)Found (\d+) partially unannotated drivers\.\n',text,re.S)
    assert match and int(match[3])==0
    rows=[v.strip() for v in match[2].splitlines() if v.strip()]
    assert len(rows)==int(match[1])==len(set(rows))
    return rows


def check_annotation(text,instances):
    rows=drivers(text);prefix='i_core.u_digital/'
    macro=[r[len(prefix):] for r in rows if r.startswith(prefix)]
    rebuilt='Found %d unannotated drivers.\n'%len(macro)+'\n'.join(macro)+'\nFound 0 partially unannotated drivers.\n'
    annotation_control(rebuilt,instances)
    return sorted(r for r in rows if not r.startswith(prefix))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,action='append',required=True)
    for name in ('top-spef','macro-spef','netlist','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    module,_,instances=parse_verilog(a.netlist.read_text());assert module=='g1_digital'
    nets,_=parse(a.top_spef.read_text());macro=macro_totals(a.macro_spef.read_text())
    assert len(nets)==57
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    held=[a.top_spef,a.macro_spef,a.netlist,Path(__file__)]
    rows=[]
    for run in a.run:
        summary=json.loads((run/'summary.json').read_text())
        assert summary['status'].startswith('passed ') and summary['shared_parasitics'] and summary['keep_couplings']
        assert Path(summary['macro_netlist'])==a.netlist and Path(summary['macro_spef'])==a.macro_spef
        assert summary['inputs'][str(a.netlist)]==sha(a.netlist)
        assert summary['inputs'][str(a.macro_spef)]==sha(a.macro_spef)
        assert summary['inputs'][str(a.top_spef)]==sha(a.top_spef)
        assert {k:int(v) for k,v in summary['counts'].items()}=={'SCLK':52,'osc_clk':1148}
        for row in summary['reports']:
            f=run/row['name'];assert sha(f)==row['sha256'] and f.stat().st_size==row['bytes']
        uncovered=check_annotation((run/'annotation.rpt').read_text(),instances)
        assert len(summary['net_reports'])==57 and set(summary['net_reports'].values())==set(nets)
        caps=[]
        for filename,name in summary['net_reports'].items():
            text=(run/filename).read_text();assert text.splitlines()[0].replace('\\','')=='Net '+name
            values=wire_values(text)
            ports=[pin for inst,pin in nets[name]['connections'] if inst=='i_core.u_digital']
            assert len(ports)<=1
            expected=float(nets[name]['total'])+sum(macro[pin] for pin in ports)
            caps.append(dict(net=name,expected_pF=expected,reported_pF=values,differences_pF=[v-expected for v in values]))
        slacks=summary['slacks_ns'];assert set(slacks)=={'setup','hold'} and all(math.isfinite(v) for v in slacks.values())
        violations=[s.strip() for s in (run/'violators.rpt').read_text().splitlines() if '(VIOLATED)' in s]
        rows.append(dict(corner=summary['corner'],slacks_ns=slacks,
            constrained_slack_status='passed' if min(slacks.values())>=0 else 'failed',
            slew_cap_fanout_status='failed' if violations else 'passed',violations=violations,
            macro_unannotated_source_open_outputs=60,partially_unannotated_drivers=0,
            other_unannotated_drivers=uncovered,physical_annotation_status='failed' if uncovered else 'passed',
            capacitance_comparison=caps,capacitance_numerical_acceptance='not run: no new tolerance'))
        held.extend(f for f in run.iterdir() if f.is_file())
    assert len(rows)==3 and {r['corner'] for r in rows}=={'fast','typ','slow'}
    result=dict(status='passed source/report audit; full-chip qualification incomplete',corners=rows,
        passed=['57 distinct positive wire-capacitance reports per corner','1200 original clocked-register coverage',
                '60 source-proven open dummy outputs per corner','Zero partial drivers','Exact report and macro source hashes'],
        failed=[r['corner']+': '+key for r in rows for key in ('constrained_slack_status','slew_cap_fanout_status','physical_annotation_status') if r[key]=='failed'],
        not_run=['Final native fill/supplemental metal/power/moved-pad extraction','Analog cell timing',
                 'Clock/load-bound qualification','Full-chip timing sign-off','Capacitance numerical acceptance'],
        not_applicable=['Statistical seed'],inputs_sha256={str(f):sha(f) for f in held})
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('corners','inputs_sha256')},indent=2))


if __name__=='__main__':main()
