#!/bin/sh
# run_queue_r4.sh <cpu> <job>...: runs the revision-4 jobs one after the other on CPU <cpu> (netlist frozen,
# sim/r4/FROZEN_NETLIST_SHA256.txt). Job syntax kind:id[:args]. Stops the queue if a job's runner stops.
#   sweep:<id>                    R2-3 / issue 3: ss_sweep64.json at ss/125 C/1.08 V, ideal VREF
#   win:<id>:<corner>:<T>:<V>     static windows cornwin2.json (codes 2048, 3072), ideal VREF
#   mc:<id>:<seed>                MC calibration windows mcwin3.json, 2 instances r1_adc4_core_fast_mc, ideal VREF
#   mux:<id>:<corner>:<T>:<V>     tb_adc4_isa.cir, full core, r1_refbuf4 (chosen option)
#   dyn:<id>:<chunk>              tb_adc4_dyn.cir chunk 0..2 of an N 256 record, 0.85 V, fin 19/256 fs, r1_refbuf4
#   refc:<id>:<corner>:<T>:<V>    R2-4 at a corner: r1_refbuf4 run, then an ideal run at the buffer's VREF
CPU=$1; shift
cd "$(dirname "$0")/../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the results root}"; export G1_RESULTS_ROOT
O="reltol=1e-4 vntol=1e-6 abstol=1e-12 gmin=1e-9 method=trap klu rshunt=1e12"
BUF="Vdda vdda 0 3.3
Vbg vbg 0 1.045
XREF vbg vref vdda 0 r1_refbuf4
Vrl vrefl vref 0"
vt() { case $1 in 1.2) echo "";; 1.08) echo "_vdd108";; 1.32) echo "_vdd132";; esac; }
for J in "$@"; do
  K=$(echo "$J" | cut -d: -f1); ID=$(echo "$J" | cut -d: -f2)
  A3=$(echo "$J" | cut -d: -f3); A4=$(echo "$J" | cut -d: -f4); A5=$(echo "$J" | cut -d: -f5)
  RC=0
  case $K in
    sweep) python3 sim/r4/run_points4.py --id $ID --cpu $CPU --points sim/r4/points/ss_sweep64.json --corner mos_ss \
             --temp 125 --vdd 1.08 --question "R2-3 / open issue 3: 64-input sweep at ss/125 C/1.08 V, ideal VREF: does the redundancy cover the unresolved decision 0 at CM 0.6 V?" \
             --disposition "item 2 evidence (post_sweep4.py)"; RC=$?;;
    win)   python3 sim/r4/run_points4.py --id $ID --cpu $CPU --points sim/r4/points/cornwin2.json --corner $A3 --temp $A4 \
             --vdd $A5 --question "static windows +-6 LSB around codes 2048/3072 at $A3/$A4 C/$A5 V, ideal VREF" \
             --disposition "item 5 evidence (post_win4.py)"; RC=$?;;
    mc)    python3 sim/r4/run_points4.py --id $ID --cpu $CPU --points sim/r4/points/mcwin3.json --mc 2 --seed $A3 \
             --question "R2-11 on the circuit with MIM mismatch: 2 MC instances (4 slices), seed $A3, toggle windows, tt, ideal VREF" \
             --disposition "item 4 evidence (post_win4.py --fit top2)"; RC=$?;;
    mux)   python3 sim/run_ngspice.py --deck sim/r4/tb_adc4_isa.cir --run-id $ID --cpuset $CPU --sub CORNER=$A3 --sub TEMP=$A4 \
             --sub VDD=$A5 --sub TIMING=r1_adc_timing_r4_mux_n0$(vt $A5).inc --sub "OPTS=$O" --sub TMAX=0.2n --sub TSTOP=3.35u \
             --sub "REFLINES=$BUF" --sub "ISAVE=i(vdda)" --timeout 21600 \
             --question "D18 frame sequence e c e e with the full core and r1_refbuf4, $A3/$A4 C/$A5 V"; RC=$?;;
    dyn)   PH=$(python3 -c "T=1/30e6;F=22*T;fin=19/256/F;c=$A3;print('%.6f'%((360*fin*(86*c-1)*F)%360))")
           PHB=$(python3 -c "print('%.6f'%(($PH+90)%360))")
           python3 sim/run_ngspice.py --deck sim/r4/tb_adc4_dyn.cir --run-id $ID --cpuset $CPU --sub CORNER=mos_tt --sub TEMP=27 \
             --sub VDD=1.2 --sub CM=0.6 --sub CORE=r1_adc4_core_fast --sub TIMING=r1_adc_timing_r4_n0.inc --sub "OPTS=$O interp" \
             --sub TMAX=0.2n --sub TSTOP=64.20u --sub AMP=0.85 --sub FIN=$(python3 -c "T=1/30e6;print('%.6f'%(19/256/(22*T)))") \
             --sub PH=$PH --sub PHB=$PHB --sub "REFLINES=$BUF" --sub "SAVE=v(rawa) v(rawb) v(vref)" --timeout 21600 \
             --question "dynamic N 256 chunk $A3 (local frames 1..86 = global 86c..86c+85), 0.85 V, fin 19/256 fs, tt, r1_refbuf4"; RC=$?;;
    refc)  python3 sim/r4/run_points4.py --id $ID-buf --cpu $CPU --points sim/r4/points/ref10.json --ref buf --corner $A3 --temp $A4 \
             --vdd $A5 --save full --question "R2-4 at $A3/$A4 C/$A5 V with r1_refbuf4 (chosen option)" --disposition "R2-4 corner (post_ref4.py)"; RC=$?
           if [ $RC -eq 0 ]; then
             VS=$(python3 -c "
import sys,os; sys.path.insert(0,'sim/r4'); from p4common import read, ts, sample
d,_=read(os.environ['G1_RESULTS_ROOT']+'/r1_adc/$ID-buf/codes.raw'); print('%.5f'%float(sample(d,'v(vref)',ts(5)-0.2e-9)))")
             python3 sim/r4/run_points4.py --id $ID-ideal --cpu $CPU --points sim/r4/points/ref10.json --vref $VS --corner $A3 --temp $A4 \
               --vdd $A5 --save full --question "R2-4 at $A3/$A4 C/$A5 V: ideal VREF at the buffer level $VS V" --disposition "R2-4 corner (post_ref4.py)"; RC=$?
           fi;;
  esac
  echo "job $J rc $RC $(date)"
  [ $RC -ne 0 ] && { echo "queue stopped at $J"; exit 1; }
done
