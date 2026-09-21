#!/usr/bin/env bash
# Run from repo root in the pinned container: flow/run.sh bash designs/g1-guardian/blocks/g1_top/sim/bridge_probe/run.sh
set -euo pipefail
B=designs/g1-guardian/blocks/g1_top/sim/bridge_probe
mkdir -p build/g1_top/bridge_probe
export LD_LIBRARY_PATH=/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
iverilog -o build/g1_top/bridge_probe/divider.vvp "$B/divider.v"
for variant in band threshold; do
  ngspice -b "$B/$variant.cir" > "$B/$variant.log" 2>&1
done
python3 - "$B" <<'CHECK'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
t = (p / 'threshold.log').read_text()
m = re.search(r'^freq = ([0-9.eE+-]+)', t, re.M)
assert m and abs(float(m[1]) / 4.9595e6 - 1) < 0.001, 'clock receiver does not divide by two'
b = (p / 'band.log').read_text()
assert 'out of interval' in b, 'old receiver no longer reproduces failure; review evidence'
print('passed: fixed receiver divides by two; old band reproduces missing valid output edges')
CHECK
