# what-if helper (sourced after common.sh): wif <variant> <cpu> <corner tag tt|ffm40|ss125>
# Deck of the B7 drift diagnosis / B8 strap target: first conversion 0 V, behavioural SAR, ideal VREF 1.045 V on the
# slice ports (lay-ideal), pre33 timing. Limit: measured 1523 s for postb8-drs03-cmp-ffm40 on CPU 105, x2.4 -> 3600 s.
wif() {
  v=$1; cpu=$2; c=$3
  case $c in
    tt) CF="--timing r1_adc_timing_r5_n0_cq_pre33.inc"; CQ="tt" ;;
    ffm40) CF="--corner mos_ff --temp -40 --vdd 1.32 --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc"; CQ="ff / -40 C / 1.32 V" ;;
    ss125) CF="--corner mos_ss --temp 125 --vdd 1.08 --timing r1_adc_timing_r5_n0_cq_vdd108_pre33.inc"; CQ="ss / 125 C / 1.08 V" ;;
  esac
  N=sim/post/b10/wif_mb7_$v.spice beh postb10-wif-$v-$c $cpu --deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045 \
    $CF --timeout 3600 --question "B10 per-net R what-if (D30 item 3): B7 extraction, variant $v (sim/post/b10/wif_mb7_$v.spice header), first conversion 0 V at $CQ" --disposition "diagnostic only"
}
