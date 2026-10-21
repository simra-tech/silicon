#!/bin/sh
# Post-layout campaign of r1_isense on the extraction <pex run id> (run_pex.sh). Run from the repo root on the host:
#   G1_CPUSET=...; export G1_CPUSET; G1_RESULTS_ROOT=...; export G1_RESULTS_ROOT
#   sh designs/r1-joint/blocks/r1_isense/layout/pex/run_post.sh <pex run id> <suffix>
# Same decks, loads and analyses as the revision-2 campaign (sim/campaign_20261021r2.sh); only the netlist differs.
# Layout b added the rows after the step run (ss/ff DC, ibias sweep, intermediate AZ state, input-gate cross-check).
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"
P=$G1_RESULTS_ROOT/r1_isense/$1
X=$2
R=designs/r1-joint/blocks/r1_isense/sim/run_deck.py
LOAD="--set RL=0.001 --set CL=2p --set CW=0"
D=$P/decks
N=$P/rc/r1_isense_post.spice
python3 $R --block r1_isense --deck $D/tb_isense_dc.cir --netlist $N --run-id isense-post-dc-$X --corners tt --set VCMIN=0 --analyze analyze_dc.py \
  --question "Post-layout (RC): gain, pedestal, residual offset after AZ, output CM at tt, Kelvin CM 0 V"
for v in _c _r; do
python3 $R --block r1_isense --deck $P/decks$v/tb_isense_dc.cir --netlist $P/rc/r1_isense_post$v.spice --run-id isense-post-dc$v-$X --corners tt --set VCMIN=0 --analyze analyze_dc.py \
  --question "Post-layout split ($v: _c devices + C, _r devices + wiring R): gain, pedestal, offset, output CM at tt"
done
python3 $R --block r1_isense --deck $D/tb_isense_dc.cir --netlist $N --run-id isense-post-dc-cmm100-$X --corners tt --set VCMIN=-0.1 --analyze analyze_dc.py \
  --question "Post-layout (RC): as isense-post-dc at tt with Kelvin common mode -0.1 V (CM rejection with the extracted resistor network)"
python3 $R --block r1_isense --deck $D/tb_isense_dc.cir --netlist $N --run-id isense-post-dc-cmp100-$X --corners tt --set VCMIN=0.1 --analyze analyze_dc.py \
  --question "Post-layout (RC): as isense-post-dc at tt with Kelvin common mode +0.1 V"
python3 $R --block r1_isense --deck $D/tb_isense_stb.cir --pre $D/tb_isense_stbpre.cir --netlist $N --run-id isense-post-stb-$X --corners tt,ffx --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "Post-layout (RC): loop gain (Tian), normal state, DM and CM/CMFB loops, 3 shunt levels, tt and ffx, joint load fixture"
python3 $R --block r1_isense --deck $D/tb_isense_stbaz.cir --netlist $N --run-id isense-post-stbaz-$X --corners tt,ffx --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "Post-layout (RC): loop gain with the auto-zero closed (az = azh = 1): AZ servo and CM/CMFB loop, tt and ffx"
python3 $R --block r1_isense --deck $D/tb_isense_stbstep.cir --netlist $N --run-id isense-post-stbstep-$X --corners tt,ss --jobs 2 $LOAD --analyze analyze_stbstep.py \
  --question "Post-layout (RC): shunt step 0 -> 100 mV, 10 ns edge, after AZ, joint load fixture: settling to 0.5 percent, overshoot count, tt and ss"
# ---- added for layout b (2026-10-21): corners, intermediate AZ state, bias range of r1_bias, input-gate cross-check
python3 $R --block r1_isense --deck $D/tb_isense_dc.cir --netlist $N --run-id isense-post-dc-ssff-$X --corners ss,ff --jobs 2 --set VCMIN=0 --analyze analyze_dc.py \
  --question "Post-layout (RC): gain, pedestal, residual offset after AZ, output CM at ss/125 C and ff/-40 C, ideal PTAT bias"
for ib in 3.5u 5.07u 7.7u; do
python3 $R --block r1_isense --deck $D/tb_isense_dc_ib.cir --netlist $N --run-id isense-post-dc-ib$ib-$X --corners tt,ss,ff --set VCMIN=0 --set IBIAS=$ib --analyze analyze_dc.py \
  --question "Post-layout (RC): gain, pedestal, residual offset after AZ, output CM with ibias = $ib (r1_bias output range 3.5-7.7 uA, INTERFACES.md), tt/ss/ff"
done
python3 $R --block r1_isense --deck $D/tb_isense_stbazi.cir --pre $D/tb_isense_stbpre.cir --netlist $N --run-id isense-post-stbazi-$X --corners tt,ffx --jobs 2 $LOAD --analyze analyze_stb.py \
  --question "Post-layout (RC): loop gain in the intermediate state az = 1, azh = 0 (RF arms at VCM, hold open), tt and ffx"
python3 $R --block r1_isense --deck $D/tb_isense_stbdiag.cir --pre $D/tb_isense_stbpre.cir --netlist $N --run-id isense-post-stbdiag-$X --corners tt,ffx --jobs 2 $LOAD \
  --question "Post-layout (RC): input-gate loop cross-check, Tian return ratio and voltage-only ratio at the same probe, normal state, tt and ffx"
echo ISENSE_POST_DONE
