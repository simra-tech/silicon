#!/usr/bin/env bash
# Run sta_final.tcl for one case and corner inside the pinned container, pinned to <cpu>.
# Usage (repository root): MACRO_NL=.. MACRO_SPEF=.. INPUTS=.. TOP_SPEF=.. [CLOCK_NET=..] [OSC_TRANS=r,f] [OSC_LAT=r,f] [BOARD_LOAD_PF=..] \
#   designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_20260928/run_sta_final.sh <chip|macro> <fast|typ|slow> <cpu> <results_root> <out_dir>
set -euo pipefail
case_=$1; corner=$2; cpu=$3; root=$4; out=$5
here=designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_20260928
mkdir -p "$out"
G1_CPUSET=$cpu G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=$root timeout 3600 flow/run.sh \
  env MACRO_NL=$MACRO_NL MACRO_SPEF=$MACRO_SPEF INPUTS=${INPUTS:-} TOP_SPEF=${TOP_SPEF:-} CLOCK_NET=${CLOCK_NET:-} \
      OSC_TRANS=${OSC_TRANS:-} OSC_LAT=${OSC_LAT:-} BOARD_LOAD_PF=${BOARD_LOAD_PF:-} PIN_SLEWS=${PIN_SLEWS:-} CASE=$case_ CORNER=$corner OUT=$out \
  sta -no_splash -exit /work/$here/sta_final.tcl > "$out/sta.log" 2>&1
grep -q "STA_FINAL_COMPLETE $case_ $corner" "$out/sta.log"
