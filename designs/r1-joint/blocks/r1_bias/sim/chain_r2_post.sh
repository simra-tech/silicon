#!/bin/sh
# Revision 2 (D20) follow-up chain (T9, 2026-10-26): schematic op re-run and the post-layout checks of the buffer.
# Usage: G1_RESULTS_ROOT=<G1_RESULTS_ROOT> sh chain_r2_post.sh <tag> <pex-run-id>   (POSIX shell)
# Status lines in <G1_RESULTS_ROOT>/r1_bias/chain-post-<tag>/status.txt.
cd "$(dirname "$0")"
: "${G1_RESULTS_ROOT:?}"; T=$1; P=$2; D="$G1_RESULTS_ROOT/r1_bias/chain-post-$T"; mkdir -p "$D"
run() { n=$1; shift; sh "$@" > "$D/$n.txt" 2>&1; echo "$n exit $?" >> "$D/status.txt"; }
run op       run.sh    op     bias-op-$T cases=tt,ss,ff,sf,fs,ssx,ffx,tt_m40,tt_125,tt_rbcs,tt_rwcs,tt_3v0,tt_3v6
run postop   run.sh    op     post-op-$T pex=$P view=rc conv=1 cases=tt,ss,ff,ssx,ffx
run poststb  run_vb.sh vbstb  post-vbstb-$T pex=$P view=rc conv=1 cases=tt,ffx
run postzout run_vb.sh vbzout post-vbzout-$T pex=$P view=rc conv=1 cases=tt
run poststep run_vb.sh vbstep post-vbstep-$T pex=$P view=rc conv=1 cases=tt
echo done >> "$D/status.txt"
