#!/bin/sh
# campaign d, part 2 (T9, 2026-10-21): POR transients and threshold MC on netlist 1d with the convergence aids
# (conv=1: gmin 1e-12, rshunt 1e12) after the chain-d stalls; one runner at a time (<= 3 ngspice jobs)
cd "$(dirname "$0")"
: "${G1_RESULTS_ROOT:?}"; D="$G1_RESULTS_ROOT/r1_bias/chain-20261021-d2"; mkdir -p "$D"
sh run.sh por bias-por-20261021-d2 conv=1 > "$D/por.txt" 2>&1; echo "por exit $?" >> "$D/status.txt"
sh run.sh mcthr bias-mcthr-20261021-d2 n=30 conv=1 > "$D/mcthr.txt" 2>&1; echo "mcthr exit $?" >> "$D/status.txt"
echo done >> "$D/status.txt"
