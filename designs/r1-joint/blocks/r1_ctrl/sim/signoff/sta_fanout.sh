LL=${LLRUN:-r1ctrl_ll_20261021_t7}; RUN=$G1_RESULTS_ROOT/r1_ctrl/$LL/flow/runs/$LL; export RUN
sta -no_splash -exit ${FANOUT_TCL:-sim/signoff/sta_fanout.tcl} > "$1" 2>&1
