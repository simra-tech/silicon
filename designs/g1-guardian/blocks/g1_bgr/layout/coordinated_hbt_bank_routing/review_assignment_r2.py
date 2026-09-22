#!/usr/bin/env python3
"""Preserve r1 row/star review and independently check the new port strip."""
import contextlib
import hashlib
import io
import json
from pathlib import Path

path=Path(__file__).with_name('review_assignment.py').resolve()
assert hashlib.sha256(path.read_bytes()).hexdigest()=='c7eeaa531c99d397b5d386cb7be6d5dfd8468cd769db5155c327a6120850759d'
captured=io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path),'__name__':'independent_r1_arithmetic'})
result=json.loads(captured.getvalue())
ports=[136+.6*i for i in range(7)]
gaps=[ports[i+1]-.15-ports[i]-.15 for i in range(6)]
assert min(gaps)>=.3-1e-10
assert 141.05-.15-(max(ports)+.15)>=.3
assert min(ports)-.15-(134+.4)>=.3
result.update(source_port_centers_um=ports,source_port_minimum_M3_edge_gap_um=min(gaps),
              first_row_collector_clearance_um=141.05-.15-(max(ports)+.15),
              general_bus_clearance_um=min(ports)-.15-(134+.4),
              status='passed independent r2 arithmetic only; actual native/route checks separate')
print(json.dumps(result,indent=2))
