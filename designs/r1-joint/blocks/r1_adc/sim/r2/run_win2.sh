#!/bin/sh
# run_win2.sh <tag> <corner> <temp> <vdd> <timing> <cpu> <half_codes> <frames_per_lsb> <centre codes...>
# Revision-2 static windows (slice A, fast core, ideal VREF 1.0 V), run one after the other on one CPU.
# LSB used to place the windows: 454 uV (full scale +-0.93 V from run r2-dbg-quick-cmpB; refined by the ramp).
TAG=$1; CORNER=$2; TEMP=$3; VDD=$4; TIM=$5; CPU=$6; HC=$7; FPL=$8; shift 8
cd "$(dirname "$0")/../.."
for C in "$@"; do
  V0=$(python3 -c "print('%.6f' % (($C - 2048 - $HC) * 454e-6))")
  VS=$(python3 -c "print('%.4e' % (454e-6 / $FPL))")
  NF=$((2 * HC * FPL))
  TS=$(python3 -c "print('%.3fu' % (0.6 + $NF + 0.1))")
  python3 sim/run_ngspice.py --deck sim/r2/tb_adc2_static.cir --run-id r2-win-$TAG-c$C --cpuset $CPU \
    --sub CORNER=$CORNER --sub TEMP=$TEMP --sub VDD=$VDD --sub VREF=1.0 --sub VSTART=$V0 --sub VSTEP=$VS \
    --sub TSTOP=$TS --sub CORE=r1_adc2_core_fast_a --sub TIMING=$TIM --sub TMAX=0.2n \
    --sub "OPTS=reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12" --timeout 7200 \
    --question "revision-2 static window around code $C ($CORNER, $TEMP C, VDD $VDD): DNL, $FPL frames per LSB"
done
