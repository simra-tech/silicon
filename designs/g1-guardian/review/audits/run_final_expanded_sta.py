#!/usr/bin/env python3
"""Unchanged digital macro plus final routed SPEF, one declared timing corner."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from check_closed_macro_odb import sha,quote
from check_fullchip_def_odb import DESIGN,PDK
from final_route_context.lef_port_stub import port_stub


def candidate_macro(flow,parent):
    """Bind the replacement to the completed, immutable routed macro flow."""
    state_path=flow/'final_state.json'
    assert sha(state_path)=='c818cccb2eabc251fd00e3e89fd3b6d4bc9f0600a13deddff113a6feb98d45d9'
    state=json.loads(state_path.read_text())
    proof=json.loads((parent/'analysis.json').read_text())
    assert proof['status']=='passed isolated digital replacement and exact other-cell preservation'
    assert sha(parent/'digital_replaced_native.gds')==proof['GDS_sha256']
    assert proof['macro_sha256']==sha(Path(state['gds']))=='1a66208253ceacd1033ae97a4f4e67051755dbd8e38254ac53c0a9f34fefe5bf'
    macro=Path(state['nl']);spef=Path(state['spef']['nom_*'])
    assert sha(macro)=='6181b988eeaa28953a37bc11b2f4fb4b66325ed518c4cfa74387bfb83845a301'
    assert sha(spef)=='e6c895752812e2f16989f4e58c1835e8ac43436fc74c75c409caadd79ab629da'
    audit_path=flow/'independent_sta_audit.json';audit=json.loads(audit_path.read_text())
    assert audit['status']=='passed scoped routed macro STA and annotation audit'
    assert audit['inputs_sha256'][str(macro)]==sha(macro)
    held=[state_path,parent/'analysis.json',parent/'digital_replaced_native.gds',Path(state['gds']),audit_path]
    return macro,spef,held


def spef_commands(spef,macro_spef,macro_first=False,shared=False,keep=False):
    commands=['read_spef -corner CURRENT '+quote(spef),
              'read_spef -corner CURRENT -path i_core.u_digital '+quote(macro_spef)]
    if shared:
        assert not macro_first
        commands[1]='read_spef -name CURRENT -path i_core.u_digital '+quote(macro_spef)
    if keep:
        assert shared
        commands=[line.replace('read_spef ','read_spef -keep_capacitive_coupling ',1)for line in commands]
    if macro_first:commands.reverse()
    return commands


def engine_override(default,requested,expected):
    assert bool(requested)==bool(expected)
    if requested is None:return default
    assert requested.is_absolute() and requested.is_file()
    assert re.fullmatch(r'[0-9a-f]{64}',expected)
    assert sha(requested)==expected
    return requested


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rcx',type=Path,required=True)
    p.add_argument('--rcx-summary-sha256',help='Explicit successor RCX binding plus independently audited SPEF')
    p.add_argument('--sta-executable',type=Path,help='Explicit pinned-engine diagnostic; requires its exact SHA256')
    p.add_argument('--sta-sha256')
    p.add_argument('--corner',choices=('fast','typ','slow'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--digital-flow',type=Path,help='Qualified replacement macro flow; requires isolated parent candidate')
    p.add_argument('--parent-candidate',type=Path)
    p.add_argument('--bus-stubs',action='store_true',help='Use exact held LEF vector/direction declarations for TRIP and OSC; no timing model')
    p.add_argument('--macro-first',action='store_true',help='Source-held diagnostic: read macro SPEF before top SPEF')
    p.add_argument('--shared-parasitics',action='store_true',help='Reuse the CURRENT parasitic set for the second hierarchical SPEF read')
    p.add_argument('--keep-couplings',action='store_true',help='Diagnostic: preserve extracted coupling objects during import, with unchanged reduction factor 1')
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    routed_audit=json.loads((a.rcx/'independent_audit_r2.json').read_text())
    assert routed_audit['status']=='passed routed SPEF numerical/coverage/graph audit' and routed_audit['routed_net_count']==57
    source=a.rcx/'final_signal.nl.v';spef=a.rcx/'final_signal.nom.spef'
    routed_inputs=[]
    if a.rcx_summary_sha256:
        rcx_summary=a.rcx/'summary.json';assert sha(rcx_summary)==a.rcx_summary_sha256
        rcx=json.loads(rcx_summary.read_text())
        assert rcx['status']=='passed stock RCX tool completion and unchanged functional DB connectivity; independent audit pending'
        assert rcx['functional_instance_and_net_connectivity_unchanged']=='passed'
        outputs={r['name']:r for r in rcx['outputs']}
        assert set(outputs)=={source.name,spef.name}
        for f in [source,spef]:
            assert sha(f)==outputs[f.name]['sha256'] and f.stat().st_size==outputs[f.name]['bytes']
        assert all(sha(Path(f))==h for f,h in rcx['inputs'].items())
        assert routed_audit['input_sha256'][str(spef)]==sha(spef)
        assert all(sha(Path(f))==h for f,h in routed_audit['input_sha256'].items())
        routed_inputs=[rcx_summary]+[Path(f) for f in rcx['inputs']]+[Path(f) for f in routed_audit['input_sha256']]
    else:
        assert sha(source)=='337db3b1e5bc4686b421c185e25cc6bcd44327bc6b8eb0411a16a2f764e533c4'
        assert sha(spef)=='ceb5651e41c4dfc3ede324dd10febcbe53ddf3809c3db20aebbea0234cfd638d'
    suffix,io_suffix={'fast':('fast_1p32V_m40C','fast_1p32V_3p6V_m40C'),
                      'typ':('typ_1p20V_25C','typ_1p2V_3p3V_25C'),
                      'slow':('slow_1p08V_125C','slow_1p08V_3p0V_125C')}[a.corner]
    libs=[PDK/('libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_'+suffix+'.lib'),
          DESIGN/('blocks/g1_padring/ip/sg13g2_io_padbare/lib/sg13g2_io_'+io_suffix+'.lib')]
    macro=DESIGN/'blocks/g1_ctrl/layout/g1_digital.nl.v'
    macro_spef=DESIGN/'blocks/g1_ctrl/layout/g1_digital.nom.spef'
    assert bool(a.digital_flow)==bool(a.parent_candidate)
    candidate_inputs=[]
    if a.digital_flow:
        assert a.bus_stubs and a.shared_parasitics and a.keep_couplings and not a.macro_first
        macro,macro_spef,candidate_inputs=candidate_macro(a.digital_flow,a.parent_candidate)
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
    if a.digital_flow:
        sta=Path('/foss/tools/openroad-librelane/bin/sta')
        assert sha(sta)=='0d4f17d67f8c839804d01cde02763113ca62636e75d224d01c56fb30ebf0b492'
    default_sta=sta
    sta=engine_override(default_sta,a.sta_executable,a.sta_sha256)
    inputs={str(p):sha(p)for p in [source,spef,macro,macro_spef,sdc,child_sdc,old,sta,a.rcx/'independent_audit_r2.json']+libs+candidate_inputs+routed_inputs}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    stubs=[];stub_pins={}
    if a.bus_stubs:
        helper=Path(__file__).parent/'final_route_context/lef_port_stub.py'
        inputs[str(helper)]=sha(helper)
        (a.output/'lef_port_stub.py').write_bytes(helper.read_bytes())
        for name in ('g1_trip','g1_osc'):
            lef=DESIGN/'blocks'/name/'layout'/(name+'.lef')
            inputs[str(lef)]=sha(lef)
            text,pins=port_stub(lef.read_text(),name)
            stub=a.output/(name+'_declaration.v');stub.write_text(text)
            stubs.append(stub);stub_pins[name]=pins
    lines=['set sta_report_default_digits 9','define_corners CURRENT']
    lines+=['read_liberty -corner CURRENT '+quote(p)for p in libs]
    lines+=['read_verilog '+quote(stub)for stub in stubs]
    lines+=['read_verilog '+quote(macro),'read_verilog '+quote(source),'link_design g1_chip_top']
    reads=spef_commands(spef,macro_spef,a.macro_first,a.shared_parasitics,a.keep_couplings)
    lines+=constraints+['read_sdc '+quote(sdc)]+reads
    lines+=['set fp [open '+quote(a.output/'counts.tsv')+' w]',
            'foreach name {SCLK osc_clk} {',
            '  if {[llength [get_clocks -quiet $name]] != 1} {error "Clock missing or duplicated: $name"}',
            '  puts $fp "$name\t[llength [all_registers -clock $name]]"','}','close $fp',
            'report_checks -path_delay min -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > '+quote(a.output/'hold.rpt'),
            'report_checks -path_delay max -fields {slew cap input net fanout} -format full_clock_expanded -group_path_count 20 > '+quote(a.output/'setup.rpt'),
            'report_check_types -max_slew -max_capacitance -max_fanout -violators > '+quote(a.output/'violators.rpt'),
            'report_parasitic_annotation -report_unannotated > '+quote(a.output/'annotation.rpt'),
            'report_net {i_core.sclk_i} > '+quote(a.output/'sclk_net.rpt'),
            'report_net {i_core.sdo_o} > '+quote(a.output/'sdo_net.rpt'),
            'check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks > '+quote(a.output/'coverage.rpt'),
            'set fp [open '+quote(a.output/'slack.tsv')+' w]',
            'puts $fp "hold\t[worst_slack -min]"','puts $fp "setup\t[worst_slack -max]"','close $fp',
            'puts "FINAL_EXPANDED_STA_COMPLETE"']
    # Capture every extracted top-level net, including nets with no timing
    # driver. Do not silently limit the annotation review to passing paths.
    net_reports={}
    for index,row in enumerate(routed_audit['nets']):
        name=row['net'];report='net_{:02d}.rpt'.format(index)
        net_reports[report]=name
        # Escape brackets for OpenSTA's pattern-based get_nets interface.
        pattern=name.replace('[',r'\[').replace(']',r'\]')
        lines.insert(-1,'report_net '+quote(pattern)+' > '+quote(a.output/report))
    script=a.output/'sta.tcl';script.write_text('\n'.join(lines)+'\n')
    command=['timeout','--kill-after=5','180',str(sta),'-no_splash','-exit',str(script)]
    result=dict(status='running',corner=a.corner,inputs=inputs,command=command,stub_pins=stub_pins,macro_first=a.macro_first,shared_parasitics=a.shared_parasitics,keep_couplings=a.keep_couplings,net_reports=net_reports,
        scope='Expanded unchanged digital macro plus final routed signal SPEF; analog cells have no timing models',
        assumptions='Unchanged existing SDC clock periods, uncertainty, IO delays and loads; not new physical bounds',
        not_run=['Independent timing coverage and slack acceptance audit','Analog comparator/LS timing',
                 'Native fill and supplemental terminal metal parasitics','Clock/load-bound qualification'])
    result['engine_selection']=dict(default_path=str(default_sta),explicit_diagnostic=bool(a.sta_executable),
                                  actual_path=str(sta),sha256=sha(sta))
    if a.digital_flow:
        result.update(scope='Qualified replacement macro plus held 57 routed signal nets; not final full-physical extraction',
                      macro_netlist=str(macro),macro_spef=str(macro_spef),parent_candidate=str(a.parent_candidate))
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    start=time.monotonic()
    with (a.output/'sta.log').open('x')as log:child=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result.update(returncode=child.returncode,wall_s=time.monotonic()-start)
    try:
        assert child.returncode==0
        log=(a.output/'sta.log').read_text()
        assert 'FINAL_EXPANDED_STA_COMPLETE' in log and not re.search(r'(^|\n)(Error:|\[ERROR)',log)
        if a.bus_stubs:
            assert not re.search(r'Warning (164\d|165[0-8]):',log), 'SPEF import warning remains'
        if a.shared_parasitics:
            assert 'Found 0 partially unannotated drivers.' in (a.output/'annotation.rpt').read_text()
        counts=dict(line.split('\t')for line in (a.output/'counts.tsv').read_text().splitlines())
        assert {k:int(v)for k,v in counts.items()}=={'SCLK':52,'osc_clk':1148}
        slacks={key:float(value)for key,value in (line.split('\t')for line in (a.output/'slack.tsv').read_text().splitlines())}
        assert set(slacks)=={'hold','setup'} and all(math.isfinite(v)for v in slacks.values())
        for report,name in net_reports.items():
            assert (a.output/report).read_text().splitlines()[0].replace('\\','')=='Net '+name
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed STA execution and original clock-register coverage; independent acceptance pending',counts=counts,slacks_ns=slacks,
                      reports=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size)for p in a.output.glob('*.rpt')])
    except Exception as exc:
        result.update(status='failed STA execution or source/clock coverage gate',error=repr(exc));raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
