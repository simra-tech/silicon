. "$(dirname "$0")/common.sh"
# after the ff gate-level run on CPU 105: D23 drift sweep, level 2, last group (wiring R only on the nets that are in
# none of the groups sup / cmp / sw: CDAC lines cp/cn, bottom plates bp/bn, SAR outputs, vref/vrefl, inputs, ibias)
until [ -f sim/post/b6/runs/b7-ms-fc-ffm40/run.json ]; do sleep 60; done
FF="--corner mos_ff --temp -40 --vdd 1.32"
P="--deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045"
N=sim/post/b7/diag_mb7_ronly_rest.spice beh postb7-dsw-ronly-rest-ffm40 105 $P $FF --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --question "D23 drift sweep: wiring R only on the rest group (not sup / cmp / sw), first conversion 0 V at ff / -40 C / 1.32 V" --disposition "diagnostic only"
N=sim/post/b7/diag_mb7_ronly_rest.spice beh postb7-dsw-ronly-rest-tt 105 $P --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "D23 drift sweep: wiring R only on the rest group (not sup / cmp / sw), first conversion 0 V at tt" --disposition "diagnostic only"
echo chain105d done
