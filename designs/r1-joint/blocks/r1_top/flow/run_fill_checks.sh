#!/bin/sh
# Checks of the filled r1_top (track T8). POSIX sh, repository root as cwd, G1_CPUSET, G1_RESULTS_ROOT, G1_WORKDIR=. exported.
#   sh designs/r1-joint/blocks/r1_top/flow/run_fill_checks.sh <source run dir> <fill run dir> [steps]
# steps (default all, in this order): density main antenna maximal lvs bondmap
# One KLayout job at a time. <source run dir> supplies the LVS reference (cdl/r1_top.cdl) and the assembly JSON.
set -u
T=designs/r1-joint/blocks/r1_top
SRC=$1; S=$2; shift; shift
STEPS=${*:-density main antenna maximal lvs bondmap}
for st in $STEPS; do
  echo "step $st start $(date -u +%H:%M:%S)" >> "$S/checks_steps.log"
  case $st in
    main|antenna|density|maximal) sh $T/flow/run_drc_set.sh "$S" $st
         flow/run.sh python3 $T/flow/drc_summary.py "$SRC/r1_top_assembly.json" "$S/drc_$st/summary.json" \
           "$S"/drc_$st/*.lyrdb > "$S/drc_$st/summary.txt" 2>&1 ;;
    lvs) sh $T/lvs/run_lvs_top.sh "$S/r1_top.gds" "$SRC/cdl/r1_top.cdl" "$S/lvs_limits" limits
         flow/run.sh klayout -b -r $T/flow/lvs_report.py -rd db="$S/lvs_limits/out/r1_top.lvsdb" -rd n=80 \
           > "$S/lvs_limits/report.txt" 2>&1 ;;
    bondmap) mkdir -p "$S/bondmap"
         SHA=$(sha256sum "$S/r1_top.gds" | cut -d' ' -f1)
         flow/run.sh klayout -b -r designs/r1-joint/padframe/bondplan_r1.py -rd gds="$S/r1_top.gds" \
           -rd src_csv=designs/r1-joint/padframe/bondmap_src_r1_1700.csv -rd out_csv="$S/bondmap/bondmap_chip.csv" \
           -rd out_svg="$S/bondmap/bondplan_chip.svg" -rd out_json="$S/bondmap/bondplan_chip.json" -rd gds_sha=$SHA -rd die_um=1700 \
           > "$S/bondmap/bondplan.log" 2>&1
         flow/run.sh klayout -b -r $T/../r1_padring/flow/verify_bondmap.py -rd g="$S/r1_top.gds" -rd csvf="$S/bondmap/bondmap_chip.csv" \
           -rd out="$S/bondmap/verify_bondmap_chip.json" > "$S/bondmap/verify.log" 2>&1 ;;
  esac
  echo "step $st end $(date -u +%H:%M:%S)" >> "$S/checks_steps.log"
done
echo done >> "$S/checks_steps.log"
