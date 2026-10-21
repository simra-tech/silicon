#!/bin/sh
# run_q5.sh <cpu> <job file>: revision-5 job queue. Each non-comment line of the job file is the argument list of
# one sim/r5/run_points5.py call (without --cpu). Jobs run one after the other on the given CPU. A failed job is
# recorded (FAILED line in the queue log, run.json status, <id>_segments.json "stopped") and is NOT resubmitted;
# the queue goes on with the next independent job and exits 1 at the end if any job failed.
# Do not edit a job file while its queue runs (revision-4 failure 8): write a new file.
CPU=$1; JOBS=$2
cd "$(dirname "$0")/../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the results root}"; export G1_RESULTS_ROOT
rc=0
while IFS= read -r line; do
  case "$line" in ''|'#'*) continue ;; esac
  echo "START $(date -u +%FT%TZ) $line"
  if eval "python3 sim/r5/run_points5.py --cpu $CPU $line"; then echo "OK $(date -u +%FT%TZ)"; else echo "FAILED $(date -u +%FT%TZ) $line"; rc=1; fi
done < "$JOBS"
echo "QUEUE END rc=$rc"
exit $rc
