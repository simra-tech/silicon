. "$(dirname "$0")/common.sh"
# D23 drift sweep, level 3: interaction check at ff (wiring R on the supply and comparator groups together)
until grep -q "chain105d done" $G1_RESULTS_ROOT/r1_adc/b7-campaign-105d.log; do sleep 30; done
FF="--corner mos_ff --temp -40 --vdd 1.32"
P="--deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045"
N=sim/post/b7/diag_mb7_ronly_supcmp.spice beh postb7-dsw-ronly-supcmp-ffm40 105 $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --question "D23 drift sweep: wiring R only on the groups sup + cmp, first conversion 0 V at ff / -40 C / 1.32 V (interaction check)" --disposition "diagnostic only"
echo chain105e done
