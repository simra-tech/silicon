#!/bin/sh
# qrc4.sh: tt queue now on CPU 104; ss125 queue on CPU 105 after the rc3 ss125 queue has ended (log line QUEUE END)
cd "$(dirname "$0")"
L=$G1_RESULTS_ROOT/r1_adc
sh run_qpost.sh 104 sim/post/jobs_rc4_tt.txt > $L/post-qrc4-tt.log 2>&1 &
until grep -q "QUEUE END" $L/post-qrc3-ss125.log; do sleep 20; done
sh run_qpost.sh 105 sim/post/jobs_rc4_ss125.txt > $L/post-qrc4-ss125.log 2>&1
wait
