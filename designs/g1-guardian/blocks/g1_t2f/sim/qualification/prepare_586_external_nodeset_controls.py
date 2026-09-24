#!/usr/bin/env python3
"""Prepare three OP-only initialization diagnostics, not a solver/population adoption."""
import difflib
import json
from pathlib import Path
import re
from run_586_source_control import HERE, ROOT
from prepare_586_population import sha

REFERENCE=HERE/'runs/t2f586-klu-adverse-calibration-s75201-20260923-a'
NODES=['vref','pbias','pcasc','vbe','dvbe']
ARMS=['sparse-original','sparse-nodeset','klu-nodeset']


def transform(original, arm, guesses):
    assert arm in ARMS and list(guesses)==NODES
    assert original.count('\n.options klu\n')==1
    assert original.count('\ntran 5n 32u\n')==1
    begin=original.index('meas tran t_a ');end=original.index('echo PHASE0_END\n',begin)
    tail=original[begin:end]
    output,=re.findall(r'^wrdata .+\n',tail,re.M)
    observations=output.replace('phase0.dat','op.dat').rstrip()+' v(pbias) v(pcasc) v(vbe) v(dvbe)\n'
    # The removed measurements all depend on a transient that this OP-only fixture does not run.
    replaced=original[:begin]+observations+original[end:]
    replaced=replaced.replace('\ntran 5n 32u\n','\nop\n')
    assert replaced.replace(observations,tail).replace('\nop\necho P0_BGR_AFTER_BEGIN','\ntran 5n 32u\necho P0_BGR_AFTER_BEGIN')==original
    result=replaced if arm=='klu-nodeset' else replaced.replace('\n.options klu\n','\n')
    if arm!='sparse-original':
        statement='.nodeset '+' '.join('v(%s)=%s'%(node,guesses[node]) for node in NODES)+'\n'
        result=result.replace('.control\n',statement+'.control\n')
    assert not re.search(r'^(tran|meas|let|\.ic|.*\buic\b)',result,re.M|re.I)
    assert result.count('\nop\n')==2 and result.count('\nreset\n')==1
    return result


def prepare():
    destination=HERE/'t2f586-external-nodeset-op-contract-20260923-a'
    assert not destination.exists()
    reference=json.loads((REFERENCE/'p00/summary.json').read_text())[0]
    assert reference['status']=='passed' and reference['full3180_status']=='passed'
    original=(REFERENCE/'p02/probe.cir').read_text()
    log=(REFERENCE/'p00/run.log').read_text()
    guesses={}
    for node in NODES:
        values=re.findall(r'^'+node+r'\s+([-+0-9.eE]+)\s*$',log,re.M)
        assert len(values)==1;guesses[node]=values[0]
    assert '.temp -40\n' in original and 'setseed 75201\n' in original
    assert 'Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr' in original
    provenance=json.loads((REFERENCE/'provenance.json').read_text())
    inventory=json.loads((REFERENCE/'population_inventory.json').read_text())
    assert inventory['parameter_count']==3180 and inventory['primitive_count']==1129
    destination.mkdir()
    cases=[]
    for arm in ARMS:
        deck=transform(original,arm,guesses);path=destination/(arm+'.cir');path.write_text(deck)
        diff=destination/(arm+'.diff')
        diff.write_text(''.join(difflib.unified_diff(original.splitlines(True),deck.splitlines(True),
            fromfile='preservedFailedKLU75201LowCold32us',tofile='OPonly/'+arm)))
        cases.append(dict(label=arm,deck_sha256=sha(path),difference_sha256=sha(diff),
            run_id='t2f586-external-nodeset-op-20260923-a-'+arm,solver='klu' if arm=='klu-nodeset' else 'sparse',watchdog_s=300))
    paths=[Path(__file__).resolve(),HERE/'test_586_external_nodeset_controls.py',REFERENCE/'provenance.json',
        REFERENCE/'population_inventory.json',REFERENCE/'p00/run.log',REFERENCE/'p00/summary.json',REFERENCE/'p02/probe.cir',
        REFERENCE/'p02/run.json',REFERENCE/'p02/run.log',REFERENCE/'p02/summary.json']
    paths += [REFERENCE/name for name in ['bgr.spice','t2f.spice']]
    paths += [REFERENCE/'p02/.spiceinit']
    packet=dict(status='prepared only; no simulation or adoption',cases=cases,seed=75201,corner='fast',
        temperature_C=-40,VDDA_V=3.,VDD_V=1.08,guesses=guesses,
        guess_scope='Literal rounded external-node values printed in the preserved successful same-seed25C initial transient solution. Hints only, not exact OP values, forced voltages or cold operating-point predictions; fixed identically in both nodeset arms.',
        source_hashes=provenance['source_hashes'],inventory_sha256=provenance['inventory_sha256'],
        runtime_identity=provenance['runtime_identity'],expected_parameters=reference['parameters_before'],
        groups={tag:[key for key,value in pairs] for tag,pairs in reference['parameters_before'].items()},
        original_failed_leaf=str((REFERENCE/'p02').relative_to(ROOT)),reference=str(REFERENCE.relative_to(ROOT)),
        bindings_sha256={str(path.relative_to(ROOT)):sha(path) for path in paths},
        differences='Common OP-only diagnostic removes32usTRAN and allfuture transient measurements, substitutes secondOP, appends4external BGR voltage observations. Sparse selector and fixed5external .nodeset are separately declared arms; no IC/UIC/tolerance/device/model/seed/rail/temperature change.',
        gates='Actual SPARSE/KLU banner; zero-exit fatal errors rejected; all3180 before/after exactly original passed75201p00; original12 physical columns first plus4 BGR voltages finite/named, OP scale explicitly not time; HBT external VCE<=1.6. Exact cross-arm OP comparisons reported independently, failed/missing baseline never promoted. No transient/frequency/accuracy or population claim.',
        resource_bound=dict(max_concurrent=1,leaf_watchdog_s=300,aggregate_child_s=900,expected_HOME_GiB=.06),
        execution='not implemented/not run; source-bound runner and tests required before root-coordinated CPU0 lease after DAC priority')
    target=destination/'contract.json';target.write_text(json.dumps(packet,indent=2)+'\n')
    print(str(target.relative_to(ROOT)),sha(target))


if __name__=='__main__':prepare()
