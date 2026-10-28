. "$(dirname "$0")/common.sh"
until grep -q "chain103b done" $G1_RESULTS_ROOT/r1_adc/b7-campaign-103b.log; do sleep 60; done
FF="--corner mos_ff --temp -40 --vdd 1.32"
P="--deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045"
# D23 drift sweep (per coupling group, first conversion 0 V): ff against the tt values of README B6 "Offset after the fix"
for v in swt cmp tcmp rgnd0 rsup0; do
  N=sim/post/b6/diag/mb6dev3_$v.spice beh postb7-dsw-$v-ffm40 103 $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc \
    --question "D23 drift sweep: B7 (= B6) extraction variant $v (sim/post/b6/diag), first conversion 0 V at ff / -40 C / 1.32 V" --disposition "diagnostic only"
done
for v in e1clk e2trk e4vdd; do
  N=sim/post/b7/diag_mb7_$v.spice beh postb7-dsw-$v-ffm40 103 $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc \
    --question "D23 drift sweep: B7 extraction, couplings of group $v to the top plates moved to gnd, first conversion 0 V at ff" --disposition "diagnostic only"
  N=sim/post/b7/diag_mb7_$v.spice beh postb7-dsw-$v-tt 103 $P --timing r1_adc_timing_r5_n0_cq_pre33.inc \
    --question "D23 drift sweep: B7 extraction, couplings of group $v to the top plates moved to gnd, first conversion 0 V at tt" --disposition "diagnostic only"
done
echo chain103c done
