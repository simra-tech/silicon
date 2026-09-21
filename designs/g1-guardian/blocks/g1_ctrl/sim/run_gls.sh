#!/usr/bin/env bash
# Gate-level simulation of the hardened g1_digital netlist with the PDK's
# sg13g2 standard-cell Verilog models, driving the same system testbench as the
# RTL run (tb_g1_digital.v with -DGLS: T11/T12, which poke RTL internals, are
# skipped). Functional models, no SDF: this checks the netlist, not the timing
# (timing is the LibreLane STA).
# From the repository root:
#   flow/run.sh bash designs/g1-guardian/blocks/g1_ctrl/sim/run_gls.sh [netlist] [tag]
# Default netlist: build/g1_digital/final_run5/nl/g1_digital.nl.v (LibreLane
# --save-views-to output, gitignored). Log: sim/tb_g1_digital_gls_<tag>.log,
# where <tag> defaults to the run tag in the netlist path (final_<tag>/nl/).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
NL="${1:-$ROOT/build/g1_digital/final_run5/nl/g1_digital.nl.v}"
TAG="${2:-$(basename "$(dirname "$(dirname "$NL")")" | sed 's/^final_//')}"
OUT="$ROOT/build/g1_digital"
PDK_V="${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/libs.ref/sg13g2_stdcell/verilog"
mkdir -p "$OUT"
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
LOG="$HERE/tb_g1_digital_gls_${TAG}.log"
{
    echo "# tb_g1_digital, gate level"
    echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
    echo "# netlist: ${NL#$ROOT/}  sha256: $(sha256sum "$NL" | cut -c1-16)"
    echo "# models: $PDK_V/sg13g2_stdcell.v (PDK commit $(cat ${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/COMMIT 2>/dev/null | cut -c1-12))"
    echo "# iverilog -g2012 -DGLS -DFUNCTIONAL -DUNIT_DELAY=#1 -Wno-timescale -o $OUT/tb_g1_digital_gls_${TAG}.vvp <models> <netlist> tb_g1_digital.v"
    iverilog -g2012 -DGLS -DFUNCTIONAL '-DUNIT_DELAY=#1' -Wno-timescale \
        -o "$OUT/tb_g1_digital_gls_${TAG}.vvp" "$PDK_V/sg13g2_udp.v" "$PDK_V/sg13g2_stdcell.v" "$NL" "$HERE/tb_g1_digital.v" 2>&1
    (cd "$OUT" && vvp -n "$OUT/tb_g1_digital_gls_${TAG}.vvp" 2>&1)
} | tee "$LOG"
grep -q "ALL TESTS PASSED" "$LOG"
