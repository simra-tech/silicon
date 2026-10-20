#!/bin/sh
# run_windows.sh <tag> <corner> <temp> <vdd> <cpus...>
# Static ramp windows around the major code transitions (lower half; the circuit is symmetric at nominal):
# centre codes 512 1024 1536 1984 2048, +/-12 codes, 0.25 LSB (142 uV) per frame, 96 frames per window.
# One window per run; runs are spread round-robin over the CPUs given (one CPU each).
TAG=$1; CORNER=$2; TEMP=$3; VDD=$4; shift 4
cd "$(dirname "$0")/.."
set -- $@
NCPU=$#
CPUS="$*"
i=0
for C in 512 1024 1536 1984 2048; do
  CPU=$(echo $CPUS | cut -d' ' -f$(( (i % NCPU) + 1 )))
  V0=$(python3 -c "print('%.6f' % (($C - 2048 - 12) * 568e-6))")
  python3 sim/run_ngspice.py --deck sim/tb_adc_static.cir --run-id win-$TAG-c$C --cpuset $CPU \
    --sub CORNER=$CORNER --sub TEMP=$TEMP --sub VDD=$VDD --sub VREF=$VDD --sub VSTART=$V0 --sub VSTEP=142e-6 \
    --sub TSTOP=97.2u --sub CORE=r1_adc_core_fast_a --sub TMAX=5n \
    --sub "OPTS=reltol=1e-3 vntol=1e-6 abstol=1e-12 method=trap klu" --timeout 20000 \
    --question "static window around code $C ($CORNER, $TEMP C, VDD $VDD): DNL at a major transition, 0.25 LSB steps" &
  i=$((i+1))
done
wait
