#!/usr/bin/env python3
"""Collect and execute independent physical checks with explicit, fail-closed status.

A fresh report directory is mandatory. A command's zero exit is insufficient:
DRC databases and checker-specific completion evidence determine check status.
"""
import argparse
import collections
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

BLOCK=Path(__file__).resolve().parents[2]
ROOT=Path(__file__).resolve().parents[6]
PDK=Path('/foss/pdks/ihp-sg13g2')
DRC=PDK/'libs.tech/klayout/tech/drc'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def portable(value):
    if isinstance(value,Path):value=str(value)
    if isinstance(value,str):return value.replace(str(ROOT)+os.sep,'').replace(str(ROOT),'.')
    if isinstance(value,list):return [portable(v) for v in value]
    if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
    return value


def markers(path):
    tree=ET.parse(path)
    if tree.getroot().tag!='report-database':raise ValueError('Not a KLayout report')
    if tree.find('items') is None:raise ValueError('KLayout item collection absent')
    names=[i.findtext('category') for i in tree.findall('./items/item')]
    if any(not name for name in names):raise ValueError('Marker category absent')
    categories=collections.Counter(name.strip("'") for name in names)
    return ('failed' if categories else 'passed'), {'markers':sum(categories.values()),'categories':dict(categories)}


def signature(path,success):
    text=path.read_text()
    if success in text:return 'passed',{'required_signature':success}
    return 'failed',{'reason':'Required explicit completion/pass signature absent','required_signature':success}


def supply_grid_status(log,metric):
    """Raw checker failures take precedence over potentially overwritten metrics."""
    if not log.exists():return 'not run',{'reason':'Raw post-strapping connectivity log absent','aggregate_metric':metric}
    value=log.read_text()
    failures=sorted(set(re.findall(r'Check connectivity failed on ([\w!]+)',value)))
    if failures:
        return 'failed',{'reason':'Raw post-strapping checker reports disconnected supply geometry',
                         'failed_nets':failures,'aggregate_metric':metric,
                         'unconnected_shape_warnings':value.count('Unconnected shape on net '),
                         'scope':'OpenROAD abstract-view check; physical GDS connectivity requires separate evidence'}
    if re.search(r'\[ERROR|\[WARNING.*PSM-',value):
        return 'failed',{'reason':'Unresolved post-strapping PSM error/warning','aggregate_metric':metric}
    requested=set(re.findall(r'check_power_grid -net (\w+)',value))
    passed=set(re.findall(r'All shapes on net (\w+) are connected',value))
    if not requested or not requested.issubset(passed):
        return 'not run',{'reason':'Explicit post-strapping completion absent for one or more requested nets',
                          'incomplete_nets':sorted(requested-passed),'aggregate_metric':metric}
    if isinstance(metric,(int,float)) and math.isfinite(metric) and metric>=0:
        return ('passed' if metric==0 else 'failed'),{'aggregate_metric':metric,'scope':'Retained abstract-view supply grid check; no fresh final-GDS validation'}
    return 'not run',{'reason':'Required retained supply-grid metric absent'}


class CheckRunner:
    def __init__(self,out,planned):
        self.out=out
        self.rows={name:{'name':name,'status':'not run','reason':'Pending execution'} for name in planned}
        self.save()

    def save(self):
        self.out.mkdir(parents=True,exist_ok=True)
        (self.out/'check_status.json').write_text(json.dumps(portable({'checks':list(self.rows.values()),
            'overall':'passed' if all(r['status'] in ('passed','not applicable') for r in self.rows.values()) else 'incomplete or failed'}),indent=2)+'\n')

    def record(self,name,status,**details):
        self.rows[name]={'name':name,'status':status,**details};self.save()

    def run(self,name,command,validate,timeout=900):
        log=self.out/(name+'.log');start=time.monotonic();code=None;timed_out=False
        try:
            with log.open('w') as output:
                proc=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
                try:code=proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
                    try:code=proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
        except OSError as error:
            self.record(name,'not run',reason=str(error),command=command);return
        details={'command':command,'exit_code':code,'timed_out':timed_out,'wall_seconds':time.monotonic()-start,'log':log.name}
        if timed_out:
            self.record(name,'not run',reason='Watchdog expired before completed check',**details);return
        if code:
            self.record(name,'failed',reason='Check process failed',**details);return
        try:
            status,assessment=validate(log);self.record(name,status,**details,**assessment)
        except (OSError,ValueError,ET.ParseError,json.JSONDecodeError) as error:
            self.record(name,'failed',reason='Missing/invalid acceptance evidence: '+str(error),**details)


