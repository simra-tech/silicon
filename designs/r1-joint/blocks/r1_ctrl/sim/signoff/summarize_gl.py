#!/usr/bin/env python3
"""Summarise gate-level runs: per test log counts of PASS / FAIL / GLSKIP, finish time, exit status.
usage: summarize_gl.py <results_root>/r1_ctrl <out_dir> <run:mode> ...   (e.g. r1ctrl_gl_20261021_f:slow)"""
import os, re, sys, json, glob
root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
GROUPS = [('biss', ['23.810', '33.333', '47.619'], 48), ('ssi', ['23.810', '33.333', '47.619'], 9),
          ('spi', ['33.333'], 26), ('gate', ['33.333'], 22), ('safe', ['33.333'], 32), ('cal', ['33.333', '23.810'], 32)]
res = {}
lines = []
for spec in sys.argv[3:]:
    run, mode = spec.split(':')
    d = os.path.join(root, run, mode)
    for g, cks, n in GROUPS:
        for ck in cks:
            base = os.path.join(d, f'top_{g}_{ck}')
            row = dict(run=run, mode=mode, group=g, clk_ns=ck, expected=n)
            if not os.path.exists(base + '.log'):
                row.update(status='not run'); res[f'{run}/{mode}/{g}/{ck}'] = row; continue
            t = open(base + '.log', errors='replace').read()
            row['pass'] = len(re.findall(r'^PASS', t, re.M)); row['fail'] = len(re.findall(r'^FAIL', t, re.M))
            row['skip'] = len(re.findall(r'^GLSKIP', t, re.M))
            m = re.search(r'\$finish called at (\d+)', t)
            row['finish_ps'] = int(m.group(1)) if m else None
            rc = open(base + '.rc').read().strip() if os.path.exists(base + '.rc') else 'rc unknown'
            row['rc'] = rc
            done = bool(re.search(r'^# \d+ checks', t, re.M))
            if not done: row['status'] = 'not completed (stopped)'
            elif row['fail'] == 0 and row['pass'] + row['skip'] == n: row['status'] = 'passed'
            else: row['status'] = 'failed'
            res[f'{run}/{mode}/{g}/{ck}'] = row
            if row['fail']:
                lines += [f'{run}/{mode}/{g}/{ck}: ' + l for l in t.splitlines() if l.startswith('FAIL')]
json.dump(res, open(os.path.join(out, 'gl_summary.json'), 'w'), indent=1)
with open(os.path.join(out, 'gl_summary.md'), 'w') as f:
    f.write('| run | mode | group | clk ns | pass | fail | skipped | status | finish (ps) | exit |\n|---|---|---|---|---|---|---|---|---|---|\n')
    for k, r in res.items():
        f.write(f"| {r['run']} | {r['mode']} | {r['group']} | {r['clk_ns']} | {r.get('pass','-')} | {r.get('fail','-')} | {r.get('skip','-')} | {r['status']} | {r.get('finish_ps','-')} | {r.get('rc','-')} |\n")
    if lines: f.write('\nFailed checks:\n\n' + '\n'.join('- ' + l for l in lines) + '\n')
print(open(os.path.join(out, 'gl_summary.md')).read())
