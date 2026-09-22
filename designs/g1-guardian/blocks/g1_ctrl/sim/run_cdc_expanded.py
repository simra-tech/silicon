#!/usr/bin/env python3
"""Required broader digital clock/phase/reset screen; not timed GLS or pad PEX."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bench=HERE/'tb_cdc_contract.v'
    assert sha(bench)=='1c7644a9d87477421aa459e7c8c475334783e9f89d348e4731f74f5a371b12d5'
    text=bench.read_text()
    changes=[
        ('integer rate, phase, cut, i, errors=0, checks=0;',
         'integer rate, phase, cut, i, divsel, skew, errors=0, checks=0;\n    real data_delay=2., output_delay=0.;\n    wire sdo_delayed;\n    assign #(output_delay) sdo_delayed=sdo;'),
        ('#2 sdi=data; #(serial_t/2-1) sclk=1;',
         '#(data_delay) sdi=data; #(serial_t/2+1-data_delay) sclk=1;'),
        ('#2 b[j]=sdo;','#2 b[j]=sdo_delayed;'),
        ('for(rate=0;rate<3;rate=rate+1)begin',
         'for(skew=0;skew<3;skew=skew+1)begin\n        for(divsel=0;divsel<3;divsel=divsel+1)begin\n        for(rate=0;rate<5;rate=rate+1)begin'),
        ('osc_t=(rate==0)?125.0:(rate==1)?100.0:83.333333;\n            serial_t=osc_t;',
         'osc_t=(rate==0)?(1000.0/7.367):(rate==1)?125.0:(rate==2)?100.0:(rate==3)?(1000.0/12.0):(1000.0/13.768);\n'
         '            serial_t=osc_t*((divsel==0)?1:(divsel==1)?2:10);\n'
         '            data_delay=(skew==0)?2.0:(skew==1)?5.0:10.0;\n'
         '            output_delay=(skew==0)?0.0:(skew==1)?5.0:10.0;'),
        ('$display("CDC_CONTRACT checks=%0d errors=%0d; 8/10/12MHz,16 phases,24 reset positions per frequency",checks,errors);',
         'end end\n        if(checks!=4410)$fatal(1,"Missing expected CDC checks");\n'
         '        $display("CDC_EXPANDED checks=%0d errors=%0d;5clockrates3serialratios3delayprofiles16phases24resetpositions",checks,errors);')]
    for old,new in changes:
        assert text.count(old)==1,old
        text=text.replace(old,new)
    sources=[HERE.parent/'rtl'/name for name in ('g1_sync2.v','g1_serial.v','g1_trip_timer.v','g1_regfile.v','g1_digital_top.v')]
    sources += [HERE.parents[1]/'g1_seu/rtl'/name for name in ('g1_tmr_reg.v','g1_seu_chain.v','g1_seu.v')]
    bindings={str(p.relative_to(ROOT)):sha(p) for p in sources+[bench,Path(__file__)]}
    a.output.mkdir(parents=True);out=a.output.resolve()
    tb=out/'testbench.v';tb.write_text(text)
    env=dict(os.environ,LD_LIBRARY_PATH='/foss/tools/iverilog/lib:'+os.environ.get('LD_LIBRARY_PATH',''))
    result=dict(status='running',source_sha256=bindings,testbench_sha256=sha(tb),
                clock_MHz=[7.367,8,10,12,13.768],serial_period_ratios=[1,2,10],
                delay_profiles_ns=[dict(SDI=2,SDO=0),dict(SDI=5,SDO=5),dict(SDI=10,SDO=10)],
                limits='Digital sensitivity fixtures; delays are assumed, not actual IO extraction. Clock extrema diagnostic until physical timing closure. No metastability MTBF or timed GLS credit.',
                expected_assertions=4410,timed_GLS='not run',actual_pad_delays='not run',seed='not applicable')
    phases=[]
    for kind,cmd in [('compile',['iverilog','-g2012','-Wall','-Wno-timescale','-o',str(out/'test.vvp'),str(tb)]+list(map(str,sources))),('simulation',['vvp','-n',str(out/'test.vvp')])]:
        start=time.monotonic()
        with (out/(kind+'.log')).open('x') as log:
            proc=subprocess.run(['timeout','--kill-after=5','120']+cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
        phases.append(dict(kind=kind,returncode=proc.returncode,wall_s=time.monotonic()-start,command=cmd,log_sha256=sha(out/(kind+'.log'))))
        if proc.returncode:break
    content=(out/'simulation.log').read_text() if (out/'simulation.log').exists() else ''
    result['phases']=phases
    result['bindings_unchanged']=all(sha(ROOT/p)==h for p,h in bindings.items())
    result['status']='passed' if len(phases)==2 and all(p['returncode']==0 for p in phases) and 'CDC_EXPANDED checks=4410 errors=0;' in content and 'ALL TESTS PASSED' in content and not re.search(r'FAIL|FATAL',content) and result['bindings_unchanged'] else 'failed'
    result['iverilog_version']=subprocess.run(['iverilog','-V'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,env=env).stdout.splitlines()[0]
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='passed' else 1)

if __name__=='__main__':main()
