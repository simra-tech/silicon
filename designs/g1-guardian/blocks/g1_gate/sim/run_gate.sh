#!/usr/bin/env bash
# G1_GATE runs. Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_gate/sim flow/run.sh bash run_gate.sh <what> [args]
#   one MOS VDDA VDD TEMP   single functional/timing run (tb_gate.cir)      -> logs/gate_<...>.log
#   pwr ORDER RPD           single power-up run (tb_gate_pwr.cir)          -> logs/gate_pwr_<...>.log
#   sum                     collect all logs into results_gate.txt / results_gate_pwr.txt
set -u
mkdir -p logs ../../../../../build/g1_gate
B=../../../../../build/g1_gate
case ${1:-sum} in
one)
  tag="gate_$2_$3V_$4V_$5C${6:+_$6}"
  sed -e "s/@@MOS@@/$2/" -e "s/@@VDDA@@/$3/" -e "s/@@VDD@@/$4/" -e "s/@@TEMP@@/$5/" tb_gate.cir > $B/$tag.cir
  # optional 6th arg "loose": retry with looser tolerances when the IO-pad model does not converge
  [ "${6:-}" = loose ] && sed -i -e "s/reltol=0.005 itl4=100 abstol=1e-9 vntol=1e-5/reltol=0.01 itl4=200 abstol=1e-8 vntol=1e-4/" $B/$tag.cir
  # optional 6th arg "nopad": replace the two IO pads by 1 Ohm links (logic-only check of the block at corners
  # where the PDK pad model does not converge); the GATE "pad" node then carries 50 fF, not 5 nF
  [ "${6:-}" = nopad ] && sed -i -e "s/^XPG .*/Rpg gate gate_core 1/" -e "s/^XPF .*/Rpf fault_n fault_core 1/" -e "s/^Cgate gfet 0 5n/Cgate gfet 0 50f/" $B/$tag.cir
  ngspice -b $B/$tag.cir > logs/$tag.log 2>&1 ;;
pwr)
  if [ $2 = A ]; then PA="0 0 1u 0 3u 3.3 11u 3.3"; PD="0 0 5u 0 7u 1.2 11u 1.2"; else PD="0 0 1u 0 3u 1.2 11u 1.2"; PA="0 0 5u 0 7u 3.3 11u 3.3"; fi
  EN="0 0 9u 0 9.1u 3.3 11u 3.3"
  tag="gate_pwr_$2_rpd$3"
  sed -e "s/@@ORDER@@/$2/g" -e "s/@@PWLA@@/$PA/" -e "s/@@PWLD@@/$PD/" -e "s/@@ENPWL@@/$EN/g" -e "s/@@RPD@@/$3/g" tb_gate_pwr.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > logs/$tag.log 2>&1 ;;
sum)
  { echo "# G1_GATE functional/timing, $(date -u +%FT%H:%MZ)"; for f in logs/gate_mos_*.log; do echo "== $(basename $f .log)"; grep -E "^(STATES|FASTPATH|DIGITAL|ARM|SUPPLY)|Timestep too small" $f; done; } > results_gate.txt
  { echo "# G1_GATE power-up, $(date -u +%FT%H:%MZ)"; for f in logs/gate_pwr_*.log; do grep -E "^POWERUP|Timestep too small" $f; done; } > results_gate_pwr.txt
  cat results_gate.txt results_gate_pwr.txt ;;
esac
