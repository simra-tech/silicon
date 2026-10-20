#!/bin/sh
# Campaign set (host). Revision A used: ac noise cm psrr ac_mc tran settle; revision B added settle_adc;
# revision C added stb, stb_revb, cmstep, overload, rsrc, temp and dropped the generic settle; revision D (default list
# below) adds stbx (cross corners) and drops stb_revb (revision-B method check, unchanged netlist, kept as history).
# Usage: sh sim/run_all.sh <suffix>   (from the repository root). Run id r1afe-<campaign>-<suffix>.
set -u
G1_CPUSET=106-108; export G1_CPUSET
G1_CPUS=3; export G1_CPUS
G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim; export G1_WORKDIR
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results root}"; export G1_RESULTS_ROOT
for c in ${CAMPAIGNS:-stbval stb stbx cmstep ac noise tran settle_adc cm psrr overload rsrc temp ac_mc}; do
  echo "== $c $(date -u +%H:%M:%S)"
  flow/run.sh python3 run_afe.py $c r1afe-$c-$1 2>&1 | grep -v "level=warning\|Resource enforcement"
done
echo "== done $(date -u +%H:%M:%S)"
