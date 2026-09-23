#!/usr/bin/env python3
"""One log-only copied-deck diagnostic; no acceptance credit or installed edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT']);pdk=Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    rules=pdk/'libs.tech/klayout/tech/lvs'
    layout=bulk/'analog-pair-integration-20260923-r1/analog_pair_native.gds'
    source=bulk/'analog-pair-reference-20260923-r1/physical_taps_reader.cdl'
    assert sha(layout)=='be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'
    assert sha(source)=='35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51'
    prior=bulk/'analog-pair-native-lvs-20260923-r1/summary.json';pj=json.loads(prior.read_text())
    assert pj['status']=='failed strict native fullchip LVS' and pj['run']['status']=='timeout'
    original={str(p.relative_to(rules)):sha(p) for p in rules.rglob('*') if p.is_file()}
    assert all(sha(pdk/k)==v for k,v in pj['stock_rule_hashes'].items())
    a.output.mkdir(parents=True);copied=a.output/'instrumented_lvs';shutil.copytree(rules,copied)
    relative='rule_decks/rfmos_model_mapping.lvs';target=copied/relative
    old=target.read_text();new=old;edits=[]
    # Every inserted statement performs logging only. Removing precisely the
    # tagged lines restores the entire original file byte for byte.
    for needle,inserted in [
        ('  class_index = {}\n', '  logger.info("PROFILE class-index BEGIN") # PROFILE_ONLY\n'),
        ('  class_index\nend\n', '  logger.info("PROFILE class-index END") # PROFILE_ONLY\n'),
        ('  target_netlist.each_circuit do |circuit|\n', '    logger.info("PROFILE circuit #{circuit.name} phase-scan") # PROFILE_ONLY\n'),
        ('    devices_to_process.each do |device|\n', '      logger.info("PROFILE device #{circuit.name}/#{device.name}") if (device.id % 10000).zero? # PROFILE_ONLY\n'),
        ('    devices_to_remove.each { |device| circuit.remove_device(device) }\n', '    logger.info("PROFILE circuit #{circuit.name} mapping-END count=#{devices_to_process.size}") # PROFILE_ONLY\n'),
        ('  target_netlist.purge_devices\n', '  logger.info("PROFILE purge_devices BEGIN") # PROFILE_ONLY\n'),
        ('  target_netlist.purge\n', '  logger.info("PROFILE purge BEGIN") # PROFILE_ONLY\n'),
    ]:
        count=new.count(needle);assert count>=1,(needle,count)
        if needle in ('  class_index\nend\n','  target_netlist.purge_devices\n','  target_netlist.purge\n'):
            new=new.replace(needle,inserted+needle)
        else:new=new.replace(needle,needle+inserted)
        edits.append(dict(anchor=needle,inserted=inserted,count=count))
    final='  target_netlist.purge\nend\n'
    assert new.count(final)==1
    new=new.replace(final,'  target_netlist.purge\n  logger.info("PROFILE purge END") # PROFILE_ONLY\nend\n')
    assert ''.join(line for line in new.splitlines(True) if '# PROFILE_ONLY' not in line)==old
    target.write_text(new)
    changed={name for name,h in original.items() if sha(copied/name)!=h};assert changed=={relative}
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    options=dict(run_mode='deep',no_net_names='false',spice_comments='true',net_only='false',top_lvl_pins='true',
        no_simplify='false',no_series_res='false',no_parallel_res='false',combine_devices='false',
        disable_tap_extraction='false',purge='false',purge_nets='false',topcell='placed_core_NOT_CONNECTED_FULLCHIP',
        input=str(layout),schematic=str(source),ignore_top_ports_mismatch='false',implicit_nets='',
        report=str(a.output/'diagnostic.lvsdb'),log=str(a.output/'engine.log'),target_netlist=str(a.output/'extracted.cir'))
    command=['klayout','-b','-r',str(copied/'sg13g2.lvs')]
    for k,v in options.items():command+=['-rd',k+'='+v]
    result=dict(status='running instrumented diagnostic; no acceptance credit',command=command,
        installed_rule_hashes=original,changed_copy_files=list(changed),logging_edits=edits,
        inverse_logging_removal_byte_exact=True,watchdog_seconds=600,
        inputs={str(p):sha(p) for p in [layout,source,prior,Path(__file__)]},
        native_LVS_acceptance='not run by this instrumented diagnostic')
    def save():(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    with (a.output/'console.log').open('x') as log:
        run=run_bounded(command,log,a.output/'run.json',600,cwd=ROOT,
            env=dict(os.environ,KLAYOUT_PATH=str(pdk/'libs.tech/klayout')),interval_s=3)
    assert all(sha(rules/name)==h for name,h in original.items())
    assert all(sha(Path(p))==h for p,h in result['inputs'].items())
    result.update(status='completed bounded instrumentation; inspect diagnostic outcome',run=run,
        installed_rules_and_inputs_unchanged=True)
    save()


if __name__=='__main__':main()
