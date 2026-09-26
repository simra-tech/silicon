#!/usr/bin/env bash
# GLS of the r3 candidate v2 g1_digital netlist with one SDF corner annotated on dut
# (tb_g1_digital_eco.v -DGLS -DSDF, 20 ns sampling; tb_redteam_eco.v -DGLS with the same SDF).
# Icarus: -gspecify -ginterconnect, typical value of each (min:typ:max) triple, no timing checks.
# From the repository root (CPUs 46-49):
#   G1_CPUSET=48 G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/sim \
#     flow/run.sh bash gls_eco_r3v2/sdf_corners/run_sdf_corner.sh <netlist under /work> <sdf under /work> <tag>
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM="$(cd "$HERE/../.." && pwd)"
ROOT="$(cd "$SIM/../../../../.." && pwd)"
OUT="$ROOT/build/g1_gls_eco/$3"; mkdir -p "$OUT"
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
PDK_V="${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/libs.ref/sg13g2_stdcell/verilog"
NL="$1"; SDF="$2"; TAG="$3"
status=0
for tb in tb_g1_digital_eco tb_redteam_eco; do
  TB="$OUT/${tb}_sdf.v"; LOG="$HERE/${tb}_gls_sdf_${TAG}.log"
  sed "s|^module ${tb};|module ${tb};\ninitial begin \$sdf_annotate(\"$SDF\", dut); \$display(\"SDF_ANNOTATION_RETURNED\"); end|" \
      "$SIM/eco_20260925/$tb.v" > "$TB"
  { echo "# $tb gate level, SDF annotated on dut, -gspecify -ginterconnect ($TAG)"
    echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)  $(iverilog -V 2>&1 | head -1)"
    echo "# PDK commit $(cat ${PDK_ROOT:-/foss/pdks}/${PDK:-ihp-sg13g2}/COMMIT)"
    echo "# tb sha256: $(sha256sum "$SIM/eco_20260925/$tb.v" | cut -c1-16)"
    echo "# netlist: ${NL#$ROOT/}  sha256: $(sha256sum "$NL" | cut -c1-64)"
    echo "# sdf: ${SDF#$ROOT/}  sha256: $(sha256sum "$SDF" | cut -c1-64)"
    echo "# iverilog -g2012 -DGLS -DSDF -gspecify -ginterconnect -Wno-timescale <models> <netlist> <tb with \$sdf_annotate>"
    iverilog -g2012 -DGLS -DSDF -gspecify -ginterconnect -Wno-timescale -o "$OUT/$tb.vvp" \
      "$PDK_V/sg13g2_udp.v" "$PDK_V/sg13g2_stdcell.v" "$NL" "$TB" 2>&1 | grep -v "sorry: ifnone"
    (cd "$OUT" && timeout 5000 vvp -n "$OUT/$tb.vvp" 2>&1) || echo "# vvp exit status $?"
  } > "$LOG"
  grep -q "ALL TESTS PASSED\|RED-TEAM RUN COMPLETE" "$LOG" || status=1
done
exit $status
