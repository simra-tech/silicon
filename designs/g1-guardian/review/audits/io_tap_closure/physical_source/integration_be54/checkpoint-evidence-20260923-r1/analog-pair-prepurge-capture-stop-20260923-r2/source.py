#!/usr/bin/env python3
"""Exact-PID kill after the preserved graceful diagnostic-stop failure."""
import json
from pathlib import Path

prior=Path('<results-root>/analog-pair-prepurge-capture-stop-20260923-r1/summary.json')
j=json.loads(prior.read_text())
assert j['pid']==4006633 and j['start_ticks']==968959998 and j['signal']=='SIGTERM'
assert j['exact_engine_process_gone'] is False
base=Path(__file__).resolve().with_name('stop_capture.py');code=base.read_text()
assert code.count("signal='SIGTERM'")==1 and code.count('os.kill(a.pid,signal.SIGTERM)')==1
code=code.replace("signal='SIGTERM'","signal='SIGKILL after preserved SIGTERM did not terminate'")
code=code.replace('os.kill(a.pid,signal.SIGTERM)','os.kill(a.pid,signal.SIGKILL)')
exec(compile(code,str(base),'exec'),globals())
