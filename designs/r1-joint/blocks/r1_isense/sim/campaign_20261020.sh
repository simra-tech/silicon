#!/bin/sh
# r1_isense evidence campaign 2026-10-20 (schematic level). Run from the repository root:
#   sh designs/r1-joint/blocks/r1_isense/sim/campaign_20261020.sh
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results directory}"; export G1_RESULTS_ROOT
R=designs/r1-joint/blocks/r1_isense/sim/run_deck.py
C5=tt,ss,ff,ss_cold,ff_hot
G1_CPUSET=109-111; export G1_CPUSET
python3 $R --block r1_isense --deck tb_isense_step.cir --run-id isense-step-20261020-r1 --corners $C5 --set VCMIN=0 --analyze analyze_step.py \
  --question "Settling to 0.5 % within 300 ns after 100 mV / 120 mV PWM edges, overload recovery, output node range, at 5 corners"
python3 $R --block r1_isense --deck tb_isense_dc.cir --run-id isense-dc-20261020-r1 --corners $C5 --set VCMIN=0 --analyze analyze_dc.py \
  --question "Gain, pedestal, residual offset after AZ, INL over -20..100 mV at 5 corners, Kelvin common mode 0 V"
python3 $R --block r1_isense --deck tb_isense_dc.cir --run-id isense-dc-cmm100-20261020-r1 --corners tt --set VCMIN=-0.1 --analyze analyze_dc.py \
  --question "Same as isense-dc at tt with Kelvin common mode -0.1 V"
python3 $R --block r1_isense --deck tb_isense_dc.cir --run-id isense-dc-cmp100-20261020-r1 --corners tt --set VCMIN=0.1 --analyze analyze_dc.py \
  --question "Same as isense-dc at tt with Kelvin common mode +0.1 V"
G1_CPUSET=109-110; export G1_CPUSET
python3 $R --block r1_isense --deck tb_isense_mc.cir --run-id isense-mc-20261020-r1 --corners tt_mm_s1,tt_mm_s2 --set N=25 --analyze analyze_mc.py \
  --question "Mismatch MC, 50 samples (2 seeds x 25), tt 27 C: raw offset, residual offset after AZ (target <= 100 uV), pedestal, gain" &
G1_CPUSET=111; export G1_CPUSET
python3 $R --block r1_isense --deck tb_isense_noise.cir --run-id isense-noise-20261020-r1 --corners $C5 --jobs 1 --set VH=0.93 --analyze analyze_noise.py \
  --question "Closed-loop bandwidth (>= 1 MHz), peaking, input noise density and 10 kHz-5 MHz total, CM and supply rejection at 5 corners"
wait
echo CAMPAIGN_DONE
