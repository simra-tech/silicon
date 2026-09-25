#!/usr/bin/env bash
# Red-team 2026-09-25: run tb_redteam.v (and optionally the existing system testbench)
# against the RTL or a gate-level g1_digital netlist, inside the pinned container.
# From the repository root:
#   G1_CONTAINER_ENGINE=podman G1_CPUSET=<cpus> flow/run.sh bash \
#     designs/g1-guardian/blocks/g1_ctrl/sim/redteam_20260925/run_redteam.sh rtl
#   ... run_redteam.sh gls <netlist under /work> <tag>          (tb_redteam.v on the netlist)
#   ... run_redteam.sh gls-system <netlist under /work> <tag>   (existing tb_g1_digital.v -DGLS on the netlist)
# Logs are written next to this script; build products to build/g1_redteam/ (gitignored).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKS="$(cd "$HERE/../../.." && pwd)"
ROOT="$(cd "$BLOCKS/../../.." && pwd)"
OUT="$ROOT/build/g1_redteam"; mkdir -p "$OUT"
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
PDK_V="${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/libs.ref/sg13g2_stdcell/verilog"
MODE="${1:-rtl}"; NL="${2:-}"; TAG="${3:-${MODE}}"
RTL="$BLOCKS/g1_ctrl/rtl/g1_sync2.v $BLOCKS/g1_ctrl/rtl/g1_serial.v $BLOCKS/g1_ctrl/rtl/g1_trip_timer.v $BLOCKS/g1_ctrl/rtl/g1_regfile.v $BLOCKS/g1_ctrl/rtl/g1_digital_top.v $BLOCKS/g1_ctrl/rtl/g1_digital.v $BLOCKS/g1_seu/rtl/g1_tmr_reg.v $BLOCKS/g1_seu/rtl/g1_seu_chain.v $BLOCKS/g1_seu/rtl/g1_seu.v"
hdr() {
  echo "# $1"
  echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
  echo "# PDK commit $(cat ${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/COMMIT)"
  echo "# tb sha256: $(sha256sum "$2" | cut -c1-16)"
  [[ -n "$NL" ]] && echo "# netlist: ${NL#$ROOT/}  sha256: $(sha256sum "$NL" | cut -c1-16)"
  return 0
}
case "$MODE" in
  rtl)
    LOG="$HERE/tb_redteam_rtl.log"
    { hdr "tb_redteam, RTL" "$HERE/tb_redteam.v"
      echo "# iverilog -g2005 -Wall -Wno-timescale <rtl> tb_redteam.v"
      iverilog -g2005 -Wall -Wno-timescale -o "$OUT/tb_redteam_rtl.vvp" $RTL "$HERE/tb_redteam.v" 2>&1
      (cd "$OUT" && vvp -n "$OUT/tb_redteam_rtl.vvp" 2>&1); } | tee "$LOG" ;;
  gls)
    LOG="$HERE/tb_redteam_gls_${TAG}.log"
    { hdr "tb_redteam, gate level (functional models, UNIT_DELAY=#1, no SDF)" "$HERE/tb_redteam.v"
      echo "# iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -Wno-timescale <models> <netlist> tb_redteam.v"
      iverilog -g2012 -DFUNCTIONAL '-DUNIT_DELAY=#1' -Wno-timescale -o "$OUT/tb_redteam_gls_${TAG}.vvp" \
        "$PDK_V/sg13g2_udp.v" "$PDK_V/sg13g2_stdcell.v" "$NL" "$HERE/tb_redteam.v" 2>&1
      (cd "$OUT" && vvp -n "$OUT/tb_redteam_gls_${TAG}.vvp" 2>&1); } | tee "$LOG" ;;
  gls-system)
    LOG="$HERE/tb_g1_digital_gls_${TAG}.log"
    { hdr "tb_g1_digital (existing system testbench, unmodified), gate level (functional, UNIT_DELAY=#1, no SDF)" "$BLOCKS/g1_ctrl/sim/tb_g1_digital.v"
      echo "# iverilog -g2012 -DGLS -DFUNCTIONAL -DUNIT_DELAY=#1 -Wno-timescale <models> <netlist> tb_g1_digital.v"
      iverilog -g2012 -DGLS -DFUNCTIONAL '-DUNIT_DELAY=#1' -Wno-timescale -o "$OUT/tb_g1_digital_gls_${TAG}.vvp" \
        "$PDK_V/sg13g2_udp.v" "$PDK_V/sg13g2_stdcell.v" "$NL" "$BLOCKS/g1_ctrl/sim/tb_g1_digital.v" 2>&1
      (cd "$OUT" && vvp -n "$OUT/tb_g1_digital_gls_${TAG}.vvp" 2>&1); } | tee "$LOG" ;;
  *) echo "mode rtl | gls | gls-system" >&2; exit 2 ;;
esac
grep -q "RED-TEAM RUN COMPLETE\|ALL TESTS PASSED" "$LOG"
