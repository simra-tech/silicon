#!/usr/bin/env python3
"""One strict saved-native comparison of the authorized VSS source derivative."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').exists())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--preparation',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); assert not a.output.exists() and os.sched_getaffinity(0)=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    prep=json.loads((a.preparation/'summary.json').read_text())
    assert prep['status'].startswith('passed authorized explicit VSS')
    assert prep['flattened_exact_expected_partition'] and prep['exact_reverse_byte_restoration']
    assert all(prep['negative_controls'].values())
    assert prep['reachable_taps']==386 and prep['original_body_nodes']==245
    selected=a.preparation/'explicit_vss_tap_reader.cdl'
    assert sha(selected)==prep['adapter_sha256']
    prior=bulk/'full-io-marker-comparison-worker-20260923-r2'
    manifest=json.loads((prior/'summary.json').read_text())
    database=bulk/'full-io-marker-lvs-original-20260923-r1/reports/io_marker_native.lvsdb'
    interface=bulk/'full-io-marker-ports-20260923-r2/summary.json'
    flat=bulk/'full-io-marker-flatten-proof-20260923-r1/summary.json'
    assert sha(database)==manifest['database_sha256']=='3ed5cd2b78b3d4f4ed724730fcba2388148340d6442249e143c17a9f7ac99f04'
    assert sha(interface)==manifest['interface_proof_sha256']
    assert sha(flat)==manifest['flatten_proof_sha256']
    original=bulk/'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    adapted=bulk/'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl'
    assert sha(original)==prep['source_sha256']
    assert sha(adapted)=='7395c32d170a787dbc81fd10c67148301d168e51f5ac38de3f0866efe5894006'
    a.output.mkdir(parents=True)
    bound=[database,interface,flat,original,adapted,selected,a.preparation/'summary.json',Path(__file__)]
    changes=[]
    for row in manifest['workers']:
        source=prior/row['file']; assert sha(source)==row['prepared_sha256']; bound.append(source)
        old=source.read_text(); new=old
        if row['file']=='compare_saved_flat.rb':
            begin=old.index('comparison_source = $variant')
            end=old.index('reference.read(comparison_source,',begin)
            replacement="""raise 'Explicit body derivative missing' unless $comparison_reference
raise 'Explicit body derivative hash changed' unless Digest::SHA256.file($comparison_reference).hexdigest == '%s'
comparison_source = $comparison_reference
report[:actual_comparison_source_sha256] = Digest::SHA256.file(comparison_source).hexdigest
report[:intentional_source_interface_change] = 'All 245 originally local IO substrate domains explicitly connected to VSS; 941 terminal incidences, all devices/models/AP held'
report[:extraction_reference_excludes_exact_three_dummies] = false
report[:canonical_electrical_and_physical_dummies] = 'retained'
""" % prep['adapter_sha256']
            new=old[:begin]+replacement+old[end:]
            key="report[:before_simplify] = {layout: inventory.call(lc), reference: inventory.call(rc)}"
            proof="""vss_pin = rc.each_pin.find { |p| p.name.upcase == 'VSS' }
raise 'Missing VSS source pin' unless vss_pin
rc.net_for_pin(vss_pin.id).set_property('G1_EXPLICIT_VSS_SOURCE_NODE', true)
taps = rc.each_device.select { |d| d.device_class.name.downcase == 'ptap1' }
raise 'Reachable PTAP count changed' unless taps.size == 386
raise 'Explicit PTAP WELL not on VSS' unless taps.all? { |d| d.net_for_terminal('WELL').property('G1_EXPLICIT_VSS_SOURCE_NODE') == true }
raise 'Unpropagated local substrate survived' if rc.each_net.any? { |n| n.expanded_name.upcase.split('.').last == 'SUB!' }
%w[IOVSS VDD IOVDD].each do |name|
  p = rc.each_pin.find { |q| q.name.upcase == name }
  raise 'Supply domain missing or merged' unless p && rc.net_for_pin(p.id).property('G1_EXPLICIT_VSS_SOURCE_NODE') != true
end
report[:explicit_body_reader_controls] = {reachable_PTAP: taps.size, all_WELL_on_VSS: true, no_local_SUB: true, three_other_supply_domains_distinct_from_VSS: true}
"""
            assert new.count(key)==1
            new=new.replace(key,proof+key)
        target=a.output/row['file']; target.write_text(new)
        changes.append(dict(file=row['file'],original_sha256=sha(source),prepared_sha256=sha(target),
                            diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True)))))
        bound.append(target)
    (a.output/'preparation_diff.json').write_text(json.dumps(changes,indent=2)+'\n')
    hashes={str(p):sha(p) for p in bound}
    command=['klayout','-b','-r',str(a.output/'compare_saved_flat.rb'),
             '-rd','original='+str(original),'-rd','adapted='+str(adapted),
             '-rd','database='+str(database),'-rd','variant=adapter',
             '-rd','comparison_reference='+str(selected),'-rd','physical_interface='+str(interface),
             '-rd','output_dir='+str(a.output/'diagnostic')]
    report=dict(status='running authorized source-interface comparison',inputs=hashes,command=command,
                stock_rules_models='unchanged',new_native_extraction='not run; exact saved native database',
                geometry_parent='ae62bf68 marker candidate, not root new digital assembly',
                source_change='explicit owner-authorized VSS bulk interface',
                tap_AP='unchanged and unresolved',electrical_ESD_power_sequencing='not run')
    dest=a.output/'summary.json';dest.write_text(json.dumps(report,indent=2)+'\n')
    with (a.output/'console.log').open('x') as log:
        run=run_bounded(command,log,a.output/'run.json',900,cwd=ROOT,interval_s=5)
    path=a.output/'diagnostic/summary.json'
    parsed=json.loads(path.read_text()) if path.exists() else None
    held=all(sha(Path(p))==h for p,h in hashes.items())
    complete=run['status']=='completed' and run['returncode']==0 and held and parsed and 'engine_equivalent' in parsed
    report.update(status='completed comparison; inspect strict outcome' if complete else 'failed harness or bounded comparison',
                  run=run,inputs_unchanged=held,diagnostic=parsed)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],run=run,strict=parsed.get('status') if parsed else None),indent=2))
    assert complete


if __name__=='__main__':main()
