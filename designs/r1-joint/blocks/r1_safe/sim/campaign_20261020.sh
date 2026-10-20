#!/bin/sh
# r1_safe evidence campaign 2026-10-20 (schematic level). Run from the repository root.
# Revision 1 (undegenerated input pairs) was run as safe-cmp-20261020-r1 (failed, kept as a record).
# Revision 2 (source-degenerated input pairs, this netlist):
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the bulk results directory}"; export G1_RESULTS_ROOT
R=designs/r1-joint/blocks/r1_safe/sim/run_deck.py
G1_CPUSET=109-111; export G1_CPUSET
python3 $R --block r1_safe --deck tb_safe_dcmc.cir --run-id safe-dcmc-20261020-r2 --corners tt_mm_s1,tt_mm_s2,tt_mm_s3 --set N=17 --analyze analyze_dcmc.py \
  --question "DC mismatch MC of r1_safe_cmp (revision 2, degenerated pairs), 51 samples, tt 27 C, thresholds +16.7/+916.7/-916.7 mV Vod: threshold (hysteresis centre) error and hysteresis"
python3 $R --block r1_safe --deck tb_safe_cmp.cir --run-id safe-cmp-20261020-r2 --corners tt,ss,ff --analyze analyze_cmp.py \
  --question "Revision 2: trip/release vs code (4,20,32,44,59) for OC and NEG, hysteresis, delay at 10 % overdrive and at 1 LSB, full four-comparator block, 3 corners"
# Not run: tb_safe_mc.cir (transient MC of the full threshold path, 51 samples). The DC MC above already fails the
# +-0.5 LSB criterion with sigma about 1 LSB; the transient MC is deferred to the next revision.
echo CAMPAIGN_DONE
