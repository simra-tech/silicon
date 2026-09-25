#!/usr/bin/env bash
# Launch one containerised tool run pinned to a CPU, detached, with a wall-clock bound.
# Usage: flow/launch_pinned.sh <cpu> <workdir-rel-to-repo> <wall-seconds> <logfile> <command...>
# Writes <logfile> (stdout+stderr) and <logfile>.pid; exit code lands in <logfile>.rc.
set -euo pipefail
CPU="$1"; WD="$2"; WALL="$3"; LOG="$4"; shift 4
if [ "$(nice)" != "0" ]; then echo "warning: launching from a shell at nice level $(nice); the solver will yield to other users' load (cannot be lowered without privileges)" >&2; fi
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$(dirname "$LOG")"
(
  cd "$REPO"
  G1_CPUSET="$CPU" G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_WORKDIR="$WD" \
  G1_RESULTS_ROOT="${G1_RESULTS_ROOT:-${BULK:?set BULK to the external artifact root}}" \
  timeout --kill-after=10s "$WALL" flow/run.sh "$@" >"$LOG" 2>&1
  echo $? >"$LOG.rc"
) &
echo $! >"$LOG.pid"
echo "launched cpu=$CPU pid=$! log=$LOG"
