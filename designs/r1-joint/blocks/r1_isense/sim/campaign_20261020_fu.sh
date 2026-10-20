#!/bin/sh
# r1_isense follow-ups 2026-10-20 (schematic level): AZ loop gain, hold droop. Run from the repository root.
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results directory}"; export G1_RESULTS_ROOT
# (mismatch MC at ss/ff was run first: isense-mc-ssff-20261020-r1)
# python3 designs/r1-joint/blocks/r1_isense/sim/run_deck.py --block r1_isense --deck tb_isense_mc.cir --run-id isense-mc-ssff-20261020-r1 --corners ss_mm_s4,ff_mm_s5 --set N=30 --analyze analyze_mc.py
R=designs/r1-joint/blocks/r1_isense/sim/run_deck.py
export G1_CPUSET=110-111
python3 $R --block r1_isense --deck tb_isense_azloop.cir --run-id isense-azloop-20261020-r1 --corners tt,ss,ff,ss_cold,ff_hot --jobs 2 --question "Return ratio of the auto-zero loop (differential and common mode) during AZ hold, loop broken at the aux-pair gates: unity-gain frequency and phase margin at 5 corners"
python3 designs/r1-joint/blocks/r1_isense/sim/analyze_azloop.py "$G1_RESULTS_ROOT/r1_isense/isense-azloop-20261020-r1" designs/r1-joint/blocks/r1_isense/sim/results/isense-azloop-20261020-r1
python3 $R --block r1_isense --deck tb_isense_droop.cir --run-id isense-droop-20261020-r1 --corners tt,ss,ff_hot --jobs 2 --analyze analyze_droop.py --question "Hold droop: drift of the zero-current output over one 50 us PWM period after AZ (input-referred), gmin 1e-15"
python3 $R --block r1_isense --deck tb_isense_droop.cir --run-id isense-droop-150C-20261020-r1 --corners ff_hot,ss --set TEMP=150 --jobs 2 --analyze analyze_droop.py --question "Hold droop as isense-droop-20261020-r1 at 150 C junction temperature (TEMP override of the ff_hot and ss corners)"
# droop: re-analysed from the full-precision waveforms (the in-deck echo prints 6 digits only)
for r in isense-droop-20261020-r1 isense-droop-150C-20261020-r1; do
  python3 designs/r1-joint/blocks/r1_isense/sim/analyze_droop.py "$G1_RESULTS_ROOT/r1_isense/$r" designs/r1-joint/blocks/r1_isense/sim/results/$r
done
echo ISENSE_FU_DONE
