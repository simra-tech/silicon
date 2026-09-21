#!/usr/bin/env bash
# Run the G1 digital testbenches with Icarus Verilog inside the pinned container.
# From the repository root:   flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_sim.sh
# Logs: blocks/g1_ctrl/sim/tb_g1_digital.log, blocks/g1_seu/sim/tb_g1_seu.log
# VCDs go to build/g1_digital/ (gitignored).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKS="$(cd "$HERE/../.." && pwd)"
ROOT="$(cd "$BLOCKS/../../.." && pwd)"
OUT="$ROOT/build/g1_digital"
mkdir -p "$OUT"
# The pinned container ships vvp without its library on the loader path.
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

CTRL_RTL="$BLOCKS/g1_ctrl/rtl/g1_sync2.v $BLOCKS/g1_ctrl/rtl/g1_serial.v $BLOCKS/g1_ctrl/rtl/g1_trip_timer.v $BLOCKS/g1_ctrl/rtl/g1_regfile.v $BLOCKS/g1_ctrl/rtl/g1_digital_top.v"
SEU_RTL="$BLOCKS/g1_seu/rtl/g1_tmr_reg.v $BLOCKS/g1_seu/rtl/g1_seu_chain.v $BLOCKS/g1_seu/rtl/g1_seu.v"

status=0
run_tb() {   # name  tb_file  log_file  sources...
    local name="$1" tb="$2" log="$3"; shift 3
    {
        echo "# $name"
        echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
        echo "# iverilog -g2005 -Wall -Wno-timescale -o $OUT/$name.vvp $* $tb"
        iverilog -g2005 -Wall -Wno-timescale -o "$OUT/$name.vvp" "$@" "$tb" 2>&1
        (cd "$OUT" && vvp -n "$OUT/$name.vvp" 2>&1)
    } | tee "$log"
    grep -q "ALL TESTS PASSED" "$log" || status=1
}

run_tb tb_g1_digital "$HERE/tb_g1_digital.v" "$HERE/tb_g1_digital.log" $CTRL_RTL $SEU_RTL
run_tb tb_g1_seu     "$BLOCKS/g1_seu/sim/tb_g1_seu.v" "$BLOCKS/g1_seu/sim/tb_g1_seu.log" $SEU_RTL
exit $status
