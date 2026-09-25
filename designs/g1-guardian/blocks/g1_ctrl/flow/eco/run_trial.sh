#!/usr/bin/env bash
# Run one LibreLane re-hardening trial of g1_digital inside the pinned container.
# Usage (repository root): BULK=<artifact root> G1_CPUSET=<cpus> G1_CPUS=<n> \
#   designs/g1-guardian/blocks/g1_ctrl/flow/eco/run_trial.sh <config.yaml> <run-tag> [librelane args...]
# Run directories go to ${ECO_ROOT:-$BULK/digital-eco-feasibility-20260925}/runs/<tag> through the
# gitignored symlink flow/eco/runs. OpenROAD is the image's openroad-librelane
# 26Q1-1024 build (the one run7 and the chip macro used; the PATH 26Q3 build fails
# set_layer_rc with this LibreLane, see review/audits/DIGITAL_CTS_FANOUT_20260923.md).
# flow/eco is put on PYTHONPATH so LibreLane discovers librelane_plugin_g1eco.
set -euo pipefail
cfg=$1; tag=$2; shift 2
here=designs/g1-guardian/blocks/g1_ctrl/flow/eco
root="${ECO_ROOT:-$BULK/digital-eco-feasibility-20260925}"
mkdir -p "$root/runs" "$root/logs"
ln -sfn "$root/runs" "$here/runs"   # gitignored; points at the bulk root of this run
G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT="$BULK" G1_WORKDIR=$here flow/run.sh \
  sh -c 'export PYTHONPATH="$0:$PYTHONPATH" _LLN_OVERRIDE_OPENROAD=/foss/tools/openroad-librelane/bin/openroad; exec librelane "$@"' \
  "/work/$here" "$cfg" --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk --run-tag "$tag" "$@"