COPY_MAP={
 'drc.klayout.json':'*-klayout-drc/reports/drc.klayout.json',
 'drc.klayout.lyrdb':'*-klayout-drc/reports/drc.klayout.lyrdb',
 'klayout-drc.log':'*-klayout-drc/klayout-drc.log',
 'density.klayout.json':'*-klayout-density/reports/density.klayout.json',
 'density.klayout.lyrdb':'*-klayout-density/reports/density.klayout.lyrdb',
 'antenna.klayout.json':'*-klayout-antenna/reports/antenna.klayout.json',
 'antenna.klayout.lyrdb':'*-klayout-antenna/reports/antenna.klayout.lyrdb',
 'klayout-xor.log':'*-klayout-xor/klayout-xor.log',
 'stapostpnr_summary.rpt':'*-openroad-stapostpnr/summary.rpt',
 'drc.magic.rpt':'*-magic-drc/reports/drc.magic.rpt',
 'lvs.netgen.rpt':'*-netgen-lvs/reports/lvs.netgen.rpt',
 'openroad-generatepdn.log':'*-openroad-generatepdn/openroad-generatepdn.log',
 'analog_straps.log':'*-openroad-generatepdn/analog_straps.log',
 'openroad-detailedrouting.log':'*-openroad-detailedrouting/openroad-detailedrouting.log',
 'odb-reportdisconnectedpins.log':'*-odb-reportdisconnectedpins/*.log',
 'full_disconnected_pins_table.txt':'*-odb-reportdisconnectedpins/full_disconnected_pins_table.txt',
 'flow.log':'flow.log','warning.log':'warning.log','error.log':'error.log',
 'metrics.json':'final/metrics.json',
}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('tag',nargs='?',default='assembly-1350')
    p.add_argument('--output',type=Path)
    p.add_argument('--collect-only',action='store_true',help='Preserve and assess existing evidence; new checks explicitly not run')
    p.add_argument('--threads',type=int,default=2,choices=[1,2])
    args=p.parse_args()
    os.environ['KLAYOUT_PATH']=str(PDK/'libs.tech/klayout')
    run=BLOCK/'flow/runs'/args.tag
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=(args.output or BLOCK/'reports'/f'{args.tag}-signoff-{stamp}-{os.getpid()}').resolve()
    if out.exists():raise FileExistsError('Refusing to overwrite prior signoff evidence')
    out.mkdir(parents=True)
    planned=['retained_hard_drc','retained_density','retained_antenna','retained_streamout_xor',
             'retained_routing','retained_sta','retained_magic_drc','retained_netgen_lvs',
             'retained_supply_grid','retained_critical_pins',
             'hard_drc','recommended_drc','precheck_drc','density','density_precheck','antenna',
             'pdn_net_overlap','pdn_macro_overlap','supply_isolation','core_lvs','full_io_lvs']
    checks=CheckRunner(out,planned)
    archive=out/'retained';archive.mkdir()
    copies=[]
    for target,pattern in COPY_MAP.items():
        matches=sorted(run.glob(pattern))
        if matches:
            source=matches[0];dest=archive/target;shutil.copyfile(source,dest)
            copies.append({'source':str(source.relative_to(ROOT)),'output':str(dest.relative_to(out)),
                           'sha256':sha(source),'selection':'first sorted match','matching_files':len(matches)})
        else:copies.append({'requested':pattern,'status':'not run','reason':'Source evidence absent'})
    for key,filename in [('retained_hard_drc','drc.klayout.json'),('retained_density','density.klayout.json'),('retained_antenna','antenna.klayout.json')]:
        path=archive/filename
        try:
            value=json.loads(path.read_text());total=value['total']
            if not isinstance(total,int) or total<0:raise ValueError('Invalid total')
            checks.record(key,'passed' if total==0 else 'failed',markers=total,evidence=str(path.relative_to(out)),scope='Retained original run; not a new final-GDS check')
        except (OSError,KeyError,ValueError) as error:checks.record(key,'not run',reason=str(error))
    xor=archive/'klayout-xor.log'
    if xor.exists() and (m:=re.search(r'Total XOR differences:\s*(\d+)',xor.read_text())):
        count=int(m[1]);checks.record('retained_streamout_xor','passed' if count==0 else 'failed',differences=count,scope='Retained original pre-fill streamout')
    else:checks.record('retained_streamout_xor','not run',reason='Explicit XOR count absent')
    metric_path=archive/'metrics.json'
    try:metrics=json.loads(metric_path.read_text())
    except (OSError,ValueError):metrics={}
    for name,key in [('retained_routing','route__drc_errors'),
                     ('retained_magic_drc','magic__drc_error__count'),
                     ('retained_netgen_lvs','design__lvs_error__count'),
                     ('retained_critical_pins','design__critical_disconnected_pin__count')]:
        count=metrics.get(key)
        if isinstance(count,(int,float)) and math.isfinite(count) and count>=0:
            checks.record(name,'passed' if count==0 else 'failed',metric=key,value=count,
                          scope='Retained flow metric, narrower than full physical signoff')
        else:checks.record(name,'not run',reason='Required retained metric absent: '+key)
    status,details=supply_grid_status(archive/'analog_straps.log',metrics.get('design__power_grid_violation__count'))
    checks.record('retained_supply_grid',status,evidence='retained/analog_straps.log',**details)
    corners=['nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C']
    slack={f'timing__{kind}__ws__corner:{corner}':metrics.get(f'timing__{kind}__ws__corner:{corner}')
           for corner in corners for kind in ('setup','hold')}
    if all(isinstance(v,(int,float)) and math.isfinite(v) for v in slack.values()):
        checks.record('retained_sta','passed' if all(v>=0 for v in slack.values()) else 'failed',
                      slacks_ns=slack,scope='Retained three-corner setup/hold metrics; no new timing or CDC analysis')
    else:checks.record('retained_sta','not run',reason='Six required retained corner slacks not all present')
    gds=run/'final/gds/g1_chip_top.gds';deffile=run/'final/def/g1_chip_top.def'
    manifest={'command_arguments':vars(args)|{'output':str(out)},'copied_evidence':copies,
              'final_gds':str(gds.relative_to(ROOT)),'final_gds_sha256':sha(gds) if gds.exists() else None,
              'collection_scope':'Fresh directory; retained evidence does not replace current final-GDS checks',
              'pdk_stamp':(PDK/'COMMIT').read_text().strip() if (PDK/'COMMIT').exists() else 'not available',
              'script_sha256':sha(Path(__file__))}
    # Path values need stable JSON conversion; no environment or private context copied.
    (out/'manifest.json').write_text(json.dumps(portable(manifest),indent=2,default=str)+'\n')
    checks.record('full_io_lvs','not run',reason='Core-only comparison excludes IO. No qualified full-IO procedure is implemented; no waiver inferred.')
    if not args.collect_only and gds.exists() and deffile.exists():
        def deckcheck(name,deck,options=()):
            report=out/(name+'.lyrdb')
            command=['klayout','-b','-zz','-r',str(deck),'-rd','input='+str(gds),'-rd','topcell=g1_chip_top',
                     '-rd','report='+str(report),'-rd','threads='+str(args.threads),*options]
            checks.run(name,command,lambda log:markers(report))
        deckcheck('hard_drc',DRC/'ihp-sg13g2.drc',['-rd','run_mode=deep','-rd','no_recommended=true'])
        deckcheck('recommended_drc',DRC/'ihp-sg13g2.drc',['-rd','run_mode=deep'])
        deckcheck('precheck_drc',DRC/'ihp-sg13g2.drc',['-rd','run_mode=deep','-rd','no_recommended=true','-rd','precheck_drc=true'])
        deckcheck('density',DRC/'rule_decks/density.drc')
        deckcheck('density_precheck',DRC/'rule_decks/density.drc',['-rd','precheck_drc=true'])
        deckcheck('antenna',DRC/'rule_decks/antenna.drc')
        lefs=[BLOCK.parent/path for path in ['g1_ctrl/layout/g1_digital.lef','g1_bgr/layout/g1_bgr.lef','g1_sense/layout/g1_sense.lef','g1_trip/layout/g1_trip.lef','g1_gate/layout/g1_gate.lef','g1_t2f/layout/g1_t2f.lef','g1_osc/layout/g1_osc.lef','g1_ctrl/ls/layout/g1_ls_up.lef','g1_dose/layout/g1_dose_macro.lef','g1_dut/layout/g1_dut_macro.lef']]
        lefs.append(BLOCK/'ip/sg13g2_io_padbare/lef/sg13g2_io.lef')
        for name,success,extra in [
            ('pdn_net_overlap','overlaps between different supply nets: 0',[]),
            ('pdn_macro_overlap','problems: 0',['-rd','lefs='+','.join(map(str,lefs))]),
            ('supply_isolation','supply isolation: passed',[])]:
            cmd=['klayout','-b','-rd','gds='+str(gds),'-rd','defp='+str(deffile),*extra,'-r',str(BLOCK/'flow/lvs'/f'{name}.py')]
            checks.run(name,cmd,lambda log,s=success:signature(log,s))
        core=ROOT/'build/scratch'/('core-'+out.name)
        checks.run('core_lvs',['bash',str(BLOCK/'flow/lvs/run_core_lvs.sh'),str(run),str(core)],
                   lambda log:signature(log,'Comparison mode: PASS (netlists match).'),timeout=1800)
    elif not args.collect_only:
        for name in planned:
            if checks.rows[name].get('reason')=='Pending execution':
                checks.record(name,'not run',reason='Final GDS or DEF missing')
    else:
        for name in planned:
            if checks.rows[name].get('reason')=='Pending execution':
                checks.record(name,'not run',reason='Collection-only invocation; execution intentionally not requested')
    print(json.dumps(portable({'output':str(out),'checks':[{k:r[k] for k in ('name','status')} for r in checks.rows.values()]}),indent=2))
    if any(r['status'] not in ('passed','not applicable') for r in checks.rows.values()):raise SystemExit(1)


if __name__=='__main__':main()
