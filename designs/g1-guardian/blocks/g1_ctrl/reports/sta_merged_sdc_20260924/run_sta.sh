#!/usr/bin/env bash
# Run sta.tcl for one case and corner inside the pinned container.
# Usage (repository root): [MACRO_NL=<nl.v> MACRO_SPEF=<spef>] designs/g1-guardian/blocks/g1_ctrl/reports/sta_merged_sdc_20260924/run_sta.sh <case> <corner> <cpu> <results_root>
# MACRO_NL/MACRO_SPEF must be container-visible (under /work or <results_root>); default = run7 views.
set -euo pipefail
case_=$1; corner=$2; cpu=$3; root=$4
here=designs/g1-guardian/blocks/g1_ctrl/reports/sta_merged_sdc_20260924
out=$root/${RUN_TAG:+$RUN_TAG/}$case_-$corner
mkdir -p "$out"
G1_CPUSET=$cpu G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=$root flow/run.sh \
  env MACRO_NL=${MACRO_NL:-} MACRO_SPEF=${MACRO_SPEF:-} CASE=$case_ CORNER=$corner OUT=$out TEMPLATE_SDC=/work/$here/g1_chip_top_template_only.sdc \
  sta -no_splash -exit /work/$here/sta.tcl > "$out/sta.log" 2>&1
grep -q "STA_MERGED_COMPLETE $case_ $corner" "$out/sta.log"
