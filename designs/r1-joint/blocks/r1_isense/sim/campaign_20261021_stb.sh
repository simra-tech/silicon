#!/bin/sh
# r1_isense stb suite (T4 follow-up c, 2026-10-21): loop gain (Tian double injection, as r1_afe) in the normal state
# and the AZ closed state at tt, ss/125 C/3.0 V, ff/-40 C/3.6 V, sf, fs; load sensitivity; comparators at the
# calibration point; shunt step 0 -> 100 mV with a 10 ns edge. Run from the repository root.
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results directory}"; export G1_RESULTS_ROOT
G1_CPUSET=109-110; export G1_CPUSET
S=designs/r1-joint/blocks/r1_isense/sim
R=$S/run_deck.py
python3 $S/gen_tb_isense_stb.py
R1_TAG=c14 R1_THR=14 python3 $S/gen_tb_isense_stb.py
LOAD="--set RL=0.001 --set CL=2p --set CW=0"
python3 $R --block r1_isense --deck tb_isense_stb.cir --pre tb_isense_stbpre.cir --run-id isense-stb-20261021-r1 --corners tt,ss,ff,sf,fs --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "Loop gain (Tian double injection) of the main differential loop, the CM/CMFB loop and the input-gate cross-check in the normal state, at three shunt levels, 5 corners, load = joint path fixture of r1_safe (2 pF per output, two real comparators)"
python3 $R --block r1_isense --deck tb_isense_stbaz.cir --run-id isense-stbaz-20261021-r1 --corners tt,ss,ff,sf,fs --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "Loop gain of the AZ servo (break at the aux-pair gates), the CMFB/CM loop and the output break with the auto-zero closed (az = azh = 1), 5 corners, same load fixture"
python3 $R --block r1_isense --deck tb_isense_stb.cir --pre tb_isense_stbpre.cir --run-id isense-stb-load28-20261021-r1 --corners tt,ss --jobs 2 --set RL=100 --set CL=2.8p --set CW=0.2p --analyze analyze_stb.py \
  --question "Load sensitivity: as isense-stb-20261021-r1 with the r1_afe style ADC load 100 ohm + 2.8 pF + 0.2 pF wiring per output (INTERFACES.md CDAC load)"
python3 $R --block r1_isense --deck tb_isense_stbc14.cir --pre tb_isense_stbpre.cir --run-id isense-stb-c14-20261021-r1 --corners tt,ss --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "Comparator-state sensitivity: as isense-stb-20261021-r1 with both comparators at code 14 (OC) / 49 (NEG), i.e. threshold at the zero-current output, input stage balanced"
python3 $R --block r1_isense --deck tb_isense_stbstep.cir --run-id isense-stbstep-20261021-r1 --corners tt,ss --jobs 2 $LOAD --analyze analyze_stbstep.py \
  --question "Shunt step 0 -> 100 mV with a 10 ns edge after AZ, joint load fixture: settling to 0.5 percent, overshoot count"
echo ISENSE_STB_DONE
