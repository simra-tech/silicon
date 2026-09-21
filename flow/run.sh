#!/usr/bin/env bash
# Run a command inside the pinned EDA container with the repository mounted at /work.
# Usage: flow/run.sh <command...>      e.g.  flow/run.sh ngspice -b deck.cir
# The image, PDK root and PDK commit are pinned in designs/g1-guardian/PLAN.md.
set -euo pipefail
IMAGE="${G1_EDA_IMAGE:-tapeoutbench-eda:latest}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec docker run --rm --network none \
  --platform linux/amd64 \
  -e PDK_ROOT=/foss/pdks -e PDK=ihp-sg13g2 \
  -e HOME=/tmp -u "$(id -u):$(id -g)" \
  -v "$REPO":/work -w "/work/${G1_WORKDIR:-.}" \
  "$IMAGE" "$@"
