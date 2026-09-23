#!/usr/bin/env python3
"""Independent saved-log coverage/gain audit of the required standalone108 grid."""
import argparse,hashlib,itertools,json,math,re
from pathlib import Path

SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
VECTORS={'v(isense)','v(vped)','v(vref_buf)','v(xdut.vp)','v(xdut.vn)','v(xdut.vped_ref)','i(vdd)','v(shp)','v(cm)'}
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def independent_rows(log):
    rows=[]
    for i in range(10):
        sections=log.split('DC_ROW_'+str(i)+'_BEGIN\n');assert len(sections)==2
        part,tail=sections[1].split('DC_ROW_'+str(i)+'_END',1)
        pairs=re.findall(r'^([vi]\([^\n=]+\))\s*=\s*(\S+)',part,re.M)
        assert len(pairs)==9 and {k for k,_ in pairs}==VECTORS
        row={k:float(v) for k,v in pairs};assert all(math.isfinite(x) for x in row.values());rows.append(row)
    return rows
def parser_controls(log):
    good=independent_rows(log);assert len(good)==10
    bad=[log.replace('DC_ROW_9_END','MISSING_END',1),log.replace('v(isense)', 'v(wrong)',1)]
    # Mutate within the detailed first row, not an earlier unrelated print.
    start=log.index('DC_ROW_0_BEGIN\n');end=log.index('DC_ROW_0_END',start)
    section=log[start:end]
    bad[1]=log[:start]+section.replace('v(isense)','v(wrong)',1)+log[end:]
    changed=re.sub(r'(v\(isense\)\s*=\s*)\S+',r'\g<1>nan',section,count=1)
    bad.append(log[:start]+changed+log[end:])
    for candidate in bad:
        try:independent_rows(candidate)
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Malformed/nonfinite row accepted')
    assert (2.-1.)/.05==20.
    return dict(status='passed',controls=['ten-row parse','missing marker rejects','wrong vector rejects','nonfinite rejects','V/V gain unit control'])
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--packet',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    pc=json.loads((a.packet/'contract.json').read_text());assert pc['candidate_source_sha256']==SOURCE and sha(a.packet/'candidate.spice')==SOURCE
    tuples=list(itertools.product(['tt','ss','ff'],['typ','bcs','wcs'],[3.0,3.3,3.6],[-40,27,85,125]))
    expected={f'{m}_{r}_{v}V_{t}C':(m,r,v,t) for m,r,v,t in tuples}
    assert set(expected)=={q['case'] for q in pc['cases']} and len(expected)==108
    tested=parser_controls((a.parent/'tt_typ_3.3V_27C/candidate/run.log').read_text())
    results=[];bindings={};query=pc['queries'];assert len(query)==len(set(query))==529
    for case,corner in sorted(expected.items()):
        folder=a.parent/case/'candidate';summary=json.loads((folder/'summary.json').read_text());contract=json.loads((folder/'contract.json').read_text());runtime=json.loads((folder/'provenance.json').read_text());log=(folder/'run.log').read_text()
        assert summary['status']=='passed source/finite DC tuple' and summary['case']==case and summary['kind']=='candidate'
        assert contract['case']==case and contract['corner']==list(corner) and contract['source_sha256']==SOURCE
        assert sha(folder/'candidate.spice')==SOURCE and sha(folder/'probe.cir')==contract['deck_sha256']
        assert contract['packet_sha256']==sha(a.packet/'contract.json') and summary['runtime']['status']=='completed' and summary['runtime']['returncode']==0
        assert not re.search(r'(?im)^\s*(?:error|fatal)\b|timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',log)
        assert 'QUALIFICATION_END' in log
        snapshots=[]
        for when in ['BEFORE','AFTER']:
            section,=re.findall(r'^SENSE_'+when+r'_BEGIN\n(.*?)^SENSE_'+when+r'_END$',log,re.M|re.S)
            pairs=re.findall(r'^(@[^\n=]+)\s*=\s*(\S+)',section,re.M)
            pairs=[[k.strip(),v] for k,v in pairs];assert [k for k,v in pairs]==query and all(math.isfinite(float(v)) for k,v in pairs);snapshots.append(pairs)
        assert snapshots[0]==snapshots[1]==summary['parameter_before']==summary['parameter_after']
        rows=independent_rows(log);assert rows==summary['rows']
        points={}
        for index,(cm,shunt) in enumerate(itertools.product([-.1,0,.3],[0,.025,.05])):
            row=rows[index];assert abs(row['v(shp)']-(cm+shunt/2))<=1e-12 and abs(row['v(cm)']-(cm-shunt/2))<=1e-12
            points[(cm,shunt)]=row
        delta={key:abs(rows[0][key]-rows[-1][key]) for key in VECTORS}
        assert all(v<=(1e-9 if key.startswith('i(') else 1e-6) for key,v in delta.items())
        gains={str(cm):(points[(cm,.05)]['v(isense)']-points[(cm,0)]['v(isense)'])/.05 for cm in [-.1,0,.3]}
        assert gains==summary['gains_V_per_V'];gain_status='passed' if all(19.9<=x<=20.1 for x in gains.values()) else 'failed';assert gain_status==summary['gain_status']
        results.append(dict(case=case,corner=corner,gains_V_per_V=gains,gain_status=gain_status,return_exact=rows[0]==rows[-1],return_absolute_delta=delta,elapsed_s=summary['runtime']['wall_s']))
        bindings[case]={n:sha(folder/n) for n in ['summary.json','contract.json','candidate.spice','probe.cir','provenance.json','run.json','run.log','runner.py']}
        if len(results)>1:assert runtime==previous_runtime
        previous_runtime=runtime
    failures=[q['case'] for q in results if q['gain_status']=='failed']
    report=dict(status='passed full declared standalone grid' if not failures else 'failed original gain requirement',
        controls=tested,tuples=108,unique_CM_shunt_points=972,return_control_points=108,source_primitive_count=159,observed_parameters_per_tuple=529,
        all529_before_after_exact=True,all_source_runtime_finite_checks='passed',failed_gain_cases=failures,
        gain_min=min(x for q in results for x in q['gains_V_per_V'].values()),gain_max=max(x for q in results for x in q['gains_V_per_V'].values()),
        exact_return_count=sum(q['return_exact'] for q in results),source_sha256=SOURCE,packet_sha256=sha(a.packet/'contract.json'),bindings=bindings,results=results,
        scope=pc['scope'],offset_acceptance='not assessed; source-dependent joint calibration remains separate',full_PEX='not qualified',actual_BGR_full_TRIP_108='not run')
    a.output.mkdir(parents=True);(a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');(a.output/'source.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in report.items() if k not in ['results','bindings']},indent=2))
if __name__=='__main__':main()
