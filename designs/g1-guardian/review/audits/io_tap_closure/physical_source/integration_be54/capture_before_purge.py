#!/usr/bin/env python3
"""Diagnostic-only pre-purge L2N snapshot; installed rules remain immutable."""
import hashlib
from pathlib import Path

base = Path(__file__).resolve().with_name('profile_mapping.py')
expected = '13ea19d50ca4331a169e39dca5bb273fe867cf42be9dbae7db6e81f6c594a412'
raw = base.read_text()
assert hashlib.sha256(base.read_bytes()).hexdigest() == expected
gate_anchor="    rules=pdk/'libs.tech/klayout/tech/lvs'\n"
assert raw.count(gate_anchor)==1
raw=raw.replace(gate_anchor,gate_anchor+"    control=bulk/'l2n-capture-control-20260923-r4/summary.json'\n"
    "    assert sha(control)=='265d7332c6537b9fda387dc6dacd4ebb5685b67d20af3ffa4a804001da97433a'\n"
    "    assert json.loads(control.read_text())['status']=='passed exact-sidecar capture control'\n")
replacements = [
    ("bulk/'analog-pair-integration-20260923-r1/analog_pair_native.gds'",
     "bulk/'analog-pair-overlay-flat-20260923-r1/overlay_flattened.gds'"),
    ("be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307",
     "dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333"),
    ("bulk/'analog-pair-native-lvs-20260923-r1/summary.json'",
     "bulk/'analog-pair-flat-native-lvs-20260923-r1/summary.json'"),
]
for old, new in replacements:
    assert raw.count(old) == 1
    raw = raw.replace(old, new)
anchor = "    assert ''.join(line for line in new.splitlines(True) if '# PROFILE_ONLY' not in line)==old\n"
assert raw.count(anchor) == 1
insertion = '''    snapshot = a.output/'before_purge.l2n'
    exact = a.output/'before_purge_binary64.json'
    capture = ('  logger.info("CAPTURE L2N BEGIN") # PROFILE_ONLY\\n'
        + '  capture_before = target_netlist.to_s # PROFILE_ONLY\\n'
        + '  require "json"; capture_rows=[] # PROFILE_ONLY\\n'
        + '  target_netlist.each_circuit { |c| c.each_device { |d| d.device_class.parameter_definitions.each { |p| capture_rows << [c.name,d.id,d.name,d.device_class.name,p.name,[d.parameter(p.id)].pack("G").unpack1("H*")] } } } # PROFILE_ONLY\\n'
        + '  File.write(' + json.dumps(str(exact)) + ',JSON.generate(capture_rows)) # PROFILE_ONLY\\n'
        + '  l2n_data.write_l2n(' + json.dumps(str(snapshot)) + ') # PROFILE_ONLY\\n'
        + '  raise "capture mutated graph" unless capture_before == target_netlist.to_s # PROFILE_ONLY\\n'
        + '  logger.info("CAPTURE L2N END") # PROFILE_ONLY\\n')
    purge_anchor = '  target_netlist.purge\\n'
    assert new.count(purge_anchor) == 1
    new = new.replace(purge_anchor, capture + purge_anchor)
    edits.append(dict(anchor=purge_anchor, inserted=capture, count=1,
        purpose='output-only actual native graph and geometry checkpoint'))
'''
raw = raw.replace(anchor, insertion + anchor)
binding='layout,source,prior,Path(__file__)'
assert raw.count(binding)==1
raw=raw.replace(binding,'layout,source,prior,control,Path(__file__)')
end='    result.update(status=\'completed bounded instrumentation; inspect diagnostic outcome\',run=run,\n'
assert raw.count(end)==1
raw=raw.replace(end,"    result['snapshot_exists']=snapshot.is_file()\n"
    "    if snapshot.is_file():\n"
    "        result['snapshot_sha256']=sha(snapshot)\n"
    "        result['snapshot_bytes']=snapshot.stat().st_size\n"
    "    if exact.is_file():\n"
    "        result['binary64_sidecar_sha256']=sha(exact)\n"
    "        result['binary64_sidecar_bytes']=exact.stat().st_size\n"+end)
exec(compile(raw, str(base), 'exec'), globals())
