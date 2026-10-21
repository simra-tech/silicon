#!/bin/sh
# Wrapper: sh run.sh <suite> <run-id> [key=value ...]   (from any directory; POSIX shell)
# Uses CPU set 116-119 (shared with the S7 study; at most 3 ngspice jobs, BIAS_JOBS) and the R1 trace root.
REPO=$(cd "$(dirname "$0")/../../../../.." && pwd)
G1_CPUSET=116-119; export G1_CPUSET
G1_WORKDIR=designs/r1-joint/blocks/r1_bias/sim; export G1_WORKDIR
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results root}"; export G1_RESULTS_ROOT
exec "$REPO/flow/run.sh" python3 run_bias.py "$@"
