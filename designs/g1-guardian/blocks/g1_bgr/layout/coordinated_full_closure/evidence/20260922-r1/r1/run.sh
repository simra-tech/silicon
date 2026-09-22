#!/usr/bin/env bash
# Run a command inside the pinned EDA container with the repository mounted at /work.
# Usage: flow/run.sh <command...>      e.g.  flow/run.sh ngspice -b deck.cir
# The image, PDK root and PDK commit are pinned in designs/g1-guardian/PLAN.md.
set -euo pipefail
IMAGE="${G1_EDA_IMAGE:-tapeoutbench-eda:latest}"
PLATFORM="${G1_EDA_PLATFORM:-linux/amd64}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE="${G1_CONTAINER_ENGINE:-docker}"
if ! command -v "$ENGINE" >/dev/null && [[ "$ENGINE" == docker ]] && command -v podman >/dev/null; then
  ENGINE=podman
fi
# Resolve tags to a verified immutable image before launching any tool.
case "$IMAGE" in
  tapeoutbench-eda:latest) EXPECTED=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2 ;;
  g1-sim-arm64:20260921) EXPECTED=sha256:154ef83dab5f62b50482a62d651dd9b851ddecb3b15e32902e0c2a5efa0b3eeb ;;
  *) EXPECTED="${G1_EXPECTED_IMAGE_ID:?Custom image requires G1_EXPECTED_IMAGE_ID}" ;;
esac
OBSERVED="$("$ENGINE" image inspect --format '{{.Id}}' "$IMAGE")"
OBSERVED="sha256:${OBSERVED#sha256:}"
if [[ "$OBSERVED" != "$EXPECTED" ]]; then
  echo "Image identity mismatch: expected $EXPECTED; observed $OBSERVED" >&2
  exit 1
fi
RESOURCE_ARGS=()
RESULT_ARGS=()
if [[ -n "${G1_RESULTS_ROOT:-}" ]]; then
  if [[ "$G1_RESULTS_ROOT" != /* || "$G1_RESULTS_ROOT" == / || ! -d "$G1_RESULTS_ROOT" ]]; then
    echo 'G1_RESULTS_ROOT must identify an existing dedicated absolute results directory.' >&2
    exit 1
  fi
  RESULT_ARGS=(-v "$G1_RESULTS_ROOT:$G1_RESULTS_ROOT" -e "G1_RESULTS_ROOT=$G1_RESULTS_ROOT")
fi
USER_ARGS=(-u "$(id -u):$(id -g)")
PREFIX=()
if [[ "$ENGINE" == podman ]]; then
  # Root in the rootless user namespace maps to the invoking host user.
  USER_ARGS=(-u 0:0)
  CGROUP_VERSION="$(podman info --format '{{.Host.CgroupsVersion}}')"
  if [[ "$CGROUP_VERSION" == v1 ]]; then
    : "${G1_CPUSET:?Rootless cgroups v1 requires an explicitly allocated G1_CPUSET}"
    PREFIX=(taskset -c "$G1_CPUSET")
    echo 'Resource enforcement: CPU affinity; memory reservation only (rootless cgroups v1).' >&2
  else
    if [[ -n "${G1_CPUS:-}" ]]; then RESOURCE_ARGS+=(--cpus "$G1_CPUS"); fi
    if [[ -n "${G1_MEMORY:-}" ]]; then RESOURCE_ARGS+=(--memory "$G1_MEMORY"); fi
  fi
else
  if [[ -n "${G1_CPUS:-}" ]]; then RESOURCE_ARGS+=(--cpus "$G1_CPUS"); fi
  if [[ -n "${G1_MEMORY:-}" ]]; then RESOURCE_ARGS+=(--memory "$G1_MEMORY"); fi
fi
exec "$ENGINE" run --rm --network none --pull never --label g1.project=silicon \
  --platform "$PLATFORM" ${RESOURCE_ARGS[@]+"${RESOURCE_ARGS[@]}"} \
  -e PDK_ROOT=/foss/pdks -e PDK=ihp-sg13g2 \
  -e HOME=/tmp -e OMP_NUM_THREADS="${G1_CPUS:-1}" \
  -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  "${USER_ARGS[@]}" \
  "${RESULT_ARGS[@]}" \
  -v "$REPO":/work -w "/work/${G1_WORKDIR:-.}" \
  "$OBSERVED" "${PREFIX[@]}" sh -c \
  'test "$(cat /foss/pdks/ihp-sg13g2/COMMIT)" = 84374023ee8b4b126bebbba67fcbada0a9c0ff0b || exit 1; exec "$@"' sh "$@"
