#!/bin/sh
# run_qt2.sh <cpu> <job file>: T2 (2026-10-21) job queue, same rules as run_q5.sh: jobs one after the other on one CPU,
# a failed job is logged FAILED and not resubmitted, the queue exits 1 at the end if any job failed. Each non-comment
# line is a complete runner call (sim/r5/run_points5.py or sim/r5/run_deck5.py) with @CPU@ for the CPU number.
CPU=$1; JOBS=$2
cd "$(dirname "$0")/../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the results root}"; export G1_RESULTS_ROOT
rc=0
while IFS= read -r line; do
  case "$line" in ''|'#'*) continue ;; esac
  cmd=$(printf '%s' "$line" | sed "s/@CPU@/$CPU/g")
  echo "START $(date -u +%FT%TZ) $cmd"
  if eval "$cmd"; then echo "OK $(date -u +%FT%TZ)"; else echo "FAILED $(date -u +%FT%TZ) $cmd"; rc=1; fi
done < "$JOBS"
echo "QUEUE END rc=$rc"
exit $rc
