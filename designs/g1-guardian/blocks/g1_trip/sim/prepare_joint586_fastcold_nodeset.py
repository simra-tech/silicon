#!/usr/bin/env python3
"""Prepare three OP-only initialization controls; no new analog execution."""
import difflib
import json
from pathlib import Path
import re
from run_joint586_transients import SIM, ROOT, sha
from result_directory import allocate_run

ORIGINAL=SIM/'qualification/joint586-fast-fixture-controls-20260923-b-low_cold_cm0'
PACKET=SIM/'qualification/joint586-fastcold-nodeset-op-contract-20260923-a.json'
NODES=['vref','iptat','vref_buf','vped','isense','xt.icmp','xt.vth_soft','xt.vth_hard']


def guesses(log):
    section=log.split('BIAS_OBSERVATION_OP\n',1)[1].split('BIAS_OBSERVATION_OP_END',1)[0]
    values=dict(re.findall(r'v\(([^)]+)\)\s*=\s*([-+0-9.eE]+)',section))
    assert all(n in values for n in NODES)
    return {n:values[n] for n in NODES}


def transform(original,run_id,label,values):
    assert label in ['sparse','sparse_nodeset','klu_nodeset']
    assert list(values)==NODES and all('#' not in n for n in values)
    lines=original.splitlines(True);replacements=[]
    for i,line in enumerate(lines):
        if line.startswith('tran '):
            assert line=='tran 0.2n 1.02u 0 0.2n\n'
            replacements.append((i,line,'* OP-only diagnostic: no transient requested\n'))
        elif line.startswith('meas tran '):
            replacements.append((i,line,'* OP-only diagnostic: removed '+line))
        elif line.startswith('wrdata '):
            replacements.append((i,line,'wrdata qualification/'+run_id+'/op.dat '+' '.join('v('+n+')' for n in NODES)+'\n'))
        elif line=='echo JOINT_POPULATION_TRAN_END\n':
            replacements.append((i,line,'echo JOINT_NODESET_OP_END\n'))
    assert len(replacements)==11 and sum(old.startswith('meas tran ') for _,old,_ in replacements)==8
    for i,old,new in replacements:assert lines[i]==old;lines[i]=new
    op=''.join(lines)
    added=''
    if label!='sparse':added+='.nodeset '+' '.join('v('+n+')='+values[n] for n in NODES)+'\n'
    if label=='klu_nodeset':added+='.options klu\n'
    assert op.count('.control\n')==1
    result=op.replace('.control\n',added+'.control\n')
    inverse=result.replace(added+'.control\n','.control\n',1).splitlines(True)
    for i,old,new in replacements:assert inverse[i]==new;inverse[i]=old
    assert ''.join(inverse)==original
    assert not any(line.startswith(('tran ','meas tran ','.ic ')) for line in result.splitlines())
    return result,dict(replacements=[dict(line=i+1,original=old,op_only=new) for i,old,new in replacements],added_algorithm_lines=added,exact_inverse_restores_original=True)


def main():
    assert not PACKET.exists()
    oldprep=json.loads((ORIGINAL/'preparation.json').read_text())
    values=guesses((ORIGINAL/'run.log').read_text())
    # These are literal canonical circuit nets: top-level XS/XT interfaces and
    # the internal named TRIP conditioning/DAC nets, not OSDI device #labels.
    body=(ORIGINAL/'population_transient.cir').read_text()
    assert 'XS shp shn vref iptat isense vped vref_buf vdda 0 g1_sense' in body
    trip=(ORIGINAL/'trip.spice').read_text().lower()
    assert all(re.search(r'\b'+n.split('.')[-1]+r'\b',trip) for n in NODES if n.startswith('xt.'))
    sources={n:sha(ORIGINAL/n) for n in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']}
    cases=[]
    for label in ['sparse','sparse_nodeset','klu_nodeset']:
        run='joint586-fastcold-op-'+label.replace('_','-')+'-20260923-a';out=allocate_run(SIM,run)
        for n in sources:(out/n).write_bytes((ORIGINAL/n).read_bytes())
        deck,audit=transform(body,run,label,values);(out/'op.cir').write_text(deck)
        (out/'declared_op_difference.diff').write_text(''.join(difflib.unified_diff(body.splitlines(True),deck.splitlines(True),fromfile='originalFailedFastLowcold',tofile=label)))
        (out/'transform_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        cases.append(dict(label=label,run=run,deck_sha256=sha(out/'op.cir'),transform_sha256=sha(out/'transform_audit.json'),watchdog_s=300,solver='klu' if label.startswith('klu') else 'sparse'))
    paths=[ORIGINAL/n for n in ['population_transient.cir','preparation.json','run.log','run.json','summary.json','provenance.json']+list(sources)]
    paths += [SIM/n for n in ['prepare_joint586_fastcold_nodeset.py','run_joint586_fastcold_nodeset.py','test_joint586_fastcold_nodeset.py','run_joint586_transients.py','run_bgr_substitution_draw_audit.py','run_nominal_clock_probe.py','analyze_bgr_substitution_outcomes.py','.spiceinit']]
    packet=dict(status='prepared only; no launch lease',cases=cases,original=ORIGINAL.name,source_hashes=sources,
        guesses_original_printed_strings=values,guess_precision='Exact original15digit printed strings; no additional precision invented.',
        canonical_aliases=dict(vref='XBGR.VREF / XS.VREF',iptat='XBGR.IPTAT / XS.IPTAT',vref_buf='XS.VREF_BUF / XT reference input',vped='XS.VPED',isense='XS.ISENSE / XT.ISENSE',**{'xt.icmp':'TRIP conditioning node','xt.vth_soft':'TRIP soft DAC output','xt.vth_hard':'TRIP hard DAC output'}),
        groups=oldprep['groups'],expected_vector=oldprep['expected_vector'],expected_runtime_identity=oldprep['expected_runtime_identity'],
        bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        scope='Three OP-only controls, same circuit/corner/rails/seed78001/codes135,151. SPARSE baseline then SPARSE+same8temporarycanonicalnodeset and KLU+same8nodeset. No IC/UIC/card/tolerance/timestep change. Before/after11512 and27 exact. Exact OP comparisons retained separately; no invented bound, no transient/fast30/physical/adoption claim.',
        interpretation='Nodeset supplies preliminary guesses, released before finalOP. It can influence solution basin. OP success alone cannot establish positive-time stepping or accuracy.',
        documentation='https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf section11.2.1')
    PACKET.write_text(json.dumps(packet,indent=2)+'\n');print(PACKET.relative_to(ROOT),sha(PACKET))

if __name__=='__main__':main()
