#!/usr/bin/env bash
# Merged-SDC STA (reports/sta_merged_sdc_20260924/run_sta.sh, unchanged) on a trial macro.
# Usage (repository root): sta_trial.sh <final views dir> <tag> <cpu>   (BULK must be set)
set -uo pipefail
views=$1; tag=$2; cpu=$3
for c in macro chip_merged; do
  for k in fast typ slow; do
    if RUN_TAG=digital-eco-feasibility-20260925/sta/$tag MACRO_NL=$views/nl/g1_digital.nl.v \
       MACRO_SPEF=$views/spef/nom/g1_digital.nom.spef \
       designs/g1-guardian/blocks/g1_ctrl/reports/sta_merged_sdc_20260924/run_sta.sh $c $k $cpu "$BULK"; then
      echo "passed-run $c $k"
    else
      echo "FAILED-run $c $k"
    fi
  done
done
for d in "$BULK/digital-eco-feasibility-20260925/sta/$tag"/*; do
  echo "## $(basename "$d")"; cat "$d/summary.tsv" 2>/dev/null | tr '\n' ' '; echo
done
