"""Freeze lowcarry implementation without approving or launching a simulation."""
import json
from pathlib import Path
from prepare_dac586_lowcarry_probe import ROOT,SIM,sha

packet=SIM/'qualification/dac586-lowcarry-controls-20260923-a.json'
assert sha(packet)=='97b296ccf573895f0eea38c39ed22787ac409b10b7bb011cbd1df28c5e0637f6'
names=['run_dac586_lowcarry_probe.py','audit_dac586_lowcarry_probe.py','freeze_dac586_lowcarry_probe.py','prepare_dac586_lowcarry_probe.py',
 'test_dac586_lowcarry_probe.py','test_dac586_lowcarry_runtime.py','prepare_dac586_dc_controls.py','run_dac586_dc_control.py','run_dac586_static_control.py','dac586_dc_metrics.py',
 'run_bgr_substitution_draw_audit.py','run_nominal_clock_probe.py','analyze_bgr_substitution_outcomes.py','result_directory.py','.spiceinit']
result=dict(status='prepared implementation only; ROOT lease/review required',packet=str(packet.relative_to(ROOT)),packet_sha256=sha(packet),
 bindings_sha256={str((SIM/n).relative_to(ROOT)):sha(SIM/n) for n in names},scope='Two serial600s lowcarry throughput diagnostics, no scaling or method adoption.')
out=SIM/'qualification/dac586-lowcarry-execution-20260923-a.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(sha(out))
