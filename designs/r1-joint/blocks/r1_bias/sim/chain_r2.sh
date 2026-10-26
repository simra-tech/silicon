#!/bin/sh
# Revision 2 (D20) schematic campaign (T9, 2026-10-26): one runner at a time (<= 3 ngspice jobs on CPU set 116-119).
# Usage: G1_RESULTS_ROOT=<G1_RESULTS_ROOT> sh chain_r2.sh <tag>   (status lines in <G1_RESULTS_ROOT>/r1_bias/chain-<tag>/)
cd "$(dirname "$0")"
: "${G1_RESULTS_ROOT:?}"; T=$1; D="$G1_RESULTS_ROOT/r1_bias/chain-$T"; mkdir -p "$D"
run() { n=$1; shift; sh "$@" > "$D/$n.txt" 2>&1; echo "$n exit $?" >> "$D/status.txt"; }
run vbstb   run_vb.sh vbstb   vb-stb-$T
run op      run.sh    op      bias-op-$T cases=tt,ss,ff,sf,fs,ssx,ffx,tt_m40,tt_125,tt_rbcs,tt_rwcs,tt_3v0,tt_3v6
run vbzout  run_vb.sh vbzout  vb-zout-$T
run vbstep  run_vb.sh vbstep  vb-step-$T
run vbaz    run_vb.sh vbaz    vb-az-$T
run vbpsrr  run_vb.sh vbpsrr  vb-psrr-$T
run vbnoise run_vb.sh vbnoise vb-noise-$T
run vbdrive run_vb.sh vbdrive vb-drive-$T
run mc      run.sh    mc      bias-mc-$T n=200
run startup run.sh    startup bias-startup-$T cases=tt,ss,ff,ssx,ffx ramps=1e-5
run stb     run.sh    stb     bias-stb-$T
run psrr    run.sh    psrr    bias-psrr-$T
echo done >> "$D/status.txt"
