. "$(dirname "$0")/common.sh"
waitrun postb7-dsw-nor-ffm40
FF="--corner mos_ff --temp -40 --vdd 1.32"
P="--deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045"
# D23 drift sweep, level 2: wiring R kept only on one net group (all other wiring R 0.05 Ohm), tt and ff
for v in sup cmp sw; do
  N=sim/post/b7/diag_mb7_ronly_$v.spice beh postb7-dsw-ronly-$v-tt 104 $P --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "D23 drift sweep: wiring R only on group $v (sim/post/b7/campaign/README groups), first conversion 0 V at tt" --disposition "diagnostic only"
  N=sim/post/b7/diag_mb7_ronly_$v.spice beh postb7-dsw-ronly-$v-ffm40 104 $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --question "D23 drift sweep: wiring R only on group $v, first conversion 0 V at ff / -40 C / 1.32 V" --disposition "diagnostic only"
done
echo sweep104 done
beh postb7-inla-tt-rc 104 --deck points --ref lay-ideal --vref 1.045 --points sim/r5/points/inlramp5a.json --question "post-layout RC (layout B7 = B6 extraction): reduced INL ramp half a, tt, ideal VREF 1.045 V" --disposition "post-layout value (INL bow tt, layout B7)"
echo chain104d done
