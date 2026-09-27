#!/usr/bin/env bash
# Red-team 2026-09-27. From the repository root:
#   G1_CPUSET=18 G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/review/redteam-20260927/digital/xflush flow/run.sh bash run_xflush.sh
set -uo pipefail
P=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog
NL=/work/build/g1_gls_eco/in_r3cand2/g1_digital.nl.v
iverilog -V 2>&1 | head -1; sha256sum $NL
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -Wno-timescale -o /tmp/xf.vvp $P/sg13g2_udp.v $P/sg13g2_stdcell.v $NL tb_xflush.v 2>&1 | grep -v "sorry: ifnone" | head -20
for n in 9 10 11 12 16; do echo "== NLOW=$n"; vvp -n /tmp/xf.vvp +NLOW=$n | grep -v "^VCD\|finish"; done
