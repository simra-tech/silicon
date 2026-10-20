#!/bin/sh
# run_static.sh <tag> <corner> <temp> <vdd> <vstep> <frames_per_segment> <cpu0> <cpu1> <cpu2>
# Three ramp segments in parallel (one CPU each) from vd = -1.19 V upward; slice-A core, reltol 1e-3, tmax 5 ns.
TAG=$1; CORNER=$2; TEMP=$3; VDD=$4; VSTEP=$5; NF=$6
cd "$(dirname "$0")/.."
i=0
for CPU in $7 $8 $9; do
  V0=$(python3 -c "print('%.6f' % (-1.19 + $i*($NF-6)*$VSTEP))")
  TS=$(python3 -c "print('%.3fu' % (1.2 + $NF - 1))")
  python3 sim/run_ngspice.py --deck sim/tb_adc_static.cir --run-id static-$TAG-s$i --cpuset $CPU \
    --sub CORNER=$CORNER --sub TEMP=$TEMP --sub VDD=$VDD --sub VREF=$VDD --sub VSTART=$V0 --sub VSTEP=$VSTEP \
    --sub TSTOP=$TS --sub CORE=r1_adc_core_fast_a --sub TMAX=5n \
    --sub "OPTS=reltol=1e-3 vntol=1e-6 abstol=1e-12 method=trap klu" --timeout 30000 \
    --question "static ramp segment $i ($CORNER, $TEMP C, VDD $VDD): codes for INL/DNL, lower half plus margin past mid-scale" &
  i=$((i+1))
done
wait
