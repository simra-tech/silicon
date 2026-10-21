#!/bin/sh
# One assembly try of r1_top (track T8): generate, render, build the LVS reference, check.
# POSIX sh, repository root as cwd, G1_CPUSET and G1_RESULTS_ROOT exported.
#   sh designs/r1-joint/blocks/r1_top/flow/run_try.sh <try name, e.g. asm-20261021-b> [steps]
# steps (default all, in this order): gen cdl lvs main antenna density stock maximal
set -u
T=designs/r1-joint/blocks/r1_top
S=$G1_RESULTS_ROOT/r1_top/$1; shift
STEPS=${*:-gen cdl lvs main antenna density stock maximal}
F=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7/final
mkdir -p "$S/cdl"
for st in $STEPS; do
  echo "step $st start $(date -u +%H:%M:%S)" >> "$S/steps.log"
  case $st in
    gen) flow/run.sh python3 $T/layout/r1_top_assemble.py "$G1_RESULTS_ROOT" "$S" > "$S/gen.log" 2>&1
         flow/run.sh python3 $T/layout/r1_top_png.py "$S/r1_top.gds" "$S/r1_top.png" 760 >> "$S/gen.log" 2>&1 ;;
    cdl) flow/run.sh python3 $T/lvs/pnl2cdl.py "$F/pnl/r1_ctrl_top.pnl.v" "$S/cdl/r1_ctrl_top.cdl" \
           /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl > "$S/cdl/cdl.log" 2>&1
         R1_TOP_ASM_JSON=$S/r1_top_assembly.json; export R1_TOP_ASM_JSON
         flow/run.sh env R1_TOP_ASM_JSON="$R1_TOP_ASM_JSON" python3 $T/lvs/make_top_cdl.py "$S/cdl/r1_ctrl_top.cdl" \
           "$S/cdl/r1_top.cdl" "$S/cdl/r1_top_cdl.json" >> "$S/cdl/cdl.log" 2>&1 ;;
    lvs) sh $T/lvs/run_lvs_top.sh "$S/r1_top.gds" "$S/cdl/r1_top.cdl" "$S/lvs_limits" limits
         flow/run.sh klayout -b -r $T/flow/lvs_report.py -rd db="$S/lvs_limits/out/r1_top.lvsdb" -rd n=60 \
           > "$S/lvs_limits/report.txt" 2>&1 ;;
    stock) sh $T/lvs/run_lvs_top.sh "$S/r1_top.gds" "$S/cdl/r1_top.cdl" "$S/lvs_stock" stock ;;
    main|antenna|density|maximal) sh $T/flow/run_drc_set.sh "$S" $st
         flow/run.sh python3 $T/flow/drc_summary.py "$S/r1_top_assembly.json" "$S/drc_$st/summary.json" \
           "$S"/drc_$st/*.lyrdb > "$S/drc_$st/summary.txt" 2>&1 ;;
  esac
  echo "step $st end $(date -u +%H:%M:%S)" >> "$S/steps.log"
done
echo done >> "$S/steps.log"
