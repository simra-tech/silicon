#!/bin/sh
# run_queue_r3.sh <cpu> <wait-file> <job>...: waits until <wait-file> exists, then runs the jobs one after the
# other on CPU <cpu>. Job syntax: kind:id:args (kind cal|corn|dyn). Revision-3 campaign helper.
CPU=$1; WAIT=$2; shift 2
cd "$(dirname "$0")/../.."
while [ ! -e "$WAIT" ]; do sleep 10; done
O="reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12"
for J in "$@"; do
  K=$(echo "$J" | cut -d: -f1); ID=$(echo "$J" | cut -d: -f2); A=$(echo "$J" | cut -d: -f3)
  case $K in
    cal)  python3 sim/r3/run_points3.py --id $ID --cpu $CPU --points sim/r3/points/calwin_c$A.json \
            --question "calibration demo window around code $A (tt, ideal VREF)";;
    corn) C=$(echo "$J" | cut -d: -f4); T=$(echo "$J" | cut -d: -f5); V=$(echo "$J" | cut -d: -f6)
          python3 sim/r3/run_points3.py --id $ID --cpu $CPU --points sim/r3/points/cornwin_c$A.json --corner $C \
            --temp $T --vdd $V --timing r1_adc_timing_r3_vdd$(echo $V | tr -d .).inc \
            --question "static window around code $A at $C / $T C / $V V (ideal VREF)";;
    dyn)  python3 sim/run_ngspice.py --deck sim/r3/tb_adc3_dyn.cir --run-id $ID --cpuset $CPU --sub CORNER=mos_tt \
            --sub TEMP=27 --sub VDD=1.2 --sub CM=0.6 --sub CORE=r1_adc3_core_fast --sub TIMING=r1_adc_timing_r3.inc \
            --sub "OPTS=$O interp" --sub TMAX=0.2n --sub TSTOP=20.7u --sub AMP=0.85 --sub FIN=$A \
            --sub "REFLINES=Vref vref 0 1.0" --sub "SAVE=v(rawa) v(rawb)" --timeout 14400 \
            --question "dynamic: sine on A, cosine on B, 0.85 V, fin $A Hz, 33 slots (N 32 used), tt, ideal VREF";;
  esac
done
