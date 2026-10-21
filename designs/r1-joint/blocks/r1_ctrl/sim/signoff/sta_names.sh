RUN=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7; export RUN
sta -no_splash -exit sim/signoff/sta_names.tcl > "$1" 2>&1
