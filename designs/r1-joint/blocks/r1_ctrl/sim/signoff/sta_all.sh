# usage (repo root): flow/run.sh sh sim/signoff/sta_all.sh <outdir>
LL=${LLRUN:-r1ctrl_ll_20261021_t7}; RUN=$G1_RESULTS_ROOT/r1_ctrl/$LL/flow/runs/$LL; export RUN
OUT="$1"; mkdir -p "$OUT"
for c in typ_1p20V_25C fast_1p32V_m40C slow_1p08V_125C; do
  CORNER=nom_$c; export CORNER; LIBNAME=$c; export LIBNAME
  sta -no_splash -exit sim/signoff/sta_true.tcl > "$OUT/sta_true_$c.rpt" 2>&1
done
