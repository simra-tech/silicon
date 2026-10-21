#!/bin/sh
# r1_isense REVISION 2 regression campaign (2026-10-21, suffix 20261021r2): every revision-1 row of the README regression
# list, re-run on the frozen revision-2 netlist (schematic/r1_isense.spice, sha256 af013b95f5fd...), plus the new
# rows (cross corners ssx/ffx, state az = 1 / azh = 0, CM-step criterion, MC of the output CM) and the joint path with
# r1_safe. Run from the repository root:  sh designs/r1-joint/blocks/r1_isense/sim/campaign_20261021r2.sh
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results directory}"; export G1_RESULTS_ROOT
G1_CPUSET=109-111; export G1_CPUSET
S=designs/r1-joint/blocks/r1_isense/sim
R=$S/run_deck.py
X=20261021r2
C5=tt,ss,ff,ss_cold,ff_hot
C7=tt,ss,ff,sf,fs,ssx,ffx
LOAD="--set RL=0.001 --set CL=2p --set CW=0"
test "$(sha256sum designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice | cut -c1-12)" = af013b95f5fd || { echo "netlist is not the frozen revision 2"; exit 1; }
python3 $S/gen_tb_isense_azloop.py
python3 $S/gen_tb_isense_stb.py
R1_TAG=c14 R1_THR=14 python3 $S/gen_tb_isense_stb.py
# --- revision-1 campaign rows (2026-10-20)
python3 $R --block r1_isense --deck tb_isense_step.cir --run-id isense-step-$X --corners $C5 --set VCMIN=0 --analyze analyze_step.py \
  --question "REV2 regression: settling to 0.5 % within 300 ns after 100 mV / 120 mV PWM edges, overload recovery, output node range, 5 corners"
python3 $R --block r1_isense --deck tb_isense_dc.cir --run-id isense-dc-$X --corners $C5 --set VCMIN=0 --analyze analyze_dc.py \
  --question "REV2 regression: gain, pedestal, residual offset after AZ, INL over -20..100 mV, 5 corners, Kelvin CM 0 V"
python3 $R --block r1_isense --deck tb_isense_dc.cir --run-id isense-dc-cmm100-$X --corners tt --set VCMIN=-0.1 --analyze analyze_dc.py \
  --question "REV2 regression: as isense-dc at tt with Kelvin common mode -0.1 V"
python3 $R --block r1_isense --deck tb_isense_dc.cir --run-id isense-dc-cmp100-$X --corners tt --set VCMIN=0.1 --analyze analyze_dc.py \
  --question "REV2 regression: as isense-dc at tt with Kelvin common mode +0.1 V"
python3 $R --block r1_isense --deck tb_isense_noise.cir --run-id isense-noise-$X --corners $C5 --set VH=0.93 --analyze analyze_noise.py \
  --question "REV2 regression: closed-loop bandwidth (>= 1 MHz), peaking, input noise, CM and supply rejection, 5 corners"
python3 $R --block r1_isense --deck tb_isense_mc.cir --run-id isense-mc-$X --corners tt_mm_s1,tt_mm_s2 --jobs 2 --set N=25 --analyze analyze_mc.py \
  --question "REV2 regression: mismatch MC, 50 samples (2 seeds x 25), tt: residual offset after AZ (<= 100 uV), pedestal, gain; output CM (new)"
python3 $R --block r1_isense --deck tb_isense_mc.cir --run-id isense-mc-ssff-$X --corners ss_mm_s4,ff_mm_s5 --jobs 2 --set N=30 --analyze analyze_mc.py \
  --question "REV2 regression: mismatch MC at ss 125 C (seed 4) and ff -40 C (seed 5), 30 samples each; output CM (new)"
