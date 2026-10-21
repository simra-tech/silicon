RUN=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7; export RUN
for c in typ_1p20V_25C fast_1p32V_m40C slow_1p08V_125C; do LIBNAME=$c; export LIBNAME; sta -no_splash -exit sim/signoff/sta_borrow.tcl > "$1/sta_borrow_$c.rpt" 2>&1; done
