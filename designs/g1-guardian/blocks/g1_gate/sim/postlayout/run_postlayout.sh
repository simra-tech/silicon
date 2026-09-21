#!/usr/bin/env bash
# Post-layout runs of the G1_GATE testbench on the kpex netlist. Usage (repo root):
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_gate/sim flow/run.sh bash postlayout/run_postlayout.sh [all|one MOS VDDA VDD TEMP [nopad]]
# tb_gate.cir with the schematic netlist swapped for postlayout/g1_gate_pex.spice (same pad models, loads, options).
# Logs: postlayout/logs/pl_<...>.log ; summary: postlayout/results_postlayout.txt
set -u
mkdir -p postlayout/logs ../../../../../build/g1_gate_pl
B=../../../../../build/g1_gate_pl
sed -e 's#^\.include netlist/g1_gate.spice#.include postlayout/g1_gate_pex.spice#' tb_gate.cir > postlayout/tb_gate_pex.cir
run() { # MOS VDDA VDD TEMP [nopad]
  tag="pl_$1_$2V_$3V_$4C${5:+_$5}"
  sed -e "s/@@MOS@@/$1/" -e "s/@@VDDA@@/$2/" -e "s/@@VDD@@/$3/" -e "s/@@TEMP@@/$4/" postlayout/tb_gate_pex.cir > $B/$tag.cir
  [ "${5:-}" = nopad ] && sed -i -e "s/^XPG .*/Rpg gate gate_core 1/" -e "s/^XPF .*/Rpf fault_n fault_core 1/" -e "s/^Cgate gfet 0 5n/Cgate gfet 0 50f/" $B/$tag.cir
  ngspice -b $B/$tag.cir > postlayout/logs/$tag.log 2>&1
  echo "== $tag"; grep -E "^(STATES|FASTPATH|DIGITAL|ARM|SUPPLY)|Timestep too small" postlayout/logs/$tag.log
}
{
echo "# G1_GATE post-layout results (kpex 2.5D CC netlist), $(date -u +%Y-%m-%dT%H:%MZ), ngspice $(ngspice -v | grep -o 'ngspice-[0-9]*')"
if [ "${1:-all}" = one ]; then run $2 $3 $4 $5 ${6:-}; exit; fi
run mos_tt 3.3 1.2 27
run mos_tt 3.3 1.2 -40
run mos_ff 3.6 1.32 -40
run mos_ff 3.6 1.32 -40 nopad
run mos_ss 3.0 1.08 175 nopad
} | tee postlayout/results_postlayout.txt