python3 $R --block r1_isense --deck tb_isense_azloop.cir --run-id isense-azloop-$X --corners $C5 --question "REV2 regression: return ratio of the auto-zero loop during AZ hold, 5 corners"
python3 $S/analyze_azloop.py "$G1_RESULTS_ROOT/r1_isense/isense-azloop-$X" $S/results/isense-azloop-$X
python3 $R --block r1_isense --deck tb_isense_droop.cir --run-id isense-droop-$X --corners tt,ss,ff_hot --analyze analyze_droop.py --question "REV2 regression: hold droop over one 50 us PWM period after AZ, gmin 1e-15"
python3 $R --block r1_isense --deck tb_isense_droop.cir --run-id isense-droop-150C-$X --corners ff_hot,ss --set TEMP=150 --jobs 2 --analyze analyze_droop.py --question "REV2 regression: hold droop at 150 C (TEMP override)"
# --- stb suite (2026-10-21 follow-up c) and the revision-2 additions
python3 $R --block r1_isense --deck tb_isense_stb.cir --pre tb_isense_stbpre.cir --run-id isense-stb-$X --corners $C7 $LOAD --analyze analyze_stb.py \
  --question "REV2: loop gain (Tian), normal state, main DM, CM/CMFB and input-gate cross-check, 3 shunt levels, 7 corners incl. ssx/ffx, joint load fixture"
python3 $R --block r1_isense --deck tb_isense_stbaz.cir --run-id isense-stbaz-$X --corners $C7 $LOAD --analyze analyze_stb.py \
  --question "REV2: loop gain with the auto-zero closed (az = azh = 1): AZ servo, CM/CMFB loop, 7 corners"
python3 $R --block r1_isense --deck tb_isense_stbazi.cir --pre tb_isense_stbpre.cir --run-id isense-stbazi-$X --corners $C7 $LOAD --analyze analyze_stb.py \
  --question "REV2 (new): loop gain in the intermediate state az = 1, azh = 0 (RF arms at VCM, hold open), 7 corners"
python3 $R --block r1_isense --deck tb_isense_stb.cir --pre tb_isense_stbpre.cir --run-id isense-stb-load28-$X --corners tt,ss --jobs 2 --set RL=100 --set CL=2.8p --set CW=0.2p --analyze analyze_stb.py \
  --question "REV2 regression: load sensitivity, ADC load 100 ohm + 2.8 pF + 0.2 pF per output"
python3 $R --block r1_isense --deck tb_isense_stbc14.cir --pre tb_isense_stbpre.cir --run-id isense-stb-c14-$X --corners tt,ss --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "REV2 regression: comparators at the calibration point (code 14 / 49)"
python3 $R --block r1_isense --deck tb_isense_stbstep.cir --run-id isense-stbstep-$X --corners tt,ss --jobs 2 $LOAD --analyze analyze_stbstep.py \
  --question "REV2 regression: shunt step 0 -> 100 mV, 10 ns edge, after AZ, joint load fixture: settling to 0.5 percent, overshoot count"
python3 $R --block r1_isense --deck tb_isense_stbcm.cir --run-id isense-stbcm-$X --corners $C7 $LOAD --analyze analyze_stbcm.py \
  --question "REV2: VCM reference step +20 mV after AZ: at most one overshoot beyond 2 %, settled to 2 % within 300 ns, 7 corners"
# --- joint path with r1_safe (path fixture, both channels), same deck and r1_safe netlist as safe-joint-20261020-r3b
R1_DECK=tb_safe_joint3 python3 $R --block r1_safe --deck tb_safe_joint3.cir --run-id safe-joint-$X --corners tt,ss_cold,ff_hot --analyze analyze_joint3.py \
  --netlist designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice \
  --question "REV2 regression: joint r1_isense revision 2 -> r1_safe rev 3 (path fixture, both channels): threshold centres, simultaneous vs staggered, delays, cross-channel kickback; compare with safe-joint-20261020-r3b (limits: centre within 0.05 LSB, delays within 20 ns)"
echo ISENSE_R2_DONE
