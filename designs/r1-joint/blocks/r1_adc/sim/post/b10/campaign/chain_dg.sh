#!/bin/sh
# B10 dev1 offset diagnosis (tt, first conversion 0 V, ideal VREF, behavioural SAR): usage chain_dg.sh <variant> <cpu> <corner>
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/wif.sh"
v=$1; cpu=$2; c=$3
case $c in tt) CF="--timing r1_adc_timing_r5_n0_cq_pre33.inc";; ffm40) CF="--corner mos_ff --temp -40 --vdd 1.32 --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc";; esac
N=sim/post/b10/dg_mb10_$v.spice beh postb10-dg-$v-$c $cpu --deck points --points sim/r5/points/fixtt.json --ref lay-ideal --vref 1.045 \
  $CF --timeout 3600 --question "B10 offset diagnosis: variant $v of the B10 extraction (sim/post/b10/dg_mb10_$v.spice header), first conversion 0 V at $c" --disposition "diagnostic only"
