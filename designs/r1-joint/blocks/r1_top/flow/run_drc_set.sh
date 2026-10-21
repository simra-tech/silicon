#!/bin/sh
# Chip-level DRC set for r1_top (track T8). POSIX sh, repository root as cwd, G1_CPUSET and G1_RESULTS_ROOT exported.
#   sh designs/r1-joint/blocks/r1_top/flow/run_drc_set.sh <run_dir with r1_top.gds> <check> [<check> ...]
# checks: main maximal density antenna. Stock PDK decks, unmodified; same switches as the r1_padring sign-off.
set -u
S=$1; shift
G=$S/r1_top.gds
D=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech
for c in "$@"; do
  mkdir -p "$S/drc_$c"
  case $c in
    main)    flow/run.sh python3 $D/drc/run_drc.py --path=$G --topcell=r1_top --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$S/drc_main ;;
    maximal) flow/run.sh python3 designs/r1-joint/blocks/r1_padring/flow/run_maximal.py $G r1_top $S/drc_maximal 4 ;;
    density) flow/run.sh python3 $D/drc/run_drc.py --path=$G --topcell=r1_top --run_mode=deep --density_thr=4 --density_only --run_dir=$S/drc_density ;;
    antenna) flow/run.sh python3 $D/drc/run_drc.py --path=$G --topcell=r1_top --run_mode=deep --density_thr=4 --antenna_only --run_dir=$S/drc_antenna --antenna ;;
  esac > "$S/drc_$c/console.log" 2>&1
  echo "exit $?" >> "$S/drc_$c/console.log"
done
