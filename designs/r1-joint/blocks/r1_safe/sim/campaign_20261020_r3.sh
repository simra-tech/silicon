#!/bin/sh
# r1_safe revision-3 campaign 2026-10-20 (schematic level). Run from the repository root. CPU set 109-111.
# Steps are listed in run order; each is one run_deck.py call (or a python model) and writes sim/results/<run-id>/.
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results directory}"; export G1_RESULTS_ROOT
R=designs/r1-joint/blocks/r1_safe/sim/run_deck.py
S=designs/r1-joint/blocks/r1_safe
G1_CPUSET=109-111; export G1_CPUSET
step="${1:-all}"
if [ "$step" = all ] || [ "$step" = dcmc ]; then
# 1. DC mismatch MC, 51 samples (3 seeds x 17), one draw per sample, 13 cell thresholds: revision 3 and two variants
python3 $R --block r1_safe --deck tb_safe_dcmc3.cir --run-id safe-dcmc-20261020-r3 --corners tt_mm_s1,tt_mm_s2,tt_mm_s3 --set N=17 --set NET=schematic/variants/r1_safe_v_rhigh.spice --analyze analyze_dcmc3.py \
  --question "Revision 3 first state (mirror w40 l10, rhigh degeneration; now variants/r1_safe_v_rhigh.spice; at run time schematic/r1_safe.spice): DC mismatch MC, 51 samples, tt 27 C, 13 cell thresholds per draw: raw centre error vs threshold (input of cal_model.py)"
python3 $R --block r1_safe --deck tb_safe_dcmc3.cir --run-id safe-dcmc-20261020-r3rppd --corners tt_mm_s1,tt_mm_s2,tt_mm_s3 --set N=17 --set NET=schematic/variants/r1_safe_v_rppd.spice --analyze analyze_dcmc3.py \
  --question "Revision 3 with rppd degeneration (w2 l308, about 40 kOhm, +9 400 um2 per block; adopted as the netlist of record): DC mismatch MC, 51 samples, same seeds"
# (a third run with the revision-2 mirror, safe-dcmc-20261020-r3r2cmp, was dropped before it started: CPU budget; not run)
fi
if [ "$step" = all ] || [ "$step" = cal ]; then
# 2. calibration model (python, host): netlist of record first, rhigh state second
python3 $S/sim/cal_model.py $S/sim/results/cal-model-20261020-r3 safe-dcmc-20261020-r3rppd safe-dcmc-20261020-r3
fi
echo CAMPAIGN_STEP_DONE $step
if [ "$step" = all ] || [ "$step" = corner ]; then
# 3. nominal comparator at 5 corners (DC): systematic centre error vs threshold; calibration model per corner
G1_CPUSET=110-111 python3 $R --block r1_safe --deck tb_safe_dcmc3.cir --run-id safe-dccorner-20261020-r3 --corners tt,ss,ff,ss_cold,ff_hot --jobs 2 --set N=1 --set NET=schematic/r1_safe.spice --analyze analyze_dcmc3.py \
  --question "Revision 3 comparator, nominal devices (no mismatch), 5 corners: systematic threshold-centre error and hysteresis vs cell threshold (13 points), input of the calibration model per corner"
python3 $S/sim/cal_model.py $S/sim/results/cal-model-corner-20261020-r3 safe-dccorner-20261020-r3
fi
if [ "$step" = all ] || [ "$step" = mc ]; then
# 4. full-path transient MC (r1_isense -> r1_safe, reduced fixture: ideal tap switches), 30 samples, in-sample calibration
python3 $S/sim/gen_tb_safe_mc3.py
python3 $R --block r1_safe --deck tb_safe_mc3.cir --run-id safe-mc-20261020-r3 --corners tt_mm_s1,tt_mm_s2,tt_mm_s3 --set N=10 --analyze analyze_mc3.py \
  --question "Full-path transient mismatch MC r1_isense -> r1_safe rev 3, 30 samples, tt: in-sample calibration search, then OC thr 54 / NEG thr 9 threshold-centre error (shunt-referred), hysteresis, delay at 10 % overdrive with the codes applied"
fi
if [ "$step" = all ] || [ "$step" = joint ]; then
# 5. joint path with the real r1_isense outputs, full revision-3 netlist, all four comparators switching together and staggered
python3 $R --block r1_safe --deck tb_safe_joint3.cir --run-id safe-joint-20261020-r3 --corners tt,ss_cold,ff_hot --analyze analyze_joint3.py \
  --question "Joint r1_isense -> r1_safe rev 3 (full netlist, nominal): shunt-referred threshold centre at code 44 (k = 32), simultaneous vs staggered switching of all four comparators, delay through r1_isense at 10 % overdrive; tt, ss_cold, ff_hot"
fi
echo CAMPAIGN_STEP_DONE2 $step
if [ "$step" = all ] || [ "$step" = joint2 ]; then
# 6. joint deck with the cross-channel segment (channel b static near threshold while channel a steps), without and
#    with 1 pF MIM decoupling on each reference node (R1_CREF=26: cap_cmim 26 x 26 um)
python3 $S/sim/gen_tb_safe_joint3.py
R1_OUT=tb_safe_joint3_cref.cir R1_CREF=26 python3 $S/sim/gen_tb_safe_joint3.py
G1_CPUSET=109-110 R1_DECK=tb_safe_joint3 python3 $R --block r1_safe --deck tb_safe_joint3.cir --run-id safe-joint-20261020-r3b --corners tt,ss_cold,ff_hot --jobs 2 --analyze analyze_joint3.py \
  --question "Joint r1_isense -> r1_safe rev 3 (path fixture, nominal) with the cross-channel segment: thresholds, simultaneous vs staggered, delay, and kickback from a channel-a step into channel b through the shared string" &
G1_CPUSET=111 R1_DECK=tb_safe_joint3_cref python3 $R --block r1_safe --deck tb_safe_joint3_cref.cir --run-id safe-joint-cref-20261020-r3 --corners tt --analyze analyze_joint3.py \
  --question "Same as safe-joint-20261020-r3b at tt with 1 pF cap_cmim on each comparator reference node (CREF option): does decoupling remove the cross-channel kickback?"
wait
fi
echo CAMPAIGN_STEP_DONE3 $step
# re-analysis of step 6 after the exclusion-window fix (run by hand on 2026-10-20 after the runs):
#   R1_DECK=tb_safe_joint3 python3 $S/sim/analyze_joint3.py $G1_RESULTS_ROOT/r1_safe/safe-joint-20261020-r3b $S/sim/results/safe-joint-20261020-r3b
#   R1_DECK=tb_safe_joint3_cref python3 $S/sim/analyze_joint3.py $G1_RESULTS_ROOT/r1_safe/safe-joint-cref-20261020-r3 $S/sim/results/safe-joint-cref-20261020-r3
