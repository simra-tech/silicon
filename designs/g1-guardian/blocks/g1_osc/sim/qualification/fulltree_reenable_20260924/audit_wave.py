"""Saved 19-node re-enable waveform observer; no solver launch."""
import argparse
import json
import math
from pathlib import Path

def crossings(rows,column,level,rising=True):
    values=[]
    for before,after in zip(rows,rows[1:]):
        left,right=before[column],after[column]
        matched=left<level<=right if rising else left>level>=right
        if matched:
            assert right!=left
            values.append(before[0]+(level-left)*(after[0]-before[0])/(right-left))
    return values


def audit_wave(path, vdd):
    expected = ['time', 'v(osc_clk)', 'v(sp__11993_A)', 'v(sp__11993_X)',
                'v(en)', 'i(vdd)', 'i(vddclk)'] + ['v(leaf%d)' % i for i in range(16)]
    rows = []
    with path.open() as stream:
        assert stream.readline().split() == expected
        for line in stream:
            if not line.strip():
                continue
            row = list(map(float, line.split()))
            assert len(row) == 23 and all(math.isfinite(x) for x in row)
            assert not rows or row[0] > rows[-1][0]
            rows.append(row)
    assert len(rows) > 1000 and rows[0][0] == 0 and abs(rows[-1][0] - 1e-5) < 1e-12
    columns = [1, 2, 3] + list(range(7, 23))
    rises = [crossings(rows, col, vdd / 2) for col in columns]
    windows = {}
    for name, lo, hi in [('before_disable', 1.8e-6, 2.9e-6), ('reenabled', 7e-6, 9.8e-6)]:
        edges = [[t for t in series if lo <= t <= hi] for series in rises]
        ref = edges[0]
        windows[name] = {'edge_counts': [len(series) for series in edges],
                         'frequency_Hz': (len(ref)-1)/(ref[-1]-ref[0]) if len(ref) >= 2 else None,
                         'all_receivers_oscillate': all(len(series) >= 4 for series in edges)}
    disabled = [sum(3.1e-6 < t < 4.9e-6 for t in series) for series in rises]
    passed = all(row['all_receivers_oscillate'] for row in windows.values()) and not any(disabled)
    return {'row_count': len(rows), 'columns': 23, 'first_time_s': rows[0][0],
            'last_time_s': rows[-1][0], 'windows': windows, 'disabled_rising_edges': disabled,
            'status': 'passed scoped re-enable observer' if passed else 'failed',
            'scope': '19 observed nodes; 1197 static terminal caps; estimated assembly pi'}



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wave", type=Path)
    parser.add_argument("--vdd", type=float, required=True)
    args = parser.parse_args()
    result = audit_wave(args.wave, args.vdd)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"].startswith("passed") else 1)
