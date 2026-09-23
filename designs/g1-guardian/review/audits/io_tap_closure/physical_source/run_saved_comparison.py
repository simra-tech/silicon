#!/usr/bin/env python3
"""Current-source comparison after independently exact graph/interface proofs."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
PRIOR=HERE.parents[1]/'fullchip_reference_closure/physical_lvs'
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    database=bulk/'io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb'
    dbhash='1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f';assert sha(database)==dbhash
    controls=bulk/'io-current-diagnostics-20260923-r1'
    flatpath=controls/'flatten/summary.json';portpath=controls/'ports/summary.json'
    flat=json.loads(flatpath.read_text());ports=json.loads(portpath.read_text())
    assert flat['status'].startswith('passed exact primitive/terminal-graph') and flat['database_sha256']==dbhash
    assert flat['complete_bijective_terminal_graph'] and flat['all_binary64_parameters_exact']
    assert ports['status'].startswith('passed read-only 24 physical ports / 22 distinct')
    assert dbhash in ports['inputs'].values()
    count,pins=flat['after_devices'],flat['original_top_pin_count'];assert len(ports['original_pins'])==pins
    source=bulk/'io-physical-ap-source-20260923-r2/physical_taps_reader.cdl'
    sourcehash='d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4';assert sha(source)==sourcehash
    original=bulk/'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    adapted=bulk/'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl'
    a.output.mkdir(parents=True);workers=[]
    def rebind(name,expected,edits):
        oldpath=PRIOR/name;assert sha(oldpath)==expected
        old=oldpath.read_text();new=old
        for before,after in edits:
            assert new.count(before)==1,(name,before,new.count(before));new=new.replace(before,after)
        path=a.output/name;path.write_text(new)
        workers.append(dict(file=name,original_sha256=sha(oldpath),prepared_sha256=sha(path),edits=edits))
        (a.output/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
        return path
    read="reference.read($variant == 'original' ? $original : $adapted, RBA::NetlistSpiceReader.new(CustomReader.new))"
    replacement="""raise 'Missing current reference' unless $comparison_reference
raise 'Changed current reference' unless Digest::SHA256.file($comparison_reference).hexdigest == '%s'
report[:actual_comparison_source_sha256] = Digest::SHA256.file($comparison_reference).hexdigest
report[:current_source_scope] = 'Current digital + authorized explicit VSS + independently verified physical AP; all three all-VDD source dummies retained'
report[:extraction_reference_excludes_exact_three_dummies] = false
reference.read($comparison_reference, RBA::NetlistSpiceReader.new(CustomReader.new))"""%sourcehash
    script=rebind('compare_saved_flat.rb','8297f92b8d9c643cfa3178666ada5f1e25bff8be75f1df078202c49320ded63a',[
        ('1c8f3f91b8be00e0fbbdf4c2a40734fb5f8fe8b0388b1780768699e1a2afcbcf',dbhash),
        ('count == 61_516','count == '+str(count)),('lc.each_pin.to_a.size == 71','lc.each_pin.to_a.size == '+str(pins)),
        ("raise 'Original 71 pins changed'","raise 'Original observed pins changed'"),
        ('all_61516_primitive_records:','all_'+str(count)+'_primitive_records:'),
        ("'passed 71 unchanged'","'passed "+str(pins)+" unchanged'"),(read,replacement)])
    rebind('physical_interface_metadata.rb','5d776ca8c2a09cbbf62ca6be099008a146ccbcfb1b80b9c8b544dc0e8fd6e4fc',[
        ('e7f9c8eef1ca1631aaa9fd7c2fdbc142bf5f7c3fe33afb1dc4eefc831c308177',sha(portpath)),
        ('original.size == 71','original.size == '+str(pins))])
    rebind('probe_tap_adapter.rb','832e082c79eb0a2194f8e42f1e972e444ff57ada44b441627a06519c9f120ca6',[])
    inputs={str(p):sha(p) for p in [source,original,adapted,database,flatpath,portpath,Path(__file__)]+[a.output/r['file'] for r in workers]}
    command=['klayout','-b','-r',str(script),'-rd','original='+str(original),'-rd','adapted='+str(adapted),
        '-rd','database='+str(database),'-rd','variant=adapter','-rd','comparison_reference='+str(source),
        '-rd','physical_interface='+str(portpath),'-rd','output_dir='+str(a.output/'diagnostic')]
    result=dict(status='running current saved comparison',inputs=inputs,workers=workers,command=command,
        native_stock_LVS='failed; original native run preserved',acceptance='not established by diagnostic',
        scope='Exact graph flatten, stock class setup/combiners, physical22pin metadata only; no net joins/parameter tolerances')
    def save():(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    with (a.output/'console.log').open('x') as log:
        run=run_bounded(command,log,a.output/'run.json',180,cwd=ROOT,interval_s=3)
    path=a.output/'diagnostic/summary.json';parsed=json.loads(path.read_text()) if path.exists() else None
    held=all(sha(Path(p))==h for p,h in inputs.items())
    complete=run['status']=='completed' and run['returncode']==0 and held and parsed and 'engine_equivalent' in parsed
    result.update(status='completed strict diagnostic; inspect outcome' if complete else 'failed diagnostic harness or bound',
        run=run,inputs_held=held,diagnostic=parsed);save()
    assert complete


if __name__=='__main__':main()
