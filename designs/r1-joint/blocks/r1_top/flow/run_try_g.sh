#!/bin/sh
# R1 top-level assembly try g (track T8e): generate, render, LVS reference, checks. POSIX sh, repository root as cwd,
# G1_CPUSET and G1_RESULTS_ROOT exported. One KLayout job at a time.
#   sh designs/r1-joint/blocks/r1_top/flow/run_try_g.sh <run name, e.g. asm-20261028-g1> [steps]
# steps (default all, in this order): gen cdl lvs lvsstock main antenna maximal
# <run>/inputs/ofrecord holds the GDS and CDL snapshots of r1_afe, r1_adc, r1_isense and r1_bias (README "Try g").
# Drop-in of a new block revision (ADC B6 final, AFE E7): replace the file there and export R1G_SHA_<macro> (GDS) /
# R1G_CDL_SHA_<macro> (CDL); see reports/integration_checklist_g.md.
set -u
T=designs/r1-joint/blocks/r1_top
S=$G1_RESULTS_ROOT/r1_top/$1; shift
O=$S/inputs/ofrecord
STEPS=${*:-gen cdl lvs lvsstock main antenna maximal}
F=$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261027_t22/flow/runs/r1ctrl_ll_20261027_t22/final
mkdir -p "$S/cdl"
for st in $STEPS; do
  echo "step $st start $(date -u +%H:%M:%S)" >> "$S/steps.log"
  case $st in
    gen) flow/run.sh env R1G_NOMAZE="${R1G_NOMAZE:-}" R1G_NO_SFEED="${R1G_NO_SFEED:-}" R1G_NO_SSTACK="${R1G_NO_SSTACK:-}" R1G_STRAP6="${R1G_STRAP6:-}" R1G_SHA_r1_adc="${R1G_SHA_r1_adc:-}" R1G_SHA_r1_afe="${R1G_SHA_r1_afe:-}" \
           python3 $T/layout/r1_top_assemble_g.py "$G1_RESULTS_ROOT" "$S" "$O" > "$S/gen.log" 2>&1
         flow/run.sh python3 $T/layout/r1_top_png.py "$S/r1_top.gds" "$S/r1_top.png" 760 1700 >> "$S/gen.log" 2>&1 ;;
    cdl) flow/run.sh python3 $T/lvs/pnl2cdl.py "$F/pnl/r1_ctrl_top.pnl.v" "$S/cdl/r1_ctrl_top.cdl" \
           /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl > "$S/cdl/cdl.log" 2>&1
         flow/run.sh env R1G_CDL_SHA_r1_adc="${R1G_CDL_SHA_r1_adc:-}" R1G_CDL_SHA_r1_afe="${R1G_CDL_SHA_r1_afe:-}" \
           python3 $T/lvs/make_top_cdl_g.py "$S/r1_top_assembly.json" \
           "$S/cdl/r1_ctrl_top.cdl" "$S/cdl/r1_top.cdl" "$S/cdl/r1_top_cdl.json" "$O" >> "$S/cdl/cdl.log" 2>&1 ;;
    lvs) sh $T/lvs/run_lvs_top.sh "$S/r1_top.gds" "$S/cdl/r1_top.cdl" "$S/lvs_limits" limits
         flow/run.sh klayout -b -r $T/flow/lvs_report.py -rd db="$S/lvs_limits/out/r1_top.lvsdb" -rd n=80 \
           > "$S/lvs_limits/report.txt" 2>&1 ;;
    lvsstock) sh $T/lvs/run_lvs_top.sh "$S/r1_top.gds" "$S/cdl/r1_top.cdl" "$S/lvs_stock" stock
         flow/run.sh klayout -b -r $T/flow/lvs_report.py -rd db="$S/lvs_stock/out/r1_top.lvsdb" -rd n=80 \
           > "$S/lvs_stock/report.txt" 2>&1 ;;
    main|antenna|density|maximal) sh $T/flow/run_drc_set.sh "$S" $st
         flow/run.sh python3 $T/flow/drc_summary.py "$S/r1_top_assembly.json" "$S/drc_$st/summary.json" \
           "$S"/drc_$st/*.lyrdb > "$S/drc_$st/summary.txt" 2>&1 ;;
  esac
  echo "step $st end $(date -u +%H:%M:%S)" >> "$S/steps.log"
done
echo done >> "$S/steps.log"
