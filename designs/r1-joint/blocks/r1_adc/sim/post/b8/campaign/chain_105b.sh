. "$(dirname "$0")/common.sh"
# D25 / B8 strap sizing: wiring R of the comparator + supply groups scaled (what-if), first conversion 0 V, tt and ff
P="--deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045"
FF="--corner mos_ff --temp -40 --vdd 1.32"
for v in supcmp cmp; do
beh postb8-drs03-$v-tt 105 sim/post/b8/diag_mb6_rs03_$v.spice $P --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "B8 strap sizing: wiring R of group(s) $v x 0.3, first conversion 0 V at tt" --disposition "diagnostic only"
beh postb8-drs03-$v-ffm40 105 sim/post/b8/diag_mb6_rs03_$v.spice $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --question "B8 strap sizing: wiring R of group(s) $v x 0.3, first conversion 0 V at ff / -40 C / 1.32 V" --disposition "diagnostic only"
done
echo chain105b done
