#!/bin/sh
# record campaign d (a, b stopped: numerical stalls; c: down-shifter race; netlist 1d) (T9, 2026-10-21): suites in sequence, one runner at a time (<= 3 ngspice jobs)
cd "$(dirname "$0")"
: "${G1_RESULTS_ROOT:?}"; mkdir -p "$G1_RESULTS_ROOT/r1_bias/chain-20261021-d"
for s in "thr cases=tt,ss,ff,sf,fs,ssx,ffx" "op cases=tt,ss,ff,sf,fs,ssx,ffx,tt_m40,tt_125,tt_rbcs,tt_rwcs,tt_3v0,tt_3v6" "startup" "comp" "psrr" "mc n=50" "stb" "por" "mcthr n=30"; do
  set -- $s
  suite=$1; shift
  sh run.sh "$suite" "bias-$suite-20261021-d" "$@" > "$G1_RESULTS_ROOT/r1_bias/chain-20261021-d/$suite.txt" 2>&1
  echo "$suite exit $?" >> $G1_RESULTS_ROOT/r1_bias/chain-20261021-d/status.txt
done
echo done >> $G1_RESULTS_ROOT/r1_bias/chain-20261021-d/status.txt
