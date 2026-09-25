#!/usr/bin/env bash
# ECO 2026-09-25 (blocks/g1_ctrl/ECO_20260925.md): run the RTL testbenches against the ECO RTL copies
# (blocks/g1_ctrl/rtl_eco_20260925, blocks/g1_seu/rtl_eco_20260925) inside the pinned container.
# From the repository root:
#   G1_CPUSET=46-47 G1_CPUS=2 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/sim \
#     flow/run.sh bash eco_20260925/run_eco.sh [suite|redteam|eco|alt-inrush|all]
#   suite      existing tb_g1_digital.v (unmodified, v1.1 expectations) and tb_g1_seu.v on the ECO RTL
#   redteam    existing redteam_20260925/tb_redteam.v (unmodified) on the ECO RTL
#              and tb_redteam_eco.v (R1 rewritten to the map-1.2 power-up contract)
#   eco        tb_g1_digital_eco.v: tb_g1_digital.v updated to map 1.2 plus the ECO tests E1..E8
#   contracts  existing tb_bench/tb_fault/tb_cdc/tb_trim_contract.v (unmodified, v1.1 expectations) on the ECO RTL
#              (iverilog -g2012 as in run_contract.py), then the map-1.2 copies tb_bench/tb_cdc_contract_eco.v
#   alt-inrush tb_redteam.v R2 on the ECO RTL with the literal "saturate at 17'h1FFFF, no sticky flag"
#              inrush variant (scratch copy under build/, shows why the sticky flag is needed)
# Logs are written next to this script; build products go to build/g1_eco/ (gitignored).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM="$(cd "$HERE/.." && pwd)"
BLOCKS="$(cd "$SIM/../.." && pwd)"
ROOT="$(cd "$BLOCKS/../../.." && pwd)"
OUT="$ROOT/build/g1_eco"; mkdir -p "$OUT"
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
E="$BLOCKS/g1_ctrl/rtl_eco_20260925"; S="$BLOCKS/g1_seu/rtl_eco_20260925"
CTRL="$E/g1_sync2.v $E/g1_serial.v $E/g1_trip_timer.v $E/g1_regfile.v $E/g1_digital_top.v $E/g1_digital.v"
SEU="$S/g1_tmr_reg.v $S/g1_seu_chain.v $S/g1_seu.v"
status=0
run_tb() {   # name tb log marker sources...
    local name="$1" tb="$2" log="$3" marker="$4"; shift 4
    {
        echo "# $name (ECO RTL rtl_eco_20260925)"
        echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
        echo "# PDK commit $(cat ${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/COMMIT)"
        echo "# tb sha256: $(sha256sum "$tb" | cut -c1-16)"
        for f in "$@"; do echo "# rtl sha256: $(sha256sum "$f" | cut -c1-16)  ${f#$ROOT/}"; done
        echo "# iverilog -g2005 -Wall -Wno-timescale -o $name.vvp <rtl> ${tb#$ROOT/}"
        iverilog -g2005 -Wall -Wno-timescale -o "$OUT/$name.vvp" "$@" "$tb" 2>&1
        (cd "$OUT" && vvp -n "$OUT/$name.vvp" 2>&1)
    } | tee "$log"
    grep -q "$marker" "$log" || status=1
}
run_tb12() {   # name tb log sources...   (contract benches are SystemVerilog-2012, as run_contract.py)
    local name="$1" tb="$2" log="$3"; shift 3
    {
        echo "# $name (ECO RTL rtl_eco_20260925)"
        echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
        echo "# tb sha256: $(sha256sum "$tb" | cut -c1-16)"
        echo "# iverilog -g2012 -Wall -Wno-timescale -o $name.vvp <rtl> ${tb#$ROOT/}"
        iverilog -g2012 -Wall -Wno-timescale -o "$OUT/$name.vvp" "$tb" "$@" 2>&1
        (cd "$OUT" && timeout 600 vvp -n "$OUT/$name.vvp" 2>&1) || echo "# vvp exit status $?"
    } | tee "$log"
    grep -q "ALL TESTS PASSED" "$log" && ! grep -q "FAIL" "$log" || status=1
}
MODE="${1:-all}"
if [[ $MODE == suite || $MODE == all ]]; then
    run_tb tb_g1_digital_on_eco "$SIM/tb_g1_digital.v" "$HERE/tb_g1_digital_on_eco.log" "ALL TESTS PASSED" $CTRL $SEU
    run_tb tb_g1_seu_on_eco "$BLOCKS/g1_seu/sim/tb_g1_seu.v" "$HERE/tb_g1_seu_on_eco.log" "ALL TESTS PASSED" $SEU
fi
if [[ $MODE == redteam || $MODE == all ]]; then
    run_tb tb_redteam_on_eco "$SIM/redteam_20260925/tb_redteam.v" "$HERE/tb_redteam_on_eco.log" "RED-TEAM RUN COMPLETE" $CTRL $SEU
fi
if [[ $MODE == redteam || $MODE == all ]]; then
    run_tb tb_redteam_eco "$HERE/tb_redteam_eco.v" "$HERE/tb_redteam_eco.log" "RED-TEAM RUN COMPLETE" $CTRL $SEU
fi
if [[ $MODE == eco || $MODE == all ]]; then
    run_tb tb_g1_digital_eco "$HERE/tb_g1_digital_eco.v" "$HERE/tb_g1_digital_eco.log" "ALL TESTS PASSED" $CTRL $SEU
fi
if [[ $MODE == contracts ]]; then
    for c in bench fault cdc; do
        run_tb12 tb_${c}_contract_on_eco "$SIM/tb_${c}_contract.v" "$HERE/tb_${c}_contract_on_eco.log" $CTRL $SEU
    done
    run_tb12 tb_trim_contract_on_eco "$SIM/tb_trim_contract.v" "$HERE/tb_trim_contract_on_eco.log" $E/g1_sync2.v $E/g1_trip_timer.v
    # map-1.2 copies (EN-low steps >= 12 cycles, INRUSH reset 0x02)
    run_tb12 tb_bench_contract_eco "$HERE/tb_bench_contract_eco.v" "$HERE/tb_bench_contract_eco.log" $CTRL $SEU
    run_tb12 tb_cdc_contract_eco "$HERE/tb_cdc_contract_eco.v" "$HERE/tb_cdc_contract_eco.log" $CTRL $SEU
fi
if [[ $MODE == alt-inrush ]]; then
    ALT="$OUT/g1_trip_timer_alt_saturate.v"
    # literal variant: no sticky flag; the counter runs on to 17'h1FFFF and saturates
    sed -e 's/assign inrush_active = ~inrush_done \& (inrush_cnt < inrush_lim);/assign inrush_active = (inrush_cnt < inrush_lim);/' \
        -e 's/end else if (inrush_active)$/end else if (inrush_cnt != 17'"'"'h1FFFF)/' "$E/g1_trip_timer.v" > "$ALT"
    echo "# alt variant diff:"; diff "$E/g1_trip_timer.v" "$ALT" || true
    run_tb tb_redteam_on_eco_alt_saturate "$SIM/redteam_20260925/tb_redteam.v" "$HERE/tb_redteam_on_eco_alt_saturate.log" "RED-TEAM RUN COMPLETE" \
        $E/g1_sync2.v $E/g1_serial.v "$ALT" $E/g1_regfile.v $E/g1_digital_top.v $E/g1_digital.v $SEU
fi
exit $status
