#!/usr/bin/env python3
"""Attribute reported analog-pad slew to unchanged abstract Liberty tables; no waiver."""
import argparse,hashlib,json,re
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def group(text,header):
    assert text.count(header)==1
    start=text.index(header)+len(header)
    assert text[start:].lstrip().startswith('{')
    start=text.index('{',start);depth=1
    for end in range(start+1,len(text)):
        depth += (text[end]=='{')-(text[end]=='}')
        if depth==0:return text[start+1:end]
    raise AssertionError('Unclosed group')

def source_tables(lib):
    cell=group(lib,'cell (sg13g2_IOPadAnalog)')
    assert 'timing_model_type : "abstracted";' in cell
    pin=group(cell,'pin (pad)')
    assert 'direction : "inout";' in pin
    timing=group(pin,'timing ()')
    assert 'related_pin : "pad";' in timing
    output={}
    for kind,expected in [('rise_transition',200.),('fall_transition',200.),('cell_rise',1000.),('cell_fall',1000.)]:
        body=group(timing,kind+' (delay_template_2x2)')
        values=[float(v) for quoted in re.findall(r'"([0-9., ]+)"',body) for v in quoted.split(',')]
        assert len(values)==4 and all(v==expected for v in values),(kind,values)
        output[kind]=values
    assert 'timing (' not in group(cell,'pin (padbare)')
    return output

def validate_violation(line,netlist):
    match=re.fullmatch(r'(\S+)/(pad|padbare)\s+(\S+)\s+(\S+)\s+(\S+)\s+\(VIOLATED\)',line)
    assert match
    instance,pin,limit,slew,slack=match.groups()
    assert float(limit)==3.5 and float(slew)==200 and float(slack)<0
    assert len(re.findall(r'\bsg13g2_IOPadAnalog\s+'+re.escape(instance)+r'\s*\(',netlist))==1
    return dict(instance=instance,pin=pin,limit_ns=float(limit),reported_slew_ns=float(slew),reported_slack_ns=float(slack))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit',type=Path,required=True);p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(a.run)==3
    root=next(v for v in Path(__file__).resolve().parents if (v/'flow/run.sh').exists())
    previous=json.loads(a.audit.read_text());assert previous['status']=='passed source/report audit; full-chip qualification incomplete'
    inputs={str(a.audit):sha(a.audit)};records=[]
    for run in a.run:
        summary=run/'summary.json';meta=json.loads(summary.read_text())
        original,=[c for c in previous['corners'] if c['corner']==meta['corner']]
        assert original['slew_cap_fanout_status']=='failed' and original['constrained_slack_status']=='passed'
        io,=[f for f in meta['inputs'] if 'sg13g2_io_padbare/lib/' in f]
        lib=root/io[len('/work/'):] if io.startswith('/work/') else Path(io)
        nl,=[Path(f) for f in meta['inputs'] if f.endswith('/final_signal.nl.v')]
        assert sha(lib)==meta['inputs'][io] and sha(nl)==meta['inputs'][str(nl)]
        tables=source_tables(lib.read_text())
        report=run/'violators.rpt';rows=[v.strip() for v in report.read_text().splitlines() if '(VIOLATED)' in v]
        assert rows==original['violations'] and len(rows)==12
        violations=[validate_violation(v,nl.read_text()) for v in rows]
        records.append(dict(corner=meta['corner'],constant_abstract_tables=tables,violations=violations,
            digital_cell_violation_count=0,original_global_slew_status='failed',
            interpretation='Reported200ns equals unchanged abstract self-related pad transition table. This is source attribution, not measured or transistor-simulated pad slew and not an electrical exemption.'))
        inputs.update({str(f):sha(f) for f in [summary,lib,nl,report]})
    assert {r['corner'] for r in records}=={'fast','typ','slow'}
    a.output.write_text(json.dumps(dict(status='passed exact analog-pad table attribution; original global timing failure retained',inputs=inputs,script_sha256=sha(Path(__file__)),corners=records,
        no_library_or_SDC_changes=True,not_run=['Actual analog-pad RC/electrical slew bounds','Complete native physical annotation','Full timing signoff'],not_applicable=['Random seed for read-only report attribution']),indent=2)+'\n')

if __name__=='__main__':main()
