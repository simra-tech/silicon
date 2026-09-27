#!/usr/bin/env bash
# Red-team 2026-09-27. From the repository root:
#   G1_CPUSET=19 G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/review/redteam-20260927/digital/tb flow/run.sh bash run_rt27.sh
set -uo pipefail
export LD_LIBRARY_PATH="/foss/tools/iverilog/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
B=/work/designs/g1-guardian/blocks; E=$B/g1_ctrl/rtl_eco_20260925; S=$B/g1_seu/rtl_eco_20260925
RTL="$E/g1_sync2.v $E/g1_serial.v $E/g1_trip_timer.v $E/g1_regfile.v $S/g1_tmr_reg.v $S/g1_seu_chain.v $S/g1_seu.v $E/g1_digital_top.v $E/g1_digital.v"
P=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog
NL=/work/build/g1_gls_eco/in_r3cand2/g1_digital.nl.v
{ echo "# RTL  $(iverilog -V 2>&1 | head -1)"; sha256sum tb_rt27.v $RTL | cut -c1-16
  iverilog -g2012 -Wno-timescale -o /tmp/rt27_rtl.vvp $RTL tb_rt27.v && vvp -n /tmp/rt27_rtl.vvp; } > tb_rt27_rtl.log 2>&1
{ echo "# GLS netlist $(sha256sum $NL | cut -c1-16), -DFUNCTIONAL -DUNIT_DELAY=#1"
  iverilog -g2012 -DGLS -DFUNCTIONAL -DUNIT_DELAY=#1 -Wno-timescale -o /tmp/rt27_gls.vvp $P/sg13g2_udp.v $P/sg13g2_stdcell.v $NL tb_rt27.v 2>&1 | grep -v "sorry: ifnone"
  vvp -n /tmp/rt27_gls.vvp; } > tb_rt27_gls.log 2>&1
grep -E "^(PASS|FAIL|RT27)|FAIL " tb_rt27_rtl.log; echo ==; grep -E "^(PASS|FAIL|RT27)|FAIL " tb_rt27_gls.log
