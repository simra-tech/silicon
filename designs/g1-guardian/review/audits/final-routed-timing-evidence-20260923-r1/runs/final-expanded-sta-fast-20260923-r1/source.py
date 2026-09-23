#!/usr/bin/env python3
"""Unchanged digital macro plus final routed SPEF, one declared timing corner."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from check_closed_macro_odb import sha,quote
from check_fullchip_def_odb import DESIGN,PDK


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rcx',type=Path,required=True)
    p.add_argument('--corner',choices=('fast','typ','slow'),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert json.loads((a.rcx/'independent_audit_r2.json').read_text())['routed_net_count']==57
    source=a.rcx/'final_signal.nl.v';spef=a.rcx/'final_signal.nom.spef'
    assert sha(source)=='337db3b1e5bc4686b421c185e25cc6bcd44327bc6b8eb0411a16a2f764e533c4'
    assert sha(spef)=='ceb5651e41c4dfc3ede324dd10febcbe53ddf3809c3db20aebbea0234cfd638d'
    suffix,io_suffix={'fast':('fast_1p32V_m40C','fast_1p32V_3p6V_m40C'),
                      'typ':('typ_1p20V_25C','typ_1p2V_3p3V_25C'),
                      'slow':('slow_1p08V_125C','slow_1p08V_3p0V_125C')}[a.corner]
    libs=[PDK/('libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_'+suffix+'.lib'),
          DESIGN/('blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_'+io_suffix+'.lib')]
    macro=DESIGN/'blocks/g1_ctrl/layout/g1_digital.nl.v'
    macro_spef=DESIGN/'blocks/g1_ctrl/layout/g1_digital.nom.spef'
    sdc=DESIGN/'blocks/g1_padring/flow/g1_chip_top.sdc'
    child_sdc=DESIGN/'blocks/g1_ctrl/layout/g1_digital_top.sdc'
    old=DESIGN/'blocks/g1_padring/flow/runs/assembly-1350/38-openroad-globalrouting/_env.tcl'
    keys=['DESIGN_NAME','CLOCK_PORT','CLOCK_NET','CLOCK_PERIOD','IO_DELAY_CONSTRAINT',
          'MAX_FANOUT_CONSTRAINT','OUTPUT_CAP_LOAD','CLOCK_UNCERTAINTY_CONSTRAINT',
          'CLOCK_TRANSITION_CONSTRAINT','TIME_DERATING_CONSTRAINT']
    constraints=[]
    for key in keys:
        values=re.findall(r'^set ::env\('+key+r'\) (.*)$',old.read_text(),re.M)
        assert len(values)==1
        constraints.append('set ::env('+key+') '+values[0])
    sta=Path(shutil.which('sta'));assert sta.is_file()
    inputs={str(p):sha(p)for p in [source,spef,macro,macro_spef,sdc,child_sdc,old,sta]+libs}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    lines=['set sta_report_default_digits 9','define_corners CURRENT']
    lines+=['read_liberty -corner CURRENT '+quote(p)for p in libs]
    lines+=['read_verilog '+quote(macro),'read_verilog '+quote(source),'link_design g1_chip_top']
    lines+=constraints+['read_sdc '+quote(sdc),'read_spef -corner CURRENT '+quote(spef),
                        'read_spef -corner CURRENT -path i_core.u_digital '+quote(macro_spef)]
    lines+=['set fp [open '+quote(a.output/'counts.tsv')+' w]',
            'foreach name {SCLK osc_clk} {',
            '  if {[llength [get_clocks -quiet $name]] != 1} {error "Clock missing or duplicated: $name"}',
            '  puts $fp "$name\t[llength [all_registers -clock $name]]"','}','close $fp',
            'report_checks -path_delay min -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > '+quote(a.output/'hold.rpt'),
            'report_checks -path_delay max -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > '+quote(a.output/'setup.rpt'),
            'report_check_types -max_slew -max_capacitance -max_fanout -violators > '+quote(a.output/'violators.rpt'),
            'report_parasitic_annotation -report_unannotated > '+quote(a.output/'annotation.rpt'),
            'check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > '+quote(a.output/'coverage.rpt'),
            'set fp [open '+quote(a.output/'slack.tsv')+' w]',
            'puts $fp "hold\t[worst_slack -min]"','puts $fp "setup\t[worst_slack -max]"','close $fp',
            'puts "FINAL_EXPANDED_STA_COMPLETE"']
    script=a.output/'sta.tcl';script.write_text('\n'.join(lines)+'\n')
    command=['timeout','--kill-after=5','180',str(sta),'-no_splash','-exit',str(script)]
    result=dict(status='running',corner=a.corner,inputs=inputs,command=command,
        scope='Expanded unchanged digital macro plus final routed signal SPEF; analog cells have no timing models',
        assumptions='Unchanged existing SDC clock periods, uncertainty, IO delays and loads; not new physical bounds',
        not_run=['Independent timing coverage and slack acceptance audit','Analog comparator/LS timing',
                 'Native fill and supplemental terminal metal parasitics','Clock/load-bound qualification'])
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    start=time.monotonic()
    with (a.output/'sta.log').open('x')as log:child=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result.update(returncode=child.returncode,wall_s=time.monotonic()-start)
    try:
        assert child.returncode==0
        log=(a.output/'sta.log').read_text()
        assert 'FINAL_EXPANDED_STA_COMPLETE' in log and not re.search(r'(^|\n)(Error:|\[ERROR)',log)
        counts=dict(line.split('\t')for line in (a.output/'counts.tsv').read_text().splitlines())
        assert {k:int(v)for k,v in counts.items()}=={'SCLK':52,'osc_clk':1148}
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed STA execution and original clock-register coverage; independent acceptance pending',counts=counts,
                      reports=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size)for p in a.output.glob('*.rpt')])
    except Exception as exc:
        result.update(status='failed STA execution or source/clock coverage gate',error=repr(exc));raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
