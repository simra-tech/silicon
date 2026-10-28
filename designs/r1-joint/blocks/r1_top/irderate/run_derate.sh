#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# T8g ctrl IR derate (method of T11b / T8f h0): characterize the 4 cells at 1.08 V / 1.32 V minus the four extracted
# losses of a supply json, derate factors, OpenSTA cases (uniform worst, mean cell, grid spread; fast bound), parse.
# repository root, POSIX shell. args: <derate run name> <supply json> <cpuset a> <cpuset b>
: "${G1_RESULTS_ROOT:?export G1_RESULTS_ROOT}"; G1_WORKDIR=.; export G1_WORKDIR
N=$1; SJ=$2; CA=$3; CB=$4
R=$G1_RESULTS_ROOT/r1_top/$N; C=$G1_RESULTS_ROOT/r1_ctrl; I=designs/r1-joint/blocks/r1_top/irderate
G3=$G1_RESULTS_ROOT/r1_top/r1ctrl_irderate_g3
mkdir -p $R/sta
LOSS=$(python3 -c "
import json,sys; s=json.load(open('$SJ'))['summary']
print(json.dumps({'typ_worst': round(s['typ']['ctrl_loss_worst_mV']/1e3,5), 'max_worst': round(s['max']['ctrl_loss_worst_mV']/1e3,5), 'typ_best': round(s['typ']['ctrl_loss_best_mV']/1e3,5), 'max_best': round(s['max']['ctrl_loss_best_mV']/1e3,5)}))")
echo "$LOSS" > $R/loss_V.json
VS=$(python3 -c "import json; l=json.load(open('$R/loss_V.json')); print(','.join(['1.08']+['%.4f'%(1.08-v) for v in l.values()]))")
VF=$(python3 -c "import json; l=json.load(open('$R/loss_V.json')); print(','.join(['1.32']+['%.4f'%(1.32-v) for v in l.values()]))")
echo "ss $VS ff $VF" > $R/voltages.txt
(G1_CPUSET=$CA; export G1_CPUSET; flow/run.sh python3 $I/char_cells.py $R/char_ss ss125 $VS 180 > $R/char_ss.console 2>&1) &
(G1_CPUSET=$CB; export G1_CPUSET; flow/run.sh python3 $I/char_cells.py $R/char_ff ff-40 $VF 180 > $R/char_ff.console 2>&1) &
wait
echo "char done" > $R/char.done
G1_CPUSET=$CA; export G1_CPUSET
flow/run.sh env R1_IRDERATE_LOSS="$LOSS" python3 $I/derate.py factors $R/factors.json 1.08 $R/char_ss/char_ss125.json $G3/char_ss_a/char_ss125.json > $R/factors.console 2>&1
flow/run.sh env R1_IRDERATE_LOSS="$LOSS" python3 $I/derate.py factors $R/factors_ff.json 1.32 $R/char_ff/char_ff-40.json $G3/char_ff/char_ff-40.json > $R/factors_ff.console 2>&1
CASES=$(python3 -c "
import json; p=json.load(open('$R/factors.json'))['points']
print('base:1.0:1.0 U_typ:%.4f:%.4f U_max:%.4f:%.4f U_max_meancell:%.4f:%.4f OCV_typ:%.4f:%.4f OCV_max:%.4f:%.4f' % (
 p['typ_worst']['F_worst'],p['typ_worst']['F_worst'],p['max_worst']['F_worst'],p['max_worst']['F_worst'],p['max_worst']['F_mean'],p['max_worst']['F_mean'],
 p['typ_best']['F_worst'],p['typ_worst']['F_worst'],p['max_best']['F_worst'],p['max_worst']['F_worst']))")
CASESF=$(python3 -c "
import json; p=json.load(open('$R/factors_ff.json'))['points']
print('base:1.0:1.0 U_max:%.4f:%.4f OCV_max:%.4f:%.4f OCV_bound:1.0:%.4f' % (p['max_worst']['F_worst'],p['max_worst']['F_worst'],p['max_best']['F_worst'],p['max_worst']['F_worst'],p['max_worst']['F_worst']))")
echo "slow $CASES" > $R/cases.txt; echo "fast $CASESF" >> $R/cases.txt
ARGS="NETLIST=$C/r1ctrl_08_release/r1_ctrl_top.nl.v SDC=$C/r1ctrl_08_release/r1_ctrl_signoff.sdc SPEF=$C/r1ctrl_ll_20261027_t22/flow/runs/r1ctrl_ll_20261027_t22/final/spef/nom/r1_ctrl_top.nom.spef"
G1_CPUSET=$CA,$CB; export G1_CPUSET
flow/run.sh env LIBNAME=slow_1p08V_125C $ARGS CASES="$CASES" sta -no_splash -exit $I/sta_derate.tcl > $R/sta/derate_slow_1p08V_125C.rpt 2>&1
echo "slow rc $?" >> $R/sta.done
flow/run.sh env LIBNAME=fast_1p32V_m40C $ARGS CASES="$CASESF" sta -no_splash -exit $I/sta_derate.tcl > $R/sta/derate_fast_1p32V_m40C.rpt 2>&1
echo "fast rc $?" >> $R/sta.done
flow/run.sh python3 $I/sta_parse.py $R/sta/derate_slow_1p08V_125C.rpt > $R/sta/derate_summary.json
flow/run.sh python3 $I/sta_parse.py $R/sta/derate_fast_1p32V_m40C.rpt > $R/sta/derate_fast_summary.json
echo done >> $R/sta.done
