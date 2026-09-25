#!/usr/bin/env bash
# Gate-level simulation of a hardened ECO g1_digital netlist (map 1.2) with the PDK sg13g2
# standard-cell models: tb_g1_digital_eco.v (-DGLS) and tb_redteam_eco.v, functional models with
# unit delay, and tb_g1_digital_eco.v with an SDF annotated (-DGLS -DSDF, Icarus -gspecify).
# From the repository root (CPUs 46-47):
#   G1_CPUSET=46-47 G1_CPUS=2 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/sim \
#     flow/run.sh bash gls_eco_r3/run_gls_eco.sh <netlist under /work> <sdf under /work> <tag>
# Logs next to this script; build products in build/g1_gls_eco/ (gitignored).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$SIM/../../../../.." && pwd)"
OUT="$ROOT/build/g1_gls_eco"; mkdir -p "$OUT"
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
PDK_V="${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/libs.ref/sg13g2_stdcell/verilog"
NL="$1"; SDF="${2:-}"; TAG="${3:-r3}"
MODELS="$PDK_V/sg13g2_udp.v $PDK_V/sg13g2_stdcell.v"
hdr() {
  echo "# $1"
  echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
  echo "# PDK commit $(cat ${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/COMMIT)"
  echo "# tb sha256: $(sha256sum "$2" | cut -c1-16)"
  test -f "$NL" || { echo "# netlist not found: $NL"; return 1; }
  echo "# netlist: ${NL#$ROOT/}  sha256: $(sha256sum "$NL" | cut -c1-64)"
  [[ -n "$SDF" && "$1" == *annotated* ]] && echo "# sdf: ${SDF#$ROOT/}  sha256: $(sha256sum "$SDF" | cut -c1-64)"
  return 0
}
status=0
run() {  # vvpname title tb log marker flags...
  local name="$1" title="$2" tb="$3" log="$4" marker="$5"; shift 5
  { hdr "$title" "$tb"
    echo "# iverilog -g2012 $* -Wno-timescale <models> <netlist> ${tb#$ROOT/}"
    iverilog -g2012 "$@" -Wno-timescale -o "$OUT/$name.vvp" $MODELS "$NL" "$tb" 2>&1
    (cd "$OUT" && timeout 3000 vvp -n "$OUT/$name.vvp" 2>&1) || echo "# vvp exit status $?"
  } | tee "$log"
  grep -q "$marker" "$log" || status=1
}
run gls_eco "tb_g1_digital_eco gate level, functional models, UNIT_DELAY=#1, no SDF" "$SIM/eco_20260925/tb_g1_digital_eco.v" \
    "$HERE/tb_g1_digital_eco_gls_${TAG}.log" "ALL TESTS PASSED" -DGLS -DFUNCTIONAL '-DUNIT_DELAY=#1'
run gls_redteam "tb_redteam_eco gate level, functional models, UNIT_DELAY=#1, no SDF" "$SIM/eco_20260925/tb_redteam_eco.v" \
    "$HERE/tb_redteam_eco_gls_${TAG}.log" "RED-TEAM RUN COMPLETE" -DGLS -DFUNCTIONAL '-DUNIT_DELAY=#1'
if [[ -n "$SDF" ]]; then
  TB="$OUT/tb_g1_digital_eco_sdf.v"
  sed "s|^module tb_g1_digital_eco;|module tb_g1_digital_eco;\ninitial begin \$sdf_annotate(\"$SDF\", dut); \$display(\"SDF_ANNOTATION_RETURNED\"); end|" \
      "$SIM/eco_20260925/tb_g1_digital_eco.v" > "$TB"
  run gls_eco_sdf "tb_g1_digital_eco gate level, SDF annotated on dut (pu_* instances unannotated), -gspecify -ginterconnect" "$TB" \
      "$HERE/tb_g1_digital_eco_gls_sdf_${TAG}.log" "ALL TESTS PASSED" -DGLS -DSDF -gspecify -ginterconnect
fi
exit $status
