#!/bin/sh
# run_dyn2.sh <run-id> <cpu> <M> <N> <amp>: sine on SIN (slice A), cosine on COS (slice B), both slices, fast core
cd "$(dirname "$0")/../.."
ID=$1; CPU=$2; M=$3; N=$4; AMP=$5
FIN=$(python3 -c "print('%.4f' % ($M / $N * 1e6))")
TS=$(python3 -c "print('%.3fu' % (0.6 + $N + 0.1))")
python3 sim/run_ngspice.py --deck sim/r2/tb_adc2_dyn.cir --run-id $ID --cpuset $CPU --sub CORNER=mos_tt --sub TEMP=27 \
  --sub VDD=1.2 --sub VREF=1.0 --sub AMP=$AMP --sub FIN=$FIN --sub TSTOP=$TS --sub CORE=r1_adc2_core_fast \
  --sub TIMING=r1_adc_timing_r2.inc --sub TMAX=5n --sub "OPTS=reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12" \
  --timeout 7200 --question "revision-2 dynamic test, tt, fin $FIN Hz (M $M, N $N), amplitude $AMP V differential peak, both slices"
