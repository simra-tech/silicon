#!/usr/bin/env python3
"""Retained positive/negative backend controls; requires the pinned image."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    runner = Path(__file__).with_name('run_digital_equivalence.py')
    gold = 'module g1_digital(input A, output X); assign X=A; endmodule\n'
    good = 'module g1_digital(input A, output X); sg13g2_buf_1 b(.A(A),.X(X)); endmodule\n'
    bad = 'module g1_digital(input A, output X); sg13g2_inv_1 b(.A(A),.Y(X)); endmodule\n'
    ff = 'module g1_digital(input D,CLK,RESET_B,output Q); sg13g2_dfrbpq_1 f(.D(D),.CLK(CLK),.RESET_B(RESET_B),.Q(Q)); endmodule\n'
    clockbuf = ff.replace('sg13g2_dfrbpq_1', 'wire C; sg13g2_buf_1 b(.A(CLK),.X(C)); sg13g2_dfrbpq_1').replace('.CLK(CLK)', '.CLK(C)')
    badreset = ff.replace('.RESET_B(RESET_B)', ".RESET_B(1'b1)")
    missing = "module g1_digital(input A,output X); sg13g2_lgcp_1 g(.CLK(A),.GATE(1'b1),.GCLK(X)); endmodule\n"
    rows = []
    for name, reference, candidate, expected, required_rejection in [
        ('buffer', gold, good, True, ''),
        ('inversion', gold, bad, False, 'unproven $equiv cells'),
        ('clock_buffer', ff, clockbuf, True, ''),
        ('reset_change', ff, badreset, False, 'unproven $equiv cells'),
        ('missing_function_cell', gold, missing, False, 'is not part of the design'),
    ]:
        folder = a.output/name
        folder.mkdir()
        (folder/'gold.v').write_text(reference)
        (folder/'gate.v').write_text(candidate)
        cmd = [sys.executable, str(runner), '--reference', str(folder/'gold.v'),
               '--candidate', str(folder/'gate.v'), '--output', str(folder/'proof')]
        with (folder/'launcher.log').open('x') as log:
            child = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
        proof = json.loads((folder/'proof/summary.json').read_text())
        backend = (folder/'proof/tool.log').read_text()
        observed = child.returncode == 0
        # A negative control must reach the actual equivalence assertion,
        # never pass merely because parsing/library loading failed.
        rejected = required_rejection in backend
        rows.append(dict(name=name, expected=expected, observed=observed,
                         negative_reached_assertion=rejected, proof=proof))
        if observed != expected or (not expected and not rejected):
            break
    passed = len(rows) == 5 and all(r['observed'] == r['expected'] and
             (r['expected'] or r['negative_reached_assertion']) for r in rows)
    result = dict(status='passed' if passed else 'failed', records=rows)
    (a.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'], len(rows))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
