#!/bin/sh
# B10 layout checks on CPU 104 (repo root): DRC main+maximal, antenna, LVS comparer-limit and stock (B5 CDL with the SAR),
# pin check, XOR of the top cell against B7. Usage: sh chain_chk104.sh <dev tag>
cd "$(dirname "$0")/../../../../../../../.."
: "${G1_RESULTS_ROOT:?}"; export G1_RESULTS_ROOT
T=$1; G=$G1_RESULTS_ROOT/r1_adc/layout-b10-$T/r1_adc.gds
G1_CPUSET=104; export G1_CPUSET
G1_WORKDIR=designs/r1-joint/blocks/r1_adc/layout; export G1_WORKDIR
flow/run.sh sh run_checks.sh layout-b10-$T drc $G; echo "drc rc $?"
flow/run.sh sh run_checks.sh layout-b10-${T}a ant $G; echo "ant rc $?"
unset G1_WORKDIR
sh designs/r1-joint/blocks/r1_adc/layout/b5/run_lvs_b5.sh lvs-b10-$T-lim $G limits; echo "lvs lim rc $?"
sh designs/r1-joint/blocks/r1_adc/layout/b5/run_lvs_b5.sh lvs-b10-$T-stock $G stock; echo "lvs stock rc $?"
G1_WORKDIR=designs/r1-joint/blocks/r1_adc/layout; export G1_WORKDIR
mkdir -p ../reports/layout-b10-$T 2>/dev/null
flow/run.sh klayout -b -r b5/check_pins_b5.py -rd gds=$G -rd out=../reports/layout-b10-$T/pin_table_b10.md > $G1_RESULTS_ROOT/r1_adc/layout-b10-$T/pins.log 2>&1; echo "pins rc $?"
echo "chain done"
