. "$(dirname "$0")/common.sh"
waitrun postb6-win3072-tt-rc
FF="--corner mos_ff --temp -40 --vdd 1.32"
P="--deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045"
# D23 drift diagnosis: which variable of the ff corner moves the offset (process, temperature, VDD), and is it R or C
beh postb7-ddec-ff27-v12 104 $P --corner mos_ff --temp 27 --vdd 1.2 --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "D23 drift diagnosis: B7 extraction, ff process only (27 C, 1.2 V), first conversion 0 V" --disposition "diagnostic only"
beh postb7-ddec-ttm40-v12 104 $P --corner mos_tt --temp -40 --vdd 1.2 --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "D23 drift diagnosis: B7 extraction, -40 C only (tt, 1.2 V), first conversion 0 V" --disposition "diagnostic only"
beh postb7-ddec-tt27-v132 104 $P --corner mos_tt --temp 27 --vdd 1.32 --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --question "D23 drift diagnosis: B7 extraction, VDD 1.32 V only (tt, 27 C), first conversion 0 V" --disposition "diagnostic only"
for v in noc nor; do
  N=sim/post/b7/diag_mb7_$v.spice beh postb7-dsw-$v-tt 104 $P --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "D23 drift diagnosis: B7 extraction variant $v (noc: no parasitic C; nor: every wiring R 0.05 Ohm), first conversion 0 V at tt" --disposition "diagnostic only"
  N=sim/post/b7/diag_mb7_$v.spice beh postb7-dsw-$v-ffm40 104 $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --question "D23 drift diagnosis: B7 extraction variant $v, first conversion 0 V at ff / -40 C / 1.32 V" --disposition "diagnostic only"
done
echo diag104 done
beh postb7-inla-tt-rc 104 --deck points --ref lay-ideal --vref 1.045 --points sim/r5/points/inlramp5a.json --question "post-layout RC (layout B7 = B6 extraction): reduced INL ramp half a, tt, ideal VREF 1.045 V" --disposition "post-layout value (INL bow tt, layout B7)"
echo chain104c done
